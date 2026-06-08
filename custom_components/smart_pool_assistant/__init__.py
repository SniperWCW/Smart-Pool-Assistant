"""The Smart Pool Assistant integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components.http import StaticPathConfig

from .const import DOMAIN
from .coordinator import SmartPoolCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Pool Assistant from a config entry."""
    coordinator = SmartPoolCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    # Listener für automatische Updates bei Sensoränderungen registrieren
    entry.async_on_unload(coordinator.async_setup_event_listeners())

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

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
                add_extra_js_url(hass, f"{url_path}?v={entry.version}")
            
            hass.data[DOMAIN]["static_path_registered"] = True
        except RuntimeError:
            # Falls der Pfad bereits existiert (z.B. durch manuelles Neuladen)
            hass.data[DOMAIN]["static_path_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok