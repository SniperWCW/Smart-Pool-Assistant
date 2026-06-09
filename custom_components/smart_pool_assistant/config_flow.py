"""Config flow for Smart Pool Assistant integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components import bluetooth
from homeassistant.helpers import selector

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION,
    CONF_BLE_ADDRESS, CONF_API_KEY
)

class SmartPoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Pool Assistant."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 1: Select Data Source."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_source_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("data_source", default="ble_api"): selector.selector({
                    "select": {
                        "options": [
                            {"label": "Bluetooth (PoolLab) + API Backup", "value": "ble_api"},
                            {"label": "Nur Cloud API", "value": "api"},
                            {"label": "Manuelle Sensoren", "value": "manual"},
                        ],
                        "mode": selector.SelectSelectorMode.LIST,
                    }
                }),
            })
        )

    async def async_step_source_config(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2: Configure the selected source."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pool_config()

        schema = {}
        source = self._data.get("data_source")

        if source in ["ble_api", "api"]:
            schema[vol.Required(CONF_API_KEY)] = selector.selector({"text": {"type": "password"}})

        if source == "ble_api":
            # Discover PoolLab devices
            discovered = bluetooth.async_discovered_service_info(self.hass)
            options = []
            for service_info in discovered:
                name = service_info.name or service_info.address
                if "PoolLab" in name:
                    options.append({"label": name, "value": service_info.address})
            
            if options:
                schema[vol.Optional(CONF_BLE_ADDRESS)] = selector.selector({
                    "select": {
                        "options": options,
                        "mode": selector.SelectSelectorMode.DROPDOWN
                    }
                })
            else:
                schema[vol.Optional(CONF_BLE_ADDRESS)] = selector.selector({"text": {}})

        if source == "manual":
            schema[vol.Required(CONF_CHLOR_SENSOR)] = selector.selector({"entity": {"domain": "sensor"}})
            schema[vol.Required(CONF_PH_SENSOR)] = selector.selector({"entity": {"domain": "sensor"}})
            schema[vol.Optional(CONF_TEMP_SENSOR)] = selector.selector({"entity": {"domain": "sensor"}})

        return self.async_show_form(step_id="source_config", data_schema=vol.Schema(schema))

    async def async_step_pool_config(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Finalize pool parameters and notification."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="Smart Pool Assistant", data=self._data)

        return self.async_show_form(
            step_id="pool_config",
            data_schema=vol.Schema({
                vol.Required(CONF_POOL_VOLUME, default=0.96): vol.Coerce(float),
                vol.Required(CONF_CHLOR_TARGET, default=1.5): vol.Coerce(float),
                vol.Required(CONF_PH_TARGET, default=7.2): vol.Coerce(float),
                vol.Required(CONF_CHLOR_CONTENT, default=0.56): vol.Coerce(float),
                vol.Required(CONF_PH_DOWN_DOSAGE, default=200.0): vol.Coerce(float),
                vol.Required(CONF_PH_UP_DOSAGE, default=100.0): vol.Coerce(float),
                vol.Optional(CONF_NOTIFY_SERVICE): selector.selector({"service": {"domain": "notify"}}),
                vol.Optional(CONF_PERSISTENT_NOTIFICATION, default=False): selector.selector({"boolean": {}}),
                vol.Optional(CONF_FOLLOW_UP_TIME, default=60): vol.Coerce(int),
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartPoolAssistantOptionsFlowHandler(config_entry)

    def _get_schema(self, defaults=None):
        if defaults is None:
            defaults = {}
        # Diese Methode wird nun primär für den OptionsFlow genutzt
        return vol.Schema({
            vol.Optional(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): selector.selector({"text": {"type": "password"}}),
            vol.Optional(CONF_BLE_ADDRESS, default=defaults.get(CONF_BLE_ADDRESS, "")): selector.selector({"text": {}}),
            vol.Optional(CONF_CHLOR_SENSOR, default=defaults.get(CONF_CHLOR_SENSOR)): selector.selector({"entity": {"domain": "sensor"}}),
            vol.Optional(CONF_PH_SENSOR, default=defaults.get(CONF_PH_SENSOR)): selector.selector({"entity": {"domain": "sensor"}}),
            vol.Optional(CONF_TEMP_SENSOR, default=defaults.get(CONF_TEMP_SENSOR)): selector.selector({"entity": {"domain": "sensor"}}),
            vol.Required(CONF_POOL_VOLUME, default=defaults.get(CONF_POOL_VOLUME, 0.96)): vol.Coerce(float),
            vol.Required(CONF_CHLOR_TARGET, default=defaults.get(CONF_CHLOR_TARGET, 1.5)): vol.Coerce(float),
            vol.Required(CONF_PH_TARGET, default=defaults.get(CONF_PH_TARGET, 7.2)): vol.Coerce(float),
            vol.Required(CONF_CHLOR_CONTENT, default=defaults.get(CONF_CHLOR_CONTENT, 0.56)): vol.Coerce(float),
            vol.Required(CONF_PH_DOWN_DOSAGE, default=defaults.get(CONF_PH_DOWN_DOSAGE, 200.0)): vol.Coerce(float),
            vol.Required(CONF_PH_UP_DOSAGE, default=defaults.get(CONF_PH_UP_DOSAGE, 100.0)): vol.Coerce(float),
            vol.Optional(CONF_NOTIFY_SERVICE, default=defaults.get(CONF_NOTIFY_SERVICE)): selector.selector({"service": {"domain": "notify"}}),
            vol.Optional(CONF_PERSISTENT_NOTIFICATION, default=defaults.get(CONF_PERSISTENT_NOTIFICATION, False)): selector.selector({"boolean": {}}),
            vol.Optional(CONF_FOLLOW_UP_TIME, default=defaults.get(CONF_FOLLOW_UP_TIME, 60)): vol.Coerce(int),
        })

class SmartPoolAssistantOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        
        current_config = {**self._config_entry.data, **self._config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=SmartPoolAssistantConfigFlow()._get_schema(current_config)
        )