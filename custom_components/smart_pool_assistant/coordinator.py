import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION
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
        self._store = Store(hass, _STORAGE_VERSION, f"{_STORAGE_KEY}_{entry.entry_id}")
        self.maintenance_history = {}

    async def async_load_history(self):
        """Load maintenance history from storage."""
        stored = await self._store.async_load()
        if stored:
            self.maintenance_history = stored

    def async_setup_event_listeners(self):
        """Set up listeners for entity state changes."""
        entities = [
            self.entry.data[CONF_CHLOR_SENSOR],
            self.entry.data[CONF_PH_SENSOR],
            self.entry.data[CONF_TEMP_SENSOR]
        ]
        return async_track_state_change_event(
            self.hass, entities, self._handle_state_change
        )

    async def _handle_state_change(self, event):
        """Handle state changes of source entities."""
        _LOGGER.debug("Source entity changed, triggering recalculation")
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
        
        msg = f"Pool-Pflege: {amount}{unit} {label} zugegeben."
        
        # Persistent Notification
        if self.entry.data.get(CONF_PERSISTENT_NOTIFICATION):
            await self.hass.services.async_call("persistent_notification", "create", {
                "title": "Smart Pool Assistant",
                "message": msg,
                "notification_id": f"{DOMAIN}_maintenance"
            })

        # Notify Service
        service = self.entry.data.get(CONF_NOTIFY_SERVICE)
        if service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": msg
            })

        # Follow-up Timer
        delay = self.entry.data.get(CONF_FOLLOW_UP_TIME, 0)
        if delay > 0:
            async_call_later(self.hass, delay * 60, self._send_follow_up)
        
        await self.async_request_refresh()

    async def _send_follow_up(self, _):
        service = self.entry.data.get(CONF_NOTIFY_SERVICE)
        if service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": "Die Einwirkzeit ist um. Bitte Pool-Werte erneut prüfen!"
            })

    async def _async_update_data(self):
        def get_state_float(entity_id):
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                return None
            try:
                return float(state.state)
            except ValueError:
                return None

        # Sensordaten abrufen
        chlor_eid = self.entry.data[CONF_CHLOR_SENSOR]
        ph_eid = self.entry.data[CONF_PH_SENSOR]
        temp_eid = self.entry.data[CONF_TEMP_SENSOR]

        c_ist = get_state_float(chlor_eid)
        ph_ist = get_state_float(ph_eid)
        temp_ist = get_state_float(temp_eid)

        # Zeitstempel der Messwerte ermitteln (jüngstes Update der Quell-Sensoren)
        last_measure = None
        for eid in [chlor_eid, ph_eid, temp_eid]:
            state = self.hass.states.get(eid)
            if state and state.state not in ("unknown", "unavailable"):
                if last_measure is None or state.last_updated > last_measure:
                    last_measure = state.last_updated

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen
        if c_ist is None or ph_ist is None:
            return {
                "chlor_dose": 0,
                "ph_senker_total": 0,
                "ph_erhoeher_total": 0,
                "is_error": True
            }

        # Konfiguration laden
        volumen = self.entry.data[CONF_POOL_VOLUME]
        c_ziel = self.entry.data[CONF_CHLOR_TARGET]
        ph_ziel = self.entry.data[CONF_PH_TARGET]
        wirkstoff = self.entry.data[CONF_CHLOR_CONTENT]
        
        # Dummy für Nutzungstag (Könnte später ein Switch in der Integration sein)
        usage_factor = 1.0 

        # Chlor Berechnung
        c_diff = max(c_ziel - c_ist, 0)
        
        # Stoßchlorung Faktor
        shock_factor = 1.0
        if c_ist < 0.1: shock_factor = 3.0
        elif c_ist < 0.3: shock_factor = 2.4
        elif c_ist < 0.6: shock_factor = 1.8
        elif c_ist < 1.0: shock_factor = 1.3

        # Mindestdosis
        min_dose = 2.0
        if c_ist < 0.3: min_dose = 6.0
        elif c_ist < 0.8: min_dose = 3.0

        raw_chlor = (c_diff * volumen / wirkstoff) * shock_factor * usage_factor
        s_g = round(min(max(raw_chlor, min_dose), 25.0), 1)
        
        # pH Berechnung
        ph_diff = ph_ziel - ph_ist
        ph_diff_abs = abs(ph_diff)
        
        ph_senker_ml = 0.0
        ph_erhoeher_g = 0.0
        
        if ph_diff < 0: # pH zu hoch -> senken
            # Berechnung: ml = Differenz * (Dosierung / 10m3 / 0.2 pH-Schritt) * Poolvolumen
            factor = self.entry.data[CONF_PH_DOWN_DOSAGE] / 10.0 / 0.2
            ph_senker_ml = round(ph_diff_abs * factor * volumen, 1)
        elif ph_diff > 0: # pH zu niedrig -> erhöhen
            # Berechnung: g = Differenz * (Dosierung / 10m3 / 0.1 pH-Schritt) * Poolvolumen
            factor = self.entry.data[CONF_PH_UP_DOSAGE] / 10.0 / 0.1
            ph_erhoeher_g = round(ph_diff_abs * factor * volumen, 1)

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
            "history": self.maintenance_history
        }
