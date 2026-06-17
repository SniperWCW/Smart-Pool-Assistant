import logging
import asyncio
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
from homeassistant.components.bluetooth import async_ble_device_from_address

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE,
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION,
    CONF_FILTER_CLEAN_INTERVAL, CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD, CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD, CONF_FILTER_REPLACE_RED_THRESHOLD
)
from .poollab_ble import PoolLabBLEClient

CONF_API_KEY = "api_key"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_BLE_ADDRESS = "ble_address"
_LOGGER = logging.getLogger(__name__)

_STORAGE_VERSION = 1
_STORAGE_KEY = f"{DOMAIN}_maintenance"

class SmartPoolCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(CONF_UPDATE_INTERVAL, entry.data.get(CONF_UPDATE_INTERVAL, 5))
            ),
        )

        self.entry = entry
        self._store = Store(hass, _STORAGE_VERSION, f"{_STORAGE_KEY}_{entry.entry_id}")
        self.maintenance_history = {}
        # Standardwerte für neue Logik initialisieren
        self.pool_covered = True
        self.usage_mode = "none" # none, normal, party

    def _activity_text(self, m_type: str | None, amount: float | int | None) -> str:
        """Return a human readable activity label."""
        if m_type == "chlor":
            return f"{amount:g}g Chlor hinzugefügt" if amount is not None else "Chlor hinzugefügt"
        if m_type == "ph_plus":
            return f"{amount:g}g PH-Plus hinzugefügt" if amount is not None else "PH-Plus hinzugefügt"
        if m_type == "ph_minus":
            return f"{amount:g}ml PH-Minus hinzugefügt" if amount is not None else "PH-Minus hinzugefügt"
        if m_type == "filter_clean":
            return "Filter gereinigt"
        if m_type == "filter_replace":
            return "Filter getauscht"
        if m_type == "set_covered":
            return "Abdeckung: " + ("Abgedeckt" if self.pool_covered else "Offen")
        if m_type == "set_usage":
            mode_labels = {"none": "Keine", "normal": "Normal", "party": "Party"}
            return f"Nutzungsmodus: {mode_labels.get(self.usage_mode, self.usage_mode)}"
        return ""

    def _normalize_loaded_history(self, stored: dict) -> dict:
        """Fix legacy history entries in-place after loading from storage."""
        if not isinstance(stored, dict):
            return {}

        history = dict(stored)
        activities = history.get("last_activities")
        if isinstance(activities, list):
            normalized: list[dict] = []
            changed = False

            for entry in activities:
                if not isinstance(entry, dict):
                    continue

                item = dict(entry)
                m_type = item.get("type")

                if m_type in ("filter_clean", "filter_replace"):
                    expected_text = self._activity_text(m_type, None)
                    if item.get("text") != expected_text:
                        item["text"] = expected_text
                        changed = True
                    if item.get("amount") == 0:
                        item["amount"] = None
                        changed = True
                elif not item.get("text"):
                    item["text"] = self._activity_text(m_type, item.get("amount")) or "--"
                    changed = True

                normalized.append(item)

            if changed:
                history["last_activities"] = normalized

        for key in ("filter_clean", "filter_replace"):
            entry = history.get(key)
            if isinstance(entry, dict) and entry.get("amount") == 0:
                entry = dict(entry)
                entry["amount"] = None
                history[key] = entry

        return history

    def _parse_ts_aware(self, ts_str: str | None):
        """Helper to parse a timestamp string into an aware datetime object."""
        if not ts_str: return None
        dt = dt_util.parse_datetime(ts_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_util.UTC)
        return dt

    @property
    def config(self):
        """Return combined config from data and options."""
        return {**self.entry.data, **self.entry.options}

    async def async_load_history(self):
        """Load maintenance history from storage."""
        stored = await self._store.async_load()
        if stored:
            normalized = self._normalize_loaded_history(stored)
            self.maintenance_history = normalized
            self.pool_covered = stored.get("pool_covered", True)
            self.usage_mode = stored.get("usage_mode", "none")
            if normalized != stored:
                await self._store.async_save(self.maintenance_history)

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

    def _collect_last_activities(self) -> list[dict]:
        """Build a compact activity list from stored maintenance actions."""
        items = self.maintenance_history.get("last_activities")
        if isinstance(items, list) and items:
            normalized = []
            for entry in items:
                if not isinstance(entry, dict):
                    continue
                raw_ts = entry.get("raw_ts")
                dt = self._parse_ts_aware(raw_ts)
                if not dt:
                    continue
                normalized.append({
                    "type": entry.get("type"),
                    "text": entry.get("text") or self._activity_text(entry.get("type"), entry.get("amount")) or "--",
                    "time": entry.get("time"),
                    "raw_ts": raw_ts,
                    "_dt": dt,
                })
            normalized.sort(key=lambda item: item["_dt"], reverse=True)
            for item in normalized:
                item.pop("_dt", None)
            return normalized[:5]

        # Fallback für ältere gespeicherte Daten ohne Aktivitätsliste
        items = []

        for key in ("chlor", "ph_plus", "ph_minus", "filter_clean", "filter_replace", "set_covered", "set_usage"):
            entry = self.maintenance_history.get(key)
            if not isinstance(entry, dict):
                continue

            raw_ts = entry.get("raw_ts")
            dt = self._parse_ts_aware(raw_ts)
            if not dt:
                continue

            items.append({
                "type": key,
                "text": format_activity({"type": key, **entry}),
                "time": entry.get("time"),
                "raw_ts": raw_ts,
                "_dt": dt,
            })

        items.sort(key=lambda item: item["_dt"], reverse=True)
        for item in items:
            item.pop("_dt", None)
        return items[:5]

    async def _handle_state_change(self, event):
        """Handle state changes of source entities."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or new_state.state in ("unknown", "unavailable", "none", "null"):
            return

        # Jedes Update der Quell-Entität triggert eine Neuberechnung,
        # um auch "Heartbeats" oder identische Werte sofort zu erfassen.
        is_real_change = True

        if is_real_change:
            _LOGGER.debug("Source entity update detected, triggering refresh")
            new_ts = new_state.attributes.get("measured_at") or new_state.attributes.get("timestamp") or dt_util.now().isoformat()
            ts_iso = new_ts if isinstance(new_ts, str) else new_ts.isoformat()

            self.maintenance_history["last_manual_measurement_raw"] = ts_iso

            # Globalen Anzeige-Zeitstempel synchronisieren
            api_ts_str = self.maintenance_history.get("last_api_measurement_raw")
            dt_api = self._parse_ts_aware(api_ts_str)
            dt_new = self._parse_ts_aware(ts_iso)

            if dt_api and dt_new and dt_api > dt_new:
                self.maintenance_history["last_measurement_raw"] = api_ts_str
            else:
                self.maintenance_history["last_measurement_raw"] = ts_iso

            await self._store.async_save(self.maintenance_history)
            await self.async_request_refresh()

    async def async_log_maintenance(self, m_type: str, amount: float):
        """Log maintenance action and send notifications."""
        now = dt_util.now()
        ts_formatted = now.strftime("%d.%m. %H:%M")

        label = ""
        unit = ""
        msg = None

        if m_type == "chlor": label, unit = "Chlor", "g"
        elif m_type == "ph_plus": label, unit = "PH-Plus", "g"
        elif m_type == "ph_minus": label, unit = "PH-Minus", "ml"
        elif m_type == "filter_clean": label, unit = "Filter gereinigt", ""
        elif m_type == "filter_replace": label, unit = "Filter getauscht", ""
        elif m_type == "set_covered":
            self.pool_covered = amount > 0
            self.maintenance_history["pool_covered"] = self.pool_covered
        elif m_type == "set_usage":
            modes = ["none", "normal", "party"]
            self.usage_mode = modes[int(amount)] if int(amount) < len(modes) else "none"
            self.maintenance_history["usage_mode"] = self.usage_mode

        action_text = self._activity_text(m_type, amount) if m_type else ""
        if not action_text:
            action_text = f"{amount:g}{unit} {label}" if amount else label

        stored_amount = None if m_type in ("filter_clean", "filter_replace") else amount

        # Update history for chemicals and filter
        if m_type in ("chlor", "ph_plus", "ph_minus", "filter_clean", "filter_replace", "set_covered", "set_usage"):
            self.maintenance_history[m_type] = {"amount": stored_amount, "time": ts_formatted, "raw_ts": now.isoformat()}
            self.maintenance_history["last_action"] = f"{action_text} am {ts_formatted}"
            activities = self.maintenance_history.get("last_activities", [])
            activities = activities if isinstance(activities, list) else []
            activities.insert(0, {
                "type": m_type,
                "text": action_text,
                "amount": stored_amount,
                "time": ts_formatted,
                "raw_ts": now.isoformat(),
            })
            self.maintenance_history["last_activities"] = activities[:5]
            # Wording für Wartung vs. Chemie anpassen
            if m_type == "filter_clean":
                msg = "Pool-Wartung: Filter gereinigt."
            elif m_type == "filter_replace":
                msg = "Pool-Wartung: Filter getauscht."
            else:
                msg = f"Pool-Pflege: {action_text}."

        await self._store.async_save(self.maintenance_history)

        conf = self.config
        # Send Notification (Persistent & Service)
        if msg:
            if conf.get(CONF_PERSISTENT_NOTIFICATION):
                await self.hass.services.async_call("persistent_notification", "create", {
                    "title": "Smart Pool Assistant",
                    "message": msg,
                    "notification_id": f"{DOMAIN}_maintenance"
                })

            service = conf.get(CONF_NOTIFY_SERVICE)
            if service:
                domain, service_name = service.split(".")
                await self.hass.services.async_call(domain, service_name, {
                    "title": "Smart Pool Assistant",
                    "message": msg
                })

        # Follow-up Timer (only for chemicals)
        if m_type in ("chlor", "ph_plus", "ph_minus"):
            delay = conf.get(CONF_FOLLOW_UP_TIME, 0)
            if delay > 0:
                async_call_later(self.hass, delay * 60, self._send_follow_up)

        await self.async_request_refresh()

    async def _send_notification(self, message: str, notification_id: str):
        """Helper to send notifications."""
        conf = self.config
        if conf.get(CONF_PERSISTENT_NOTIFICATION):
            await self.hass.services.async_call("persistent_notification", "create", {
                "title": "Smart Pool Assistant",
                "message": message,
                "notification_id": f"{DOMAIN}_{notification_id}"
            })
        service = conf.get(CONF_NOTIFY_SERVICE)
        if service:
            domain, service_name = service.split(".")
            await self.hass.services.async_call(domain, service_name, {
                "title": "Smart Pool Assistant",
                "message": message
            })

    async def _send_follow_up(self, _):
        conf = self.config
        service = conf.get(CONF_NOTIFY_SERVICE)
        if service:
            domain, service_name = service.split(".")
            await self._send_notification("Die Einwirkzeit ist um. Bitte Pool-Werte erneut prüfen!", "follow_up")

    def _get_time_since_last_action(self, action_key: str, in_hours: bool = False) -> int | None:
        """Calculate time since last action (hours or days)."""
        last_action_data = self.maintenance_history.get(action_key)
        if last_action_data and last_action_data.get("raw_ts"):
            last_ts = dt_util.parse_datetime(last_action_data["raw_ts"])
            if last_ts:
                diff = dt_util.now() - last_ts
                if in_hours:
                    return int(diff.total_seconds() // 3600)
                return diff.days
        return None

    async def _check_filter_notifications(self, conf: dict):
        """Check and send notifications for filter maintenance."""
        now = dt_util.now()

        # Filter Clean
        hours_since_clean = self._get_time_since_last_action("filter_clean", in_hours=True)
        if hours_since_clean is not None:
            clean_interval = conf.get(CONF_FILTER_CLEAN_INTERVAL, 24)
            clean_yellow = conf.get(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, 4)
            clean_red = conf.get(CONF_FILTER_CLEAN_RED_THRESHOLD, 0)

            # Yellow notification
            if hours_since_clean > 0 and (clean_interval - clean_yellow) <= hours_since_clean < clean_interval:
                last_notified = self.maintenance_history.get("last_notified_clean_yellow")
                if not last_notified or (now - dt_util.parse_datetime(last_notified)).days >= 1: # Notify once a day
                    await self._send_notification(f"Filterreinigung bald fällig! Vor {hours_since_clean} Stunden gereinigt. Empfohlen alle {clean_interval} Stunden.", "filter_clean_yellow")
                    self.maintenance_history["last_notified_clean_yellow"] = now.isoformat()

            # Red notification for cleaning
            if hours_since_clean >= (clean_interval + clean_red):
                last_notified = self.maintenance_history.get("last_notified_clean_red")
                if not last_notified or (now - dt_util.parse_datetime(last_notified)).days >= 1:
                    await self._send_notification(f"Filterreinigung ÜBERFÄLLIG! Vor {hours_since_clean} Stunden gereinigt. Empfohlen alle {clean_interval} Stunden.", "filter_clean_red")
                    self.maintenance_history["last_notified_clean_red"] = now.isoformat()

        # Filter Replace
        days_since_replace = self._get_time_since_last_action("filter_replace")
        if days_since_replace is not None:
            replace_interval = conf.get(CONF_FILTER_REPLACE_INTERVAL, 180)
            replace_yellow = conf.get(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, 30)
            replace_red = conf.get(CONF_FILTER_REPLACE_RED_THRESHOLD, 0)

            # Yellow notification for replacement
            if days_since_replace > 0 and (replace_interval - replace_yellow) <= days_since_replace < replace_interval:
                last_notified = self.maintenance_history.get("last_notified_replace_yellow")
                if not last_notified or (now - dt_util.parse_datetime(last_notified)).days >= 1:
                    await self._send_notification(
                        f"Filterwechsel bald fällig! Vor {days_since_replace} Tagen gewechselt. Empfohlen alle {replace_interval} Tage.",
                        "filter_replace_yellow"
                    )
                    self.maintenance_history["last_notified_replace_yellow"] = now.isoformat()

            # Red notification for replacement
            if days_since_replace >= (replace_interval + replace_red):
                last_notified = self.maintenance_history.get("last_notified_replace_red")
                if not last_notified or (now - dt_util.parse_datetime(last_notified)).days >= 1:
                    await self._send_notification(
                        f"Filterwechsel ÜBERFÄLLIG! Vor {days_since_replace} Tagen gewechselt. Empfohlen alle {replace_interval} Tage.",
                        "filter_replace_red"
                    )
                    self.maintenance_history["last_notified_replace_red"] = now.isoformat()

    async def _async_update_data(self):
        def get_state_info(entity_id: str):
            if not entity_id:
                return None, None
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                return None, None
            try:
                # Zeitstempel aus Attribut oder HA-Update-Zeit
                ts_raw = state.attributes.get("measured_at") or state.attributes.get("timestamp") or state.last_updated
                ts = ts_raw if isinstance(ts_raw, str) else ts_raw.isoformat()

                # Ersetze Komma durch Punkt für deutsche Sensor-Strings
                val_str = state.state.replace(',', '.')
                return float(val_str), ts
            except ValueError:
                return None, None

        def get_ble_measurement(ble_data, type_ids: tuple[int, ...]):
            """Return the first BLE measurement matching one of the supported type IDs."""
            for type_id in type_ids:
                if measurement := ble_data.measurements.get(type_id):
                    return measurement
            return None

        def get_filter_status(time_since: int | None, interval: int, yellow_threshold: int, red_threshold: int) -> str:
            """Determine filter status based on time since last action and thresholds."""
            if time_since is None:
                return "unknown"

            time_until_due = interval - time_since
            if time_until_due <= red_threshold:
                return "critical"
            if time_until_due <= yellow_threshold:
                return "warning"

            return "ok"

        # 1. Bestehende Daten laden
        # Immer einen aktuellen Zeitstempel für den "letzten Lauf" parat haben
        now_iso = dt_util.now().isoformat()
        last_calc_raw = self.maintenance_history.get("last_calc_raw", now_iso)

        conf = self.config
        api_key = conf.get(CONF_API_KEY)
        ble_address = conf.get(CONF_BLE_ADDRESS)

        data_source = "Nicht verfügbar"
        cloud_found = False
        manual_found = False
        ble_found = False
        ble_connected = False

        c_ist = ph_ist = temp_ist = None
        chlor_source = ph_source = temp_source = None
        # Lade letzte bekannte API-Messwerte aus dem Speicher
        last_api_measurements = self.maintenance_history.get("last_api_measurements", [])

        # Zeitstempel der Berechnung sofort aktualisieren, damit das UI "tickt"
        now_iso = dt_util.now().isoformat()
        self.maintenance_history["last_calc_raw"] = now_iso
        last_calc_raw = now_iso

        # 1. Versuch: Bluetooth-Daten abrufen (PoolLab direkt)
        if ble_address:
            try:
                _LOGGER.debug("Fetching data from PoolLab via Bluetooth: %s", ble_address)
                device = async_ble_device_from_address(self.hass, ble_address, connectable=True)
                if device:
                    client = PoolLabBLEClient(device)
                    try:
                        # Timeout leicht reduziert und CancelledError explizit fangen,
                        # um Setup-Abstürze unter Python 3.11+ zu verhindern.
                        ble_data = await asyncio.wait_for(client.async_read_data(), timeout=40.0)

                        ble_found = True
                        ble_connected = True
                        # Speichere Batteriestatus in der Historie
                        self.maintenance_history["ble_battery"] = ble_data.battery

                        ble_ts_list = []
                        # Erweiterte Mappings gemäß BLE-Doku: mehrere OEM-/Test-Varianten möglich
                        if m_c := get_ble_measurement(ble_data, (1, 8, 3)):
                            c_ist = m_c.value
                            chlor_source = "Bluetooth"
                            ble_ts_list.append(m_c.timestamp)
                        if m_ph := get_ble_measurement(ble_data, (9, 27, 28, 29, 30, 31, 32, 33, 34, 36, 48)):
                            ph_ist = m_ph.value
                            ph_source = "Bluetooth"
                            ble_ts_list.append(m_ph.timestamp)
                        if m_temp := ble_data.measurements.get(4):
                            temp_ist = m_temp.value
                            temp_source = "Bluetooth"
                            ble_ts_list.append(m_temp.timestamp)
                        if m_cya := ble_data.measurements.get(11):
                            self.maintenance_history["cyanuric_acid"] = m_cya.value

                        _LOGGER.debug(
                            "BLE selection result: available_types=%s chlor=%s ph=%s temp=%s cya=%s",
                            sorted(ble_data.measurements.keys()),
                            getattr(m_c, "measure_type", None),
                            getattr(m_ph, "measure_type", None),
                            getattr(m_temp, "measure_type", None),
                            getattr(m_cya, "measure_type", None),
                        )
                        _LOGGER.debug(
                            "BLE source assignment: chlor=%s ph=%s temp=%s",
                            chlor_source,
                            ph_source,
                            temp_source,
                        )
                        if m_ph is None:
                            _LOGGER.debug(
                                "No pH measurement selected from BLE response. Available measurement types were: %s",
                                sorted(ble_data.measurements.keys()),
                            )

                        if ble_ts_list:
                            # Verwende den neuesten Zeitstempel der abgerufenen BLE-Messungen
                            latest_ble_ts = max(ble_ts_list)
                            self.maintenance_history["last_ble_measurement_raw"] = dt_util.utc_from_timestamp(latest_ble_ts).isoformat()

                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        _LOGGER.warning("Bluetooth-Abfrage für PoolLab zeitlich überschritten oder abgebrochen. Nutze Cloud/Manuelle Daten falls verfügbar.")
                else:
                    _LOGGER.warning("PoolLab Bluetooth device not found: %s", ble_address)
            except Exception as err:
                _LOGGER.error("Error fetching PoolLab BLE data: %s", err)

        # 2. Versuch: Cloud-Daten nur dann als Fallback holen, wenn BLE
        # komplett nicht verfügbar war. Sonst würde die Cloud die frischere
        # Bluetooth-Messung wieder als Basis verdrängen.
        if api_key and not ble_found and (c_ist is None or ph_ist is None):
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
                            # Wir nehmen den ersten Account und sortieren Messwerte nach Zeitstempel (absteigend)
                            measurements = cloud_data["Accounts"][0].get("Measurements", [])
                            measurements.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)

                            # Neuesten Zeitstempel aus Cloud erfassen
                            if measurements and (latest_ts := measurements[0].get("timestamp")):
                                cloud_ts_iso = dt_util.utc_from_timestamp(latest_ts).isoformat()
                                self.maintenance_history["last_api_measurement_raw"] = cloud_ts_iso

                            # Sammle die letzten 4 Messwerte für die Anzeige/Fehlersuche
                            last_api_measurements = []
                            for obs in measurements[:4]:
                                p_ts = obs.get("timestamp")
                                last_api_measurements.append({
                                    "parameter": obs.get("parameter"),
                                    "value": obs.get("value"),
                                    "timestamp": dt_util.utc_from_timestamp(p_ts).isoformat() if p_ts else None
                                })
                            self.maintenance_history["last_api_measurements"] = last_api_measurements

                            for obs in measurements:
                                p_name = obs.get("parameter")
                                p_val_raw = obs.get("value")
                                if p_val_raw is None: continue
                                try:
                                    # Sicherheitshalber in Float konvertieren, falls die API Strings liefert
                                    p_val = float(p_val_raw)
                                except (ValueError, TypeError):
                                    _LOGGER.debug("Could not parse value for %s: %s", p_name, p_val_raw)
                                    continue

                                if p_name == "PL Chlorine Free" and c_ist is None and p_val is not None:
                                    c_ist = p_val
                                    chlor_source = "Cloud"
                                if p_name == "PL pH" and ph_ist is None and p_val is not None:
                                    ph_ist = p_val
                                    ph_source = "Cloud"
                                if p_name == "PL Temperature" and temp_ist is None and p_val is not None:
                                    temp_ist = p_val
                                    temp_source = "Cloud"
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
            chlor_source = "Manuell"
            if c_man_ts:
                ts_iso = c_man_ts if isinstance(c_man_ts, str) else c_man_ts.isoformat()
                old_man_str = self.maintenance_history.get("last_manual_measurement_raw")
                dt_new_man = self._parse_ts_aware(ts_iso)
                dt_old_man = self._parse_ts_aware(old_man_str)
                if not dt_old_man or (dt_new_man and dt_new_man > dt_old_man):
                    self.maintenance_history["last_manual_measurement_raw"] = ts_iso

        if ph_ist is None and ph_man is not None:
            ph_ist = ph_man
            ph_source = "Manuell"
            if ph_man_ts:
                ts_iso = ph_man_ts if isinstance(ph_man_ts, str) else ph_man_ts.isoformat()
                old_man_str = self.maintenance_history.get("last_manual_measurement_raw")
                dt_new_man = self._parse_ts_aware(ts_iso)
                dt_old_man = self._parse_ts_aware(old_man_str)
                if not dt_old_man or (dt_new_man and dt_new_man > dt_old_man):
                    self.maintenance_history["last_manual_measurement_raw"] = ts_iso

        if temp_ist is None and temp_man is not None:
            temp_ist = temp_man
            temp_source = "Manuell"

        # 4. Fallback auf Historie, falls aktuelle Quellen keine Daten liefern (Persistenz)
        if c_ist is None:
            c_ist = self.maintenance_history.get("last_c")
            if c_ist is not None:
                chlor_source = "Speicher"
        else:
            self.maintenance_history["last_c"] = c_ist

        if ph_ist is None:
            ph_ist = self.maintenance_history.get("last_ph")
            if ph_ist is not None:
                ph_source = "Speicher"
        else:
            self.maintenance_history["last_ph"] = ph_ist

        if temp_ist is None:
            temp_ist = self.maintenance_history.get("last_temp")
            if temp_ist is not None:
                temp_source = "Speicher"
        else:
            self.maintenance_history["last_temp"] = temp_ist

        last_activities = self._collect_last_activities()
        if last_activities:
            self.maintenance_history["last_activities"] = last_activities

        # Bestimmung der Datenquelle
        sources = []
        if ble_found: sources.append("Bluetooth")
        if cloud_found: sources.append("Cloud")
        if manual_found: sources.append("Manuell")
        data_source = " & ".join(sources) if sources else ("Speicher" if c_ist is not None else "Nicht verfügbar")

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen

        # Synchronisiere den kombinierten Zeitstempel für die Anzeige
        api_ts_str = self.maintenance_history.get("last_api_measurement_raw")
        manual_ts_str = self.maintenance_history.get("last_manual_measurement_raw")
        ble_ts_str = self.maintenance_history.get("last_ble_measurement_raw")
        prev_last_meas_raw = self.maintenance_history.get("last_measurement_raw")

        last_meas_raw = None
        last_meas_source = None
        dt_api = self._parse_ts_aware(api_ts_str)
        dt_man = self._parse_ts_aware(manual_ts_str)
        dt_ble = self._parse_ts_aware(ble_ts_str)

        # Für die Anzeige priorisieren wir die jeweils neueste tatsächlich
        # vorliegende Messquelle. So springt die Anzeige nicht auf eine ältere
        # Cloud-Quelle zurück, wenn Bluetooth oder manuelle Werte neuer sind.
        measurement_candidates = []

        if dt_ble:
            measurement_candidates.append((dt_ble, "Bluetooth", ble_ts_str))
        if dt_api:
            measurement_candidates.append((dt_api, "Cloud", api_ts_str))
        if dt_man:
            measurement_candidates.append((dt_man, "Manuell", manual_ts_str))

        if measurement_candidates:
            _, last_meas_source, last_meas_raw = max(measurement_candidates, key=lambda x: x[0])
        elif prev_last_meas_raw:
            last_meas_raw = prev_last_meas_raw
            last_meas_source = self.maintenance_history.get("last_measurement_source") or "Speicher"

        self.maintenance_history["last_measurement_raw"] = last_meas_raw
        self.maintenance_history["last_measurement_source"] = last_meas_source
        _LOGGER.debug(
            "Selected last measurement for display: source=%s raw=%s",
            last_meas_source,
            last_meas_raw,
        )

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen
        if c_ist is None and ph_ist is None:
            return {
                "chlor_ist": c_ist,
                "ph_ist": ph_ist,
                "temp_ist": temp_ist,
                "chlor_source": chlor_source,
                "ph_source": ph_source,
                "temp_source": temp_source,
                "chlor_dose": 0,
                "ph_senker_total": 0,
                "ph_erhoeher_total": 0,
                "data_source": data_source,
                "is_error": True,
                "last_calculation": dt_util.as_local(self._parse_ts_aware(last_calc_raw)).strftime("%d.%m.%Y %H:%M Uhr"),
                "last_calculation_raw": dt_util.now().isoformat(),
                "last_measurement": dt_util.as_local(self._parse_ts_aware(last_meas_raw)).strftime("%d.%m.%Y %H:%M Uhr") if last_meas_raw else "Noch keine Messung",
                "last_measurement_raw": last_meas_raw,
                "last_measurement_source": last_meas_source,
                "last_api_measurements": last_api_measurements,
                "last_activities": last_activities,
                "pool_covered": self.pool_covered,
                "ble_battery": self.maintenance_history.get("ble_battery"),
                "bluetooth_connected": ble_connected,
                "cyanuric_acid": self.maintenance_history.get("cyanuric_acid"),
                "usage_mode": self.usage_mode,
                "chlor_breakdown_base": 0.0,
                "chlor_breakdown_shock_adj": 0.0,
                "chlor_breakdown_temp_adj": 0.0,
                "chlor_breakdown_env_adj": 0.0,
                "chlor_breakdown_bather_adj": 0.0,
                "chlor_breakdown_sum_raw": 0.0,
                "chlor_breakdown_min_dose_applied": 0.0,
                "history": self.maintenance_history,
                "recommendation": "⚠️ Keine Messwerte vorhanden"
            }

        # Konfiguration laden
        volumen = conf.get(CONF_POOL_VOLUME, 1.0)
        c_ziel = conf.get(CONF_CHLOR_TARGET, 1.5)
        ph_ziel = conf.get(CONF_PH_TARGET, 7.2)
        wirkstoff = conf.get(CONF_CHLOR_CONTENT, 0.56)

        if wirkstoff <= 0:
            wirkstoff = 0.56 # Schutz vor Division durch Null

        # Nutzungs- und Abdeckungsfaktoren
        # Wenn offen, erhöhen wir die Grundzehrung (UV-Verlust)
        env_factor = 0.8 if self.pool_covered else 1.2

        # Badelast-Zuschlag in Gramm (Absolutwerte)
        bather_load_extra = 0.0
        if self.usage_mode == "normal": bather_load_extra = 3.0
        elif self.usage_mode == "party": bather_load_extra = 8.0

        # Chlor Berechnung
        c_diff = max(float(c_ziel) - float(c_ist), 0) if c_ist is not None else 0

        # Temperatur-Korrekturfaktor für Chlor (höhere Zehrung bei warmem Wasser)
        temp_factor = 1.0
        if temp_ist is not None:
            if float(temp_ist) > 32:
                temp_factor = 1.5
            elif float(temp_ist) > 28:
                temp_factor = 1.2

        # Stoßchlorung Faktor
        shock_factor = 1.0
        if c_ist is not None:
            if float(c_ist) < 0.1: shock_factor = 3.0
            elif float(c_ist) < 0.3: shock_factor = 2.4
            elif float(c_ist) < 0.6: shock_factor = 1.8
            elif float(c_ist) < 1.0: shock_factor = 1.3

        # Mindestdosis
        min_dose = 2.0
        if c_ist is not None:
            if float(c_ist) < 0.3: min_dose = 6.0
            elif float(c_ist) < 0.8: min_dose = 3.0

        chlor_base_amount_raw = (c_diff * volumen / wirkstoff)
        raw_chlor = (chlor_base_amount_raw * shock_factor * env_factor * temp_factor) + bather_load_extra
        if c_ist is not None and c_ist >= c_ziel:
            s_g = 0.0
        else:
            s_g = round(min(max(raw_chlor, min_dose), 25.0), 1) if c_ist is not None else 0.0

        # --- Werte für die Frontend-Anzeige der Berechnung ---
        # Basiswert (ohne Faktoren)
        chlor_breakdown_base = round(chlor_base_amount_raw, 2)

        # Anpassung durch Schock-Faktor
        chlor_after_shock = chlor_base_amount_raw * shock_factor
        chlor_breakdown_shock_adj = round(chlor_after_shock - chlor_base_amount_raw, 2)

        # Anpassung durch Temperatur
        chlor_after_temp = chlor_after_shock * temp_factor
        chlor_breakdown_temp_adj = round(chlor_after_temp - chlor_after_shock, 2)

        # Anpassung durch Abdeckung
        chlor_after_env = chlor_after_temp * env_factor
        chlor_breakdown_env_adj = round(chlor_after_env - chlor_after_temp, 2)

        # Anpassung durch Badelast (direkter Zuschlag)
        chlor_breakdown_bather_adj = round(bather_load_extra, 2)

        # Summe der Anpassungen (vor Mindest-/Maximaldosis)
        chlor_breakdown_sum_raw = round(raw_chlor, 2)

        # Mindestdosis, falls angewendet
        chlor_breakdown_min_dose_applied = round(min_dose, 2) if (s_g > 0 and raw_chlor < min_dose) else 0.0

        # pH Berechnung
        ph_diff = ph_ziel - ph_ist if ph_ist is not None else 0
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

        # Filter Wartung
        hours_since_filter_clean = self._get_time_since_last_action("filter_clean", in_hours=True)
        days_since_filter_replace = self._get_time_since_last_action("filter_replace")

        filter_clean_interval = conf.get(CONF_FILTER_CLEAN_INTERVAL, 24)
        filter_replace_interval = conf.get(CONF_FILTER_REPLACE_INTERVAL, 180)

        filter_clean_yellow_threshold = conf.get(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, 4)
        filter_clean_red_threshold = conf.get(CONF_FILTER_CLEAN_RED_THRESHOLD, 0)
        filter_replace_yellow_threshold = conf.get(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, 30)
        filter_replace_red_threshold = conf.get(CONF_FILTER_REPLACE_RED_THRESHOLD, 0)

        filter_clean_status = get_filter_status(
            hours_since_filter_clean, filter_clean_interval,
            filter_clean_yellow_threshold, filter_clean_red_threshold
        )
        filter_replace_status = get_filter_status(
            days_since_filter_replace, filter_replace_interval,
            filter_replace_yellow_threshold, filter_replace_red_threshold
        )

        # Check and send filter notifications
        await self._check_filter_notifications(conf)

        # --- Zentrale Status-Logik für Warnungen ---
        warnings = []

        # Konvertierung für sicheren Vergleich
        current_ph = float(ph_ist) if ph_ist is not None else None
        target_ph = float(ph_ziel)
        current_c = float(c_ist) if c_ist is not None else None
        target_c = float(c_ziel)

        # pH Check (Schwellenwert 0.1)
        if current_ph is not None:
            if current_ph > (target_ph + 0.1):
                warnings.append("pH zu hoch")
            elif current_ph < (target_ph - 0.1):
                warnings.append("pH zu niedrig")

        # Chlor Check (Schwellenwert 0.2)
        if current_c is not None:
            if current_c < 0.5:
                warnings.append("Stoßchlorung empfohlen")
            elif current_c > (target_c + 0.2):
                warnings.append("Chlor zu hoch")
            elif current_c < (target_c - 0.2) and s_g > 0:
                warnings.append("Chlor nachdosieren")

        # Finaler Empfehlungstext
        if not warnings:
            recommendation = "✅ Alle Werte im Zielbereich"
        else:
            # Kombiniere Warnungen mit " & "
            recommendation = "⚠️ " + " & ".join(warnings)

        # Zeitstempel der Berechnung bei jedem erfolgreichen Durchlauf aktualisieren
        new_calc_ts = dt_util.now().isoformat()
        self.maintenance_history["last_calc_raw"] = new_calc_ts

        await self._store.async_save(self.maintenance_history)

        return {
            "chlor_ist": c_ist,
            "ph_ist": ph_ist,
            "temp_ist": temp_ist,
            "chlor_source": chlor_source,
            "ph_source": ph_source,
            "temp_source": temp_source,
            "chlor_dose": s_g,
            "chlor_pre": round(max(s_g * 0.3, 1.0), 1) if s_g > 0 else 0.0,
            "ph_senker_total": ph_senker_ml,
            "ph_erhoeher_total": ph_erhoeher_g,
            "data_source": data_source,
            "ph_diff": ph_diff,
            "is_shock": (c_ist is not None and c_ist < 0.5),
            "is_error": False,
            "last_calculation": dt_util.as_local(self._parse_ts_aware(new_calc_ts)).strftime("%d.%m.%Y %H:%M Uhr"),
            "last_calculation_raw": new_calc_ts,
            "last_measurement": dt_util.as_local(self._parse_ts_aware(last_meas_raw)).strftime("%d.%m.%Y %H:%M Uhr") if last_meas_raw else "Noch keine Messung",
            "last_measurement_raw": last_meas_raw,
            "last_measurement_source": last_meas_source,
            "chlor_target": c_ziel,
            "ph_target": ph_ziel,
            "ble_battery": self.maintenance_history.get("ble_battery"),
            "bluetooth_connected": ble_connected,
            "last_activities": last_activities,
            "history": self.maintenance_history,
            "recommendation": recommendation,
            "cyanuric_acid": self.maintenance_history.get("cyanuric_acid"),
            "chlor_breakdown_base": chlor_breakdown_base,
            "last_api_measurements": last_api_measurements,
            "chlor_breakdown_shock_adj": chlor_breakdown_shock_adj,
            "chlor_breakdown_temp_adj": chlor_breakdown_temp_adj,
            "chlor_breakdown_env_adj": chlor_breakdown_env_adj,
            "chlor_breakdown_bather_adj": chlor_breakdown_bather_adj,
            "chlor_breakdown_sum_raw": chlor_breakdown_sum_raw,
            "chlor_breakdown_min_dose_applied": chlor_breakdown_min_dose_applied,
            "hours_since_filter_clean": hours_since_filter_clean,
            "pool_covered": self.pool_covered,
            "usage_mode": self.usage_mode,
            "filter_clean_status": filter_clean_status,
            "filter_clean_interval": filter_clean_interval,
            "days_since_filter_replace": days_since_filter_replace,
            "filter_replace_status": filter_replace_status,
            "filter_replace_interval": filter_replace_interval,
        }
