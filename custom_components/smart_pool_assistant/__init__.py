"""The Smart Pool Assistant integration."""
from __future__ import annotations

import json
import logging

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import SmartPoolCoordinator
from .diagnostics_log import setup_file_logging

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]
_LOGGER = logging.getLogger(__name__)

SERVICE_LOG_MAINTENANCE = "log_maintenance"
SERVICE_REPAIR_LEARNING_HISTORY = "repair_learning_history"

_MAINTENANCE_TYPES = [
    "chlor",
    "ph_plus",
    "ph_minus",
    "water_exchange",
    "filter_clean",
    "filter_replace",
    "set_covered",
    "set_usage",
    "set_bath_plan",
]
# Diese Typen werten den Betrag als Statuswert aus und brauchen ihn zwingend.
_AMOUNT_REQUIRED_TYPES = {"set_covered", "set_usage", "set_bath_plan"}

LOG_MAINTENANCE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("type"): vol.In(_MAINTENANCE_TYPES),
        vol.Optional("amount"): vol.Any(None, vol.Coerce(float)),
        vol.Optional("water_exchange_percent"): vol.Any(None, vol.Coerce(float)),
    }
)
REPAIR_LEARNING_HISTORY_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("fetch_poollab", default=False): cv.boolean,
    }
)


def _read_manifest_version(manifest_path: str) -> str:
    """Read the integration manifest version for frontend cache busting."""
    try:
        with open(manifest_path, encoding="utf-8") as manifest_file:
            return json.load(manifest_file).get("version", "1")
    except (OSError, ValueError):
        return "1"

async def _async_manifest_version(hass: HomeAssistant) -> str:
    """Return the integration manifest version without blocking the event loop."""
    manifest_path = hass.config.path("custom_components/smart_pool_assistant/manifest.json")
    return await hass.async_add_executor_job(_read_manifest_version, manifest_path)


def _coordinator_for_entity(hass: HomeAssistant, entity_id: str) -> SmartPoolCoordinator:
    """Return the coordinator that owns the given Smart Pool Assistant entity."""
    entity_entry = er.async_get(hass).async_get(entity_id)
    coordinator = (
        hass.data.get(DOMAIN, {}).get(entity_entry.config_entry_id) if entity_entry else None
    )
    if not isinstance(coordinator, SmartPoolCoordinator):
        raise ServiceValidationError(
            f"{entity_id} gehoert nicht zu einer geladenen Smart-Pool-Assistant-Instanz."
        )
    return coordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Smart Pool Assistant component and register its services."""

    async def log_maintenance_service(call: ServiceCall) -> None:
        coordinator = _coordinator_for_entity(hass, call.data["entity_id"])
        m_type = call.data["type"]
        amount = call.data.get("amount")
        if amount is None and m_type in _AMOUNT_REQUIRED_TYPES:
            raise ServiceValidationError(f"Fuer '{m_type}' ist ein Wert (amount) erforderlich.")
        await coordinator.async_log_maintenance(
            m_type,
            amount,
            call.data.get("water_exchange_percent"),
        )

    async def repair_learning_history_service(call: ServiceCall) -> None:
        coordinator = _coordinator_for_entity(hass, call.data["entity_id"])
        await coordinator.async_repair_learning_history(
            fetch_poollab=call.data["fetch_poollab"],
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOG_MAINTENANCE,
        log_maintenance_service,
        schema=LOG_MAINTENANCE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPAIR_LEARNING_HISTORY,
        repair_learning_history_service,
        schema=REPAIR_LEARNING_HISTORY_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Pool Assistant from a config entry."""
    log_path = await hass.async_add_executor_job(
        setup_file_logging,
        hass.config.path("smart_pool_assistant_logs"),
    )
    _LOGGER.info("Smart Pool Assistant diagnostic file logging active: %s", log_path)

    coordinator = SmartPoolCoordinator(hass, entry)

    # Update-Listener für Konfigurationsänderungen
    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Initialen Datenabruf starten
    await coordinator.async_load_history()
    await coordinator.async_config_entry_first_refresh()

    # Listener für automatische Updates bei Sensoränderungen registrieren
    entry.async_on_unload(coordinator.async_setup_event_listeners())

    # Statische Pfade und Frontend-Ressourcen global in hass.data tracken
    if "static_path_registered" not in hass.data[DOMAIN]:
        url_path = "/smart_pool_assistant/pool-chemistry-card.js"
        file_path = hass.config.path("custom_components/smart_pool_assistant/frontend/pool-chemistry-card.js")

        try:
            await hass.http.async_register_static_paths([
                StaticPathConfig(url_path, file_path, False)
            ])
            # Sagt dem Frontend, dass es die JS-Datei laden soll (Cache-Busting inkludiert)
            if "frontend" in hass.config.components:
                from homeassistant.components.frontend import add_extra_js_url
                add_extra_js_url(hass, f"{url_path}?v={await _async_manifest_version(hass)}")

            hass.data[DOMAIN]["static_path_registered"] = True
        except RuntimeError:
            # Falls der Pfad bereits existiert (z.B. durch manuelles Neuladen)
            hass.data[DOMAIN]["static_path_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        _LOGGER.debug("Unloading Smart Pool Assistant config entry: entry_id=%s", entry.entry_id)
        coordinator: SmartPoolCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
