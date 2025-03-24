from typing import Optional, Any
from agents import FunctionTool, RunContextWrapper
from mcp_client import MCPClient
from pydantic import BaseModel, model_validator
from functools import partial
import json

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

async def load_tools(mcp_client: MCPClient) -> list[FunctionTool]:
    """Load tools from MCP client and convert them to OpenAI `FunctionTool`s."""

    await mcp_client.load_tools()

    tools = mcp_client.tools

    async def _call_tool(tool_name: str, ctx_wrapper: RunContextWrapper[Any], args: str) -> str:
        args_dict = json.loads(args)
        result = await mcp_client.call_tool(tool_name, args_dict)
        return result.content

    return [
        FunctionTool(
            name=tool_name,
            description=tool.description,
            params_json_schema=tool.inputSchema,
            on_invoke_tool=partial(_call_tool, tool_name)
        )
        for tool_name, tool in tools.items()
    ]