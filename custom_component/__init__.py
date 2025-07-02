"""The Home Agent integration."""

from __future__ import annotations

import logging

import httpx

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, ADDON_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CONVERSATION]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Agent from a config entry."""
    # Create client
    client = httpx.AsyncClient()

    # Test connection to add-on
    # try:
    #     async with client.get(f"{addon_url}/api/health") as response:
    #         if response.status != 200:
    #             raise ConfigEntryNotReady(
    #                 f"Failed to connect to Home Agent add-on: {response.status}"
    #             )
    # except httpx.HTTPError as err:
    #     await client.aclose()
    #     raise ConfigEntryNotReady(
    #         f"Failed to connect to Home Agent add-on: {err}"
    #     ) from err

    # Store the client in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Home Agent."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close the client when unloading
        client = hass.data[DOMAIN].pop(entry.entry_id)
        await client.aclose()
    return unload_ok
