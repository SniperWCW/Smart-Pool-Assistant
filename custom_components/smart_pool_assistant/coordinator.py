import logging
import asyncio
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN, CONF_API_KEY, CONF_BLE_ADDRESS, CONF_UPDATE_INTERVAL, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_PUMP_ENTITY,
    CONF_FOLLOW_UP_TIME,
    CONF_CHLOR_PRODUCT_TYPE,
    CONF_CHLOR_SHOCK_MAX,
    CONF_FILTER_CLEAN_INTERVAL, CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD, CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD, CONF_FILTER_REPLACE_RED_THRESHOLD,
    CONF_POOL_VOLUME,
    CONF_WEATHER_ENTITY, CONF_UV_SENSOR,
    CONF_POOL_CONNECTION_SENSOR, CONF_POOL_CONNECTION_OFFLINE_DELAY,
)
from .calculation import (
    build_recommendation,
    calculate_pool_chemistry,
    calculate_retest_status,
)
from .chlorine_learning import (
    MIN_DOSE_FACTOR_SAMPLES,
    MIN_DOSE_EFFECT_HOURS,
    MAX_DOSE_EFFECT_HOURS,
    calculate_chlorine_learning,
    diagnose_chlorine_dose_samples,
    record_chlor_dose,
    record_chlor_measurement,
)
from .cya_learning import (
    calculate_cya_learning,
    normalize_water_exchange,
    record_cya_measurement,
    record_water_exchange,
)
from .ph_learning import (
    calculate_ph_learning,
    record_ph_correction,
    record_ph_measurement,
)
from .maintenance import (
    activity_text,
    collect_last_activities,
    get_action_dt,
    get_filter_status,
    get_time_since_last_action,
    normalize_loaded_history,
    update_maintenance_history,
)
from .notifications import (
    async_check_filter_notifications,
    async_send_pool_connection_lost,
    async_send_follow_up,
    async_send_notification,
)
from .poollab_ble import PoolLabBLEClient
from .poollab_ble_source import select_poollab_ble_measurements
from .poollab_cloud import async_fetch_poollab_cloud_measurements
from .weather import async_get_weather_data

_LOGGER = logging.getLogger(__name__)

_STORAGE_VERSION = 1
_STORAGE_KEY = f"{DOMAIN}_maintenance"
_DEFAULT_UPDATE_INTERVAL_MINUTES = 5
_BLE_SUCCESS_COOLDOWN = timedelta(seconds=20)
_BLE_ERROR_COOLDOWN = timedelta(seconds=30)
_RECENT_MEASUREMENTS_HISTORY_LIMIT = 40

class SmartPoolCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        update_interval_minutes = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, _DEFAULT_UPDATE_INTERVAL_MINUTES),
        )
        try:
            update_interval_minutes = max(1, int(update_interval_minutes))
        except (TypeError, ValueError):
            update_interval_minutes = _DEFAULT_UPDATE_INTERVAL_MINUTES

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_minutes),
        )

        self.entry = entry
        self._store = Store(hass, _STORAGE_VERSION, f"{_STORAGE_KEY}_{entry.entry_id}")
        self.maintenance_history = {}
        self._poollab_fetch_lock = asyncio.Lock()
        self._poollab_fetch_requested = False
        self._next_poollab_fetch_allowed_at = None
        self._pool_connection_offline_cancel = None
        # Standardwerte für neue Logik initialisieren
        self.pool_covered = True
        self.usage_mode = "none" # none, normal, party

    def _activity_text(self, m_type: str | None, amount: float | int | None) -> str:
        """Return a human readable activity label."""
        return activity_text(m_type, amount, self.pool_covered, self.usage_mode)

    def _normalize_loaded_history(self, stored: dict) -> dict:
        """Fix legacy history entries in-place after loading from storage."""
        return normalize_loaded_history(stored, self.pool_covered, self.usage_mode)

    def _parse_ts_aware(self, ts_str: str | None):
        """Helper to parse a timestamp string into an aware datetime object."""
        if not ts_str: return None
        dt = dt_util.parse_datetime(ts_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_util.UTC)
        return dt

    def _normalize_ble_measurement_ts(
        self,
        ts: int,
        fetched_at_iso: str | None,
        *,
        latest_raw_ts: int | None = None,
    ) -> str:
        """Map BLE timestamps onto the fetch timeline while preserving spacing."""
        fetched_at_dt = self._parse_ts_aware(fetched_at_iso) if fetched_at_iso else None
        ble_dt = dt_util.utc_from_timestamp(ts)

        if fetched_at_dt:
            if latest_raw_ts is None:
                latest_raw_ts = ts
            delta_seconds = ts - latest_raw_ts
            normalized_dt = fetched_at_dt + timedelta(seconds=delta_seconds)
            if ble_dt != normalized_dt:
                _LOGGER.debug(
                    "Normalizing PoolLab BLE timestamp relative to latest chemistry sample: ble=%s latest_raw=%s fetched_at=%s normalized=%s",
                    ble_dt.isoformat(),
                    dt_util.utc_from_timestamp(latest_raw_ts).isoformat(),
                    fetched_at_dt.isoformat(),
                    normalized_dt.isoformat(),
                )
            return normalized_dt.isoformat()

        return ble_dt.isoformat()

    def _canonical_measurement_parameter(self, parameter: str | None) -> str | None:
        """Normalize measurement labels across API, BLE and manual sources."""
        if not parameter:
            return None

        normalized = str(parameter).strip()
        mapping = {
            "PL Chlorine Free": "Chlor",
            "PL pH": "pH",
            "PL Temperature": "Temperatur",
            "PL Cyanuric Acid": "Cyanursaeure",
            "PL Cyanuric acid": "Cyanursaeure",
            "PL CYA": "Cyanursaeure",
            "chlor": "Chlor",
            "ph": "pH",
            "temperature": "Temperatur",
            "cyanuric_acid": "Cyanursaeure",
        }
        return mapping.get(normalized, normalized)

    def _is_chemistry_measurement_parameter(self, parameter: str | None) -> bool:
        """Return whether a normalized parameter belongs to chemistry history."""
        return parameter in {"Chlor", "pH", "Cyanursaeure"}

    def _build_recent_measurement_entry(
        self,
        *,
        parameter: str | None,
        value: object,
        timestamp_raw: str | None,
        source: str,
    ) -> dict | None:
        """Create a normalized history row for the Lovelace card."""
        if value is None or not timestamp_raw:
            return None

        parsed_ts = self._parse_ts_aware(timestamp_raw)
        if parsed_ts is None:
            return None

        canonical_parameter = self._canonical_measurement_parameter(parameter)
        if not canonical_parameter:
            return None
        if not self._is_chemistry_measurement_parameter(canonical_parameter):
            return None

        try:
            numeric_value = round(float(value), 2)
        except (TypeError, ValueError):
            numeric_value = value

        return {
            "parameter": canonical_parameter,
            "value": numeric_value,
            "timestamp": parsed_ts.isoformat(),
            "source": source,
        }

    def _merge_recent_measurements(self, new_entries: list[dict]) -> list[dict]:
        """Persist a deduplicated mixed-source measurement history for display."""
        existing = self.maintenance_history.get("last_measurements_display", [])
        merged: list[dict] = []
        seen: set[tuple[str | None, str | None, str | None, str]] = set()

        for item in [*(existing if isinstance(existing, list) else []), *new_entries]:
            if not isinstance(item, dict):
                continue
            key = (
                item.get("timestamp"),
                item.get("parameter"),
                item.get("source"),
                str(item.get("value")),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

        merged.sort(
            key=lambda item: self._parse_ts_aware(item.get("timestamp")) or dt_util.utc_from_timestamp(0),
            reverse=True,
        )
        merged = merged[:_RECENT_MEASUREMENTS_HISTORY_LIMIT]
        self.maintenance_history["last_measurements_display"] = merged
        return merged

    def _format_measurement_ts(self, ts_raw: str | None) -> str | None:
        """Format a raw timestamp for compact frontend display."""
        dt_value = self._parse_ts_aware(ts_raw)
        if dt_value is None:
            return None
        return dt_util.as_local(dt_value).strftime("%d.%m.%Y %H:%M Uhr")

    def _normalize_ble_history_ts(
        self,
        raw_ts: int,
        *,
        latest_raw_ts: int | None,
        fetched_at_iso: str | None,
    ) -> str | None:
        """Map stored BLE history timestamps onto the current fetch timeline.

        PoolLab timestamps are often offset, but their relative spacing is useful.
        We anchor the newest chemistry timestamp to the fetch completion time and
        preserve the deltas for older records so stored BLE history can repair
        learning samples retroactively.
        """
        fetched_at_dt = self._parse_ts_aware(fetched_at_iso) if fetched_at_iso else None
        if fetched_at_dt is None:
            return None
        if latest_raw_ts is None:
            return fetched_at_dt.isoformat()
        delta_seconds = raw_ts - latest_raw_ts
        normalized_dt = fetched_at_dt + timedelta(seconds=delta_seconds)
        return normalized_dt.isoformat()

    def _backfill_ble_learning_history(self, ble_data, fetched_at_iso: str | None) -> None:
        """Import historical BLE chemistry measurements into learning storage."""
        measurements = getattr(ble_data, "measurements", None)
        if not isinstance(measurements, dict) or not measurements:
            return

        chlor_type_ids = {1, 3, 8}
        ph_type_ids = {9, 27, 28, 29, 30, 31, 32, 33, 34, 36, 48}
        cya_type_id = 11

        chemistry_measurements = [
            item for item in measurements.values()
            if getattr(item, "measure_type", None) in chlor_type_ids | ph_type_ids | {cya_type_id}
        ]
        if not chemistry_measurements:
            return

        latest_raw_ts = max(getattr(item, "timestamp", 0) for item in chemistry_measurements)
        imported_chlor = 0
        imported_ph = 0
        imported_cya = 0

        for item in sorted(chemistry_measurements, key=lambda measurement: getattr(measurement, "timestamp", 0)):
            normalized_ts = self._normalize_ble_history_ts(
                int(item.timestamp),
                latest_raw_ts=latest_raw_ts,
                fetched_at_iso=fetched_at_iso,
            )
            if not normalized_ts:
                continue
            if item.measure_type in chlor_type_ids:
                before = len(self.maintenance_history.get("chlor_learning_measurements", []) or [])
                record_chlor_measurement(self.maintenance_history, normalized_ts, item.value)
                after = len(self.maintenance_history.get("chlor_learning_measurements", []) or [])
                if after > before:
                    imported_chlor += 1
            elif item.measure_type in ph_type_ids:
                before = len(self.maintenance_history.get("ph_learning_measurements", []) or [])
                record_ph_measurement(self.maintenance_history, normalized_ts, item.value)
                after = len(self.maintenance_history.get("ph_learning_measurements", []) or [])
                if after > before:
                    imported_ph += 1
            elif item.measure_type == cya_type_id:
                before = len(self.maintenance_history.get("cya_learning_measurements", []) or [])
                record_cya_measurement(self.maintenance_history, normalized_ts, item.value)
                after = len(self.maintenance_history.get("cya_learning_measurements", []) or [])
                if after > before:
                    imported_cya += 1

        if imported_chlor or imported_ph or imported_cya:
            _LOGGER.debug(
                "Backfilled BLE learning history: chlor=%s ph=%s cya=%s",
                imported_chlor,
                imported_ph,
                imported_cya,
            )

    def _backfill_cloud_learning_history(self, last_measurements: list[dict]) -> None:
        """Import cloud chemistry history into learning storage when available."""
        if not isinstance(last_measurements, list):
            return

        imported_chlor = 0
        imported_ph = 0
        for item in last_measurements:
            if not isinstance(item, dict):
                continue
            raw_ts = item.get("timestamp")
            parameter = item.get("parameter")
            value = item.get("value")
            if not isinstance(raw_ts, str) or not raw_ts:
                continue
            if parameter == "PL Chlorine Free":
                before = len(self.maintenance_history.get("chlor_learning_measurements", []) or [])
                record_chlor_measurement(self.maintenance_history, raw_ts, value)
                after = len(self.maintenance_history.get("chlor_learning_measurements", []) or [])
                if after > before:
                    imported_chlor += 1
            elif parameter == "PL pH":
                before = len(self.maintenance_history.get("ph_learning_measurements", []) or [])
                record_ph_measurement(self.maintenance_history, raw_ts, value)
                after = len(self.maintenance_history.get("ph_learning_measurements", []) or [])
                if after > before:
                    imported_ph += 1

        if imported_chlor or imported_ph:
            _LOGGER.debug(
                "Backfilled cloud learning history: chlor=%s ph=%s",
                imported_chlor,
                imported_ph,
            )

    @property
    def config(self):
        """Return combined config from data and options."""
        return {**self.entry.data, **self.entry.options}

    def _pump_tracking_state(self) -> tuple[str | None, bool | None]:
        """Return configured pump entity and current active state."""
        entity_id = self.config.get(CONF_PUMP_ENTITY)
        if not entity_id:
            return None, None
        state = self.hass.states.get(entity_id)
        if state is None:
            return entity_id, None
        return entity_id, state.state == "on"

    def _sync_pump_runtime_tracking(self, now: object | None = None) -> float | None:
        """Persist a cumulative pump runtime counter for learning snapshots."""
        entity_id, pump_active = self._pump_tracking_state()
        if not entity_id:
            return None

        now_dt = now if isinstance(now, datetime) else dt_util.now()
        tracking = self.maintenance_history.get("pump_tracking")
        tracking = dict(tracking) if isinstance(tracking, dict) else {}

        total_hours = float(tracking.get("total_hours") or 0.0)
        last_sync_dt = self._parse_ts_aware(tracking.get("last_sync_raw"))
        last_state = tracking.get("last_state")
        if last_sync_dt and last_state == "on":
            elapsed_hours = (now_dt - last_sync_dt).total_seconds() / 3600.0
            if 0 <= elapsed_hours <= 24 * 14:
                total_hours += elapsed_hours

        tracking["total_hours"] = round(total_hours, 3)
        tracking["last_sync_raw"] = now_dt.isoformat()
        tracking["last_state"] = "on" if pump_active else "off"
        self.maintenance_history["pump_tracking"] = tracking
        return tracking["total_hours"]

    def _current_pump_runtime_hours(self, now: object | None = None) -> float | None:
        """Return the up-to-date cumulative pump runtime hours."""
        return self._sync_pump_runtime_tracking(now)

    def _get_next_poollab_fetch_allowed_at(self) -> str | None:
        """Return the next allowed fetch timestamp if the cooldown is still active."""
        if self._next_poollab_fetch_allowed_at and self._next_poollab_fetch_allowed_at <= dt_util.now():
            self._next_poollab_fetch_allowed_at = None
            self.maintenance_history.pop("next_poollab_fetch_allowed_at", None)
        return self._next_poollab_fetch_allowed_at.isoformat() if self._next_poollab_fetch_allowed_at else None

    def _set_poollab_cooldown(self, cooldown: timedelta | None) -> None:
        """Persist the next allowed manual PoolLab fetch time."""
        if cooldown is None:
            self._next_poollab_fetch_allowed_at = None
            self.maintenance_history.pop("next_poollab_fetch_allowed_at", None)
            return

        self._next_poollab_fetch_allowed_at = dt_util.now() + cooldown
        self.maintenance_history["next_poollab_fetch_allowed_at"] = self._next_poollab_fetch_allowed_at.isoformat()

    def _remaining_poollab_cooldown(self) -> int:
        """Return the remaining cooldown in whole seconds."""
        next_allowed = self._get_next_poollab_fetch_allowed_at()
        if not next_allowed:
            return 0

        next_allowed_dt = self._parse_ts_aware(next_allowed)
        if next_allowed_dt is None:
            return 0

        remaining = (next_allowed_dt - dt_util.now()).total_seconds()
        if remaining <= 0:
            self._next_poollab_fetch_allowed_at = None
            self.maintenance_history.pop("next_poollab_fetch_allowed_at", None)
            return 0

        return int(remaining + 0.999)

    async def async_fetch_poollab_measurements(self) -> None:
        """Fetch PoolLab values exactly once on explicit user request."""
        _LOGGER.debug(
            "Manual PoolLab fetch requested: entry_id=%s has_ble=%s has_api_key=%s",
            self.entry.entry_id,
            bool(self.config.get(CONF_BLE_ADDRESS)),
            bool(self.config.get(CONF_API_KEY)),
        )
        if not self.config.get(CONF_BLE_ADDRESS) and not self.config.get(CONF_API_KEY):
            raise HomeAssistantError("Kein PoolLab-Abruf konfiguriert.")

        if self._poollab_fetch_lock.locked():
            raise HomeAssistantError("Ein PoolLab-Abruf laeuft bereits.")

        if remaining := self._remaining_poollab_cooldown():
            message = f"PoolLab-Abruf bitte erst in {remaining} Sekunden erneut ausloesen."
            self.maintenance_history["last_poollab_fetch_result"] = "cooldown"
            self.maintenance_history["last_poollab_fetch_error"] = message
            await self._store.async_save(self.maintenance_history)
            await self.async_request_refresh()
            raise HomeAssistantError(message)

        async with self._poollab_fetch_lock:
            self._poollab_fetch_requested = True
            self.maintenance_history["last_poollab_fetch_requested_at"] = dt_util.now().isoformat()
            self.maintenance_history["last_poollab_fetch_result"] = "running"
            self.maintenance_history["last_poollab_fetch_error"] = None
            await self._store.async_save(self.maintenance_history)
            try:
                await self.async_request_refresh()
            finally:
                self._poollab_fetch_requested = False

        fetch_result = self.data.get("poollab_fetch_result")
        _LOGGER.debug(
            "Manual PoolLab fetch finished: result=%s error=%s completed_at=%s next_allowed_at=%s",
            fetch_result,
            self.data.get("poollab_fetch_error"),
            self.data.get("last_poollab_fetch_completed_at"),
            self.data.get("next_poollab_fetch_allowed_at"),
        )
        if fetch_result == "error":
            raise HomeAssistantError(self.data.get("poollab_fetch_error") or "PoolLab-Abruf fehlgeschlagen.")
        if fetch_result == "cooldown":
            raise HomeAssistantError(self.data.get("poollab_fetch_error") or "PoolLab-Abruf ist noch gesperrt.")

    async def async_load_history(self):
        """Load maintenance history from storage."""
        stored = await self._store.async_load()
        if stored:
            normalized = self._normalize_loaded_history(stored)
            self.maintenance_history = normalized
            self.pool_covered = stored.get("pool_covered", True)
            self.usage_mode = stored.get("usage_mode", "none")
            next_allowed = stored.get("next_poollab_fetch_allowed_at")
            if isinstance(next_allowed, str):
                self._next_poollab_fetch_allowed_at = self._parse_ts_aware(next_allowed)
            if normalized != stored:
                await self._store.async_save(self.maintenance_history)

    def async_setup_event_listeners(self):
        """Set up listeners for entity state changes."""
        conf = self.config
        unsubscribers = []
        entities = []
        # Nur Entitäten überwachen, die auch wirklich konfiguriert wurden
        for key in [CONF_CHLOR_SENSOR, CONF_PH_SENSOR]:
            if eid := conf.get(key):
                entities.append(eid)

        if entities:
            unsubscribers.append(
                async_track_state_change_event(
                    self.hass, entities, self._handle_state_change
                )
            )
        else:
            _LOGGER.debug("No manual sensors configured, relying solely on API/Cloud")

        if connection_entity := conf.get(CONF_POOL_CONNECTION_SENSOR):
            unsubscribers.append(
                async_track_state_change_event(
                    self.hass, [connection_entity], self._handle_pool_connection_change
                )
            )
            self._schedule_pool_connection_check(connection_entity)

        if pump_entity := conf.get(CONF_PUMP_ENTITY):
            unsubscribers.append(
                async_track_state_change_event(
                    self.hass, [pump_entity], self._handle_pump_change
                )
            )
            self._sync_pump_runtime_tracking()

        def unsubscribe_all():
            if self._pool_connection_offline_cancel:
                self._pool_connection_offline_cancel()
                self._pool_connection_offline_cancel = None
            for unsubscribe in unsubscribers:
                unsubscribe()

        return unsubscribe_all

    async def _handle_pool_connection_change(self, event):
        """Schedule or reset the pool connection lost notification."""
        entity_id = event.data.get("entity_id")
        self._schedule_pool_connection_check(entity_id)
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is not None and state.state == "on":
            await self._store.async_save(self.maintenance_history)

    async def _handle_pump_change(self, _event):
        """Persist pump runtime deltas on every state change."""
        self._sync_pump_runtime_tracking()
        await self._store.async_save(self.maintenance_history)

    def _schedule_pool_connection_check(self, entity_id: str | None) -> None:
        """Schedule an offline check for the configured pool connection entity."""
        if not entity_id:
            return

        state = self.hass.states.get(entity_id)
        if state is not None and state.state == "on":
            if self._pool_connection_offline_cancel:
                self._pool_connection_offline_cancel()
                self._pool_connection_offline_cancel = None
            self.maintenance_history.pop("pool_connection_lost_notified", None)
            return

        if state is None or state.state not in ("off", "unavailable"):
            return

        if self.maintenance_history.get("pool_connection_lost_notified"):
            return

        if self._pool_connection_offline_cancel:
            self._pool_connection_offline_cancel()

        delay_minutes = self._pool_connection_offline_delay_minutes()
        self._pool_connection_offline_cancel = async_call_later(
            self.hass,
            delay_minutes * 60,
            self._async_check_pool_connection_offline,
        )

    def _pool_connection_offline_delay_minutes(self) -> int:
        """Return the configured pool connection offline delay in minutes."""
        try:
            return max(1, int(self.config.get(CONF_POOL_CONNECTION_OFFLINE_DELAY, 5)))
        except (TypeError, ValueError):
            return 5

    async def _async_check_pool_connection_offline(self, _now) -> None:
        """Send a notification if the pool connection is still offline."""
        self._pool_connection_offline_cancel = None
        entity_id = self.config.get(CONF_POOL_CONNECTION_SENSOR)
        state = self.hass.states.get(entity_id) if entity_id else None

        if state is None or state.state not in ("off", "unavailable"):
            return

        if self.maintenance_history.get("pool_connection_lost_notified"):
            return

        delay_minutes = self._pool_connection_offline_delay_minutes()
        await async_send_pool_connection_lost(self.hass, self.config, delay_minutes)
        self.maintenance_history["pool_connection_lost_notified"] = dt_util.now().isoformat()
        await self._store.async_save(self.maintenance_history)

    def _collect_last_activities(self) -> list[dict]:
        """Build a compact activity list from stored maintenance actions."""
        return collect_last_activities(
            self.maintenance_history,
            self._parse_ts_aware,
            self.pool_covered,
            self.usage_mode,
        )

    async def _build_learning_context(self, *, temperature: float | None = None, now: object | None = None) -> dict:
        """Collect the current context for chlorine learning snapshots."""
        weather_data = await async_get_weather_data(self.hass, self.config, limit=2)
        weather_today = weather_data.get("today") if isinstance(weather_data, dict) else None
        _, pump_active = self._pump_tracking_state()
        pump_runtime_hours_total = self._current_pump_runtime_hours(now)
        return {
            "temperature": temperature,
            "pool_covered": self.pool_covered,
            "usage_mode": self.usage_mode,
            "uv_index": weather_today.get("uv_index") if isinstance(weather_today, dict) else None,
            "weather_condition": weather_today.get("condition") if isinstance(weather_today, dict) else None,
            "precipitation_probability": weather_today.get("precipitation_probability") if isinstance(weather_today, dict) else None,
            "precipitation_amount": weather_today.get("precipitation_amount") if isinstance(weather_today, dict) else None,
            "pump_runtime_hours_total": pump_runtime_hours_total,
            "pump_active": pump_active,
        }

    async def _handle_state_change(self, event):
        """Handle state changes of source entities."""
        new_state = event.data.get("new_state")

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

    async def async_log_maintenance(self, m_type: str, amount: float, percent: float | None = None):
        """Log maintenance action and send notifications."""
        now = dt_util.now()
        _LOGGER.debug(
            "Maintenance action requested: type=%s amount=%s at=%s",
            m_type,
            amount,
            now.isoformat(),
        )
        details = None
        if m_type == "water_exchange":
            pool_volume_liters = max(float(self.config.get(CONF_POOL_VOLUME, 0.0)) * 1000.0, 0.0)
            details = normalize_water_exchange(amount, percent, pool_volume_liters)
            if details is None:
                raise HomeAssistantError("Wasserwechsel braucht Liter oder Prozent groesser 0.")
            amount = details["liters"]

        self.pool_covered, self.usage_mode, msg = update_maintenance_history(
            self.maintenance_history,
            m_type,
            amount,
            now,
            self.pool_covered,
            self.usage_mode,
            details,
        )
        if m_type == "chlor":
            temp_value = self.data.get("temp_ist") if isinstance(self.data, dict) else None
            learning_context = await self._build_learning_context(temperature=temp_value, now=now)
            record_chlor_dose(
                self.maintenance_history,
                now.isoformat(),
                amount,
                **learning_context,
            )
        elif m_type in ("ph_plus", "ph_minus"):
            record_ph_correction(self.maintenance_history, now.isoformat(), m_type, amount)
        elif m_type == "water_exchange":
            record_water_exchange(
                self.maintenance_history,
                now.isoformat(),
                details["liters"] if details else amount,
                details["percent"] if details else percent,
                max(float(self.config.get(CONF_POOL_VOLUME, 0.0)) * 1000.0, 0.0),
            )

        await self._store.async_save(self.maintenance_history)

        conf = self.config
        # Send Notification (Persistent & Service)
        if msg:
            await async_send_notification(self.hass, conf, msg, "maintenance")
        if m_type == "chlor":
            await self._async_notify_chlor_sample_window(now)

        # Follow-up Timer (only for chemicals)
        if m_type in ("chlor", "ph_plus", "ph_minus"):
            delay = conf.get(CONF_FOLLOW_UP_TIME, 0)
            if delay > 0:
                async_call_later(self.hass, delay * 60, self._send_follow_up)

    async def async_repair_learning_history(self, *, fetch_poollab: bool = False) -> None:
        """Re-run learning backfill and log why dose samples are accepted or rejected."""
        _LOGGER.info(
            "Learning history repair requested: entry_id=%s fetch_poollab=%s",
            self.entry.entry_id,
            fetch_poollab,
        )

        if fetch_poollab:
            await self.async_fetch_poollab_measurements()

        last_api_measurements = self.maintenance_history.get("last_api_measurements")
        self._backfill_cloud_learning_history(last_api_measurements if isinstance(last_api_measurements, list) else [])

        diagnosis = diagnose_chlorine_dose_samples(
            self.maintenance_history,
            self.config,
            self._parse_ts_aware,
            dt_util.now(),
        )
        _LOGGER.info(
            "Learning history repair summary: entry_id=%s measurements=%s doses=%s accepted=%s rejected=%s",
            self.entry.entry_id,
            diagnosis.get("measurement_count"),
            diagnosis.get("dose_count"),
            diagnosis.get("accepted_count"),
            diagnosis.get("rejected_count"),
        )

        for item in diagnosis.get("accepted", [])[-5:]:
            _LOGGER.info(
                "Dose sample accepted: dose_at=%s amount=%sg previous_at=%s following_at=%s baseline_gap_h=%s effect_h=%s factor=%s",
                item.get("dose_at"),
                item.get("dose_amount"),
                item.get("previous_at"),
                item.get("following_at"),
                item.get("baseline_gap_hours"),
                item.get("effect_hours"),
                item.get("dose_factor"),
            )

        for item in diagnosis.get("rejected", [])[-10:]:
            _LOGGER.info(
                "Dose sample rejected: reason=%s dose_at=%s amount=%sg previous_at=%s following_at=%s baseline_gap_h=%s effect_h=%s factor=%s",
                item.get("reason"),
                item.get("dose_at"),
                item.get("dose_amount"),
                item.get("previous_at"),
                item.get("following_at"),
                item.get("baseline_gap_hours"),
                item.get("effect_hours"),
                item.get("dose_factor"),
            )

        await self._async_notify_latest_chlor_sample_status(diagnosis)
        await self._store.async_save(self.maintenance_history)
        await self.async_request_refresh()

    def _format_local_time(self, dt_value: datetime | None) -> str:
        """Format a timestamp in local wall-clock time."""
        if dt_value is None:
            return "--:--"
        return dt_util.as_local(dt_value).strftime("%H:%M")

    async def _async_notify_chlor_sample_window(self, dose_dt: datetime) -> None:
        """Notify the user about the valid chlorine follow-up window."""
        start_dt = dose_dt + timedelta(hours=MIN_DOSE_EFFECT_HOURS)
        end_dt = dose_dt + timedelta(hours=MAX_DOSE_EFFECT_HOURS)
        await async_send_notification(
            self.hass,
            self.config,
            (
                "Bitte fuer die Dosierqualitaet erneut messen. "
                f"Gueltiges Zeitfenster: zwischen {self._format_local_time(start_dt)} Uhr "
                f"und {self._format_local_time(end_dt)} Uhr."
            ),
            "chlor_sample_window",
        )

    async def _async_notify_latest_chlor_sample_status(self, diagnosis: dict) -> None:
        """Send a status notification for the latest chlorine dose sample."""
        doses = self.maintenance_history.get("chlor_learning_doses", [])
        if not isinstance(doses, list) or not doses:
            return

        latest_dose_raw = None
        for item in reversed(doses):
            if isinstance(item, dict) and isinstance(item.get("raw_ts"), str):
                latest_dose_raw = item.get("raw_ts")
                break
        if not latest_dose_raw:
            return

        latest_entry = None
        for item in diagnosis.get("accepted", []):
            if item.get("dose_at") == latest_dose_raw:
                latest_entry = item
                break
        if latest_entry is None:
            for item in diagnosis.get("rejected", []):
                if item.get("dose_at") == latest_dose_raw:
                    latest_entry = item
                    break
        if latest_entry is None:
            return

        state_token = "|".join(
            str(latest_entry.get(key) or "")
            for key in ("reason", "dose_at", "following_at", "first_following_at")
        )
        if self.maintenance_history.get("last_chlor_sample_status_token") == state_token:
            return

        reason = latest_entry.get("reason")
        message = None
        details = (
            f"Vorher: {latest_entry.get('previous_chlor')} mg/l, "
            f"Nachher: {latest_entry.get('following_chlor')} mg/l, "
            f"Zugabe: {latest_entry.get('dose_amount')} g, "
            f"Theoretisch: {latest_entry.get('theoretical_increase')} mg/l, "
            f"Beobachtet: {latest_entry.get('observed_increase')} mg/l."
        )
        if reason == "accepted":
            message = (
                "Dosier-Sample erfolgreich erkannt. "
                f"Nachmessung um {self._format_local_time(self._parse_ts_aware(latest_entry.get('following_at')))} Uhr "
                f"wurde verwendet. Faktor: {latest_entry.get('dose_factor')}. {details}"
            )
        elif reason == "follow_up_too_early":
            dose_dt = self._parse_ts_aware(latest_entry.get("dose_at"))
            start_dt = dose_dt + timedelta(hours=MIN_DOSE_EFFECT_HOURS) if dose_dt else None
            end_dt = dose_dt + timedelta(hours=MAX_DOSE_EFFECT_HOURS) if dose_dt else None
            message = (
                "Nachmessung war zu frueh und zaehlt noch nicht als Dosier-Sample. "
                f"Bitte zwischen {self._format_local_time(start_dt)} Uhr und {self._format_local_time(end_dt)} Uhr erneut messen."
            )
        elif reason == "follow_up_too_late":
            message = "Nachmessung war zu spaet und konnte nicht mehr als Dosier-Sample gewertet werden."
        elif reason == "dose_factor_out_of_range":
            message = (
                "Dosier-Sample konnte nicht gewertet werden. "
                f"Der berechnete Faktor ({latest_entry.get('dose_factor')}) liegt ausserhalb des erlaubten Bereichs. "
                f"{details}"
            )
        elif reason == "next_dose_before_follow_up":
            message = "Dosier-Sample konnte nicht gewertet werden, weil vor der gueltigen Nachmessung bereits eine weitere Zugabe erfasst wurde."
        elif reason == "missing_following_measurement":
            message = "Fuer die letzte Chlorzugabe fehlt noch eine passende Nachmessung im gueltigen Zeitfenster."

        if message:
            await async_send_notification(self.hass, self.config, message, "chlor_sample_status")
            self.maintenance_history["last_chlor_sample_status_token"] = state_token

    async def _send_follow_up(self, _):
        await self._async_check_follow_up_notification()

    def _get_time_since_last_action(self, action_key: str, in_hours: bool = False) -> int | None:
        """Calculate time since last action (hours or days)."""
        return get_time_since_last_action(self.maintenance_history, action_key, in_hours)

    def _get_action_dt(self, action_key: str):
        """Return the aware timestamp of a stored maintenance action."""
        return get_action_dt(self.maintenance_history, action_key, self._parse_ts_aware)

    def _get_latest_chemical_action(self):
        """Return raw timestamp and datetime for the latest chemical action."""
        candidates = []
        for action_key in ("chlor", "ph_plus", "ph_minus"):
            action = self.maintenance_history.get(action_key)
            if not isinstance(action, dict):
                continue
            raw_ts = action.get("raw_ts")
            action_dt = self._parse_ts_aware(raw_ts)
            if raw_ts and action_dt:
                candidates.append((action_dt, raw_ts))

        if not candidates:
            return None

        action_dt, raw_ts = max(candidates, key=lambda item: item[0])
        return raw_ts, action_dt

    async def _async_check_follow_up_notification(self) -> None:
        """Send a missed chemical follow-up reminder based on persisted history."""
        try:
            delay_minutes = float(self.config.get(CONF_FOLLOW_UP_TIME, 0) or 0)
        except (TypeError, ValueError):
            delay_minutes = 0

        if delay_minutes <= 0:
            return

        latest_action = self._get_latest_chemical_action()
        if latest_action is None:
            return

        action_raw, action_dt = latest_action
        last_measurement_dt = self._parse_ts_aware(self.maintenance_history.get("last_measurement_raw"))
        if last_measurement_dt and last_measurement_dt > action_dt:
            return

        if self.maintenance_history.get("last_follow_up_action_raw") == action_raw:
            return

        if dt_util.now() < action_dt + timedelta(minutes=delay_minutes):
            return

        await async_send_follow_up(self.hass, self.config)
        self.maintenance_history["last_follow_up_action_raw"] = action_raw
        self.maintenance_history["last_follow_up_sent_raw"] = dt_util.now().isoformat()
        await self._store.async_save(self.maintenance_history)

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

        def add_value_candidate(
            bucket: list[tuple[datetime | None, object, str, str | None]],
            value: object,
            source: str,
            ts_raw: str | None,
        ) -> None:
            """Track candidate values so the newest source wins per metric."""
            if value is None:
                return
            bucket.append((self._parse_ts_aware(ts_raw), value, source, ts_raw))

        def select_latest_candidate(
            bucket: list[tuple[datetime | None, object, str, str | None]],
        ) -> tuple[object | None, str | None, str | None]:
            """Return the newest candidate value, source and raw timestamp."""
            if not bucket:
                return None, None, None
            dt_value, value, source, ts_raw = max(
                bucket,
                key=lambda item: item[0] or dt_util.parse_datetime("1970-01-01T00:00:00+00:00"),
            )
            return value, source, ts_raw

        # 1. Bestehende Daten laden
        # Immer einen aktuellen Zeitstempel für den "letzten Lauf" parat haben
        now_iso = dt_util.now().isoformat()
        last_calc_raw = self.maintenance_history.get("last_calc_raw", now_iso)

        conf = self.config
        api_key = conf.get(CONF_API_KEY)
        ble_address = conf.get(CONF_BLE_ADDRESS)
        perform_remote_fetch = self._poollab_fetch_requested

        data_source = "Nicht verfügbar"
        cloud_found = False
        manual_found = False
        ble_found = False
        cached_ble_found = False
        ble_connected = False
        poollab_fetch_result = self.maintenance_history.get("last_poollab_fetch_result")
        poollab_fetch_error = self.maintenance_history.get("last_poollab_fetch_error")
        poollab_fetch_completed_at = self.maintenance_history.get("last_poollab_fetch_completed_at")
        self.maintenance_history.pop("bluetooth_connected", None)

        c_ist = ph_ist = temp_ist = cya_ist = None
        chlor_source = ph_source = temp_source = cya_source = None
        c_meas_raw = ph_meas_raw = temp_meas_raw = cya_meas_raw = None
        c_candidates: list[tuple[datetime | None, object, str, str | None]] = []
        ph_candidates: list[tuple[datetime | None, object, str, str | None]] = []
        temp_candidates: list[tuple[datetime | None, object, str, str | None]] = []
        cya_candidates: list[tuple[datetime | None, object, str, str | None]] = []
        # Lade letzte bekannte API-Messwerte aus dem Speicher
        last_api_measurements = self.maintenance_history.get("last_api_measurements", [])

        # Zeitstempel der Berechnung sofort aktualisieren, damit das UI "tickt"
        now_iso = dt_util.now().isoformat()
        self.maintenance_history["last_calc_raw"] = now_iso
        last_calc_raw = now_iso

        # 1. Versuch: Bluetooth-Daten nur auf expliziten Abruf verbinden.
        if perform_remote_fetch and ble_address:
            try:
                _LOGGER.debug("Fetching data from PoolLab via Bluetooth: %s", ble_address)
                device = async_ble_device_from_address(self.hass, ble_address, connectable=True)
                if device:
                    _LOGGER.debug(
                        "PoolLab BLE device resolved: name=%s address=%s rssi=%s details=%s",
                        getattr(device, "name", None),
                        getattr(device, "address", None),
                        getattr(device, "rssi", None),
                        getattr(device, "details", None),
                    )
                    client = PoolLabBLEClient(device)
                    try:
                        # Timeout leicht reduziert und CancelledError explizit fangen,
                        # um Setup-Abstürze unter Python 3.11+ zu verhindern.
                        ble_data = await asyncio.wait_for(client.async_read_data(), timeout=40.0)

                        ble_found = True
                        ble_connected = True
                        poollab_fetch_result = "success"
                        poollab_fetch_error = None
                        poollab_fetch_completed_at = dt_util.now().isoformat()
                        self._set_poollab_cooldown(_BLE_SUCCESS_COOLDOWN)
                        self._backfill_ble_learning_history(ble_data, poollab_fetch_completed_at)
                        ble_selection = select_poollab_ble_measurements(
                            ble_data,
                            poollab_fetch_completed_at,
                            self._normalize_ble_measurement_ts,
                        )
                        self.maintenance_history["ble_battery"] = ble_selection.battery
                        _LOGGER.debug(
                            "PoolLab BLE values selected: battery=%s chlor=%s ph=%s temp=%s cya=%s measurement_raw=%s",
                            ble_selection.battery,
                            ble_selection.chlor,
                            ble_selection.ph,
                            ble_selection.temperature,
                            ble_selection.cyanuric_acid,
                            ble_selection.measurement_raw,
                        )

                        if ble_selection.chlor is not None:
                            self.maintenance_history["last_ble_c"] = ble_selection.chlor
                            self.maintenance_history["last_ble_chlor_raw"] = ble_selection.chlor_measurement_raw
                        if ble_selection.ph is not None:
                            self.maintenance_history["last_ble_ph"] = ble_selection.ph
                            self.maintenance_history["last_ble_ph_raw"] = ble_selection.ph_measurement_raw
                        if ble_selection.temperature is not None:
                            self.maintenance_history["last_ble_temp"] = ble_selection.temperature
                            self.maintenance_history["last_ble_temp_raw"] = ble_selection.temperature_measurement_raw
                        if ble_selection.cyanuric_acid is not None:
                            self.maintenance_history["cyanuric_acid"] = ble_selection.cyanuric_acid
                            self.maintenance_history["last_ble_cya"] = ble_selection.cyanuric_acid
                            self.maintenance_history["last_ble_cya_raw"] = ble_selection.cyanuric_acid_measurement_raw

                        add_value_candidate(
                            c_candidates, ble_selection.chlor, "Bluetooth", ble_selection.chlor_measurement_raw
                        )
                        add_value_candidate(
                            ph_candidates, ble_selection.ph, "Bluetooth", ble_selection.ph_measurement_raw
                        )
                        add_value_candidate(
                            temp_candidates, ble_selection.temperature, "Bluetooth", ble_selection.temperature_measurement_raw
                        )
                        add_value_candidate(
                            cya_candidates, ble_selection.cyanuric_acid, "Bluetooth", ble_selection.cyanuric_acid_measurement_raw
                        )
                        c_ist, chlor_source, c_meas_raw = select_latest_candidate(c_candidates)
                        ph_ist, ph_source, ph_meas_raw = select_latest_candidate(ph_candidates)
                        temp_ist, temp_source, temp_meas_raw = select_latest_candidate(temp_candidates)
                        cya_ist, cya_source, cya_meas_raw = select_latest_candidate(cya_candidates)
                        _LOGGER.debug(
                            "BLE source assignment: chlor=%s ph=%s temp=%s cya=%s",
                            chlor_source,
                            ph_source,
                            temp_source,
                            cya_source,
                        )
                        if ble_selection.measurement_raw:
                            self.maintenance_history["last_ble_measurement_raw"] = ble_selection.measurement_raw

                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        poollab_fetch_result = "error"
                        poollab_fetch_error = "Bluetooth-Abfrage fuer PoolLab wurde abgebrochen oder hat das Timeout erreicht."
                        poollab_fetch_completed_at = dt_util.now().isoformat()
                        self._set_poollab_cooldown(_BLE_ERROR_COOLDOWN)
                        _LOGGER.warning("Bluetooth-Abfrage fuer PoolLab zeitlich ueberschritten oder abgebrochen. Nutze Cache oder manuelle Daten.")
                else:
                    poollab_fetch_result = "error"
                    poollab_fetch_error = f"PoolLab Bluetooth-Geraet nicht gefunden: {ble_address}"
                    poollab_fetch_completed_at = dt_util.now().isoformat()
                    self._set_poollab_cooldown(_BLE_ERROR_COOLDOWN)
                    _LOGGER.warning("PoolLab Bluetooth device not found: %s", ble_address)
            except Exception as err:
                poollab_fetch_result = "error"
                poollab_fetch_error = f"{type(err).__name__}: {err}"
                poollab_fetch_completed_at = dt_util.now().isoformat()
                self._set_poollab_cooldown(_BLE_ERROR_COOLDOWN)
                _LOGGER.warning(
                    "PoolLab BLE read failed, using fallback data if available: address=%s error_type=%s error=%s",
                    ble_address,
                    type(err).__name__,
                    err,
                )

        # 2. Versuch: Cloud-Daten zyklisch abrufen. Ein manueller Abruf soll BLE priorisieren
        # und nur dann die Cloud verwenden, wenn kein BLE-Geraet konfiguriert ist.
        should_fetch_cloud = bool(api_key) and (c_ist is None or ph_ist is None or cya_ist is None) and (
            not perform_remote_fetch or not ble_address
        )
        if should_fetch_cloud:
            try:
                _LOGGER.debug("Fetching data from PoolLab Cloud")
                session = async_get_clientsession(self.hass)
                cloud_result = await async_fetch_poollab_cloud_measurements(session, api_key)

                if cloud_result.measurement_raw:
                    self.maintenance_history["last_api_measurement_raw"] = cloud_result.measurement_raw
                if cloud_result.chlor_measurement_raw:
                    self.maintenance_history["last_api_chlor_raw"] = cloud_result.chlor_measurement_raw
                if cloud_result.ph_measurement_raw:
                    self.maintenance_history["last_api_ph_raw"] = cloud_result.ph_measurement_raw
                if cloud_result.temperature_measurement_raw:
                    self.maintenance_history["last_api_temp_raw"] = cloud_result.temperature_measurement_raw
                if cloud_result.cyanuric_acid_measurement_raw:
                    self.maintenance_history["last_api_cya_raw"] = cloud_result.cyanuric_acid_measurement_raw
                if cloud_result.last_measurements:
                    last_api_measurements = cloud_result.last_measurements
                    self.maintenance_history["last_api_measurements"] = last_api_measurements
                    self._backfill_cloud_learning_history(last_api_measurements)

                add_value_candidate(
                    c_candidates, cloud_result.chlor, "Cloud", cloud_result.chlor_measurement_raw
                )
                add_value_candidate(
                    ph_candidates, cloud_result.ph, "Cloud", cloud_result.ph_measurement_raw
                )
                add_value_candidate(
                    temp_candidates, cloud_result.temperature, "Cloud", cloud_result.temperature_measurement_raw
                )
                add_value_candidate(
                    cya_candidates, cloud_result.cyanuric_acid, "Cloud", cloud_result.cyanuric_acid_measurement_raw
                )
                c_ist, chlor_source, c_meas_raw = select_latest_candidate(c_candidates)
                ph_ist, ph_source, ph_meas_raw = select_latest_candidate(ph_candidates)
                temp_ist, temp_source, temp_meas_raw = select_latest_candidate(temp_candidates)
                cya_ist, cya_source, cya_meas_raw = select_latest_candidate(cya_candidates)

                if cloud_result.found:
                    cloud_found = True
                    if perform_remote_fetch:
                        poollab_fetch_result = "success"
                        poollab_fetch_error = None
                        poollab_fetch_completed_at = dt_util.now().isoformat()
            except Exception as err:
                if perform_remote_fetch:
                    poollab_fetch_result = "error"
                    poollab_fetch_error = f"Cloud API Fehler: {err}"
                    poollab_fetch_completed_at = dt_util.now().isoformat()
                _LOGGER.error("Error fetching PoolLab data: %s", err)

        next_poollab_fetch_allowed_at = self._get_next_poollab_fetch_allowed_at()
        self.maintenance_history["last_poollab_fetch_result"] = poollab_fetch_result
        if poollab_fetch_error:
            self.maintenance_history["last_poollab_fetch_error"] = poollab_fetch_error
        else:
            self.maintenance_history.pop("last_poollab_fetch_error", None)
        if poollab_fetch_completed_at:
            self.maintenance_history["last_poollab_fetch_completed_at"] = poollab_fetch_completed_at

        api_ts_str = self.maintenance_history.get("last_api_measurement_raw")
        ble_ts_str = self.maintenance_history.get("last_ble_measurement_raw")
        dt_api_for_values = self._parse_ts_aware(api_ts_str)
        dt_ble_for_values = self._parse_ts_aware(ble_ts_str)
        if not ble_found and dt_ble_for_values is not None:
            cached_ble_c = self.maintenance_history.get("last_ble_c")
            cached_ble_ph = self.maintenance_history.get("last_ble_ph")
            cached_ble_temp = self.maintenance_history.get("last_ble_temp")
            cached_ble_cya = self.maintenance_history.get("last_ble_cya")
            cached_ble_c_raw = self.maintenance_history.get("last_ble_chlor_raw") or ble_ts_str
            cached_ble_ph_raw = self.maintenance_history.get("last_ble_ph_raw") or ble_ts_str
            cached_ble_temp_raw = self.maintenance_history.get("last_ble_temp_raw") or ble_ts_str
            cached_ble_cya_raw = self.maintenance_history.get("last_ble_cya_raw") or ble_ts_str

            add_value_candidate(c_candidates, cached_ble_c, "Bluetooth", cached_ble_c_raw)
            add_value_candidate(ph_candidates, cached_ble_ph, "Bluetooth", cached_ble_ph_raw)
            add_value_candidate(temp_candidates, cached_ble_temp, "Bluetooth", cached_ble_temp_raw)
            add_value_candidate(cya_candidates, cached_ble_cya, "Bluetooth", cached_ble_cya_raw)

            if (
                cached_ble_c is not None
                or cached_ble_ph is not None
                or cached_ble_temp is not None
                or cached_ble_cya is not None
            ):
                cached_ble_found = True
                c_ist, chlor_source, c_meas_raw = select_latest_candidate(c_candidates)
                ph_ist, ph_source, ph_meas_raw = select_latest_candidate(ph_candidates)
                temp_ist, temp_source, temp_meas_raw = select_latest_candidate(temp_candidates)
                cya_ist, cya_source, cya_meas_raw = select_latest_candidate(cya_candidates)
                _LOGGER.debug(
                    "Considering cached BLE values in source selection: ble=%s api=%s selected=(%s,%s,%s,%s)",
                    ble_ts_str,
                    api_ts_str,
                    chlor_source,
                    ph_source,
                    temp_source,
                    cya_source,
                )

        # 2. Versuch: Manuelle Sensoren prüfen (immer prüfen für Quellen-Erkennung)
        c_man, c_man_ts = get_state_info(conf.get(CONF_CHLOR_SENSOR))
        ph_man, ph_man_ts = get_state_info(conf.get(CONF_PH_SENSOR))
        temp_man, temp_man_ts = get_state_info(conf.get(CONF_TEMP_SENSOR))

        if c_man is not None or ph_man is not None:
            manual_found = True

        add_value_candidate(c_candidates, c_man, "Manuell", c_man_ts)
        add_value_candidate(ph_candidates, ph_man, "Manuell", ph_man_ts)
        add_value_candidate(temp_candidates, temp_man, "Manuell", temp_man_ts)

        c_ist, chlor_source, c_meas_raw = select_latest_candidate(c_candidates)
        ph_ist, ph_source, ph_meas_raw = select_latest_candidate(ph_candidates)
        temp_ist, temp_source, temp_meas_raw = select_latest_candidate(temp_candidates)
        cya_ist, cya_source, cya_meas_raw = select_latest_candidate(cya_candidates)

        for ts_candidate in (c_man_ts, ph_man_ts, temp_man_ts):
            if not ts_candidate:
                continue
            ts_iso = ts_candidate if isinstance(ts_candidate, str) else ts_candidate.isoformat()
            old_man_str = self.maintenance_history.get("last_manual_measurement_raw")
            dt_new_man = self._parse_ts_aware(ts_iso)
            dt_old_man = self._parse_ts_aware(old_man_str)
            if not dt_old_man or (dt_new_man and dt_new_man > dt_old_man):
                self.maintenance_history["last_manual_measurement_raw"] = ts_iso

        # 4. Fallback auf Historie, falls aktuelle Quellen keine Daten liefern (Persistenz)
        if c_ist is None:
            c_ist = self.maintenance_history.get("last_c")
            if c_ist is not None:
                chlor_source = "Speicher"
                c_meas_raw = self.maintenance_history.get("last_chlor_measurement_raw")
        else:
            self.maintenance_history["last_c"] = c_ist
            self.maintenance_history["last_chlor_measurement_raw"] = c_meas_raw

        if ph_ist is None:
            ph_ist = self.maintenance_history.get("last_ph")
            if ph_ist is not None:
                ph_source = "Speicher"
                ph_meas_raw = self.maintenance_history.get("last_ph_measurement_raw")
        else:
            self.maintenance_history["last_ph"] = ph_ist
            self.maintenance_history["last_ph_measurement_raw"] = ph_meas_raw

        if temp_ist is None:
            temp_ist = self.maintenance_history.get("last_temp")
            if temp_ist is not None:
                temp_source = "Speicher"
                temp_meas_raw = self.maintenance_history.get("last_temp_measurement_raw")
        else:
            self.maintenance_history["last_temp"] = temp_ist
            self.maintenance_history["last_temp_measurement_raw"] = temp_meas_raw

        if cya_ist is None:
            cya_ist = self.maintenance_history.get("cyanuric_acid")
            if cya_ist is not None:
                cya_source = self.maintenance_history.get("cyanuric_acid_source") or "Speicher"
                cya_meas_raw = self.maintenance_history.get("last_cya_measurement_raw")
        else:
            self.maintenance_history["cyanuric_acid"] = cya_ist
            self.maintenance_history["cyanuric_acid_source"] = cya_source
            self.maintenance_history["last_cya_measurement_raw"] = cya_meas_raw

        last_activities = self._collect_last_activities()
        if last_activities:
            self.maintenance_history["last_activities"] = last_activities

        # Bestimmung der Datenquelle
        sources = []
        if ble_found or cached_ble_found: sources.append("Bluetooth")
        if cloud_found: sources.append("Cloud")
        if manual_found: sources.append("Manuell")
        data_source = " & ".join(sources) if sources else ("Speicher" if c_ist is not None else "Nicht verfügbar")

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen

        # Synchronisiere den kombinierten Zeitstempel für die Anzeige
        _LOGGER.debug(
            "PoolLab source collection summary: remote_fetch=%s ble_found=%s cloud_found=%s manual_found=%s "
            "cached_ble_found=%s result=%s error=%s data_source=%s c=%s ph=%s temp=%s cya=%s sources=(%s,%s,%s,%s)",
            perform_remote_fetch,
            ble_found,
            cloud_found,
            manual_found,
            cached_ble_found,
            poollab_fetch_result,
            poollab_fetch_error,
            data_source,
            c_ist,
            ph_ist,
            temp_ist,
            cya_ist,
            chlor_source,
            ph_source,
            temp_source,
            cya_source,
        )

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
        dt_last_meas = self._parse_ts_aware(last_meas_raw)
        chlor_measurement = self._format_measurement_ts(c_meas_raw)
        ph_measurement = self._format_measurement_ts(ph_meas_raw)
        temp_measurement = self._format_measurement_ts(temp_meas_raw)
        cya_measurement = self._format_measurement_ts(cya_meas_raw)
        ble_measurement = self._format_measurement_ts(ble_ts_str)
        recent_measurement_entries: list[dict] = []
        for api_item in last_api_measurements if isinstance(last_api_measurements, list) else []:
            if not isinstance(api_item, dict):
                continue
            entry = self._build_recent_measurement_entry(
                parameter=api_item.get("parameter"),
                value=api_item.get("value"),
                timestamp_raw=api_item.get("timestamp"),
                source="API",
            )
            if entry:
                recent_measurement_entries.append(entry)

        for parameter, value, timestamp_raw, source in (
            ("chlor", self.maintenance_history.get("last_ble_c"), self.maintenance_history.get("last_ble_chlor_raw") or ble_ts_str, "BLE"),
            ("ph", self.maintenance_history.get("last_ble_ph"), self.maintenance_history.get("last_ble_ph_raw") or ble_ts_str, "BLE"),
            ("temperature", self.maintenance_history.get("last_ble_temp"), self.maintenance_history.get("last_ble_temp_raw") or ble_ts_str, "BLE"),
            ("cyanuric_acid", self.maintenance_history.get("last_ble_cya"), self.maintenance_history.get("last_ble_cya_raw") or ble_ts_str, "BLE"),
            ("chlor", c_man, c_man_ts.isoformat() if isinstance(c_man_ts, datetime) else c_man_ts, "Manuell"),
            ("ph", ph_man, ph_man_ts.isoformat() if isinstance(ph_man_ts, datetime) else ph_man_ts, "Manuell"),
            ("temperature", temp_man, temp_man_ts.isoformat() if isinstance(temp_man_ts, datetime) else temp_man_ts, "Manuell"),
        ):
            entry = self._build_recent_measurement_entry(
                parameter=parameter,
                value=value,
                timestamp_raw=timestamp_raw,
                source=source,
            )
            if entry:
                recent_measurement_entries.append(entry)

        recent_measurements_display = self._merge_recent_measurements(recent_measurement_entries)[:5]
        dt_last_chlor_action = self._get_action_dt("chlor")
        dt_last_ph_plus_action = self._get_action_dt("ph_plus")
        dt_last_ph_minus_action = self._get_action_dt("ph_minus")
        pump_runtime_hours_total = self._current_pump_runtime_hours()
        _, pump_active = self._pump_tracking_state()
        weather_data = await async_get_weather_data(self.hass, conf, limit=2)
        weather_today = weather_data.get("today") if isinstance(weather_data, dict) else None
        weather_forecast_days = weather_data.get("forecast_days") if isinstance(weather_data, dict) else []
        if c_ist is not None and c_meas_raw:
            record_chlor_measurement(
                self.maintenance_history,
                c_meas_raw,
                c_ist,
                temperature=temp_ist,
                pool_covered=self.pool_covered,
                usage_mode=self.usage_mode,
                uv_index=weather_today.get("uv_index") if isinstance(weather_today, dict) else None,
                weather_condition=weather_today.get("condition") if isinstance(weather_today, dict) else None,
                precipitation_probability=weather_today.get("precipitation_probability") if isinstance(weather_today, dict) else None,
                precipitation_amount=weather_today.get("precipitation_amount") if isinstance(weather_today, dict) else None,
                pump_runtime_hours_total=pump_runtime_hours_total,
                pump_active=pump_active,
            )
        if ph_ist is not None and ph_meas_raw:
            record_ph_measurement(self.maintenance_history, ph_meas_raw, ph_ist)
        if cya_ist is not None and cya_meas_raw:
            record_cya_measurement(self.maintenance_history, cya_meas_raw, cya_ist)
        chlorine_learning = calculate_chlorine_learning(
            self.maintenance_history,
            conf,
            self._parse_ts_aware,
            dt_util.now(),
            current_chlorine=c_ist,
            current_temperature=temp_ist,
            pool_covered=self.pool_covered,
            usage_mode=self.usage_mode,
            weather_today=weather_today,
            pump_active=pump_active,
        )
        sample_diagnosis = diagnose_chlorine_dose_samples(
            self.maintenance_history,
            conf,
            self._parse_ts_aware,
            dt_util.now(),
        )
        await self._async_notify_latest_chlor_sample_status(sample_diagnosis)
        learned_dose_factor = None
        dose_factor_attrs = chlorine_learning.get("chlor_dose_factor_attributes")
        if (
            isinstance(dose_factor_attrs, dict)
            and int(dose_factor_attrs.get("samples") or 0) >= MIN_DOSE_FACTOR_SAMPLES
        ):
            learned_dose_factor = chlorine_learning.get("personal_chlor_dose_factor")
        ph_learning = calculate_ph_learning(
            self.maintenance_history,
            conf,
            self._parse_ts_aware,
            dt_util.now(),
        )
        cya_learning = calculate_cya_learning(
            self.maintenance_history,
            conf,
            self._parse_ts_aware,
            dt_util.now(),
            current_cya=cya_ist,
        )
        ph_learning_attr = ph_learning.get("ph_stability_attributes") or {}
        _LOGGER.debug(
            "pH learning summary: stability=%s trend=%s samples=%s avg_14d=%s drift_24h=%s drift_7d=%s "
            "min=%s max=%s quality=%s stars=%s",
            ph_learning.get("ph_stability"),
            ph_learning.get("ph_trend"),
            ph_learning_attr.get("samples"),
            ph_learning_attr.get("average_daily_drift"),
            ph_learning.get("ph_drift_24h"),
            ph_learning.get("ph_drift_7d"),
            ph_learning_attr.get("min_daily_drift"),
            ph_learning_attr.get("max_daily_drift"),
            ph_learning_attr.get("prediction_quality"),
            ph_learning_attr.get("prediction_quality_stars"),
        )

        # Wenn wichtige Sensoren fehlen, keine Berechnung durchführen
        await self._async_check_follow_up_notification()

        if c_ist is None and ph_ist is None:
            await self._store.async_save(self.maintenance_history)
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
                "chlor_measurement": chlor_measurement,
                "chlor_measurement_raw": c_meas_raw,
                "ph_measurement": ph_measurement,
                "ph_measurement_raw": ph_meas_raw,
                "temp_measurement": temp_measurement,
                "temp_measurement_raw": temp_meas_raw,
                "cyanuric_acid_measurement": cya_measurement,
                "cyanuric_acid_measurement_raw": cya_meas_raw,
                "ble_measurement": ble_measurement,
                "ble_measurement_raw": ble_ts_str,
                "last_api_measurements": last_api_measurements,
                "last_measurements_display": recent_measurements_display,
                "last_activities": last_activities,
                "last_chlor_action": self.maintenance_history.get("chlor"),
                "last_ph_plus_action": self.maintenance_history.get("ph_plus"),
                "last_ph_minus_action": self.maintenance_history.get("ph_minus"),
                "last_water_exchange_action": self.maintenance_history.get("water_exchange"),
                "pool_covered": self.pool_covered,
                "ble_battery": self.maintenance_history.get("ble_battery"),
                "bluetooth_connected": ble_connected,
                "cyanuric_acid": cya_ist,
                "cyanuric_acid_source": cya_source,
                "chlor_product_type": conf.get(CONF_CHLOR_PRODUCT_TYPE, "organic"),
                "chlor_shock_max": max(float(conf.get(CONF_CHLOR_SHOCK_MAX, 5.0) or 5.0), 0.0),
                "usage_mode": self.usage_mode,
                "chlor_breakdown_base": 0.0,
                "chlor_breakdown_shock_adj": 0.0,
                "chlor_breakdown_temp_adj": 0.0,
                "chlor_breakdown_env_adj": 0.0,
                "chlor_breakdown_bather_adj": 0.0,
                "chlor_breakdown_sum_raw": 0.0,
                "chlor_breakdown_min_dose_applied": 0.0,
                "poollab_fetch_result": poollab_fetch_result,
                "poollab_fetch_error": poollab_fetch_error,
                "last_poollab_fetch_requested_at": self.maintenance_history.get("last_poollab_fetch_requested_at"),
                "last_poollab_fetch_completed_at": poollab_fetch_completed_at,
                "next_poollab_fetch_allowed_at": next_poollab_fetch_allowed_at,
                "awaiting_retest": False,
                "awaiting_retest_chlor": False,
                "awaiting_retest_ph": False,
                "awaiting_retest_since": None,
                "weather_entity": conf.get(CONF_WEATHER_ENTITY),
                "weather_uv_sensor": conf.get(CONF_UV_SENSOR),
                "weather_available": weather_data.get("available") if isinstance(weather_data, dict) else False,
                "weather_uv_today": weather_today.get("uv_index") if isinstance(weather_today, dict) else None,
                "weather_rain_probability_today": weather_today.get("precipitation_probability") if isinstance(weather_today, dict) else None,
                "weather_rain_amount_today": weather_today.get("precipitation_amount") if isinstance(weather_today, dict) else None,
                "weather_condition_today": weather_today.get("condition") if isinstance(weather_today, dict) else None,
                "weather_temperature_today": weather_today.get("temperature") if isinstance(weather_today, dict) else None,
                "weather_wind_speed_today": weather_today.get("wind_speed") if isinstance(weather_today, dict) else None,
                "weather_wind_speed_unit": weather_today.get("wind_speed_unit") if isinstance(weather_today, dict) else None,
                "weather_forecast_days": weather_forecast_days,
                "weather_note": None,
                "chlor_breakdown_uv_adj": 0.0,
                **chlorine_learning,
                **ph_learning,
                **cya_learning,
                "recommendation": "⚠️ Keine Messwerte vorhanden"
            }

        chemistry = calculate_pool_chemistry(
            conf,
            c_ist,
            ph_ist,
            temp_ist,
            self.pool_covered,
            self.usage_mode,
            weather_today,
            learned_dose_factor,
        )
        s_g = chemistry["chlor_dose"]
        chlor_pre = chemistry["chlor_pre"]
        ph_senker_ml = chemistry["ph_senker_total"]
        ph_erhoeher_g = chemistry["ph_erhoeher_total"]
        c_ziel = chemistry["chlor_target"]
        c_min = chemistry["chlor_min"]
        c_max = chemistry["chlor_max"]
        ph_ziel = chemistry["ph_target"]
        ph_min = chemistry["ph_min"]
        ph_max = chemistry["ph_max"]
        ph_diff = chemistry["ph_diff"]
        weather_note = chemistry["weather_note"]
        chlor_breakdown_base = chemistry["chlor_breakdown_base"]
        chlor_breakdown_shock_adj = chemistry["chlor_breakdown_shock_adj"]
        chlor_breakdown_temp_adj = chemistry["chlor_breakdown_temp_adj"]
        chlor_breakdown_env_adj = chemistry["chlor_breakdown_env_adj"]
        chlor_breakdown_uv_adj = chemistry["chlor_breakdown_uv_adj"]
        chlor_breakdown_bather_adj = chemistry["chlor_breakdown_bather_adj"]
        chlor_breakdown_sum_raw = chemistry["chlor_breakdown_sum_raw"]
        chlor_breakdown_min_dose_applied = chemistry["chlor_breakdown_min_dose_applied"]
        volume_m3 = chemistry["volume_m3"]
        volume_liters = chemistry["volume_liters"]
        effective_chlor_content = chemistry["effective_chlor_content"]

        retest_status = calculate_retest_status(
            s_g,
            ph_senker_ml,
            ph_erhoeher_g,
            dt_last_meas,
            dt_last_chlor_action,
            dt_last_ph_plus_action,
            dt_last_ph_minus_action,
        )
        awaiting_retest = retest_status["awaiting_retest"]
        awaiting_retest_chlor = retest_status["awaiting_retest_chlor"]
        awaiting_retest_ph = retest_status["awaiting_retest_ph"]
        awaiting_retest_since = retest_status["awaiting_retest_since"]

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

        await async_check_filter_notifications(self.hass, conf, self.maintenance_history)
        await self._async_check_follow_up_notification()

        recommendation = build_recommendation(
            awaiting_retest,
            ph_ist,
            c_ist,
            cya_ist,
            conf.get(CONF_CHLOR_PRODUCT_TYPE),
            chemistry["chlor_shock_max"],
            ph_min,
            ph_max,
            c_min,
            c_max,
            s_g,
            chlor_pre,
        )

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
            "chlor_pre": chlor_pre,
            "ph_senker_total": ph_senker_ml,
            "ph_erhoeher_total": ph_erhoeher_g,
            "data_source": data_source,
            "ph_diff": ph_diff,
            "is_shock": (c_ist is not None and 3.0 <= float(c_ist) <= 5.0),
            "is_error": False,
            "last_calculation": dt_util.as_local(self._parse_ts_aware(new_calc_ts)).strftime("%d.%m.%Y %H:%M Uhr"),
            "last_calculation_raw": new_calc_ts,
            "last_measurement": dt_util.as_local(self._parse_ts_aware(last_meas_raw)).strftime("%d.%m.%Y %H:%M Uhr") if last_meas_raw else "Noch keine Messung",
            "last_measurement_raw": last_meas_raw,
            "last_measurement_source": last_meas_source,
            "chlor_measurement": chlor_measurement,
            "chlor_measurement_raw": c_meas_raw,
            "ph_measurement": ph_measurement,
            "ph_measurement_raw": ph_meas_raw,
            "temp_measurement": temp_measurement,
            "temp_measurement_raw": temp_meas_raw,
            "cyanuric_acid_measurement": cya_measurement,
            "cyanuric_acid_measurement_raw": cya_meas_raw,
            "ble_measurement": ble_measurement,
            "ble_measurement_raw": ble_ts_str,
            "last_measurements_display": recent_measurements_display,
            "chlor_target": c_ziel,
            "chlor_min": c_min,
            "chlor_max": c_max,
            "chlor_shock_max": chemistry["chlor_shock_max"],
            "ph_target": ph_ziel,
            "ph_min": ph_min,
            "ph_max": ph_max,
            "ble_battery": self.maintenance_history.get("ble_battery"),
            "bluetooth_connected": ble_connected,
            "last_activities": last_activities,
            "last_chlor_action": self.maintenance_history.get("chlor"),
            "last_ph_plus_action": self.maintenance_history.get("ph_plus"),
            "last_ph_minus_action": self.maintenance_history.get("ph_minus"),
            "last_water_exchange_action": self.maintenance_history.get("water_exchange"),
            "recommendation": recommendation,
            "cyanuric_acid": cya_ist,
            "cyanuric_acid_source": cya_source,
            "chlor_product_type": conf.get(CONF_CHLOR_PRODUCT_TYPE, "organic"),
            "chlor_breakdown_base": chlor_breakdown_base,
            "last_api_measurements": last_api_measurements,
            "chlor_breakdown_shock_adj": chlor_breakdown_shock_adj,
            "chlor_breakdown_temp_adj": chlor_breakdown_temp_adj,
            "chlor_breakdown_env_adj": chlor_breakdown_env_adj,
            "chlor_breakdown_uv_adj": chlor_breakdown_uv_adj,
            "chlor_breakdown_bather_adj": chlor_breakdown_bather_adj,
            "chlor_breakdown_sum_raw": chlor_breakdown_sum_raw,
            "chlor_breakdown_min_dose_applied": chlor_breakdown_min_dose_applied,
            "volume_m3": volume_m3,
            "volume_liters": volume_liters,
            "effective_chlor_content": effective_chlor_content,
            "poollab_fetch_result": poollab_fetch_result,
            "poollab_fetch_error": poollab_fetch_error,
            "last_poollab_fetch_requested_at": self.maintenance_history.get("last_poollab_fetch_requested_at"),
            "last_poollab_fetch_completed_at": poollab_fetch_completed_at,
            "next_poollab_fetch_allowed_at": next_poollab_fetch_allowed_at,
            "awaiting_retest": awaiting_retest,
            "awaiting_retest_chlor": awaiting_retest_chlor,
            "awaiting_retest_ph": awaiting_retest_ph,
            "awaiting_retest_since": awaiting_retest_since,
            "weather_entity": conf.get(CONF_WEATHER_ENTITY),
            "weather_uv_sensor": conf.get(CONF_UV_SENSOR),
            "weather_available": weather_data.get("available") if isinstance(weather_data, dict) else False,
            "weather_uv_today": weather_today.get("uv_index") if isinstance(weather_today, dict) else None,
            "weather_rain_probability_today": weather_today.get("precipitation_probability") if isinstance(weather_today, dict) else None,
            "weather_rain_amount_today": weather_today.get("precipitation_amount") if isinstance(weather_today, dict) else None,
            "weather_condition_today": weather_today.get("condition") if isinstance(weather_today, dict) else None,
            "weather_temperature_today": weather_today.get("temperature") if isinstance(weather_today, dict) else None,
            "weather_wind_speed_today": weather_today.get("wind_speed") if isinstance(weather_today, dict) else None,
            "weather_wind_speed_unit": weather_today.get("wind_speed_unit") if isinstance(weather_today, dict) else None,
            "weather_forecast_days": weather_forecast_days,
            "weather_note": weather_note,
            "hours_since_filter_clean": hours_since_filter_clean,
            "pool_covered": self.pool_covered,
            "usage_mode": self.usage_mode,
            "filter_clean_status": filter_clean_status,
            "filter_clean_interval": filter_clean_interval,
            "days_since_filter_replace": days_since_filter_replace,
            "filter_replace_status": filter_replace_status,
            "filter_replace_interval": filter_replace_interval,
            **chlorine_learning,
            **ph_learning,
            **cya_learning,
        }
