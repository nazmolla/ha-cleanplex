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
