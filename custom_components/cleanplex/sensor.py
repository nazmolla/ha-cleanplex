"""Cleanplex sensors: queue, scan progress, library counts, streams and skip history."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CleanplexConfigEntry
from .entity import CleanplexEntity


@dataclass(frozen=True, kw_only=True)
class CleanplexSensorDescription(SensorEntityDescription):
    """A sensor reading one key of the coordinator data, or a computed value."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _filtered(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for s in data["streams"] if s["filtering"] == "active"]


def _last_skip_attrs(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in (data["last_skip"] or {}).items() if k != "time"}


M = SensorStateClass.MEASUREMENT

SENSORS: tuple[CleanplexSensorDescription, ...] = (
    CleanplexSensorDescription(key="queue_size", translation_key="queue_size", state_class=M),
    CleanplexSensorDescription(key="scan_progress", translation_key="scan_progress",
                               native_unit_of_measurement=PERCENTAGE, state_class=M),
    CleanplexSensorDescription(key="current_title", translation_key="current_title"),
    CleanplexSensorDescription(key="workers_active", translation_key="workers_active", state_class=M),
    CleanplexSensorDescription(key="titles_scanned", translation_key="titles_scanned",
                               state_class=SensorStateClass.TOTAL),
    CleanplexSensorDescription(key="titles_pending", translation_key="titles_pending", state_class=M),
    CleanplexSensorDescription(key="titles_failed", translation_key="titles_failed", state_class=M),
    CleanplexSensorDescription(key="active_streams", translation_key="active_streams", state_class=M,
                               attrs_fn=lambda d: {"streams": d["streams"]}),
    CleanplexSensorDescription(key="filtered_streams", translation_key="filtered_streams", state_class=M,
                               value_fn=lambda d: len(_filtered(d)),
                               attrs_fn=lambda d: {"streams": _filtered(d)}),
    CleanplexSensorDescription(key="skips_total", translation_key="skips_total",
                               state_class=SensorStateClass.TOTAL_INCREASING),
    CleanplexSensorDescription(key="skips_24h", translation_key="skips_24h", state_class=M),
    CleanplexSensorDescription(key="false_positives", translation_key="false_positives", state_class=M),
    CleanplexSensorDescription(key="last_skip", translation_key="last_skip",
                               device_class=SensorDeviceClass.TIMESTAMP,
                               value_fn=lambda d: d["last_skip"]["time"] if d["last_skip"] else None,
                               attrs_fn=_last_skip_attrs),
)


async def async_setup_entry(hass: HomeAssistant, entry: CleanplexConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Add one sensor per description."""
    async_add_entities(CleanplexSensor(entry.runtime_data, d) for d in SENSORS)


class CleanplexSensor(CleanplexEntity, SensorEntity):
    """A numeric, text or timestamp value from Cleanplex."""

    entity_description: CleanplexSensorDescription

    def __init__(self, coordinator, description: CleanplexSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        d = self.entity_description
        return d.value_fn(self.coordinator.data) if d.value_fn else self.coordinator.data[d.key]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        d = self.entity_description
        return d.attrs_fn(self.coordinator.data) if d.attrs_fn else None
