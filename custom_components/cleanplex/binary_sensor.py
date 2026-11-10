"""Cleanplex binary sensors: scanning, Plex connection and the front door."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CleanplexConfigEntry
from .entity import CleanplexEntity

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(key="scanning", translation_key="scanning", device_class=BinarySensorDeviceClass.RUNNING),
    BinarySensorEntityDescription(key="plex_connected", translation_key="plex_connected",
                                  device_class=BinarySensorDeviceClass.CONNECTIVITY),
    BinarySensorEntityDescription(key="front_door_enabled", translation_key="front_door_enabled"),
)


async def async_setup_entry(hass: HomeAssistant, entry: CleanplexConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Add one binary sensor per description."""
    async_add_entities(CleanplexBinarySensor(entry.runtime_data, d) for d in BINARY_SENSORS)


class CleanplexBinarySensor(CleanplexEntity, BinarySensorEntity):
    """A true/false value from Cleanplex."""

    def __init__(self, coordinator, description: BinarySensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data[self.entity_description.key])
