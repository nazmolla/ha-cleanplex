"""Cleanplex switch: pause and resume scanning."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CleanplexConfigEntry
from .entity import CleanplexEntity


async def async_setup_entry(hass: HomeAssistant, entry: CleanplexConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Add the scanner switch."""
    async_add_entities([CleanplexScannerSwitch(entry.runtime_data)])


class CleanplexScannerSwitch(CleanplexEntity, SwitchEntity):
    """On while the scanner may run; off while paused."""

    _attr_translation_key = "scanner"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "scanner")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data["scanner_enabled"])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_scanning(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_scanning(False)
        await self.coordinator.async_request_refresh()
