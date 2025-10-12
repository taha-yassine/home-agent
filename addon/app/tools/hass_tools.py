from agents import RunContextWrapper, function_tool, FunctionTool
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
INTENT_SET_POSITION = "HassSetPosition"
# INTENT_GET_STATE = "HassGetState"
# INTENT_TOGGLE = "HassToggle"
# INTENT_NEVERMIND = "HassNevermind"
# INTENT_RESPOND = "HassRespond"
# INTENT_BROADCAST = "HassBroadcast"

INTENT_LIGHT_SET = "HassLightSet"
INTENT_LIST_ADD_ITEM = "HassListAddItem"
INTENT_VACUUM_START = "HassVacuumStart"
INTENT_VACUUM_RETURN_TO_BASE = "HassVacuumReturnToBase"
INTENT_MEDIA_PAUSE = "HassMediaPause"
INTENT_MEDIA_UNPAUSE = "HassMediaUnpause"
INTENT_MEDIA_NEXT = "HassMediaNext"
INTENT_MEDIA_PREVIOUS = "HassMediaPrevious"
INTENT_SET_VOLUME = "HassSetVolume"

intents_names = [
    INTENT_TURN_OFF,
    INTENT_TURN_ON,
    INTENT_LIGHT_SET,
    INTENT_LIST_ADD_ITEM,
    INTENT_VACUUM_START,
    INTENT_VACUUM_RETURN_TO_BASE,
    INTENT_MEDIA_PAUSE,
    INTENT_MEDIA_UNPAUSE,
    INTENT_MEDIA_NEXT,
    INTENT_MEDIA_PREVIOUS,
    INTENT_SET_VOLUME,
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
    INTENT_SET_POSITION,
    # INTENT_GET_STATE,
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
    name: str,
    domain: str,
) -> str:
    """
    Turns on/opens/presses a device or entity. For locks, this performs a 'lock' action. Use for requests like 'turn on', 'activate', 'enable', or 'lock'. Always specify the domain of the entity.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    
    response = await handle_intent(hass_client, INTENT_TURN_ON, {"name": name, "domain": domain})
    
    if response.get("response_type") == "action_done":
        return "Done."
    else:
        return "Failed."

@function_tool
async def turn_off(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    domain: str,
) -> str:
    """
    Turns off/closes/releases a device or entity. For locks, this performs a 'unlock' action. Use for requests like 'turn off', 'deactivate', 'disable', or 'unlock'. Always specify the domain of the entity.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]

    response = await handle_intent(hass_client, INTENT_TURN_OFF, {"name": name, "domain": domain})

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
    name: str,
    # area: Optional[str] = None,
    # floor: Optional[str] = None,
) -> str:
    """Gets the current temperature from a climate device or sensor."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {}
    if name:
        slots["name"] = name
    # if area:
    #     slots["area"] = area
    # if floor:
    #     slots["floor"] = floor
    response = await handle_intent(hass_client, INTENT_GET_TEMPERATURE, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    return "Could not retrieve the temperature."

@function_tool
async def set_position(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    position: int,
) -> str:
    """Sets the position of an entity.
    
    Args:
        name: The name of the entity to set the position of.
        position: The position to set the entity to, between 0 and 100.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name, "position": position}

    response = await handle_intent(hass_client, INTENT_SET_POSITION, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    if response.get("response_type") == "action_done":
        return "Position set."
    return "Failed to set position."

@function_tool
async def set_light(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    brightness: Optional[int] = None,
    color: Optional[str] = None,
) -> str:
    """Sets the color of a light.
    
    Args:
        name: The name of the light to set.
        brightness: The brightness of the light to set, between 0 and 100.
        color: The name of the color to set the light to.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {
        "name": name,
        "domain": "light", # Avoids confusion when a non-light entity with the same name exists
    }
    if brightness is not None:
        slots["brightness"] = brightness
    if color is not None:
        slots["color"] = color
    response = await handle_intent(hass_client, INTENT_LIGHT_SET, slots)
    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    if response.get("response_type") == "action_done":
        return "Light set."
    return "Failed to set light."
    
@function_tool
async def add_list_item(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    item: str,
) -> str:
    """Adds an item to a to-do list.
    
    Args:
        name: The name of the list to add the item to.
        item: The item to add to the list.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name, "item": item}
    response = await handle_intent(hass_client, INTENT_LIST_ADD_ITEM, slots)
    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech
    if response.get("response_type") == "action_done":
        return "Item added."
    return "Failed to add item."

@function_tool
async def start_vacuum(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Starts a vacuum cleaner."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"name": name}

    response = await handle_intent(hass_client, INTENT_VACUUM_START, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Vacuum started."
    return "Failed to start vacuum."

@function_tool
async def return_vacuum_to_base(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Tells a vacuum cleaner to return to its base/dock."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name}

    response = await handle_intent(hass_client, INTENT_VACUUM_RETURN_TO_BASE, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Done."
    return "Failed."

@function_tool
async def pause_media(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Pauses a media player."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name}

    response = await handle_intent(hass_client, INTENT_MEDIA_PAUSE, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Done."
    return "Failed."

@function_tool
async def unpause_media(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Unpauses a media player."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name}

    response = await handle_intent(hass_client, INTENT_MEDIA_UNPAUSE, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Done."
    return "Failed."

@function_tool
async def next_track(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Skips to the next track on a media player."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name}

    response = await handle_intent(hass_client, INTENT_MEDIA_NEXT, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Done."
    return "Failed."

@function_tool
async def previous_track(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
) -> str:
    """Skips to the previous track on a media player."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots = {"name": name}

    response = await handle_intent(hass_client, INTENT_MEDIA_PREVIOUS, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Done."
    return "Failed."

@function_tool
async def set_volume(
    ctx_wrapper: RunContextWrapper[Any],
    volume_level: int,
    name: str,
) -> str:
    """Sets the volume of a media player.
    
    Args:
        volume_level: The volume level to set, between 0 and 100.
        name: The name of the media player to set the volume of.
    """
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]
    slots: dict[str, Any] = {"volume_level": volume_level}
    slots["name"] = name

    response = await handle_intent(hass_client, INTENT_SET_VOLUME, slots)

    speech = response.get("speech", {}).get("plain", {}).get("speech")
    if speech:
        return speech

    if response.get("response_type") == "action_done":
        return "Done."
    return "Failed."

@function_tool
async def get_state(
    ctx_wrapper: RunContextWrapper[Any],
    name: str,
    domain: str,
) -> str:
    """Gets the state of an entity."""
    hass_client: AsyncClient = ctx_wrapper.context["hass_client"]

    response = await hass_client.get("/home_agent/entities/state", params={"name": name, "domain": domain})
    
    return response.json()

def get_tools() -> list[FunctionTool]:
    return [
        turn_on,
        turn_off,
        set_light,
        add_list_item,
        start_vacuum,
        return_vacuum_to_base,
        pause_media,
        unpause_media,
        next_track,
        previous_track,
        set_volume,
        start_timer,
        cancel_timer,
        cancel_all_timers,
        increase_timer,
        decrease_timer,
        pause_timer,
        unpause_timer,
        get_timer_status,
        # get_current_date,
        # get_current_time,
        # get_temperature,
        set_position,
        get_state,
    ]