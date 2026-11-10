"""Cleanplex HTTP API client and response parsing (no Home Assistant imports, so it is unit-testable)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
        # Skip history and false-positive totals are nice to have: an older Cleanplex may lack them.
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        skips = await self._optional("/api/analytics/skips/history?limit=5")
        skips_day = await self._optional(f"/api/analytics/skips/history?limit=1&start={since}")
        false_positives = await self._optional("/api/analytics/false-positives?limit=1")
        return parse_data(status, queue, sessions, enforcement, skips, skips_day, false_positives)

    async def _optional(self, path: str) -> dict:
        try:
            return await self._request("GET", path)
        except CleanplexError:
            return {}

    async def set_scanning(self, enabled: bool) -> None:
        """Resume (True) or pause (False) the scanner."""
        await self._request("POST", "/api/scan/resume" if enabled else "/api/scan/pause")


def parse_data(status: dict, queue: dict, sessions: dict, enforcement: dict, skips: dict | None = None,
               skips_day: dict | None = None, false_positives: dict | None = None) -> dict[str, Any]:
    """Turn the raw API answers into the flat values the entities read."""
    skips, skips_day, false_positives = skips or {}, skips_day or {}, false_positives or {}
    recent = [_skip(e) for e in skips.get("events", []) or []]
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
        "streams": [
            {"user": s.get("user", ""), "title": s.get("title", ""), "client": s.get("client", ""),
             "filtering": s.get("filtering_state", "")}
            for s in streams
        ],
        "skips_total": int(skips.get("total", 0) or 0),
        "skips_24h": int(skips_day.get("total", 0) or 0),
        "false_positives": int(false_positives.get("total", 0) or 0),
        "recent_skips": recent,  # newest first
        "last_skip": recent[0] if recent else None,
    }


def _skip(event: dict) -> dict[str, Any]:
    """One skip-history row, trimmed to what Home Assistant shows. created_at is naive UTC."""
    created = None
    try:
        created = datetime.strptime(event["created_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (KeyError, ValueError, TypeError):
        pass
    return {
        "id": int(event.get("id", 0) or 0),
        "time": created,
        "title": event.get("title", ""),
        "user": event.get("username", ""),
        "client": event.get("client_title", ""),
        "category": event.get("category", ""),
        "action": event.get("action", "skip"),
        "success": bool(event.get("success", 1)),
    }
