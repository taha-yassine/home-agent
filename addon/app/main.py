import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 6789))

from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager
import httpx
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from openai import AsyncOpenAI
from starlette.middleware.base import BaseHTTPMiddleware

from .tools import get_all_tools
from .api import router as api_router
from .db.base import Base
from .settings import Settings, get_settings


# TODO: Set up
# OpenRouter metadata
# os.environ["OR_SITE_URL"] = "https://github.com/taha-yassine/home-agent"
# os.environ["OR_APP_NAME"] = "home-agent"

_LOGGER = logging.getLogger('uvicorn.error')



def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    if settings is None:
        settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Manage application startup and shutdown events.
        """
        # Startup

        # DB
        settings.db_path.mkdir(parents=True, exist_ok=True)

        db_async_engine = create_async_engine(f"sqlite+aiosqlite:///{settings.db_path / 'home_agent.db'}")
        async_session = async_sessionmaker(bind=db_async_engine, expire_on_commit=False)

        async with db_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # For use with sync trace exporter
        # May need better handling
        db_sync_engine = create_engine(f"sqlite:///{settings.db_path / 'home_agent.db'}")
        
        # Home Assistant
        hass_client = httpx.AsyncClient(
            base_url=settings.ha_api_url,
            headers={"Authorization": f"Bearer {settings.ha_api_key}"},
            verify=False
        )

        # TODO: Optimize tool handling
        tools = get_all_tools()

        # OpenAI client
        openai_client = AsyncOpenAI(api_key="") # API key is required for initialization

        try:
            
            _LOGGER.info("Pinging Home Assistant API...")
            response = await hass_client.get("/")
            response.raise_for_status()
            _LOGGER.info("Home Assistant API is up and running.")

            # Warm up the KV cache if llama.cpp
            # Check LLM backend type
            # openai_client = app.state.openai_client
            # try:
            #     # Remove the /v1 from the base URL
            #     backend_url = str(openai_client.base_url).rstrip('/v1').rstrip('/')
            #     # Reuse the existing OpenAI client
            #     response = await openai_client.with_options(base_url=backend_url).get(
            #         "/health",
            #         cast_to=httpx.Response,
            #         options={}
            #     )
            #     response.raise_for_status()
        
            #     backend_name = response.headers.get("server")
            #     if backend_name.lower() == "llama.cpp":
            #         _LOGGER.info("LLM backend: llama.cpp")

            #         _LOGGER.info("Warming up KV cache...")

            #         tools = app.state.tools
            #         home_state = (await get_mcp_client().call_tool("GetLiveContext", {})).content[0].text # type: ignore
            #         context = { "context": home_state }
            #         prompt = construct_prompt(RunContextWrapper(context=context), None)

            #         try:
            #             warmup_response = await openai_client.chat.completions.create(
            #                 model="whatever",
            #                 messages=[
            #                     {
            #                         "role": "system",
            #                         "content": prompt
            #                     },
            #                     # Adding user message to load the corresponding special tokens
            #                     # "content" can't be empty
            #                     {
            #                         "role": "user",
            #                         "content": " "
            #                     }
            #                 ],
            #                 max_tokens=0 # Still generates 1 token. Good enough.
            #             )
            #             _LOGGER.info(f"Warmup response: {warmup_response}")
            #         except Exception as warmup_err:
            #             _LOGGER.error(f"Failed to warm up llama.cpp: {warmup_err}")

            # except (httpx.RequestError, APIStatusError) as e:
            #     _LOGGER.warning(f"Could not connect to LLM backend at {backend_url}: {e}")
            # except Exception as e:
            #     _LOGGER.error(f"Error during LLM backend check: {e}")
            
            yield {
                "hass_client": hass_client,
                "tools": tools,
                "db": async_session,
                "db_sync_engine": db_sync_engine,
                "openai_client": openai_client,
            }
        finally:
            # Shutdown
            _LOGGER.info("Closing resources...")
            await hass_client.aclose()
            await db_async_engine.dispose()
            db_sync_engine.dispose()
            await openai_client.close()
    
    app = FastAPI(lifespan=lifespan)

    class IngressBaseMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)

            # Only modify HTML responses
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return response

            # Derive base href from HA header or URL path
            base_href = request.headers.get("X-Ingress-Path") or "/"
            if not base_href.startswith("/"):
                base_href = "/" + base_href
            if not base_href.endswith("/"):
                base_href = base_href + "/"

            try:
                body = b""  # type: ignore
                async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                    body += chunk
            except Exception:
                # Fallback if body_iterator is not available
                body = await response.body()

            html = body.decode("utf-8", errors="ignore")

            # If a <base> exists, replace it; else inject right after <head>
            if "<base" in html:
                import re
                html = re.sub(r"<base[^>]*>", f"<base href=\"{base_href}\">", html, count=1)
            else:
                html = html.replace("<head>", f"<head><base href=\"{base_href}\">")

            new_response = Response(
                content=html,
                media_type="text/html; charset=utf-8",
                status_code=response.status_code,
                headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
            )
            return new_response

    app.add_middleware(IngressBaseMiddleware)

    app.include_router(api_router)

    # Frontend
    frontend_dir = Path(__file__).parent.parent / "frontend" / "build" / "client"
    
    app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

    # SPA fallback: serve built files if they exist, otherwise index.html
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        target = (frontend_dir / full_path).resolve()
        # Security: ensure target stays within frontend_dir
        try:
            target.relative_to(frontend_dir.resolve())
        except ValueError:
            # Outside of allowed directory
            return Response(status_code=404)

        if target.is_file():
            return FileResponse(target)
        # For any non-file route (e.g., "/conversations"), serve index.html
        return FileResponse(frontend_dir / "index.html")

    return app


app = create_app()


