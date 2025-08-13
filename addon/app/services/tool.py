from ..models import Tool
from ..tools import get_all_tools

class ToolService:
    @staticmethod
    def get_tools() -> list[Tool]:
        """Get all tools."""
        return [
            Tool(
                name=tool.name,
                description=tool.description,
                params_json_schema=tool.params_json_schema,
            )
            for tool in get_all_tools()
        ]