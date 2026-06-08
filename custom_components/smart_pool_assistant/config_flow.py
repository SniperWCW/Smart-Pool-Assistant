"""Config flow for Smart Pool Assistant integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME
)

class SmartPoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Pool Assistant."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Smart Pool Assistant", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CHLOR_SENSOR): selector.EntitySelector({"domain": "sensor"}),
                vol.Required(CONF_PH_SENSOR): selector.EntitySelector({"domain": "sensor"}),
                vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector({"domain": "sensor"}),
                vol.Required(CONF_POOL_VOLUME, default=0.96): vol.Coerce(float),
                vol.Required(CONF_CHLOR_TARGET, default=1.5): vol.Coerce(float),
                vol.Required(CONF_PH_TARGET, default=7.2): vol.Coerce(float),
                vol.Required(CONF_CHLOR_CONTENT, default=0.56): vol.Coerce(float),
                vol.Required(CONF_PH_DOWN_DOSAGE, default=200.0): vol.Coerce(float),
                vol.Required(CONF_PH_UP_DOSAGE, default=100.0): vol.Coerce(float),
                vol.Optional(CONF_NOTIFY_SERVICE): selector.TextSelector(),
                vol.Optional(CONF_FOLLOW_UP_TIME, default=60): vol.Coerce(int),
            })
        )