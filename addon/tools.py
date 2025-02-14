from typing import Any, Optional
from smolagents.tools import Tool, AUTHORIZED_TYPES
from mcp.types import Tool as MCPToolSpec
from mcp_client import MCPClient
import logging
import asyncio
from pydantic import BaseModel, model_validator
_LOGGER = logging.getLogger(__name__)

class HASlots(BaseModel):
    """Pydantic model for validating Home Assistant intent slots."""
    name: Optional[str] = None
    area: Optional[str] = None
    domain: Optional[str] = None
    device_class: Optional[str] = None

    @model_validator(mode='after')
    def validate_combinations(self) -> 'HASlots':
        """Validate that the parameter combinations are valid.
        
        Valid combinations are:
        - name only
        - area only
        - area and name
        - area and domain
        - area and device_class
        - device_class and domain

        From https://developers.home-assistant.io/docs/intent_builtin
        """
        valid = (
            (self.name is not None and not any([self.area, self.domain, self.device_class])) or  # name only
            (self.area is not None and not any([self.domain, self.device_class]) and self.name is None) or  # area only
            (self.area is not None and self.name is not None and not any([self.domain, self.device_class])) or  # area and name
            (self.area is not None and self.domain is not None and not any([self.name, self.device_class])) or  # area and domain
            (self.area is not None and self.device_class is not None and not any([self.name, self.domain])) or  # area and device class
            (self.device_class is not None and self.domain is not None and not any([self.name, self.area]))  # device class and domain
        )
        
        if not valid:
            raise ValueError("Invalid parameter combination")
        return self

class MCPTool(Tool):
    """Tool implementation for MCP tools.
    
    This class wraps an MCP tool specification and provides the interface
    expected by smolagents.
    """

    skip_forward_signature_validation = True
    
    def __init__(self, *args, tool_spec: MCPToolSpec, mcp_client: MCPClient, **kwargs):
        """Initialize the MCP tool.
        
        Args:
            tool_spec: The MCP tool specification
            mcp_client: The MCP client instance to use for tool calls
        """
        super().__init__(*args, **kwargs)
        self.tool_spec = tool_spec
        self.mcp_client = mcp_client
        self._convert_mcp_spec()
        
    def _convert_mcp_spec(self):
        """Convert the MCP tool specification to the smolagents format.
        
        This method converts the MCP tool spec into the format expected by smolagents,
        setting up the name, description, inputs and output type.
        """
        # Required class attributes from Tool
        self.name = self.tool_spec.name
        self.description = self.tool_spec.description or ""
        
        # Convert MCP schema to inputs dict
        self.inputs = self.tool_spec.inputSchema.get("properties", {})

        # Ensure all inputs have a description field
        for input_name, input_spec in self.inputs.items():
            self.inputs[input_name]["description"] = input_spec.get("description", "")
                
        # MCP tools don't specify return types
        self.output_type = "any"
        
    def forward(self, **kwargs: Any) -> Any:
        """Execute the MCP tool.
        
        This is called by the agent when the tool should be used.
        We delegate to the MCP client's call_tool method.
        """
        try:
            return asyncio.run(self.mcp_client.call_tool(self.name, kwargs))
        except Exception as e:
            _LOGGER.error(f"Error calling tool {self.name}: {e}")
            raise 

class HATool(MCPTool):
    """Home Assistant specific MCP tool with additional parameter validation."""
    
    def forward(self, **kwargs: Any) -> Any:
        """Execute the Home Assistant tool with parameter validation.
        
        This method adds an additional validation layer to ensure the parameters
        conform to the expected Home Assistant entity query patterns.
        """
        # Validate the parameters using the pydantic model
        try:
            HASlots(**kwargs)
        except ValueError as e:
            _LOGGER.error(f"Invalid parameter combination for HA tool {self.name}: {e}")
            raise ValueError(f"Invalid parameter combination for HA tool: {str(e)}")
            
        # If validation passes, proceed with the normal MCP tool execution
        return super().forward(**kwargs) 