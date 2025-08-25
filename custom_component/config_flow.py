"""Config flow for the Home Agent integration."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    BooleanSelector,
    BooleanSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_STREAMING,
    DEFAULT_STREAMING,
)


class HomeAgentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Agent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

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
        self._options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_llm_option = self._options.get(CONF_LLM_HASS_API)
        if current_llm_option == "none":
            current_llm_option = None

        schema = {
            vol.Optional(
                CONF_LLM_HASS_API,
                description={"suggested_value": current_llm_option},
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(label=api.name, value=api.id)
                        for api in sorted(
                            llm.async_get_apis(self.hass), key=lambda a: a.name
                        )
                    ],
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_STREAMING,
                default=self._options.get(CONF_STREAMING, DEFAULT_STREAMING),
            ): BooleanSelector(BooleanSelectorConfig()),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
