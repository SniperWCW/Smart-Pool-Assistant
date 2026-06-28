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

from .chlorine_products import (
    default_chlor_content_for_product_type,
    normalize_chlor_product_type,
)
from .const import (
    DOMAIN, CONF_API_KEY, CONF_BLE_ADDRESS, CONF_UPDATE_INTERVAL, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_PUMP_ENTITY,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_CHLOR_MIN, CONF_CHLOR_MAX, CONF_PH_TARGET, CONF_PH_MIN, CONF_PH_MAX,
    CONF_CHLOR_PRODUCT_TYPE, CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_NOTIFY_SERVICE_2, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION,
    CONF_POOL_CONNECTION_SENSOR, CONF_POOL_CONNECTION_OFFLINE_DELAY,
    CONF_FILTER_CLEAN_INTERVAL, CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD, CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD, CONF_FILTER_REPLACE_RED_THRESHOLD,
    CONF_WEATHER_ENTITY, CONF_UV_SENSOR,
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


def _range_defaults(defaults: dict[str, Any]) -> dict[str, float]:
    """Return target ranges with backwards-compatible fallbacks."""
    old_chlor_target = defaults.get(CONF_CHLOR_TARGET, 1.5)
    old_ph_target = defaults.get(CONF_PH_TARGET, 7.2)
    return {
        CONF_CHLOR_MIN: defaults.get(CONF_CHLOR_MIN, old_chlor_target),
        CONF_CHLOR_MAX: defaults.get(CONF_CHLOR_MAX, old_chlor_target),
        CONF_PH_MIN: defaults.get(CONF_PH_MIN, old_ph_target),
        CONF_PH_MAX: defaults.get(CONF_PH_MAX, old_ph_target),
    }


def validate_target_ranges(user_input: dict[str, Any]) -> bool:
    """Check that configured chemistry ranges are ordered correctly."""
    ranges = _range_defaults(user_input)
    try:
        return (
            float(ranges[CONF_CHLOR_MIN]) <= float(ranges[CONF_CHLOR_MAX])
            and float(ranges[CONF_PH_MIN]) <= float(ranges[CONF_PH_MAX])
        )
    except (TypeError, ValueError):
        return False


def _chlor_product_type(defaults: dict[str, Any]) -> str:
    return normalize_chlor_product_type(defaults.get(CONF_CHLOR_PRODUCT_TYPE, "organic"))


def _chlor_content_default(defaults: dict[str, Any]) -> float:
    if CONF_CHLOR_CONTENT in defaults:
        return defaults.get(CONF_CHLOR_CONTENT, default_chlor_content_for_product_type(_chlor_product_type(defaults)))
    return default_chlor_content_for_product_type(_chlor_product_type(defaults))

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
            ble_address = user_input.get(CONF_BLE_ADDRESS)
            if isinstance(ble_address, str) and ble_address.strip():
                await self.async_set_unique_id(ble_address.strip())
                self._abort_if_unique_id_configured()
            # Prüfen, ob dies eine vollständige Übermittlung ist (erforderliches Feld vorhanden)
            if CONF_POOL_VOLUME in user_input:
                if not validate_data_source(user_input):
                    errors["base"] = "missing_data_source"
                elif not validate_target_ranges(user_input):
                    errors["base"] = "invalid_target_range"
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

    range_defaults = _range_defaults(defaults)
    chlor_product_type = _chlor_product_type(defaults)

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
        vol.Optional(CONF_PUMP_ENTITY, default=defaults.get(CONF_PUMP_ENTITY, vol.UNDEFINED)): selector.EntitySelector({"domain": ["switch", "binary_sensor"]}),
        vol.Optional(CONF_POOL_CONNECTION_SENSOR, default=defaults.get(CONF_POOL_CONNECTION_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "binary_sensor"}),
        vol.Optional(CONF_WEATHER_ENTITY, default=defaults.get(CONF_WEATHER_ENTITY, vol.UNDEFINED)): selector.EntitySelector({"domain": "weather"}),
        vol.Optional(CONF_UV_SENSOR, default=defaults.get(CONF_UV_SENSOR, vol.UNDEFINED)): selector.EntitySelector({"domain": "sensor"}),
        vol.Required(CONF_POOL_VOLUME, default=defaults.get(CONF_POOL_VOLUME, 0.916)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="m³", step="any")
        ),
        vol.Required(CONF_CHLOR_MIN, default=range_defaults[CONF_CHLOR_MIN]): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="mg/l", step=0.1)
        ),
        vol.Required(CONF_CHLOR_MAX, default=range_defaults[CONF_CHLOR_MAX]): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="mg/l", step=0.1)
        ),
        vol.Required(CONF_PH_MIN, default=range_defaults[CONF_PH_MIN]): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Required(CONF_PH_MAX, default=range_defaults[CONF_PH_MAX]): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Required(CONF_CHLOR_PRODUCT_TYPE, default=chlor_product_type): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"label": "Organisch / stabilisiert", "value": "organic"},
                    {"label": "Anorganisch / unstabilisiert", "value": "inorganic"},
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_CHLOR_CONTENT, default=_chlor_content_default(defaults)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=0.01)
        ),
        vol.Required(CONF_PH_DOWN_DOSAGE, default=defaults.get(CONF_PH_DOWN_DOSAGE, 200.0)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="ml", step=1.0)
        ),
        vol.Required(CONF_PH_UP_DOSAGE, default=defaults.get(CONF_PH_UP_DOSAGE, 100.0)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="g", step=1.0)
        ),
        vol.Optional(CONF_NOTIFY_SERVICE, default=defaults.get(CONF_NOTIFY_SERVICE, "")): notify_selector,
        vol.Optional(CONF_NOTIFY_SERVICE_2, default=defaults.get(CONF_NOTIFY_SERVICE_2, "")): notify_selector,
        vol.Optional(CONF_PERSISTENT_NOTIFICATION, default=defaults.get(CONF_PERSISTENT_NOTIFICATION, False)): selector.BooleanSelector(),
        vol.Optional(CONF_FOLLOW_UP_TIME, default=defaults.get(CONF_FOLLOW_UP_TIME, 60)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min", step=1)
        ),
        vol.Optional(CONF_POOL_CONNECTION_OFFLINE_DELAY, default=defaults.get(CONF_POOL_CONNECTION_OFFLINE_DELAY, 5)): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min", step=1, min=1, max=120)
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
            elif not validate_target_ranges(user_input):
                errors["base"] = "invalid_target_range"
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
