from agents import function_tool, RunContextWrapper, FunctionTool
from typing import Any
from datetime import datetime

@function_tool
async def get_date_time(
    ctx_wrapper: RunContextWrapper[Any],
) -> str:
    """Get the current date and time in the format YYYY-MM-DD HH:MM:SS."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_tools() -> list[FunctionTool]:
    return [
        get_date_time,
    ]