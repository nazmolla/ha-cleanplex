"""Polling coordinator shared by every Cleanplex entity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CleanplexApi, CleanplexError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CleanplexCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches Cleanplex's scanner, queue and stream state every SCAN_INTERVAL."""

    def __init__(self, hass: HomeAssistant, api: CleanplexApi) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.fetch_all()
        except CleanplexError as err:
            raise UpdateFailed(f"Cannot reach Cleanplex: {err}") from err
