"""The Smart Pool Assistant integration."""
from __future__ import annotations

import json
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import SmartPoolCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]
_LOGGER = logging.getLogger(__name__)


def _manifest_version(hass: HomeAssistant) -> str:
    """Return the integration manifest version for frontend cache busting."""
    manifest_path = hass.config.path("custom_components/smart_pool_assistant/manifest.json")
    try:
        with open(manifest_path, encoding="utf-8") as manifest_file:
            return json.load(manifest_file).get("version", "1")
    except (OSError, ValueError):
        return "1"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Smart Pool Assistant component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Pool Assistant from a config entry."""
    coordinator = SmartPoolCoordinator(hass, entry)

    # Update-Listener für Konfigurationsänderungen
    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Dienste registrieren (bevor der erste Refresh evtl. fehlschlägt)
    async def log_maintenance_service(call):
        entity_id = call.data.get("entity_id")
        reg = er.async_get(hass)
        entity_entry = reg.async_get(entity_id)
        if entity_entry:
            coord = hass.data[DOMAIN].get(entity_entry.config_entry_id)
            if coord:
                await coord.async_log_maintenance(
                    call.data.get("type"),
                    call.data.get("amount")
                )

    if not hass.services.has_service(DOMAIN, "log_maintenance"):
        hass.services.async_register(DOMAIN, "log_maintenance", log_maintenance_service)

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
                add_extra_js_url(hass, f"{url_path}?v={_manifest_version(hass)}")
            
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
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
