"""The conversation platform for Home Agent."""

from __future__ import annotations

from collections.abc import Callable
import logging
import time
from typing import Any, Literal

import aiohttp
import voluptuous as vol
from voluptuous_openapi import convert

from homeassistant.components import assist_pipeline, conversation
from homeassistant.components.intent import async_device_supports_timers
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LLM_HASS_API, MATCH_ALL
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    floor_registry as fr,
    intent,
    llm,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import (
    ADDON_URL,
    DEFAULT_MAX_HISTORY,
    DOMAIN,
    MAX_HISTORY_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Home Agent conversation."""
    agent = HomeAgentConversationEntity(config_entry)
    async_add_entities([agent])


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> dict[str, Any]:
    """Format tool specification."""
    tool_spec = {
        "name": tool.name,
        "parameters": convert(tool.parameters, custom_serializer=custom_serializer),
    }
    if tool.description:
        tool_spec["description"] = tool.description
    return {"type": "function", "function": tool_spec}


class HomeAgentConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """Home Agent conversation agent."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = entry
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
        if self.entry.options.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        assist_pipeline.async_migrate_engine(
            self.hass, "conversation", self.entry.entry_id, self.entity_id
        )
        conversation.async_set_agent(self.hass, self.entry, self)
        self.entry.async_on_unload(
            self.entry.add_update_listener(self._async_entry_update_listener)
        )

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        conversation_id = user_input.conversation_id or ulid.ulid_now()
        intent_response = intent.IntentResponse(language=user_input.language)

        # Get the client session from hass.data
        session: aiohttp.ClientSession = self.hass.data[DOMAIN][self.entry.entry_id]

        home_state = llm._get_exposed_entities(
            self.hass, conversation.DOMAIN
        )  # TODO: use _get_context()

        try:
            # Forward the conversation to the add-on with additional LLM context
            addon_url = ADDON_URL

            payload = {
                "text": user_input.text,
                "conversation_id": conversation_id,
                "language": user_input.language,
                "home_state": home_state,
            }

            async with session.post(
                f"{addon_url}/api/conversation",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise HomeAssistantError(
                        f"Error from add-on: {response.status} {await response.text()}"
                    )

                result = await response.json()
                intent_response.async_set_speech(result["response"])

        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Failed to communicate with Home Agent add-on: %s", err)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Failed to communicate with Home Agent: {err}",
            )

        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )

    async def _async_entry_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle options update."""
        await hass.config_entries.async_reload(entry.entry_id)


@callback
def _get_context(
    hass: HomeAssistant,
    llm_context: llm.LLMContext,
    exposed_entities: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Get the context to send to the Home Agent.

    NOTE: We avoid using the prompt from HA's built-in LLM API `APIInstance.api_prompt`
    and prefer delegating to the Home Agent to generate the prompt.

    Args:
        hass: The Home Assistant instance
        llm_context: The LLM context
        exposed_entities: Optional dict of exposed entities

    Returns:
        Dictionary containing context information

    """
    context = {}

    # Get location context if device_id provided
    if llm_context.device_id:
        device_reg = dr.async_get(hass)
        device = device_reg.async_get(llm_context.device_id)

        if device:
            location = {}
            area_reg = ar.async_get(hass)
            if device.area_id and (area := area_reg.async_get_area(device.area_id)):
                location["area"] = area.name
                floor_reg = fr.async_get(hass)
                if area.floor_id:
                    floor = floor_reg.async_get_floor(area.floor_id)
                    if floor:
                        location["floor"] = floor.name
            if location:
                context["location"] = location

    # Add device capabilities
    if llm_context.device_id:
        context["device_capabilities"] = {
            "supports_timers": async_device_supports_timers(hass, llm_context.device_id)
        }

    # Add exposed entities
    if exposed_entities:
        context["exposed_entities"] = exposed_entities

    return context
