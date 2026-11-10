"""parse_data: raw Cleanplex answers to entity values (loaded without Home Assistant)."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("cp_api", Path(__file__).parent.parent / "custom_components/cleanplex/api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def test_parse_full_answers():
    data = api.parse_data(
        {"paused": False, "queue_size": 4, "current_progress": 0.425, "workers_active": 1,
         "active_scans": [{"guid": "g"}], "current_title": "X"},
        {"counts": {"done": 120, "pending": 4, "failed": 2}},
        {"sessions": [{"filtering_state": "active"}, {"filtering_state": "clear"}]},
        {"enabled": True},
    )
    assert data["scan_progress"] == 42.5 and data["scanning"] is True and data["scanner_enabled"] is True
    assert (data["titles_total"], data["titles_scanned"], data["titles_failed"]) == (126, 120, 2)
    assert (data["active_streams"], data["filtered_streams"]) == (2, 1)
    assert data["front_door_enabled"] is True and data["plex_connected"] is True


def test_parse_handles_a_paused_idle_server_with_plex_down():
    data = api.parse_data({"paused": True}, {}, {"error": "Plex not configured"}, {})
    assert data["scanner_enabled"] is False and data["scanning"] is False
    assert data["plex_connected"] is False and data["titles_total"] == 0 and data["front_door_enabled"] is False


def test_parse_skip_history_and_streams():
    data = api.parse_data(
        {}, {}, {"sessions": [{"user": "a", "title": "T", "client": "C", "filtering_state": "active"}]}, {},
        {"total": 5, "events": [{"id": 5, "created_at": "2026-11-10 15:00:00", "title": "T", "username": "a",
                                 "client_title": "C", "category": "profanity", "action": "mute", "success": 0}]},
        {"total": 2}, {"total": 7},
    )
    assert (data["skips_total"], data["skips_24h"], data["false_positives"]) == (5, 2, 7)
    last = data["last_skip"]
    assert last["time"].isoformat() == "2026-11-10T15:00:00+00:00" and last["success"] is False
    assert last["user"] == "a" and last["action"] == "mute"
    assert data["streams"][0]["filtering"] == "active"


def test_parse_without_skip_history_from_an_older_cleanplex():
    data = api.parse_data({}, {}, {}, {})
    assert data["last_skip"] is None and data["skips_total"] == 0 and data["recent_skips"] == []
