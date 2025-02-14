import asyncio
from typing import Dict, Any, AsyncGenerator
import logging
from datetime import datetime, timedelta
import httpx
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool

from exceptions import MCPConnectionError, MCPToolError, MCPInitializationError

_LOGGER = logging.getLogger('uvicorn.error')

class MCPClient:
    def __init__(self, update_interval: int = 30, initial_retry_delay: int = 5, max_retries: int = 5):
        """Initialize MCP Client.
        
        Args:
            update_interval: Minutes between tool updates
            initial_retry_delay: Seconds to wait before the first retry attempt
            max_retries: Maximum number of retry attempts for initial connection
        """
        self.session: ClientSession | None = None
        self.tools: Dict[str, Tool] = {}
        self.last_update: datetime | None = None
        self.update_interval = timedelta(minutes=update_interval)
        self.update_task: asyncio.Task | None = None
        self._ctx_mgr = None
        self._is_running = False
        self._token: str | None = None
        self.initial_retry_delay = initial_retry_delay
        self.max_retries = max_retries

    @asynccontextmanager
    async def _create_session(self, url: str) -> AsyncGenerator[ClientSession, None]:
        """Create an SSE-based MCP client session."""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            async with sse_client(url=url, headers=headers) as streams, ClientSession(*streams) as session:
                await session.initialize()
                yield session
        except httpx.HTTPError as err:
            raise MCPConnectionError(f"Failed to connect to MCP server: {err}") from err
        except Exception as err:
            raise MCPInitializationError(f"Failed to initialize MCP client: {err}") from err

    async def initialize(self, url: str, token: str | None = None):
        """Initialize the MCP client and start periodic updates with connection retry.
        
        Args:
            url: URL of the MCP server
            token: Optional bearer token for authentication
        """
        self._token = token
        retry_delay = self.initial_retry_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                _LOGGER.info(f"Attempting to connect to MCP server (attempt {attempt}/{self.max_retries})...")
                self._ctx_mgr = self._create_session(url)
                self.session = await self._ctx_mgr.__aenter__()
                _LOGGER.info(f"Connected to MCP server {url}")
                
                await self._update_tools()
                
                # Start periodic updates
                self._is_running = True
                self.update_task = asyncio.create_task(self._periodic_update())
                
                _LOGGER.info("MCP client initialized successfully")
                return  # Initialization successful, exit retry loop

            except (MCPConnectionError, MCPInitializationError) as e:
                _LOGGER.warning(f"Connection attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    _LOGGER.info(f"Retrying in {retry_delay} seconds...")
                    # FIXME: `^C` to cancel doesn't seem to work
                    try:
                        await asyncio.sleep(retry_delay)
                    except asyncio.CancelledError:
                        await self.cleanup()
                        raise # Re-raise CancelledError to stop initialization
                    retry_delay *= 2  # Exponential backoff
                else:
                    _LOGGER.error("Max connection attempts reached. Initialization failed.")
                    await self.cleanup()
                    raise  # Re-raise the last exception

            except asyncio.CancelledError:
                _LOGGER.info("MCP client initialization cancelled.")
                await self.cleanup()
                raise # Re-raise CancelledError to stop initialization

            except Exception as e:
                _LOGGER.error(f"An unexpected error occurred during initialization: {e}")
                await self.cleanup()
                raise MCPInitializationError(f"MCP client initialization failed due to an unexpected error: {e}") from e

    async def _update_tools(self):
        """Update the list of available tools."""
        if not self.session:
            raise MCPConnectionError("Session not initialized")
        
        try:
            result = await self.session.list_tools()
            self.tools = {tool.name: tool for tool in result.tools}
            self.last_update = datetime.now()
            
            _LOGGER.info(f"Updated {len(self.tools)} tools from MCP server")
            _LOGGER.debug(f"Available tools: {', '.join(self.tools.keys())}")
        except Exception as e:
            _LOGGER.error(f"Failed to update tools: {e}")
            raise MCPToolError(f"Failed to update tools: {e}")

    # TODO: Remove in future when we have a proper notification system from the MCP server side
    # `notifications/tools/list_changed`
    async def _periodic_update(self):
        """Periodically update tools."""
        while self._is_running:
            try:
                await asyncio.sleep(self.update_interval.total_seconds())
                if self._is_running:  # Check again after sleep
                    await self._update_tools()
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error(f"Error in periodic update: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def cleanup(self):
        """Cleanup MCP client resources."""
        self._is_running = False
        
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
            self.update_task = None

        if self._ctx_mgr:
            try:
                await self._ctx_mgr.__aexit__(None, None, None)
            except Exception as e:
                _LOGGER.error(f"Error closing MCP session: {e}")
            self._ctx_mgr = None
            self.session = None

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