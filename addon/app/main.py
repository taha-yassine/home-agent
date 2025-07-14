import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 6789))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
import httpx
from functools import lru_cache
from pathlib import Path

from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from agents import set_trace_processors

from .tools.hass_tools import get_tools as get_hass_tools
from .api import router as api_router



# TODO: Set up
# OpenRouter metadata
# os.environ["OR_SITE_URL"] = "https://github.com/taha-yassine/home-agent"
# os.environ["OR_APP_NAME"] = "home-agent"

_LOGGER = logging.getLogger('uvicorn.error')

class Settings(BaseSettings):
    """Application settings."""
    app_env: str = "prod"
    llm_server_url: str # URL of the LLM inference server
    llm_server_api_key: str # API key for the LLM inference server
    llm_server_proxy: str | None = None # Proxy for the LLM inference server
    model_id: str = "generic" # ID of the LLM model to use; some backends ignore this
    ha_api_url: str  # Home Assistant API URL
    ha_api_key: str  # Bearer token for Home Assistant authentication
    
    model_config = SettingsConfigDict(
        env_prefix="HOME_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings.
    This function is cached to ensure settings are loaded only once.
    """
    load_dotenv()
    app_env = os.getenv("APP_ENV", "prod")
    if app_env == "prod":
        return Settings(
            ha_api_url="http://supervisor/core/api",
            ha_api_key=os.getenv("SUPERVISOR_TOKEN")
        ) # pyright: ignore
    else:
        return Settings() # pyright: ignore





@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    
    openai_client = AsyncOpenAI(
        base_url=settings.llm_server_url,
        api_key=settings.llm_server_api_key,
        http_client=DefaultAsyncHttpxClient(
            proxy=settings.llm_server_proxy,
            verify=False
        )
    )
    hass_client = httpx.AsyncClient(
        base_url=settings.ha_api_url,
        headers={"Authorization": f"Bearer {settings.ha_api_key}"},
        verify=False
    )
    tools = get_hass_tools()

    try:
        set_trace_processors([])
        
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
            "openai_client": openai_client,
            "hass_client": hass_client,
            "tools": tools,
            "model_id": settings.model_id,
        }
    finally:
        # Shutdown
        _LOGGER.info("Closing resources...")
        await hass_client.aclose()




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


