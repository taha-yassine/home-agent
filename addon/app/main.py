import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 6789))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager
import httpx
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .tools.hass_tools import get_tools as get_hass_tools
from .api import router as api_router
from .db.base import Base
from .settings import get_settings


# TODO: Set up
# OpenRouter metadata
# os.environ["OR_SITE_URL"] = "https://github.com/taha-yassine/home-agent"
# os.environ["OR_APP_NAME"] = "home-agent"

_LOGGER = logging.getLogger('uvicorn.error')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    # Startup
    settings = get_settings()

    settings.db_path.mkdir(parents=True, exist_ok=True)

    db_async_engine = create_async_engine(f"sqlite+aiosqlite:///{settings.db_path / 'home_agent.db'}")
    async_session = async_sessionmaker(bind=db_async_engine, expire_on_commit=False)

    async with db_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # For use with sync trace exporter
    # May need better handling
    db_sync_engine = create_engine(f"sqlite:///{settings.db_path / 'home_agent.db'}")
    
    hass_client = httpx.AsyncClient(
        base_url=settings.ha_api_url,
        headers={"Authorization": f"Bearer {settings.ha_api_key}"},
        verify=False
    )
    tools = get_hass_tools()

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
            "model_id": settings.model_id,
            "db": async_session,
            "db_sync_engine": db_sync_engine
        }
    finally:
        # Shutdown
        _LOGGER.info("Closing resources...")
        await hass_client.aclose()
        await db_async_engine.dispose()
        db_sync_engine.dispose()




def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(lifespan=lifespan)

    app.include_router(api_router)

    # Frontend
    frontend_dir = Path(__file__).parent.parent / "frontend" / "build" / "client"
    
    app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(frontend_dir / "index.html")

    return app


app = create_app()


