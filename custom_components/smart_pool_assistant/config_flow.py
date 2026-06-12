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
    , CONF_FILTER_CLEAN_INTERVAL, CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD, CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD, CONF_FILTER_REPLACE_RED_THRESHOLD
)
CONF_API_KEY = "api_key"

class SmartPoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Pool Assistant."""

    VERSION = 1
    _notify_services: list[str] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            chlor_sensor = user_input.get(CONF_CHLOR_SENSOR)
            ph_sensor = user_input.get(CONF_PH_SENSOR)

            if not api_key and (not chlor_sensor or not ph_sensor):
                errors["base"] = "missing_data_source"
            else:
                return self.async_create_entry(title="Smart Pool Assistant", data=user_input)

        services = self.hass.services.async_services().get("notify", {})
        self._notify_services = [f"notify.{s}" for s in sorted(services.keys())]
        return self.async_show_form(step_id="user", data_schema=self._get_schema(user_input or {}, notify_services=self._notify_services), errors=errors)

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
            vol.Optional(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
            vol.Optional(CONF_CHLOR_SENSOR, default=defaults.get(CONF_CHLOR_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
            vol.Optional(CONF_PH_SENSOR, default=defaults.get(CONF_PH_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
            vol.Optional(CONF_TEMP_SENSOR, default=defaults.get(CONF_TEMP_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
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
            vol.Required(CONF_FILTER_CLEAN_INTERVAL, default=defaults.get(CONF_FILTER_CLEAN_INTERVAL, 30)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=1)
            ),
            vol.Required(CONF_FILTER_REPLACE_INTERVAL, default=defaults.get(CONF_FILTER_REPLACE_INTERVAL, 180)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=1)
            ),
            vol.Required(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, default=defaults.get(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, 7)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=0)
            ),
            vol.Required(CONF_FILTER_CLEAN_RED_THRESHOLD, default=defaults.get(CONF_FILTER_CLEAN_RED_THRESHOLD, 0)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=0)
            ),
            vol.Required(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, default=defaults.get(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, 30)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=0)
            ),
            vol.Required(CONF_FILTER_REPLACE_RED_THRESHOLD, default=defaults.get(CONF_FILTER_REPLACE_RED_THRESHOLD, 0)): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=0)
            ),
        })

class SmartPoolAssistantOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._notify_services: list[str] = [] # Initialize _notify_services

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            chlor_sensor = user_input.get(CONF_CHLOR_SENSOR)
            ph_sensor = user_input.get(CONF_PH_SENSOR)

            if not api_key and (not chlor_sensor or not ph_sensor):
                errors["base"] = "missing_data_source"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Kombiniere Daten und Optionen für die Standardwerte
        current_config = {**self.config_entry.data, **self.config_entry.options}
        if user_input:
            current_config.update(user_input)

        services = self.hass.services.async_services().get("notify", {})
        notify_list = [f"notify.{s}" for s in sorted(services.keys())]

        # Instanziieren eines ConfigFlow-Objekts um Zugriff auf die Schema-Logik zu erhalten
        config_flow = SmartPoolAssistantConfigFlow()

        return self.async_show_form(
            step_id="init",
            data_schema=config_flow._get_schema(current_config, notify_services=notify_list),
            errors=errors
        )