"""Cleanplex sensors: queue, scan progress, library counts and streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CleanplexConfigEntry
from .entity import CleanplexEntity


@dataclass(frozen=True, kw_only=True)
class CleanplexSensorDescription(SensorEntityDescription):
    """A sensor reading one key of the coordinator data."""


SENSORS: tuple[CleanplexSensorDescription, ...] = (
    CleanplexSensorDescription(key="queue_size", translation_key="queue_size", state_class=SensorStateClass.MEASUREMENT),
    CleanplexSensorDescription(key="scan_progress", translation_key="scan_progress",
                               native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    CleanplexSensorDescription(key="current_title", translation_key="current_title"),
    CleanplexSensorDescription(key="workers_active", translation_key="workers_active",
                               state_class=SensorStateClass.MEASUREMENT),
    CleanplexSensorDescription(key="titles_scanned", translation_key="titles_scanned",
                               state_class=SensorStateClass.TOTAL),
    CleanplexSensorDescription(key="titles_pending", translation_key="titles_pending",
                               state_class=SensorStateClass.MEASUREMENT),
    CleanplexSensorDescription(key="titles_failed", translation_key="titles_failed",
                               state_class=SensorStateClass.MEASUREMENT),
    CleanplexSensorDescription(key="active_streams", translation_key="active_streams",
                               state_class=SensorStateClass.MEASUREMENT),
    CleanplexSensorDescription(key="filtered_streams", translation_key="filtered_streams",
                               state_class=SensorStateClass.MEASUREMENT),
)


async def async_setup_entry(hass: HomeAssistant, entry: CleanplexConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Add one sensor per description."""
    async_add_entities(CleanplexSensor(entry.runtime_data, d) for d in SENSORS)


class CleanplexSensor(CleanplexEntity, SensorEntity):
    """A numeric or text value from Cleanplex."""

    entity_description: CleanplexSensorDescription

    def __init__(self, coordinator, description: CleanplexSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.coordinator.data[self.entity_description.key]
