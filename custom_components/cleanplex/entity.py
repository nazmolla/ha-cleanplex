"""Base entity: groups every Cleanplex entity under one device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CleanplexCoordinator


class CleanplexEntity(CoordinatorEntity[CleanplexCoordinator]):
    """An entity backed by the Cleanplex coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CleanplexCoordinator, key: str) -> None:
        super().__init__(coordinator)
        base = coordinator.api.base_url
        self._attr_unique_id = f"{base}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, base)}, name="Cleanplex", manufacturer="Cleanplex", configuration_url=base,
        )
