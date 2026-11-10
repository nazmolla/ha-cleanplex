"""Config flow: ask for the Cleanplex URL and check that it answers."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CleanplexApi, CleanplexError
from .const import DEFAULT_PORT, DOMAIN


class CleanplexConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a Cleanplex server by URL."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if "://" not in url:
                url = f"http://{url}"
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()
            try:
                await CleanplexApi(async_get_clientsession(self.hass), url).fetch_all()
            except CleanplexError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="Cleanplex", data={CONF_URL: url})
        schema = vol.Schema({vol.Required(CONF_URL, default=f"http://homeassistant.local:{DEFAULT_PORT}"): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
