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
    CONF_NOTIFY_SERVICE, CONF_FOLLOW_UP_TIME, CONF_PERSISTENT_NOTIFICATION,
    CONF_FILTER_CLEAN_INTERVAL, CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD, CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD, CONF_FILTER_REPLACE_RED_THRESHOLD
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
        # Standardwerte für neue Logik initialisieren
        self.pool_covered = True
        self.usage_mode = "none" # none, normal, party

    @property
    def config(self):
        """Return combined config from data and options."""
        return {**self.entry.data, **self.entry.options}

    async def async_load_history(self):
        """Load maintenance history from storage."""
        stored = await self._store.async_load()
        if stored:
            self.maintenance_history = stored
            self.pool_covered = stored.get("pool_covered", True)
            self.usage_mode = stored.get("usage_mode", "none")

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
        ts_formatted = now.strftime("%d.%m. %H:%M")
        
        label = ""
        unit = ""
        msg = None

        if m_type == "chlor": label, unit = "Chlor", "g"
        elif m_type == "ph_plus": label, unit = "PH-Plus", "g"
        elif m_type == "ph_minus": label, unit = "PH-Minus", "ml"
        elif m_type == "filter_clean": label, unit = "Filter gereinigt", ""
        elif m_type == "filter_replace": label, unit = "Filter gewechselt", ""
        elif m_type == "set_covered":
            self.pool_covered = amount > 0
            self.maintenance_history["pool_covered"] = self.pool_covered
        elif m_type == "set_usage":
            modes = ["none", "normal", "party"]
            self.usage_mode = modes[int(amount)] if int(amount) < len(modes) else "none"
            self.maintenance_history["usage_mode"] = self.usage_mode
        
        # Update history for chemicals and filter
        if m_type in ("chlor", "ph_plus", "ph_minus", "filter_clean", "filter_replace"):
            self.maintenance_history[m_type] = {"amount": amount, "time": ts_formatted, "raw_ts": now.isoformat()}
            action_text = f"{amount}{unit} {label}" if amount else label
            self.maintenance_history["last_action"] = f"{action_text} am {ts_formatted}"
            # Wording für Wartung vs. Chemie anpassen
            if m_type == "filter_clean":
                msg = "Pool-Wartung: Der Filter wurde erfolgreich gereinigt."
            elif m_type == "filter_replace":
                msg = "Pool-Wartung: Der Filter wurde erfolgreich gewechselt."
            else:
                msg = f"Pool-Pflege: {amount}{unit} {label} zugegeben."

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
                ts = state.attributes.get("measured_at") or state.attributes.get("timestamp")
                return float(state.state), ts
            except ValueError:
                return None, None

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

        # 1. Bestehende Daten aus der Historie laden (Basis für die Anzeige)
        last_meas_raw = self.maintenance_history.get("last_measurement_raw")
        last_calc_raw = self.maintenance_history.get("last_calc_raw")
        
        # Falls noch nie berechnet wurde, initialisieren wir mit jetzt (nur für die Anzeige)
        if not last_calc_raw:
            last_calc_raw = dt_util.now().isoformat()

        conf = self.config
        api_key = conf.get(CONF_API_KEY)

        data_source = "Nicht verfügbar"
        cloud_found = False
        manual_found = False

        c_ist = ph_ist = temp_ist = None
        new_meas_ts = None
        last_api_measurements = []

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
                            # Wir nehmen den ersten Account und sortieren Messwerte nach Zeitstempel (absteigend)
                            measurements = cloud_data["Accounts"][0].get("Measurements", [])
                            measurements.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
                            
                            # Sammle die letzten 4 Messwerte für die Anzeige/Fehlersuche
                            for obs in measurements[:4]:
                                p_ts = obs.get("timestamp")
                                last_api_measurements.append({
                                    "parameter": obs.get("parameter"),
                                    "value": obs.get("value"),
                                    "timestamp": dt_util.utc_from_timestamp(p_ts).isoformat() if p_ts else None
                                })

                            for obs in measurements:
                                p_name = obs.get("parameter")
                                p_val_raw = obs.get("value")
                                try:
                                    # Sicherheitshalber in Float konvertieren, falls die API Strings liefert
                                    p_val = float(p_val_raw) if p_val_raw is not None else None
                                except (ValueError, TypeError):
                                    _LOGGER.debug("Could not parse value for %s: %s", p_name, p_val_raw)
                                    continue

                                p_ts = obs.get("timestamp")
                                
                                if p_name == "PL Chlorine Free" and c_ist is None and p_val is not None:
                                    c_ist = p_val
                                    if p_ts:
                                        new_meas_ts = dt_util.utc_from_timestamp(p_ts).isoformat()
                                if p_name == "PL pH" and ph_ist is None and p_val is not None:
                                    ph_ist = p_val
                                    if p_ts and not new_meas_ts:
                                        new_meas_ts = dt_util.utc_from_timestamp(p_ts).isoformat()
                                if p_name == "PL Temperature" and temp_ist is None and p_val is not None:
                                    temp_ist = p_val
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
                "chlor_ist": c_ist,
                "ph_ist": ph_ist,
                "temp_ist": temp_ist,
                "chlor_dose": 0,
                "ph_senker_total": 0,
                "ph_erhoeher_total": 0,
                "data_source": data_source,
                "is_error": True,
                "last_calculation": dt_util.parse_datetime(last_calc_raw).strftime("%d.%m.%Y %H:%M Uhr"),
                "last_measurement": dt_util.parse_datetime(last_meas_raw).strftime("%d.%m.%Y %H:%M Uhr") if last_meas_raw else "Noch keine Messung",
                "last_api_measurements": last_api_measurements,
                "pool_covered": self.pool_covered,
                "usage_mode": self.usage_mode,
                "chlor_breakdown_base": 0.0,
                "chlor_breakdown_shock_adj": 0.0,
                "chlor_breakdown_temp_adj": 0.0,
                "chlor_breakdown_env_adj": 0.0,
                "chlor_breakdown_bather_adj": 0.0,
                "chlor_breakdown_sum_raw": 0.0,
                "chlor_breakdown_min_dose_applied": 0.0,
                "history": self.maintenance_history
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
        c_diff = max(c_ziel - c_ist, 0)
        
        # Temperatur-Korrekturfaktor für Chlor (höhere Zehrung bei warmem Wasser)
        temp_factor = 1.0
        if temp_ist is not None:
            if temp_ist > 32:
                temp_factor = 1.5
            elif temp_ist > 28:
                temp_factor = 1.2

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

        chlor_base_amount_raw = (c_diff * volumen / wirkstoff)
        raw_chlor = (chlor_base_amount_raw * shock_factor * env_factor * temp_factor) + bather_load_extra
        s_g = round(min(max(raw_chlor, min_dose), 25.0), 1)

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
        chlor_breakdown_min_dose_applied = round(min_dose, 2) if raw_chlor < min_dose else 0.0
        
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
            "last_measurement": dt_util.parse_datetime(last_meas_raw).strftime("%d.%m.%Y %H:%M Uhr") if last_meas_raw else "Noch keine Messung",
            "chlor_target": c_ziel,
            "ph_target": ph_ziel,
            "history": self.maintenance_history,
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
