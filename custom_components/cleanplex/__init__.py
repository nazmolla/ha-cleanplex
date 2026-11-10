"""The Cleanplex integration: status and scan control for a Cleanplex server."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CleanplexApi
from .coordinator import CleanplexCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.EVENT]

type CleanplexConfigEntry = ConfigEntry[CleanplexCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CleanplexConfigEntry) -> bool:
    """Create the coordinator, do the first poll and set up the platforms."""
    api = CleanplexApi(async_get_clientsession(hass), entry.data[CONF_URL])
    coordinator = CleanplexCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CleanplexConfigEntry) -> bool:
    """Unload the platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
