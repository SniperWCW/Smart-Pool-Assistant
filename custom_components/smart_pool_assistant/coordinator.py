import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION
)

CONF_API_KEY = "api_key"
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
        # Nur Entitäten überwachen, die auch wirklich konfiguriert wurden
        for key in [CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR]:
            if eid := conf.get(key):
                entities.append(eid)

        if not entities:
            _LOGGER.debug("No manual sensors configured, relying solely on API/Cloud")
            return lambda: None

        return async_track_state_change_event(
            self.hass, entities, self._handle_state_change
        )

    async def _handle_state_change(self, event):
        """Handle state changes of source entities."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or new_state.state in ("unknown", "unavailable", "none", "null"):
            return
            
        # Prüfen auf Attribut-Änderungen (z.B. measured_at von PoolLab)
        old_ts = old_state.attributes.get("measured_at") if old_state else None
        new_ts = new_state.attributes.get("measured_at") or new_state.attributes.get("timestamp")

        is_real_change = (
            old_state is not None 
            and old_state.state not in ("unknown", "unavailable") 
            and (new_state.state != old_state.state or (new_ts and new_ts != old_ts))
        )

        if is_real_change:
            _LOGGER.debug("Source entity value changed, updating measurement timestamp")
            if new_ts:
                self.maintenance_history["last_measurement_raw"] = new_ts if isinstance(new_ts, str) else new_ts.isoformat()
            else:
                self.maintenance_history["last_measurement_raw"] = dt_util.now().isoformat()
            
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
        if service:
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
        conf = self.config
        service = conf.get(CONF_NOTIFY_SERVICE)
        if service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": "Die Einwirkzeit ist um. Bitte Pool-Werte erneut prüfen!"
            })

    async def _async_update_data(self):
        def get_state_info(entity_id: str):
            if not entity_id:
                return None, None
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                return None, None
            try:
                ts = state.attributes.get("measured_at") or state.attributes.get("timestamp")
                return float(state.state), ts
            except ValueError:
                return None, None

        # 1. Bestehende Daten aus der Historie laden (Basis für die Anzeige)
        last_meas_raw = self.maintenance_history.get("last_measurement_raw")
        if not last_meas_raw:
            last_meas_raw = dt_util.now().isoformat()
            self.maintenance_history["last_measurement_raw"] = last_meas_raw

        last_calc_raw = self.maintenance_history.get("last_calc_raw")
        if not last_calc_raw:
            last_calc_raw = dt_util.now().isoformat()
            self.maintenance_history["last_calc_raw"] = last_calc_raw

        conf = self.config
        api_key = conf.get(CONF_API_KEY)

        data_source = "Nicht verfügbar"
        cloud_found = False
        manual_found = False

        c_ist = ph_ist = temp_ist = None
        new_meas_ts = None

        # 1. Versuch: Cloud-Daten abrufen wenn Key vorhanden
        if api_key:
            try:
                _LOGGER.debug("Fetching data from PoolLab Cloud")
                session = async_get_clientsession(self.hass)

                # GraphQL Query für die Cloud API
                payload = {
                    "query": "query { CloudAccount { Accounts { Measurements { parameter value timestamp } } } }"
                }
                headers = {"Authorization": api_key}
                
                async with session.post(
                    "https://backend.labcom.cloud/graphql", 
                    json=payload, 
                    headers=headers, 
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        cloud_data = result.get("data", {}).get("CloudAccount")
                        if cloud_data and cloud_data.get("Accounts"):
                            # Wir nehmen den ersten Account und sortieren Messwerte nach Zeitstempel
                            measurements = cloud_data["Accounts"][0].get("Measurements", [])
                            measurements.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
                            
                            for obs in measurements:
                                p_name = obs.get("parameter")
                                p_val = obs.get("value")
                                p_ts = obs.get("timestamp")
                                if p_name == "PL Chlorine Free" and c_ist is None:
                                    c_ist = float(p_val)
                                    if p_ts:
                                        new_meas_ts = dt_util.utc_from_timestamp(p_ts).isoformat()
                                if p_name == "PL pH" and ph_ist is None:
                                    ph_ist = float(p_val)
                                    if p_ts and not new_meas_ts:
                                        new_meas_ts = dt_util.utc_from_timestamp(p_ts).isoformat()
                                if p_name == "PL Temperature" and temp_ist is None:
                                    temp_ist = float(p_val)
                                if c_ist is not None and ph_ist is not None:
                                    break

                            if c_ist is not None or ph_ist is not None:
                                cloud_found = True
            except Exception as err:
                _LOGGER.error("Error fetching PoolLab data: %s", err)

        # 2. Versuch: Manuelle Sensoren prüfen (immer prüfen für Quellen-Erkennung)
        c_man, c_man_ts = get_state_info(conf.get(CONF_CHLOR_SENSOR))
        ph_man, ph_man_ts = get_state_info(conf.get(CONF_PH_SENSOR))
        temp_man, _ = get_state_info(conf.get(CONF_TEMP_SENSOR))

        if c_man is not None or ph_man is not None:
            manual_found = True

        # Werte zuweisen, falls Cloud nichts geliefert hat
        if c_ist is None and c_man is not None:
            c_ist = c_man
            if c_man_ts and not new_meas_ts:
                new_meas_ts = c_man_ts if isinstance(c_man_ts, str) else c_man_ts.isoformat()

        if ph_ist is None and ph_man is not None:
            ph_ist = ph_man
            if ph_man_ts and not new_meas_ts:
                new_meas_ts = ph_man_ts if isinstance(ph_man_ts, str) else ph_man_ts.isoformat()

        if temp_ist is None and temp_man is not None:
            temp_ist = temp_man

        # Bestimmung der Datenquelle
        if cloud_found and manual_found:
            data_source = "Cloud & Manuell"
        elif cloud_found:
            data_source = "Cloud/API"
        elif manual_found:
            data_source = "Manuell"

        # 2. Zeitstempel nur aktualisieren, wenn wir wirklich neue Daten erhalten haben
        if new_meas_ts:
            last_meas_raw = new_meas_ts
            self.maintenance_history["last_measurement_raw"] = last_meas_raw

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen
        if c_ist is None and ph_ist is None:
            return {
                "chlor_ist": None,
                "ph_ist": None,
                "temp_ist": None,
                "chlor_dose": 0,
                "ph_senker_total": 0,
                "ph_erhoeher_total": 0,
                "data_source": data_source,
                "is_error": True,
                "last_calculation": dt_util.parse_datetime(last_calc_raw).strftime("%d.%m.%Y %H:%M Uhr"),
                "last_measurement": dt_util.parse_datetime(last_meas_raw).strftime("%d.%m.%Y %H:%M Uhr"),
                "history": self.maintenance_history
            }

        # Konfiguration laden
        volumen = conf.get(CONF_POOL_VOLUME, 1.0)
        c_ziel = conf.get(CONF_CHLOR_TARGET, 1.5)
        ph_ziel = conf.get(CONF_PH_TARGET, 7.2)
        wirkstoff = conf.get(CONF_CHLOR_CONTENT, 0.56)
        
        if wirkstoff <= 0:
            wirkstoff = 0.56 # Schutz vor Division durch Null
        
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
            factor = conf[CONF_PH_DOWN_DOSAGE] / 10.0 / 0.2
            ph_senker_ml = round(ph_diff_abs * factor * volumen, 1)
        elif ph_diff > 0: # pH zu niedrig -> erhöhen
            # Berechnung: g = Differenz * (Dosierung / 10m3 / 0.1 pH-Schritt) * Poolvolumen
            factor = conf[CONF_PH_UP_DOSAGE] / 10.0 / 0.1
            ph_erhoeher_g = round(ph_diff_abs * factor * volumen, 1)

        # Zeitstempel der Berechnung bei jedem erfolgreichen Durchlauf aktualisieren
        new_calc_ts = dt_util.now().isoformat()
        self.maintenance_history["last_calc_raw"] = new_calc_ts

        await self._store.async_save(self.maintenance_history)

        return {
            "chlor_ist": c_ist,
            "ph_ist": ph_ist,
            "temp_ist": temp_ist,
            "chlor_dose": s_g,
            "chlor_pre": round(max(s_g * 0.3, 1.0), 1),
            "ph_senker_total": ph_senker_ml,
            "ph_erhoeher_total": ph_erhoeher_g,
            "data_source": data_source,
            "ph_diff": ph_diff,
            "is_shock": c_ist < 0.5,
            "is_error": False,
            "last_calculation": dt_util.parse_datetime(new_calc_ts).strftime("%d.%m.%Y %H:%M Uhr"),
            "last_measurement": dt_util.parse_datetime(last_meas_raw).strftime("%d.%m.%Y %H:%M Uhr"),
            "chlor_target": c_ziel,
            "ph_target": ph_ziel,
            "history": self.maintenance_history
        }
