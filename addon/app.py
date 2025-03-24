import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict, Optional
import logging
from contextlib import asynccontextmanager

from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from agents import (
    FunctionTool,
    RunContextWrapper,
    Agent,
    Runner,
    set_trace_processors,
    OpenAIChatCompletionsModel
)

from mcp_client import MCPClient
from tools import load_tools


# TODO: Set up
# OpenRouter metadata
# os.environ["OR_SITE_URL"] = "https://github.com/taha-yassine/home-agent"
# os.environ["OR_APP_NAME"] = "home-agent"

_LOGGER = logging.getLogger('uvicorn.error')

class Settings(BaseSettings):
    """Application settings."""
    llm_server_url: str # URL of the LLM inference server
    llm_server_api_key: str # API key for the LLM inference server
    model_id: str # ID of the LLM model to use
    ha_mcp_url: str  # Home Assistant URL of the MCP server
    ha_api_key: str  # Bearer token for Home Assistant authentication
    mcp_update_interval: int = 30  # Minutes between tool updates
    
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
        self._mcp_client: Optional[MCPClient] = None

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = Settings() # pyright: ignore
        return self._settings

    @property
    def openai_client(self) -> AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(
                base_url=self.settings.llm_server_url,
                api_key=self.settings.llm_server_api_key,
            )
        return self._openai_client

    @property
    def mcp_client(self) -> MCPClient:
        if self._mcp_client is None:
            self._mcp_client = MCPClient(
                url=self.settings.ha_mcp_url,
                token=self.settings.ha_api_key
            )
        return self._mcp_client


app_state = AppState()

# Dependencies
def get_settings() -> Settings:
    return app_state.settings


def get_openai_client() -> AsyncOpenAI:
    return app_state.openai_client


def get_mcp_client() -> MCPClient:
    return app_state.mcp_client


async def get_tools() -> list[FunctionTool]:
    return await load_tools(app_state.mcp_client)


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
        tools=tools
    )

def construct_prompt(ctx_wrapper: RunContextWrapper[Any], agent: Agent) -> str:
    """Construct prompt for the agent."""
    instructions = "You are a helpful assistant that helps with tasks around the home. You will be given instructions that you are asked to follow. You can use the tools provided to you to control devices in the home in order to complete the task. When you have completed the task, you should respond with a summary of the task and the result."

    home_state = ctx_wrapper.context["context"]

    return instructions + "\n\n" + str(home_state)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Set up OpenAI client in Agents
        set_trace_processors([])
        
        # Initialize MCP client
        await app_state.mcp_client.initialize()
        
        yield
    finally:
        # Clean up resources
        if app_state.mcp_client:
            await app_state.mcp_client.cleanup()
            # app_state.mcp_client = None


app = FastAPI(lifespan=lifespan)


class ConversationRequest(BaseModel):
    """Model for conversation request."""
    text: str
    conversation_id: str
    language: str
    context: Dict[str, Any] | None = None
    llm_api: Dict[str, Any] | None = None


class ConversationResponse(BaseModel):
    """Model for conversation response."""
    response: str


@app.post("/api/conversation", response_model=ConversationResponse)
async def process_conversation(
    request: ConversationRequest,
    agent: Agent = Depends(get_agent)
):
    """Process a conversation with the agent."""
    full_context = {
        "conversation_id": request.conversation_id,
        "language": request.language
    }
    if request.context:
        full_context.update(request.context)
    if request.llm_api:
        full_context.update(request.llm_api)
        
    try:
        result = await Runner.run(
            starting_agent=agent,
            input=request.text,
            context=full_context
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


@app.get("/api/tools")
async def list_tools(mcp_client: MCPClient = Depends(get_mcp_client)):
    """Return list of available MCP tools."""
    return mcp_client.tools


@app.get("/api/tools/{tool_name}")
async def get_tool(
    tool_name: str, 
    mcp_client: MCPClient = Depends(get_mcp_client)
):
    """Get details about a specific tool."""
    tool = mcp_client.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return tool 