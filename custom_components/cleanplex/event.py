"""Cleanplex event entity: fires once for every skip or mute Cleanplex performs, for automations."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CleanplexConfigEntry
from .entity import CleanplexEntity

EVENT_TYPES = ["skip", "mute"]


async def async_setup_entry(hass: HomeAssistant, entry: CleanplexConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Add the filter-action event entity."""
    async_add_entities([CleanplexFilterEvent(entry.runtime_data)])


class CleanplexFilterEvent(CleanplexEntity, EventEntity):
    """Triggers when a new skip-history row appears; attributes carry title, user, client and category."""

    _attr_translation_key = "filter_action"
    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "filter_action")
        # Start at the newest existing row so the history is not replayed after a restart.
        self._last_id = max((e["id"] for e in coordinator.data["recent_skips"]), default=0)

    @callback
    def _handle_coordinator_update(self) -> None:
        # recent_skips is newest first and holds at most the last few rows; older ones are dropped.
        new = [e for e in reversed(self.coordinator.data["recent_skips"]) if e["id"] > self._last_id]
        for event in new:
            self._last_id = event["id"]
            action = event["action"] if event["action"] in EVENT_TYPES else "skip"
            self._trigger_event(action, {
                "title": event["title"], "user": event["user"], "client": event["client"],
                "category": event["category"], "success": event["success"],
            })
        if new:
            self.async_write_ha_state()
        super()._handle_coordinator_update()
