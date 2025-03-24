import asyncio
from typing import Dict, Any
import logging
import httpx
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool
from exceptions import MCPConnectionError, MCPToolError, MCPInitializationError

_LOGGER = logging.getLogger('uvicorn.error')

class MCPClient:
    def __init__(self, url: str, token: str | None = None):
        """Initialize MCP Client.
        
        Args:
            url: URL of the MCP server
            token: Optional bearer token for authentication
        """
        self.url = url
        self._token = token
        self.session: ClientSession | None = None
        self.tools: Dict[str, Tool] = {}
        self.exit_stack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection."""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            _LOGGER.info("Connecting to MCP server...")
            
            # Setup SSE connection using exit stack
            streams = await self.exit_stack.enter_async_context(
                sse_client(url=self.url, headers=headers)
            )
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(*streams)
            )
            
            await self.session.initialize()
            _LOGGER.info(f"Connected to MCP server {self.url}")

        except httpx.HTTPError as err:
            await self.cleanup()
            raise MCPConnectionError(f"Failed to connect to MCP server: {err}") from err
        except asyncio.CancelledError:
            _LOGGER.info("MCP client connection cancelled")
            await self.cleanup()
            raise
        except Exception as err:
            await self.cleanup()
            raise MCPInitializationError(f"Failed to initialize MCP client: {err}") from err

    async def load_tools(self):
        """Load tools from MCP server."""
        try:
            result = await self.session.list_tools()
            self.tools = {tool.name: tool for tool in result.tools}
                        
            _LOGGER.info(f"Updated {len(self.tools)} tools from MCP server")
            _LOGGER.debug(f"Available tools: {', '.join(self.tools.keys())}")
        except Exception as e:
            _LOGGER.error(f"Error loading tools: {e}")
            raise MCPToolError(f"Failed to load tools: {e}") from e

    async def cleanup(self):
        """Cleanup MCP client resources."""
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            _LOGGER.error(f"Error during cleanup: {e}")
        finally:
            self.session = None
            self.tools = {}

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call an MCP tool by name with arguments."""
        if not self.session:
            raise MCPConnectionError("MCP client not initialized")
        
        if tool_name not in self.tools:
            raise MCPToolError(
                f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
            )
        
        try:
            return await self.session.call_tool(tool_name, arguments)
        except Exception as e:
            raise MCPToolError(f"Failed to call tool {tool_name}: {e}")

    def get_tool(self, tool_name: str) -> Tool | None:
        """Get tool details by name."""
        return self.tools.get(tool_name) 