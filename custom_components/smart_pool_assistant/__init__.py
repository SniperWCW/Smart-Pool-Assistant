"""The Smart Pool Assistant integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import SmartPoolCoordinator

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.components.http import StaticPathConfig
except ImportError:
    StaticPathConfig = None

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Pool Assistant from a config entry."""
    _LOGGER.debug("Starte Setup für Entry: %s", entry.title)
    hass.data.setdefault(DOMAIN, {})
    
    _LOGGER.debug("Initialisiere Coordinator")
    coordinator = SmartPoolCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        _LOGGER.debug("Lade Wartungshistorie")
        await coordinator.async_load_history()
    except Exception as err:
        _LOGGER.warning("Konnte Wartungshistorie nicht laden: %s", err)

    # Listener für automatische Updates bei Sensoränderungen registrieren
    if listener := coordinator.async_setup_event_listeners():
        _LOGGER.debug("Registriere Event-Listener")
        entry.async_on_unload(listener)

    # Update-Listener für Konfigurationsänderungen
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Statische Pfade und Frontend-Ressourcen global in hass.data tracken
    if "static_path_registered" not in hass.data[DOMAIN]:
        _LOGGER.debug("Registriere statische Pfade für Frontend")
        url_path = "/smart_pool_assistant/pool-chemistry-card.js"
        file_path = hass.config.path("custom_components", DOMAIN, "frontend", "pool-chemistry-card.js")
        
        try:
            if StaticPathConfig is None:
                # Sicherer Weg für Dateisystemzugriff
                await hass.async_add_executor_job(hass.http.register_static_path, url_path, file_path, False)
            else:
                # Moderner Weg
                await hass.http.async_register_static_paths([
                StaticPathConfig(url_path, file_path, False)
            ])
            # Sagt dem Frontend, dass es die JS-Datei laden soll (Cache-Busting inkludiert)
            if "frontend" in hass.config.components:
                from homeassistant.components.frontend import add_extra_js_url
                add_extra_js_url(hass, f"{url_path}?v={entry.version}")
            
            hass.data[DOMAIN]["static_path_registered"] = True
        except RuntimeError:
            # Falls der Pfad bereits existiert (z.B. durch manuelles Neuladen)
            hass.data[DOMAIN]["static_path_registered"] = True

    # Plattformen laden
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    hass.services.async_register(DOMAIN, "log_maintenance", log_maintenance_service)
    _LOGGER.debug("Setup für %s erfolgreich abgeschlossen", entry.title)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok