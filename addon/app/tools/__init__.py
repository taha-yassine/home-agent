from agents import FunctionTool
from .hass_tools import get_tools as get_hass_tools
from .tools import get_tools

def get_all_tools() -> list[FunctionTool]:
    return get_hass_tools() + get_tools()