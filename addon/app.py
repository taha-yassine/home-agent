import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Optional
import logging
from contextlib import asynccontextmanager

from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from agents import (
    FunctionTool,
    RunContextWrapper,
    Agent,
    set_default_openai_client,
    Runner,
    set_trace_processors, set_default_openai_api    
)

from mcp_client import MCPClient
from tools import setup_tools


# TODO: Set up
# OpenRouter metadata
# os.environ["OR_SITE_URL"] = "https://github.com/taha-yassine/home-agent"
# os.environ["OR_APP_NAME"] = "home-agent"

_LOGGER = logging.getLogger('uvicorn.error')

class Settings(BaseSettings):
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

settings = Settings() # pyright: ignore
openai_client = AsyncOpenAI(
    base_url=settings.llm_server_url,
    api_key=settings.llm_server_api_key,
)
mcp_client = MCPClient()
agent: Optional[Agent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        set_default_openai_client(
            client=openai_client
        )

        # Remove the default OpenAI processor
        set_trace_processors([])

        set_default_openai_api("chat_completions")

        await mcp_client.initialize(
            url=settings.ha_mcp_url,
            token=settings.ha_api_key
        )
        
        global agent

        tools: list[FunctionTool] = await setup_tools(mcp_client)
        
        agent = Agent(
            name="Home Agent",
            model=settings.model_id,
            instructions=construct_prompt,
            tools=tools
        )
        
        yield
    finally:
        await mcp_client.cleanup()

app = FastAPI(lifespan=lifespan)

# TODO: Organize better
def construct_prompt(ctx_wrapper: RunContextWrapper[Any], agent: Agent) -> str:
    instructions = "You are a helpful assistant that helps with tasks around the home. You will be given instructions that you are asked to follow. You can use the tools provided to you to control devices in the home in order to complete the task. When you have completed the task, you should respond with a summary of the task and the result."

    home_state = ctx_wrapper.context["context"]

    return instructions + "\n\n" + str(home_state)

class ConversationRequest(BaseModel):
    text: str
    conversation_id: str
    language: str
    context: dict | None = None
    llm_api: dict[str, Any] | None = None

class ConversationResponse(BaseModel):
    response: str

@app.post("/api/conversation", response_model=ConversationResponse)
async def process_conversation(request: ConversationRequest):
    if not agent:
        raise RuntimeError("Agent not initialized")
        
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
async def get_config():
    """Return current configuration."""
    return {
        "llm_server_url": settings.llm_server_url
    } 

@app.get("/api/tools")
async def list_tools():
    """Return list of available MCP tools and last update time."""
    return {
        "tools": list(mcp_client.tools.keys()),
        "last_update": mcp_client.last_update.isoformat() if mcp_client.last_update else None
    }

@app.get("/api/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get details about a specific tool."""
    tool = mcp_client.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return tool 