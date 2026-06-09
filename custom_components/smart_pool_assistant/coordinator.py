import logging
import asyncio
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR, CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET, CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE, CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION
)

_LOGGER = logging.getLogger(__name__)

_STORAGE_VERSION = 1
_STORAGE_KEY = f"{DOMAIN}_maintenance"

class SmartPoolCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

        self.entry = entry
        self._store = Store(hass, _STORAGE_VERSION, f"{_STORAGE_KEY}_{entry.entry_id}") # Store bleibt für Historie
        self.maintenance_history = {}

    @property
    def config(self):
        """Return combined config from data and options."""
        return {**self.entry.data, **self.entry.options}

    async def async_load_history(self):
        """Load maintenance history from storage."""
        stored = await self._store.async_load()
        if stored:
            self.maintenance_history = stored

    def async_setup_event_listeners(self):
        """Set up listeners for entity state changes."""
        conf = self.config
        entities = []
        for key in [CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR]:
            if entity_id := conf.get(key):
                entities.append(entity_id)

        if not entities:
            return None

        return async_track_state_change_event(
            self.hass, entities, self._handle_state_change
        )

    async def _handle_state_change(self, event):
        """Handle state changes of source entities."""
        _LOGGER.debug("Source entity changed, triggering recalculation")
        
        # Zeitstempel der tatsächlichen Änderung im persistenten Speicher festhalten
        new_state = event.data.get("new_state")
        if new_state and new_state.state not in ("unknown", "unavailable"):
            self.maintenance_history["last_sensor_update_raw"] = new_state.last_updated.isoformat()
            await self._store.async_save(self.maintenance_history)
            
        await self.async_request_refresh()

    async def async_log_maintenance(self, m_type: str, amount: float):
        """Log maintenance action and send notifications."""
        now = dt_util.now()
        ts = now.strftime("%d.%m. %H:%M")
        label = "Chlor" if m_type == "chlor" else "PH-Plus" if m_type == "ph_plus" else "PH-Minus"
        unit = "g" if m_type != "ph_minus" else "ml"
        
        # Update history
        self.maintenance_history[m_type] = {"amount": amount, "time": ts, "raw_ts": now.isoformat()}
        self.maintenance_history["last_action"] = f"{amount}{unit} {label} am {ts}"
        await self._store.async_save(self.maintenance_history)
        
        conf = self.config
        msg = f"Pool-Pflege: {amount}{unit} {label} zugegeben."
        
        # Persistent Notification
        if conf.get(CONF_PERSISTENT_NOTIFICATION):
            await self.hass.services.async_call("persistent_notification", "create", {
                "title": "Smart Pool Assistant",
                "message": msg,
                "notification_id": f"{DOMAIN}_maintenance"
            })

        # Notify Service
        service = conf.get(CONF_NOTIFY_SERVICE)
        if service and "." in service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": msg
            })

        # Follow-up Timer
        delay = conf.get(CONF_FOLLOW_UP_TIME, 0)
        if delay > 0:
            async_call_later(self.hass, delay * 60, self._send_follow_up)
        
        await self.async_request_refresh()

    async def _send_follow_up(self, _):
        service = self.config.get(CONF_NOTIFY_SERVICE)
        if service and "." in service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": "Die Einwirkzeit ist um. Bitte Pool-Werte erneut prüfen!"
            })

    def _get_state_float(self, entity_id):
        """Helper to get a float state from a HA entity."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    async def _async_update_data(self):
        # Variablen initialisieren um UnboundLocalError zu vermeiden
        c_ist = ph_ist = temp_ist = None
        last_measure = None
        volumen = self.config.get(CONF_POOL_VOLUME, 1.0)
        wirkstoff = self.config.get(CONF_CHLOR_CONTENT, 0.56)
        c_ziel = self.config.get(CONF_CHLOR_TARGET, 1.5)
        ph_ziel = self.config.get(CONF_PH_TARGET, 7.2)

        _LOGGER.debug("Starte Daten-Update-Zyklus für manuelle Entitäten")
        try:
            conf = self.config

            # Sensordaten abrufen
            chlor_eid = conf.get(CONF_CHLOR_SENSOR)
            ph_eid = conf.get(CONF_PH_SENSOR)
            temp_eid = conf.get(CONF_TEMP_SENSOR)

            # Werte priorisieren
            c_ist = self._get_state_float(chlor_eid)
            ph_ist = self._get_state_float(ph_eid)
            temp_ist = self._get_state_float(temp_eid)

            _LOGGER.debug("Aktuelle Werte - Chlor: %s, pH: %s, Temp: %s", c_ist, ph_ist, temp_ist)

            # Zeitstempel aktualisieren (nur wenn manuelle Sensoren sich ändern)
            # Die Logik für "last_sensor_update_raw" wird jetzt durch async_track_state_change_event in _handle_state_change ausgelöst
            # Hier nur, wenn keine Historie vorhanden ist, um einen Startwert zu haben
            if not self.maintenance_history.get("last_sensor_update_raw"):
                self.maintenance_history["last_sensor_update_raw"] = dt_util.now().isoformat()
                await self._store.async_save(self.maintenance_history)

            stored_ts = self.maintenance_history.get("last_sensor_update_raw")
            last_measure = dt_util.parse_datetime(stored_ts) if stored_ts else None
            if last_measure:
                last_measure = dt_util.as_local(last_measure)

            # Wenn wichtige Sensoren fehlen oder Konfiguration ungültig ist, keine Berechnung durchführen
            if c_ist is None or ph_ist is None or volumen <= 0 or wirkstoff <= 0:
                return self._get_error_dict(c_ist, ph_ist, temp_ist, last_measure, "Manuelle Entitäten")

            usage_factor = 1.0 
            c_diff = max(c_ziel - c_ist, 0)
            
            shock_factor = 1.0
            if c_ist < 0.1: shock_factor = 3.0
            elif c_ist < 0.3: shock_factor = 2.4
            elif c_ist < 0.6: shock_factor = 1.8
            elif c_ist < 1.0: shock_factor = 1.3

            min_dose = 2.0
            if c_ist < 0.3: min_dose = 6.0
            elif c_ist < 0.8: min_dose = 3.0

            raw_chlor = (c_diff * volumen / wirkstoff) * shock_factor * usage_factor
            s_g = round(min(max(raw_chlor, min_dose), 25.0), 1)
            
            ph_diff = ph_ziel - ph_ist
            ph_diff_abs = abs(ph_diff)
            
            ph_senker_ml = 0.0
            ph_erhoeher_g = 0.0
            
            if ph_diff < 0: # pH zu hoch -> senken
                factor = conf.get(CONF_PH_DOWN_DOSAGE, 200.0) / 10.0 / 0.2
                ph_senker_ml = round(ph_diff_abs * factor * volumen, 1)
            elif ph_diff > 0: # pH zu niedrig -> erhöhen
                factor = conf.get(CONF_PH_UP_DOSAGE, 100.0) / 10.0 / 0.1
                ph_erhoeher_g = round(ph_diff_abs * factor * volumen, 1)

            _LOGGER.debug("Berechnung abgeschlossen: Chlor-Dosis=%s, pH-Korrektur=%s", s_g, ph_senker_ml or ph_erhoeher_g)

            return {
                "chlor_ist": c_ist,
                "ph_ist": ph_ist,
                "temp_ist": temp_ist,
                "chlor_dose": s_g,
                "chlor_pre": round(max(s_g * 0.3, 1.0), 1),
                "ph_senker_total": ph_senker_ml,
                "ph_erhoeher_total": ph_erhoeher_g,
                "ph_diff": ph_diff,
                "is_shock": c_ist < 0.5,
                "is_error": False,
                "last_calculation": dt_util.now().strftime("%d.%m. um %H:%M"),
                "last_measurement": last_measure.strftime("%d.%m. um %H:%M") if last_measure else "Unbekannt",
                "chlor_target": c_ziel,
                "ph_target": ph_ziel,
                "maintenance_history": self.maintenance_history,
            }

        except Exception as err:
            _LOGGER.error("Schwerer Fehler bei Datenaktualisierung: %s", err)
            return self._get_error_dict(None, None, None, None, "Fehler")

    def _get_error_dict(self, c_ist, ph_ist, temp_ist, last_measure, source):
        """Gibt ein sicheres Dictionary mit Standardwerten zurück."""
        return {
            "chlor_ist": c_ist or 0.0,
            "ph_ist": ph_ist or 0.0,
            "temp_ist": temp_ist or 0.0,
            "chlor_dose": 0,
            "chlor_pre": 0,
            "ph_senker_total": 0,
            "ph_erhoeher_total": 0,
            "ph_diff": 0,
            "is_shock": False,
            "is_error": True,
            "last_calculation": dt_util.now().strftime("%d.%m. um %H:%M"),
            "last_measurement": last_measure.strftime("%d.%m. um %H:%M") if last_measure else "Unbekannt",
            "chlor_target": self.config.get(CONF_CHLOR_TARGET, 1.5),
            "ph_target": self.config.get(CONF_PH_TARGET, 7.2),
            "maintenance_history": self.maintenance_history,
            "source": source
        }
