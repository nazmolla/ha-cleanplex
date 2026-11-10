"""Config flow, entities and the scanner switch against canned API answers."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_URL, STATE_OFF, STATE_ON
from homeassistant.data_entry_flow import FlowResultType

from custom_components.cleanplex.const import DOMAIN

from .conftest import BASE


async def test_config_flow_creates_an_entry(hass, mock_api):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: "cleanplex.test:7979/"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_URL: BASE}


async def test_config_flow_reports_an_unreachable_server(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/api/sessions/scanner-status", status=500)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_URL: BASE})
    assert result["errors"] == {"base": "cannot_connect"}


async def test_sensors_show_the_polled_values(hass, entry):
    assert hass.states.get("sensor.cleanplex_scan_queue").state == "4"
    assert hass.states.get("sensor.cleanplex_scan_progress").state == "42.5"
    assert hass.states.get("sensor.cleanplex_titles_scanned").state == "120"
    assert hass.states.get("sensor.cleanplex_filtered_streams").state == "1"
    assert hass.states.get("binary_sensor.cleanplex_scanning").state == STATE_ON
    assert hass.states.get("binary_sensor.cleanplex_front_door").state == STATE_ON


async def test_switch_pauses_and_resumes_the_scanner(hass, entry, mock_api):
    assert hass.states.get("switch.cleanplex_scanner").state == STATE_ON
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.cleanplex_scanner"}, blocking=True)
    assert any(c[0] == "POST" and str(c[1]).endswith("/api/scan/pause") for c in mock_api.mock_calls)
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.cleanplex_scanner"}, blocking=True)
    assert any(c[0] == "POST" and str(c[1]).endswith("/api/scan/resume") for c in mock_api.mock_calls)
    assert hass.states.get("switch.cleanplex_scanner").state in (STATE_ON, STATE_OFF)


async def test_skip_history_sensors_and_attributes(hass, entry):
    assert hass.states.get("sensor.cleanplex_skips_total").state == "57"
    assert hass.states.get("sensor.cleanplex_skips_24_h").state == "3"
    assert hass.states.get("sensor.cleanplex_false_positives").state == "9"
    last = hass.states.get("sensor.cleanplex_last_skip")
    assert last.state == "2026-11-10T15:00:00+00:00"
    assert last.attributes["title"] == "Some Movie" and last.attributes["category"] == "sex_nudity"
    streams = hass.states.get("sensor.cleanplex_active_streams")
    assert len(streams.attributes["streams"]) == 2
    assert len(hass.states.get("sensor.cleanplex_filtered_streams").attributes["streams"]) == 1


async def test_event_entity_fires_only_for_new_skips(hass, entry, skips_state):
    from datetime import timedelta
    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    from .conftest import SKIPS

    state = hass.states.get("event.cleanplex_filter_action")
    assert state is not None and state.attributes.get("event_type") is None  # history is not replayed
    skips_state["data"] = {"total": 58, "events": [
        {"id": 58, "created_at": "2026-11-10 16:00:00", "title": "New", "username": "kid", "client_title": "TV",
         "category": "profanity", "action": "mute", "success": 1}, *SKIPS["events"]]}
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=45))
    await hass.async_block_till_done()
    state = hass.states.get("event.cleanplex_filter_action")
    assert state.attributes["event_type"] == "mute" and state.attributes["title"] == "New"
