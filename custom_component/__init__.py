"""The Home Agent integration."""

from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_ADDON_URL, DEFAULT_ADDON_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CONVERSATION]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Agent from a config entry."""
    # Create client session
    session = aiohttp.ClientSession()

    # Test connection to add-on
    addon_url = entry.data.get(CONF_ADDON_URL, DEFAULT_ADDON_URL)
    # try:
    #     async with session.get(f"{addon_url}/api/health") as response:
    #         if response.status != 200:
    #             raise ConfigEntryNotReady(
    #                 f"Failed to connect to Home Agent add-on: {response.status}"
    #             )
    # except aiohttp.ClientError as err:
    #     await session.close()
    #     raise ConfigEntryNotReady(
    #         f"Failed to connect to Home Agent add-on: {err}"
    #     ) from err

    # Store the session in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = session

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Home Agent."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close the session when unloading
        session = hass.data[DOMAIN].pop(entry.entry_id)
        await session.close()
    return unload_ok
