"""Shared fixtures: canned Cleanplex API answers and an added config entry."""

import re

import pytest
from homeassistant.const import CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.cleanplex.const import DOMAIN

BASE = "http://cleanplex.test:7979"

STATUS = {"paused": False, "queue_size": 4, "current_progress": 0.425, "current_title": "Some Movie",
          "workers_active": 1, "active_scans": [{"guid": "g", "title": "Some Movie", "progress": 0.425}]}
QUEUE = {"counts": {"done": 120, "pending": 4, "failed": 2, "scanning": 1}}
SESSIONS = {"sessions": [{"filtering_state": "active"}, {"filtering_state": "clear"}]}
ENFORCEMENT = {"enabled": True}
SKIPS = {"total": 57, "events": [
    {"id": 57, "created_at": "2026-11-10 15:00:00", "title": "Some Movie", "username": "kid", "client_title": "Living room",
     "category": "sex_nudity", "action": "skip", "success": 1},
    {"id": 56, "created_at": "2026-11-10 14:00:00", "title": "Other", "username": "kid", "client_title": "Phone",
     "category": "profanity", "action": "mute", "success": 1},
]}
SKIPS_DAY = {"total": 3, "events": SKIPS["events"][:1]}
FALSE_POSITIVES = {"total": 9, "segments": []}


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components from this repo."""


@pytest.fixture
def skips_state():
    """The skip history the fake API serves; a test replaces ["data"] to simulate new skips."""
    return {"data": SKIPS}


@pytest.fixture
def mock_api(aioclient_mock, skips_state):
    aioclient_mock.get(f"{BASE}/api/sessions/scanner-status", json=STATUS)
    aioclient_mock.get(f"{BASE}/api/scan/queue?limit=1", json=QUEUE)
    aioclient_mock.get(re.compile(rf"{re.escape(BASE)}/api/analytics/skips/history\?limit=1&start="), json=SKIPS_DAY)
    async def skips(method, url, data):
        return AiohttpClientMockResponse(method, url, json=skips_state["data"])

    aioclient_mock.get(f"{BASE}/api/analytics/skips/history?limit=5", side_effect=skips)
    aioclient_mock.get(f"{BASE}/api/analytics/false-positives?limit=1", json=FALSE_POSITIVES)
    aioclient_mock.get(f"{BASE}/api/sessions", json=SESSIONS)
    aioclient_mock.get(f"{BASE}/api/enforcement", json=ENFORCEMENT)
    aioclient_mock.post(f"{BASE}/api/scan/pause", json={"ok": True, "paused": True})
    aioclient_mock.post(f"{BASE}/api/scan/resume", json={"ok": True, "paused": False})
    return aioclient_mock


@pytest.fixture
async def entry(hass, mock_api):
    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE}, unique_id=BASE)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
