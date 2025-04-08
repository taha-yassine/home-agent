from typing import Optional, Any
from agents import FunctionTool, RunContextWrapper
from mcp_client import MCPClient
from pydantic import BaseModel, model_validator
from functools import partial
import json
from mcp.types import Tool
import jsonschema

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
    

async def _on_invoke_tool(tool: Tool, mcp_client: MCPClient, ctx_wrapper: RunContextWrapper[Any], args: str) -> str:
    """Utility function to verify the tool call args and return the result.
    
    `args` corresponds to the `tool_calls[_].function.arguments` field.  It is a JSON string that the model generates. As a results, and contrary to the other fields, structured generation can't be used and the result isn't always garanteed to conform to the tool's input schema.

    This function attempts to validate the arguments against the tool's input schema as a workaround.
    """
    try:
        # JSON validation and parsing
        args_dict = json.loads(args)
        
        if tool.inputSchema and tool.inputSchema.get("properties"):
            try:
                # Disable additional properties to avoid the model hallucinating properties
                tool.inputSchema["additionalProperties"] = False

                jsonschema.validate(
                    instance=args_dict,
                    schema=tool.inputSchema    
                )
            except jsonschema.ValidationError as e:
                # Return an informative error message to the model if validation fails
                return(f"Invalid arguments {args_dict} for tool {tool.name}. Validation Error: {e.message}. Try again with valid arguments.")
            except jsonschema.SchemaError:
                # If the schema is invalid, it's out-of-scope for the model to handle
                # Re-raise the error in this case
                raise

        result = await mcp_client.call_tool(tool.name, args_dict)
        return str(result.content) 
    except json.JSONDecodeError as e:
        # Return an informative error message to the model if the JSON is invalid
        return(f"Invalid JSON arguments {args} for tool {tool.name}. Error: {e}. Try again with valid JSON.")

async def load_tools(mcp_client: MCPClient) -> list[FunctionTool]:
    """Load tools from MCP client and convert them to OpenAI `FunctionTool`s."""

    await mcp_client.load_tools()

    tools = mcp_client.tools

    return [
        FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=tool.inputSchema if tool.inputSchema["properties"] else {}, # Certain providers don't like it when the inputSchema is empty, i.e., {'type': 'object', 'properties': {}}
            on_invoke_tool=partial(_on_invoke_tool, tool, mcp_client)
        )
        for tool in tools.values()
    ]