import os
if os.getenv("DEBUGPY", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Optional
import logging
import asyncio
from contextlib import asynccontextmanager
from smolagents import ToolCallingAgent, CodeAgent, LiteLLMModel
import litellm
import yaml
from mcp_client import MCPClient
from tools import MCPTool

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# smolagents telemetry
arize_endpoint = "http://0.0.0.0:6006/v1/traces"
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(arize_endpoint)))

SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)

os.environ["LITELLM_LOG"] = "DEBUG"
litellm.set_verbose = True
# LiteLLM telemetry
litellm.log_raw_request_response = True
litellm.callbacks = ["otel"]
os.environ["OTEL_EXPORTER"] = "otlp_grpc"
os.environ["OTLP_ENDPOINT"] = "http://0.0.0.0:4317"

# TODO: Set up
# OpenRouter metadata
# os.environ["OR_SITE_URL"] = "https://github.com/taha-yassine/home-agent"
# os.environ["OR_APP_NAME"] = "home-agent"

_LOGGER = logging.getLogger('uvicorn.error')

class Settings(BaseSettings):
    llm_server_url: str # URL of the LLM inference server
    llm_server_type: str = litellm.LlmProviders.OPENAI # Type of the LLM server
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

settings = Settings()
mcp_client = MCPClient()
agent: Optional[CodeAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MCP client on startup
    try:
        await mcp_client.initialize(
            url=settings.ha_mcp_url,
            token=settings.ha_api_key
        )
        
        global agent
        
        model = LiteLLMModel(
            api_base=settings.llm_server_url,
            api_key=settings.llm_server_api_key,
            model_id=f'{settings.llm_server_type}/{settings.model_id}',
            tool_choice="auto",
        )
        
        tools = [
            MCPTool(
                tool_spec=tool,
                mcp_client=mcp_client
            )
            for tool in mcp_client.tools.values()
        ]
        
        agent = ToolCallingAgent(
            model=model,
            tools=tools,
            prompt_templates=yaml.safe_load(open("prompts.yaml")),
            max_steps=1
        )
        
        yield
    finally:
        await mcp_client.cleanup()

app = FastAPI(lifespan=lifespan)

class ConversationRequest(BaseModel):
    text: str
    conversation_id: str
    language: str
    context: dict | None = None
    llm_api: dict[str, Any] | None = None

class ConversationResponse(BaseModel):
    response: str

from concurrent.futures import ThreadPoolExecutor

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
        # Run the synchronous agent.run in a thread pool
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            response = await loop.run_in_executor(
                pool,
                agent.run,
                request.text
            )
        return ConversationResponse(response=response)
        
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