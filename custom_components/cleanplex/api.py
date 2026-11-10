"""Cleanplex HTTP API client and response parsing (no Home Assistant imports, so it is unit-testable)."""

from __future__ import annotations

from typing import Any

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=15)


class CleanplexError(Exception):
    """Cleanplex could not be reached or answered with an error."""


class CleanplexApi:
    """Thin client over the Cleanplex web API (the endpoints its own web UI uses)."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str) -> None:
        self._session = session
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str) -> Any:
        try:
            async with self._session.request(method, f"{self.base_url}{path}", timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise CleanplexError(str(err)) from err

    async def fetch_all(self) -> dict[str, Any]:
        """Poll everything the entities need. Scanner status and queue are required; the rest is best effort."""
        status = await self._request("GET", "/api/sessions/scanner-status")
        queue = await self._request("GET", "/api/scan/queue?limit=1")  # limit=1: only the per-status counts matter
        try:
            sessions = await self._request("GET", "/api/sessions")
        except CleanplexError:
            sessions = {"error": "unreachable"}
        try:
            enforcement = await self._request("GET", "/api/enforcement")
        except CleanplexError:
            enforcement = {}
        return parse_data(status, queue, sessions, enforcement)

    async def set_scanning(self, enabled: bool) -> None:
        """Resume (True) or pause (False) the scanner."""
        await self._request("POST", "/api/scan/resume" if enabled else "/api/scan/pause")


def parse_data(status: dict, queue: dict, sessions: dict, enforcement: dict) -> dict[str, Any]:
    """Turn the raw API answers into the flat values the entities read."""
    counts = queue.get("counts", {}) or {}
    active_scans = status.get("active_scans", []) or []
    streams = sessions.get("sessions", []) or []
    return {
        "scanner_enabled": not status.get("paused", False),
        "scanning": bool(active_scans),
        "queue_size": int(status.get("queue_size", 0) or 0),
        "scan_progress": round(float(status.get("current_progress", 0.0) or 0.0) * 100, 1),
        "current_title": status.get("current_title") or "",
        "workers_active": int(status.get("workers_active", 0) or 0),
        "titles_total": sum(int(n) for n in counts.values()),
        "titles_scanned": int(counts.get("done", 0)),
        "titles_pending": int(counts.get("pending", 0)),
        "titles_failed": int(counts.get("failed", 0)),
        "active_streams": len(streams),
        "filtered_streams": sum(1 for s in streams if s.get("filtering_state") == "active"),
        "plex_connected": "error" not in sessions,
        "front_door_enabled": bool(enforcement.get("enabled", False)),
    }
