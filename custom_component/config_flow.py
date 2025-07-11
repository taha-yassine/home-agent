"""Config flow for the Home Agent integration."""

from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HomeAgentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Agent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="Home Agent", data={})

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return HomeAgentOptionsFlow(config_entry)


class HomeAgentOptionsFlow(OptionsFlow):
    """Home Agent options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry  # TODO: deprecated, fix this

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            if user_input[CONF_LLM_HASS_API] == "none":
                user_input.pop(CONF_LLM_HASS_API)
            return self.async_create_entry(title="", data=user_input)

        schema = {
            vol.Optional(
                CONF_LLM_HASS_API,
                description={
                    "suggested_value": self.config_entry.options.get(CONF_LLM_HASS_API)
                },
                default="none",
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            label="No control",
                            value="none",
                        )
                    ]
                    + [
                        SelectOptionDict(
                            label=api.name,
                            value=api.id,
                        )
                        for api in llm.async_get_apis(self.hass)
                    ]
                )
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
