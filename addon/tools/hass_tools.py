from agents import RunContextWrapper, function_tool
from typing import Any
from httpx import AsyncClient, Response

# from homeassistant.helpers.intent
INTENT_TURN_ON = "HassTurnOn"
INTENT_TURN_OFF = "HassTurnOff"
INTENT_START_TIMER = "HassStartTimer"
INTENT_CANCEL_TIMER = "HassCancelTimer"
INTENT_CANCEL_ALL_TIMERS = "HassCancelAllTimers"
INTENT_INCREASE_TIMER = "HassIncreaseTimer"
INTENT_DECREASE_TIMER = "HassDecreaseTimer"
INTENT_PAUSE_TIMER = "HassPauseTimer"
INTENT_UNPAUSE_TIMER = "HassUnpauseTimer"
INTENT_TIMER_STATUS = "HassTimerStatus"
INTENT_GET_CURRENT_DATE = "HassGetCurrentDate" # keep?
INTENT_GET_CURRENT_TIME = "HassGetCurrentTime" # keep?
INTENT_GET_TEMPERATURE = "HassClimateGetTemperature" # keep?
# INTENT_SET_POSITION = "HassSetPosition"
# INTENT_GET_STATE = "HassGetState"
# INTENT_TOGGLE = "HassToggle"
# INTENT_NEVERMIND = "HassNevermind"
# INTENT_RESPOND = "HassRespond"
# INTENT_BROADCAST = "HassBroadcast"

intents_names = [
    INTENT_TURN_OFF,
    INTENT_TURN_ON,
    INTENT_START_TIMER,
    INTENT_CANCEL_TIMER,
    INTENT_CANCEL_ALL_TIMERS,
    INTENT_INCREASE_TIMER,
    INTENT_DECREASE_TIMER,
    INTENT_PAUSE_TIMER,
    INTENT_UNPAUSE_TIMER,
    INTENT_TIMER_STATUS,
    INTENT_GET_CURRENT_DATE,
    INTENT_GET_CURRENT_TIME,
    INTENT_GET_TEMPERATURE,
]

async def handle_intent(
    hass_client: AsyncClient,
    intent_name: str,
    name: str,
) -> dict:
    """
    Calls Home Assistant to handle an intent.
    """
    response: Response = await hass_client.post("/intent/handle", json={"name": intent_name, "data": {"name": name}})
    return response.json()

@function_tool
async def turn_on(
    ctx_wrapper: RunContextWrapper[Any],
    name: str
) -> str:
    """
    Turns on/opens/presses a device or entity. For locks, this performs a 'lock' action. Use for requests like 'turn on', 'activate', 'enable', or 'lock'.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    
    response = await handle_intent(hass_client, INTENT_TURN_ON, name)
    
    if response.get("response_type") == "action_done":
        return "Done."
    else:
        return "Failed."

@function_tool
async def turn_off(
    ctx_wrapper: RunContextWrapper[Any],
    name: str
) -> str:
    """
    Turns off/closes/releases a device or entity. For locks, this performs a 'unlock' action. Use for requests like 'turn off', 'deactivate', 'disable', or 'unlock'.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]

    response = await handle_intent(hass_client, INTENT_TURN_OFF, name)

    if response.get("response_type") == "action_done":
        return "Done."
    else:
        return "Failed."
    
@function_tool

def get_tools():
    return [
        turn_on,
        turn_off,
    ]