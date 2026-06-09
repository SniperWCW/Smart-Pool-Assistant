import logging
import asyncio
from datetime import timedelta

from bleak import BleakClient
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
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION,
    CONF_BLE_ADDRESS, POOL_LAB_WRITE_CHAR, POOL_LAB_NOTIFY_CHAR, CONF_API_KEY
)
from .poollab_ble_parser import PoolLabBLEParser, PARAM_PH, PARAM_CHLORINE_FREE, PARAM_WATER_TEMP

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
        self._parser = PoolLabBLEParser()
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
        service = self.entry.data.get(CONF_NOTIFY_SERVICE)
        if service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": "Die Einwirkzeit ist um. Bitte Pool-Werte erneut prüfen!"
            })

    async def _fetch_api_data(self):
        """Fetch data from PoolLab Cloud GraphQL API."""
        api_key = self.config.get(CONF_API_KEY)
        if not api_key:
            return None

        url = "https://backend.labcom.cloud/graphql"
        query = """
        {
          get_export_data {
            measurements {
              parameter
              value
              timestamp
            }
          }
        }
        """
        try:
            session = async_get_clientsession(self.hass)
            headers = {"Authorization-Token": api_key}
            async with session.post(url, json={"query": query}, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    measurements = data.get("data", {}).get("get_export_data", {}).get("measurements", [])
                    # Mappe Cloud Namen auf unsere internen IDs
                    mapping = {"pH": PARAM_PH, "Free Chlorine": PARAM_CHLORINE_FREE, "Water Temperature": PARAM_WATER_TEMP}
                    results = {}
                    for m in measurements:
                        p_id = mapping.get(m["parameter"])
                        if p_id:
                            # Nur den aktuellsten Wert behalten
                            if p_id not in results or m["timestamp"] > results[p_id]["ts"]:
                                results[p_id] = {"val": float(m["value"]), "ts": m["timestamp"]}
                    return {k: v["val"] for k, v in results.items()}
        except Exception as err:
            _LOGGER.error("Fehler beim Abruf der PoolLab API: %s", err)
        return None

    async def _fetch_ble_data(self):
        """Fetch data directly from PoolLab via BLE."""
        address = self.config.get(CONF_BLE_ADDRESS)
        if not address or address == "":
            return None
        
        _LOGGER.debug("Versuche Verbindung zu PoolLab unter %s", address)
        try:
            async with BleakClient(address, timeout=10.0) as client:
                if not client.is_connected:
                    return None

                received_data = bytearray()
                def callback(sender, data):
                    received_data.extend(data)

                await client.start_notify(POOL_LAB_NOTIFY_CHAR, callback)
                
                # Befehl 0x10 (Get Measurements) senden
                # Paket: [STX] [LEN_L] [LEN_H] [CMD] [CRC_L] [CRC_H] [ETX]
                # Für 0x10 ohne Daten: 0x02 0x01 0x00 0x10 0x13 0x00 0x03 (Summe 0x13)
                request = bytes([0x02, 0x01, 0x00, 0x10, 0x13, 0x00, 0x03])
                await client.write_gatt_char(POOL_LAB_WRITE_CHAR, request)
                
                await asyncio.sleep(2.0) # Warten auf Antwort
                await client.stop_notify(POOL_LAB_NOTIFY_CHAR)
                
                measurements = self._parser.parse_response_packet(bytes(received_data))
                if measurements:
                    # Sortieren nach Zeitstempel, um die aktuellsten Werte zu erhalten
                    measurements.sort(key=lambda x: x.timestamp, reverse=True)
                    return measurements
        except Exception as err:
            _LOGGER.debug("PoolLab BLE Verbindung fehlgeschlagen (Gerät vermutlich offline): %s", err)
        return None

    async def _async_update_data(self):
        source = "Manuelle Entitäten"
        # BLE Daten abrufen (falls Gerät erreichbar)
        measurements = await self._fetch_ble_data()
        ble_vals = {}
        if measurements:
            source = "Bluetooth (PoolLab)"
            for m in measurements:
                if m.parameter_id not in ble_vals: # Nur den neuesten Wert pro Parameter nehmen
                    ble_vals[m.parameter_id] = m.value
        
        # Wenn kein BLE, dann Cloud API versuchen
        api_vals = {}
        if not ble_vals:
            api_vals = await self._fetch_api_data()
            if api_vals:
                source = "Cloud API (PoolLab)"
        
        # Kombinierte Werte (Priorität: BLE > API > Sensor)
        pool_data = ble_vals or api_vals or {}

        def get_state_float(entity_id):
            if not entity_id: return None
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                return None
            try:
                return float(state.state)
            except ValueError:
                return None

        conf = self.config
        # Sensordaten abrufen
        chlor_eid = conf.get(CONF_CHLOR_SENSOR)
        ph_eid = conf.get(CONF_PH_SENSOR)
        temp_eid = conf.get(CONF_TEMP_SENSOR)

        # Werte priorisieren: Erst BLE, dann HA-Sensoren
        c_ist = pool_data.get(PARAM_CHLORINE_FREE) or get_state_float(chlor_eid)
        ph_ist = pool_data.get(PARAM_PH) or get_state_float(ph_eid)
        temp_ist = pool_data.get(PARAM_WATER_TEMP) or get_state_float(temp_eid)

        # Zeitstempel aktualisieren, falls wir neue BLE Daten haben
        if measurements or api_vals:
            self.maintenance_history["last_sensor_update_raw"] = dt_util.now().isoformat()
            await self._store.async_save(self.maintenance_history)

        # Zeitstempel der Messwerte aus dem Speicher laden (für Persistenz über Neustarts)
        stored_ts = self.maintenance_history.get("last_sensor_update_raw")
        last_measure = dt_util.parse_datetime(stored_ts) if stored_ts else None
        
        if last_measure:
            last_measure = dt_util.as_local(last_measure)

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen
        if c_ist is None or ph_ist is None:
            return {
                "chlor_dose": 0,
                "ph_senker_total": 0,
                "ph_erhoeher_total": 0,
                "is_error": True
            }

        # Konfiguration laden
        volumen = conf.get(CONF_POOL_VOLUME, 1.0)
        c_ziel = conf.get(CONF_CHLOR_TARGET, 1.5)
        ph_ziel = conf.get(CONF_PH_TARGET, 7.2)
        wirkstoff = conf.get(CONF_CHLOR_CONTENT, 0.56)
        
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
            factor = conf.get(CONF_PH_DOWN_DOSAGE, 200.0) / 10.0 / 0.2
            ph_senker_ml = round(ph_diff_abs * factor * volumen, 1)
        elif ph_diff > 0: # pH zu niedrig -> erhöhen
            # Berechnung: g = Differenz * (Dosierung / 10m3 / 0.1 pH-Schritt) * Poolvolumen
            factor = conf.get(CONF_PH_UP_DOSAGE, 100.0) / 10.0 / 0.1
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
            "history": self.maintenance_history,
            "source": source
        }
