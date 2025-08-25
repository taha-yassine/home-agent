"""The conversation platform for Home Agent."""

from __future__ import annotations

from collections.abc import Callable
import logging
import time
from typing import Any, Literal

import httpx
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
    DEFAULT_MAX_HISTORY,
    DOMAIN,
    MAX_HISTORY_SECONDS,
    CONF_STREAMING,
    DEFAULT_STREAMING,
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
    _attr_supports_streaming = True

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
        conversation.async_set_agent(self.hass, self.entry, self)

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
        client: httpx.AsyncClient = self.entry.runtime_data

        payload = {
            "text": user_input.text,
            "conversation_id": user_input.conversation_id or ulid.ulid_now(),
            "language": user_input.language,
        }

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                self.entry.options.get(CONF_LLM_HASS_API),
                None,
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        streaming = self.entry.options.get(CONF_STREAMING, DEFAULT_STREAMING)

        try:
            if streaming:
                async with client.stream(
                    "POST",
                    "/api/agent/conversation",
                    params={"stream": True},
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_text = (
                            (await response.aread()).decode()
                            if response.content is None
                            else response.text
                        )
                        raise HomeAssistantError(
                            f"Error from add-on: {response.status_code} {error_text}"
                        )

                    async def _delta_stream():
                        """Yield assistant deltas from HTTP stream (text only)."""
                        new_message = True
                        async for chunk in response.aiter_text():
                            if new_message:
                                new_message = False
                                yield {"role": "assistant"}
                            if chunk:
                                yield {"content": chunk}

                    async for _ in chat_log.async_add_delta_content_stream(
                        self.entity_id, _delta_stream()
                    ):
                        pass
            else:
                resp = await client.post(
                    "/api/agent/conversation",
                    params={"stream": False},
                    json=payload,
                )
                if resp.status_code != 200:
                    raise HomeAssistantError(
                        f"Error from add-on: {resp.status_code} {resp.text}"
                    )
                data = resp.json()
                chat_log.async_add_assistant_content_without_tools(
                    conversation.AssistantContent(
                        agent_id=self.entity_id, content=data.get("response", "")
                    )
                )

        except (httpx.HTTPError, TimeoutError) as err:
            _LOGGER.error("Failed to communicate with Home Agent: %s", err)
            raise HomeAssistantError(
                f"Failed to communicate with Home Agent: {err}"
            ) from err

        return conversation.async_get_result_from_chat_log(user_input, chat_log)

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
