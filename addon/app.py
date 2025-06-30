import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 6789))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import logging
from contextlib import asynccontextmanager
import httpx

from openai import (
    AsyncOpenAI,
    DefaultAsyncHttpxClient,
    APIStatusError
)
from agents import (
    FunctionTool,
    RunContextWrapper,
    Agent,
    Runner,
    set_trace_processors,
    OpenAIChatCompletionsModel
)

from tools.hass_tools import get_tools as get_hass_tools



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


class AppState:
    """
    Application state that holds shared resources.
    """
    def __init__(self):
        self._settings: Optional[Settings] = None
        self._openai_client: Optional[AsyncOpenAI] = None
        self._hass_client: Optional[httpx.AsyncClient] = None

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            load_dotenv()
            app_env = os.getenv("APP_ENV", "prod")
            if app_env == "prod":
                self._settings = Settings(
                    ha_api_url="http://supervisor/core/api",
                    ha_api_key=os.getenv("SUPERVISOR_TOKEN")
                ) # pyright: ignore
            else:
                self._settings = Settings() # pyright: ignore
        return self._settings

    @property
    def openai_client(self) -> AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(
                base_url=self.settings.llm_server_url,
                api_key=self.settings.llm_server_api_key,
                http_client=DefaultAsyncHttpxClient(
                    proxy=self.settings.llm_server_proxy,
                    verify=False
                )
            )
        return self._openai_client

    @property
    def hass_client(self) -> httpx.AsyncClient:
        if self._hass_client is None:
            self._hass_client = httpx.AsyncClient(
                base_url=self.settings.ha_api_url,
                headers={"Authorization": f"Bearer {self.settings.ha_api_key}"},
                verify=False
            )
        return self._hass_client


app_state = AppState()

# Dependencies
def get_settings() -> Settings:
    return app_state.settings


def get_openai_client() -> AsyncOpenAI:
    return app_state.openai_client


def get_hass_client() -> httpx.AsyncClient:
    return app_state.hass_client


async def get_tools() -> list[FunctionTool]:
    return get_hass_tools()


def get_agent(
        openai_client: AsyncOpenAI = Depends(get_openai_client),
        settings: Settings = Depends(get_settings),
        tools: list[FunctionTool] = Depends(get_tools)
    ) -> Agent:
    return Agent(
        name="Home Agent",
        model=OpenAIChatCompletionsModel(
            model=settings.model_id,
            openai_client=openai_client
        ),
        instructions=construct_prompt,
        tools=tools # type: ignore
    )

def construct_prompt(ctx_wrapper: RunContextWrapper[Any], agent: Agent | None) -> str:
    """Construct prompt for the agent."""
    instructions = "You are a helpful assistant that helps with tasks around the home. You will be given instructions that you are asked to follow. You can use the tools provided to you to control devices in the home in order to complete the task. When you have completed the task, you should respond with a summary of the task and the result."

    home_state = ctx_wrapper.context["home_state"]

    return instructions + "\n\n" + str(home_state)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Set up OpenAI client in Agents
        set_trace_processors([])
        
        # Ping Home Assistant
        try:
            response = await get_hass_client().get("/")
            response.raise_for_status()
            _LOGGER.info(f"Home Assistant API is up and running")
        except Exception as e:
            _LOGGER.error(f"Failed to ping Home Assistant API: {e}")
            raise HTTPException(status_code=500, detail="Home Assistant API is not responding")

        # Warm up the KV cache if llama.cpp
        # Check LLM backend type
        # openai_client = get_openai_client()
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

        #         await get_tools()
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
        
        yield
    finally:
        # Clean up resources
        pass


app = FastAPI(lifespan=lifespan)


class ConversationRequest(BaseModel):
    """Model for conversation request."""
    text: str
    conversation_id: str
    language: str
    home_state: Dict[str, Any]

class ConversationResponse(BaseModel):
    """Model for conversation response."""
    response: str


@app.post("/api/conversation", response_model=ConversationResponse)
async def process_conversation(
    request: ConversationRequest,
    agent: Agent = Depends(get_agent),
    hass_client: httpx.AsyncClient = Depends(get_hass_client)
):
    """Process a conversation with the agent."""
    context: Dict[str, Any] = {
        "conversation_id": request.conversation_id,
        "language": request.language,
        "home_state": request.home_state
    }
        
    context["hass_client"] = hass_client

    input = request.text

    try:
        result = await Runner.run(
            starting_agent=agent,
            input=input,
            context=context
        )
        return ConversationResponse(response=result.final_output)
        
    except Exception as e:
        _LOGGER.error(f"Error processing conversation: {e}")
        return ConversationResponse(
            response=f"I apologize, but I encountered an error: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Return health status of the API."""
    return {"status": "ok"}


@app.get("/api/config")
async def get_config(settings: Settings = Depends(get_settings)):
    """Return current configuration."""
    return {
        "llm_server_url": settings.llm_server_url
    }
