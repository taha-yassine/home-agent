"""Custom exceptions for MCP client."""

class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass

class MCPConnectionError(MCPError):
    """Raised when there are connection issues with the MCP server."""
    pass

class MCPToolError(MCPError):
    """Raised when there are issues with MCP tools."""
    pass

class MCPInitializationError(MCPError):
    """Raised when the MCP client fails to initialize."""
    pass 