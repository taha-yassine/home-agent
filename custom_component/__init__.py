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
from .api import async_register_api_endpoints

_LOGGER = logging.getLogger(__name__)

PLATFORMS: tuple[Platform, ...] = (Platform.CONVERSATION,)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Agent from a config entry."""
    # Create client
    client = httpx.AsyncClient(
        base_url=ADDON_URL,
        timeout=httpx.Timeout(None),  # TODO: Modify once streaming is implemented
    )

    # Store the client on the config entry
    entry.runtime_data = client

    # TODO: Enable connectivity testing for the add-on
    # try:
    #     async with asyncio.timeout(10):
    #         resp = await client.get("/api/health")
    #         resp.raise_for_status()
    # except (TimeoutError, httpx.ConnectError, httpx.HTTPError) as err:
    #     await client.aclose()
    #     raise ConfigEntryNotReady(err) from err

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry on options update
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Register API endpoint
    async_register_api_endpoints(hass)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options by reloading the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Home Agent."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close the client when unloading
        client = entry.runtime_data
        await client.aclose()
    return unload_ok
