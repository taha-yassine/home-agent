from agents import RunContextWrapper, function_tool
from typing import Any, Optional
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
    slots: dict[str, Any],
) -> dict:
    """
    Calls Home Assistant to handle an intent.
    """
    response: Response = await hass_client.post("/intent/handle", json={"name": intent_name, "data": slots})
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
    
    response = await handle_intent(hass_client, INTENT_TURN_ON, {"name": name})
    
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

    response = await handle_intent(hass_client, INTENT_TURN_OFF, {"name": name})

    if response.get("response_type") == "action_done":
        return "Done."
    else:
        return "Failed."
    
@function_tool
async def start_timer(
    ctx_wrapper: RunContextWrapper[Any],
    hours: Optional[int] = None,
    minutes: Optional[int] = None,
    seconds: Optional[int] = None,
    name: Optional[str] = None
) -> str:
    """Starts a new timer."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {}
    if hours is not None:
        slots["hours"] = hours
    if minutes is not None:
        slots["minutes"] = minutes
    if seconds is not None:
        slots["seconds"] = seconds
    if name is not None:
        slots["name"] = name
    
    if not slots:
        return "You must provide at least one of hours, minutes, or seconds to start a timer."

    response = await handle_intent(hass_client, INTENT_START_TIMER, slots)
    
    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "Timer started."
    return "Failed to start timer."

@function_tool
async def cancel_timer(
    ctx_wrapper: RunContextWrapper[Any],
    name: str
) -> str:
    """Cancels a timer. You must provide the name of the timer to identify it."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name}

    response = await handle_intent(hass_client, INTENT_CANCEL_TIMER, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "Timer cancelled."
    return "Failed to cancel timer."

@function_tool
async def cancel_all_timers(
    ctx_wrapper: RunContextWrapper[Any]
) -> str:
    """Cancels all active timers."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    response = await handle_intent(hass_client, INTENT_CANCEL_ALL_TIMERS, {})

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "All timers cancelled."
    return "Failed to cancel all timers."

@function_tool
async def increase_timer(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    hours: Optional[int] = None,
    minutes: Optional[int] = None,
    seconds: Optional[int] = None,
) -> str:
    """Adds time to a running timer. You must specify which timer and how much time to add."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name}
    if hours is not None:
        slots["hours"] = hours
    if minutes is not None:
        slots["minutes"] = minutes
    if seconds is not None:
        slots["seconds"] = seconds
    
    if not any([hours, minutes, seconds]):
        return "You must specify how much time to add."

    response = await handle_intent(hass_client, INTENT_INCREASE_TIMER, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "Timer increased."
    return "Failed to increase timer."

@function_tool
async def decrease_timer(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    hours: Optional[int] = None,
    minutes: Optional[int] = None,
    seconds: Optional[int] = None,
) -> str:
    """Removes time from a running timer. You must specify which timer and how much time to remove."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name}
    if hours is not None:
        slots["hours"] = hours
    if minutes is not None:
        slots["minutes"] = minutes
    if seconds is not None:
        slots["seconds"] = seconds

    if not any([hours, minutes, seconds]):
        return "You must specify how much time to remove."

    response = await handle_intent(hass_client, INTENT_DECREASE_TIMER, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "Timer decreased."
    return "Failed to decrease timer."

@function_tool
async def pause_timer(
    ctx_wrapper: RunContextWrapper[Any],
    name: str
) -> str:
    """Pauses a running timer. You must provide the name of the timer to identify it."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name}

    response = await handle_intent(hass_client, INTENT_PAUSE_TIMER, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "Timer paused."
    return "Failed to pause timer."

@function_tool
async def unpause_timer(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Resumes a paused timer. You must provide the name of the timer to identify it."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name}

    response = await handle_intent(hass_client, INTENT_UNPAUSE_TIMER, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    if response.get("response_type") == "action_done":
        return "Timer unpaused."
    return "Failed to unpause timer."

@function_tool
async def get_timer_status(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Gets the status of a timer. You must provide the name of the timer to identify it."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name}

    response = await handle_intent(hass_client, INTENT_TIMER_STATUS, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    
    return "Could not retrieve timer status."

@function_tool
async def get_current_date(
    ctx_wrapper: RunContextWrapper[Any]
) -> str:
    """Gets the current date."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    response = await handle_intent(hass_client, INTENT_GET_CURRENT_DATE, {})
    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    return "Could not retrieve the current date."

@function_tool
async def get_current_time(
    ctx_wrapper: RunContextWrapper[Any]
) -> str:
    """Gets the current time."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    response = await handle_intent(hass_client, INTENT_GET_CURRENT_TIME, {})
    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    return "Could not retrieve the current time."

@function_tool
async def get_temperature(
    ctx_wrapper: RunContextWrapper[Any],
    name: Optional[str] = None,
    area: Optional[str] = None,
    floor: Optional[str] = None,
) -> str:
    """Gets the current temperature from a climate device or sensor."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {}
    if name:
        slots["name"] = name
    if area:
        slots["area"] = area
    if floor:
        slots["floor"] = floor
    response = await handle_intent(hass_client, INTENT_GET_TEMPERATURE, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    return "Could not retrieve the temperature."
    
def get_tools():
    return [
        turn_on,
        turn_off,
        start_timer,
        cancel_timer,
        cancel_all_timers,
        increase_timer,
        decrease_timer,
        pause_timer,
        unpause_timer,
        get_timer_status,
        get_current_date,
        get_current_time,
        get_temperature,
    ]