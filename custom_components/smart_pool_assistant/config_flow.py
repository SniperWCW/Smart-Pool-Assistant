"""Config flow for Smart Pool Assistant integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback, HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers import selector
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)

from .const import (
    DOMAIN, CONF_API_KEY, CONF_BLE_ADDRESS, CONF_UPDATE_INTERVAL, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION
    , CONF_FILTER_CLEAN_INTERVAL, CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD, CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD, CONF_FILTER_REPLACE_RED_THRESHOLD,
    CONF_WEATHER_ENTITY,
)
SERVICE_UUID = "a7ee04a9-507b-4910-a528-b619d5501924"

def validate_data_source(user_input: dict[str, Any]) -> bool:
    """Überprüft, ob mindestens eine gültige Datenquelle konfiguriert wurde."""
    api_key = user_input.get(CONF_API_KEY, "").strip() if isinstance(user_input.get(CONF_API_KEY), str) else ""
    ble_address = user_input.get(CONF_BLE_ADDRESS, "").strip() if isinstance(user_input.get(CONF_BLE_ADDRESS), str) else ""

    # Manuelle Sensoren: Beide müssen vorhanden sein, um als Quelle zu zählen
    chlor_sensor = user_input.get(CONF_CHLOR_SENSOR)
    ph_sensor = user_input.get(CONF_PH_SENSOR)
    has_manual = bool(chlor_sensor) and bool(ph_sensor)

    return bool(api_key or ble_address or has_manual)

class SmartPoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Pool Assistant."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._ble_address: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Prüfen, ob dies eine vollständige Übermittlung ist (erforderliches Feld vorhanden)
            if CONF_POOL_VOLUME in user_input:
                if not validate_data_source(user_input):
                    errors["base"] = "missing_data_source"
                else:
                    return self.async_create_entry(title="Smart Pool Assistant", data=user_input)

        # Verfügbare Benachrichtigungsdienste abrufen
        services = self.hass.services.async_services().get("notify", {})
        notify_list = [f"notify.{s}" for s in sorted(services.keys())]

        return self.async_show_form(step_id="user", data_schema=get_schema(self.hass, user_input or {}, notify_services=notify_list), errors=errors)

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._ble_address = discovery_info.address
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm bluetooth discovery."""
        if user_input is not None:
            return await self.async_step_user({CONF_BLE_ADDRESS: self._ble_address})
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"address": self._ble_address},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartPoolAssistantOptionsFlowHandler(config_entry)

def get_schema(hass: HomeAssistant, defaults=None, notify_services=None):
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

    # Bluetooth Scan für die manuelle Auswahl
    discovered_devices = {}

    # 1. Aktuell konfiguriertes Gerät immer in der Liste behalten (auch wenn offline)
    if current_ble := defaults.get(CONF_BLE_ADDRESS):
        discovered_devices[current_ble] = f"Konfiguriertes Gerät ({current_ble})"

    # 2. Scanner-Ergebnisse hinzufügen (Filter auf Name optimiert)
    for info in async_discovered_service_info(hass, connectable=True):
        if (info.name and "PoolLab" in info.name) or SERVICE_UUID in info.service_uuids:
            discovered_devices[info.address] = f"{info.name or 'PoolLab'} ({info.address})"

    return vol.Schema({
        vol.Optional(CONF_BLE_ADDRESS, default=defaults.get(CONF_BLE_ADDRESS, "")): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[{"label": v, "value": k} for k, v in discovered_devices.items()],
                mode=selector.SelectSelectorMode.DROPDOWN,
                custom_value=True
            )
        ),
        vol.Optional(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        vol.Required(CONF_UPDATE_INTERVAL, default=defaults.get(CONF_UPDATE_INTERVAL, 5)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min", step=1, min=1, max=60)
        ),
        vol.Optional(CONF_CHLOR_SENSOR, default=defaults.get(CONF_CHLOR_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
        vol.Optional(CONF_PH_SENSOR, default=defaults.get(CONF_PH_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
        vol.Optional(CONF_TEMP_SENSOR, default=defaults.get(CONF_TEMP_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
        vol.Optional(CONF_WEATHER_ENTITY, default=defaults.get(CONF_WEATHER_ENTITY, vol.UNDEFINED)): selector.EntitySelector({"domain": "weather"}),
        vol.Required(CONF_POOL_VOLUME, default=defaults.get(CONF_POOL_VOLUME, 0.916)): selector.NumberSelector(
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
        vol.Required(CONF_FILTER_CLEAN_INTERVAL, default=defaults.get(CONF_FILTER_CLEAN_INTERVAL, 24)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Stunden", step=1, min=1)
        ),
        vol.Required(CONF_FILTER_REPLACE_INTERVAL, default=defaults.get(CONF_FILTER_REPLACE_INTERVAL, 5)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=1)
        ),
        vol.Required(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, default=defaults.get(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, 8)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Stunden", step=1, min=0)
        ),
        vol.Required(CONF_FILTER_CLEAN_RED_THRESHOLD, default=defaults.get(CONF_FILTER_CLEAN_RED_THRESHOLD, 2)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Stunden", step=1, min=0)
        ),
        vol.Required(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, default=defaults.get(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, 2)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=0)
        ),
        vol.Required(CONF_FILTER_REPLACE_RED_THRESHOLD, default=defaults.get(CONF_FILTER_REPLACE_RED_THRESHOLD, 1)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="Tage", step=1, min=0)
        ),
    })

class SmartPoolAssistantOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not validate_data_source(user_input):
                errors["base"] = "missing_data_source"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Kombiniere Daten und Optionen für die Standardwerte
        current_config = {**self.config_entry.data, **self.config_entry.options}
        if user_input:
            current_config.update(user_input)

        services = self.hass.services.async_services().get("notify", {})
        notify_list = [f"notify.{s}" for s in sorted(services.keys())]

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(self.hass, current_config, notify_services=notify_list),
            errors=errors
        )
