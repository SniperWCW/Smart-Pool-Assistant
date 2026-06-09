"""Config flow for Smart Pool Assistant integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION
)

class SmartPoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Pool Assistant."""

    VERSION = 1
    _notify_services: list[str] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Smart Pool Assistant", data=user_input)

        services = self.hass.services.async_services().get("notify", {})
        self._notify_services = [f"notify.{s}" for s in sorted(services.keys())]
        return self.async_show_form(step_id="user", data_schema=self._get_schema(notify_services=self._notify_services))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartPoolAssistantOptionsFlowHandler(config_entry)

    def _get_schema(self, defaults=None, notify_services=None):
        if defaults is None:
            defaults = {}
        
        if notify_services:
            notify_selector = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=notify_services,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value=True
                )
            )
        else:
            notify_selector = selector.TextSelector()

        return vol.Schema({
            vol.Required(CONF_CHLOR_SENSOR, default=defaults.get(CONF_CHLOR_SENSOR)): selector.EntitySelector({"domain": "sensor"}),
            vol.Required(CONF_PH_SENSOR, default=defaults.get(CONF_PH_SENSOR)): selector.EntitySelector({"domain": "sensor"}),
            vol.Required(CONF_TEMP_SENSOR, default=defaults.get(CONF_TEMP_SENSOR)): selector.EntitySelector({"domain": "sensor"}),
            vol.Required(CONF_POOL_VOLUME, default=defaults.get(CONF_POOL_VOLUME, 0.96)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="m³", step="any")
            ),
            vol.Required(CONF_CHLOR_TARGET, default=defaults.get(CONF_CHLOR_TARGET, 1.5)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="mg/l", step=0.1)
            ),
            vol.Required(CONF_PH_TARGET, default=defaults.get(CONF_PH_TARGET, 7.2)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=0.1)
            ),
            vol.Required(CONF_CHLOR_CONTENT, default=defaults.get(CONF_CHLOR_CONTENT, 0.56)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=0.01)
            ),
            vol.Required(CONF_PH_DOWN_DOSAGE, default=defaults.get(CONF_PH_DOWN_DOSAGE, 200.0)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="ml", step=1.0)
            ),
            vol.Required(CONF_PH_UP_DOSAGE, default=defaults.get(CONF_PH_UP_DOSAGE, 100.0)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="g", step=1.0)
            ),
            vol.Optional(CONF_NOTIFY_SERVICE, default=defaults.get(CONF_NOTIFY_SERVICE, "")): notify_selector,
            vol.Optional(CONF_PERSISTENT_NOTIFICATION, default=defaults.get(CONF_PERSISTENT_NOTIFICATION, False)): selector.BooleanSelector(),
            vol.Optional(CONF_FOLLOW_UP_TIME, default=defaults.get(CONF_FOLLOW_UP_TIME, 60)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min", step=1)
            ),
        })

class SmartPoolAssistantOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Kombiniere Daten und Optionen für die Standardwerte
        current_config = {**self.config_entry.data, **self.config_entry.options}

        services = self.hass.services.async_services().get("notify", {})
        notify_list = [f"notify.{s}" for s in sorted(services.keys())]

        # Instanziieren eines ConfigFlow-Objekts um Zugriff auf die Schema-Logik zu erhalten
        config_flow = SmartPoolAssistantConfigFlow()

        return self.async_show_form(
            step_id="init",
            data_schema=config_flow._get_schema(current_config, notify_services=notify_list)
        )