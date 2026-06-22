"""Sensor platform for Smart Pool Assistant."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartPoolCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: SmartPoolCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        PoolAssistantSensor(coordinator, "Chlor Nachdosierung", "chlor_dose", "g", "mdi:pill"),
        PoolAssistantSensor(coordinator, "Chlor Vor Baden", "chlor_pre", "g", "mdi:pill"),
        PoolAssistantSensor(coordinator, "PH-Minus", "ph_senker_total", "ml", "mdi:arrow-down-bold"),
        PoolAssistantSensor(coordinator, "PH-Plus", "ph_erhoeher_total", "g", "mdi:arrow-up-bold"),
        PoolAssistantSensor(coordinator, "Chlor Istwert", "chlor_ist", "mg/l", "mdi:water-percent"),
        PoolAssistantSensor(coordinator, "pH Istwert", "ph_ist", "pH", "mdi:ph"),
        PoolAssistantSensor(coordinator, "Temperatur Istwert", "temp_ist", "°C", "mdi:thermometer"),
        PoolAssistantSensor(coordinator, "Datenquelle", "data_source", None, "mdi:database-import"),
        PoolAssistantSensor(coordinator, "Abdeckung Status", "pool_covered", None, "mdi:pool"),
        PoolAssistantSensor(coordinator, "Nutzungsmodus", "usage_mode", None, "mdi:account-group"),
        PoolAssistantSensor(coordinator, "Chlorverbrauch 24h", "chlor_consumption_24h", "mg/l/d", "mdi:chart-line"),
        PoolAssistantSensor(coordinator, "Chlorverbrauch 7d", "chlor_consumption_7d", "mg/l/d", "mdi:chart-line"),
        PoolAssistantSensor(coordinator, "Chlorverbrauch 14d", "chlor_consumption_14d", "mg/l/d", "mdi:chart-line"),
        PoolAssistantSensor(coordinator, "Persoenlicher Chlorfaktor", "personal_chlor_factor", None, "mdi:brain"),
        PoolAssistantSensor(coordinator, "Persoenlicher Chlor Dosierfaktor", "personal_chlor_dose_factor", None, "mdi:scale-balance"),
        PoolAssistantSensor(coordinator, "Chlor Vorhersagequalitaet", "chlor_prediction_quality", None, "mdi:star-check"),
        PoolAssistantSensor(coordinator, "Chlor Dosierqualitaet", "chlor_dose_prediction_quality", None, "mdi:star-check"),
        PoolAssistantSensor(coordinator, "Chlor Prognose Tagesverlust", "chlor_forecast_daily_loss", "mg/l/d", "mdi:chart-timeline-variant"),
        PoolAssistantSensor(coordinator, "Chlor Bis Minimum", "chlor_hours_to_min", "h", "mdi:timer-sand"),
        PoolAssistantSensor(coordinator, "Chlor Bis 0 6", "chlor_hours_to_critical_low", "h", "mdi:timer-alert-outline"),
        PoolAssistantSensor(coordinator, "Chlor Prognose", "chlor_forecast_message", None, "mdi:timeline-clock-outline"),
        PoolAssistantChlorStabilitySensor(coordinator),
        PoolAssistantSensor(coordinator, "pH Drift 24h", "ph_drift_24h", "pH/d", "mdi:chart-line"),
        PoolAssistantSensor(coordinator, "pH Drift 7d", "ph_drift_7d", "pH/d", "mdi:chart-line"),
        PoolAssistantSensor(coordinator, "pH Drift 14d", "ph_drift_14d", "pH/d", "mdi:chart-line"),
        PoolAssistantSensor(coordinator, "pH Vorhersagequalitaet", "ph_prediction_quality", None, "mdi:star-check"),
        PoolAssistantSensor(coordinator, "pH Trend", "ph_trend", None, "mdi:trending-up"),
        PoolAssistantPhStabilitySensor(coordinator),
        PoolAssistantSensor(coordinator, "Filter Reinigung Fällig", "hours_since_filter_clean", "h", "mdi:filter-outline"),
        PoolAssistantSensor(coordinator, "Filter Wechsel Fällig", "days_since_filter_replace", "Tage", "mdi:filter-cog-outline"),
        PoolAssistantSensor(coordinator, "Cyanursäure", "cyanuric_acid", "ppm", "mdi:shield-check"),
        PoolAssistantBatterySensor(coordinator),
        PoolAssistantStatusSensor(coordinator),
    ]
    async_add_entities(sensors)

class PoolAssistantSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pool Assistant sensor."""

    def __init__(self, coordinator: SmartPoolCoordinator, name: str, key: str, unit: str, icon: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Pool {name}"
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        # Nur bei numerischen Messwerten eine State Class setzen
        if unit is not None:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)

class PoolAssistantBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of the PoolLab battery level via BLE."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: SmartPoolCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "PoolLab Batterie"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ble_battery"

    @property
    def native_value(self):
        return self.coordinator.data.get("history", {}).get("ble_battery")


class PoolAssistantChlorStabilitySensor(CoordinatorEntity, SensorEntity):
    """Representation of learned chlorine stability."""

    def __init__(self, coordinator: SmartPoolCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Pool Chlor Stabilitaet"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_chlor_stability"
        self._attr_icon = "mdi:chart-bell-curve"

    @property
    def native_value(self):
        return self.coordinator.data.get("chlor_stability")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("chlor_stability_attributes")


class PoolAssistantPhStabilitySensor(CoordinatorEntity, SensorEntity):
    """Representation of learned pH stability."""

    def __init__(self, coordinator: SmartPoolCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Pool pH Stabilitaet"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ph_stability"
        self._attr_icon = "mdi:chart-bell-curve"

    @property
    def native_value(self):
        return self.coordinator.data.get("ph_stability")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("ph_stability_attributes")

class PoolAssistantStatusSensor(CoordinatorEntity, SensorEntity):
    """Status sensor for recommendation text."""

    def __init__(self, coordinator: SmartPoolCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Pool Empfehlung"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_recommendation"
        self._attr_icon = "mdi:alert-circle-outline"

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        data = self.coordinator.data
        return {
            "last_calculation": data.get("last_calculation"),
            "last_measurement": data.get("last_measurement"),
            "last_measurement_source": data.get("last_measurement_source"),
            "chlor_ist": data.get("chlor_ist"),
            "ph_ist": data.get("ph_ist"),
            "temp_ist": data.get("temp_ist"),
            "chlor_source": data.get("chlor_source"),
            "ph_source": data.get("ph_source"),
            "temp_source": data.get("temp_source"),
            "chlor_target": data.get("chlor_target"),
            "chlor_min": data.get("chlor_min"),
            "chlor_max": data.get("chlor_max"),
            "ph_target": data.get("ph_target"),
            "ph_min": data.get("ph_min"),
            "ph_max": data.get("ph_max"),
            "chlor_dose": data.get("chlor_dose"),
            "chlor_pre": data.get("chlor_pre"),
            "hours_since_filter_clean": data.get("hours_since_filter_clean"),
            "filter_clean_status": data.get("filter_clean_status"),
            "filter_clean_interval": data.get("filter_clean_interval"),
            "days_since_filter_replace": data.get("days_since_filter_replace"),
            "filter_replace_status": data.get("filter_replace_status"),
            "filter_replace_interval": data.get("filter_replace_interval"),
            "ph_senker_total": data.get("ph_senker_total"),
            "ph_erhoeher_total": data.get("ph_erhoeher_total"),
            "history": data.get("history"),
            "last_activities": data.get("last_activities") or data.get("history", {}).get("last_activities"),
            "is_shock": data.get("is_shock"),
            "pool_covered": data.get("pool_covered"),
            "usage_mode": data.get("usage_mode"),
            "chlor_consumption_24h": data.get("chlor_consumption_24h"),
            "chlor_consumption_7d": data.get("chlor_consumption_7d"),
            "chlor_consumption_14d": data.get("chlor_consumption_14d"),
            "personal_chlor_factor": data.get("personal_chlor_factor"),
            "personal_chlor_dose_factor": data.get("personal_chlor_dose_factor"),
            "chlor_prediction_quality": data.get("chlor_prediction_quality"),
            "chlor_dose_prediction_quality": data.get("chlor_dose_prediction_quality"),
            "chlor_stability": data.get("chlor_stability"),
            "chlor_stability_attributes": data.get("chlor_stability_attributes"),
            "chlor_dose_factor_attributes": data.get("chlor_dose_factor_attributes"),
            "effective_chlor_content": data.get("effective_chlor_content"),
            "chlor_forecast_daily_loss": data.get("chlor_forecast_daily_loss"),
            "chlor_forecast_hourly_loss": data.get("chlor_forecast_hourly_loss"),
            "chlor_hours_to_min": data.get("chlor_hours_to_min"),
            "chlor_hours_to_critical_low": data.get("chlor_hours_to_critical_low"),
            "chlor_forecast_threshold_min": data.get("chlor_forecast_threshold_min"),
            "chlor_forecast_threshold_critical_low": data.get("chlor_forecast_threshold_critical_low"),
            "chlor_forecast_confidence": data.get("chlor_forecast_confidence"),
            "chlor_forecast_basis": data.get("chlor_forecast_basis"),
            "chlor_forecast_message": data.get("chlor_forecast_message"),
            "chlor_forecast_attributes": data.get("chlor_forecast_attributes"),
            "ph_drift_24h": data.get("ph_drift_24h"),
            "ph_drift_7d": data.get("ph_drift_7d"),
            "ph_drift_14d": data.get("ph_drift_14d"),
            "ph_prediction_quality": data.get("ph_prediction_quality"),
            "ph_stability": data.get("ph_stability"),
            "ph_trend": data.get("ph_trend"),
            "ph_stability_attributes": data.get("ph_stability_attributes"),
            "chlor_breakdown_base": data.get("chlor_breakdown_base"),
            "chlor_breakdown_shock_adj": data.get("chlor_breakdown_shock_adj"),
            "chlor_breakdown_temp_adj": data.get("chlor_breakdown_temp_adj"),
            "chlor_breakdown_env_adj": data.get("chlor_breakdown_env_adj"),
            "chlor_breakdown_uv_adj": data.get("chlor_breakdown_uv_adj"),
            "chlor_breakdown_bather_adj": data.get("chlor_breakdown_bather_adj"),
            "chlor_breakdown_sum_raw": data.get("chlor_breakdown_sum_raw"),
            "chlor_breakdown_min_dose_applied": data.get("chlor_breakdown_min_dose_applied"),
            "data_source": data.get("data_source"),
            "bluetooth_connected": data.get("bluetooth_connected"),
            "last_api_measurements": data.get("last_api_measurements"),
            "poollab_fetch_result": data.get("poollab_fetch_result"),
            "poollab_fetch_error": data.get("poollab_fetch_error"),
            "last_poollab_fetch_requested_at": data.get("last_poollab_fetch_requested_at"),
            "last_poollab_fetch_completed_at": data.get("last_poollab_fetch_completed_at"),
            "next_poollab_fetch_allowed_at": data.get("next_poollab_fetch_allowed_at"),
            "awaiting_retest": data.get("awaiting_retest"),
            "awaiting_retest_chlor": data.get("awaiting_retest_chlor"),
            "awaiting_retest_ph": data.get("awaiting_retest_ph"),
            "awaiting_retest_since": data.get("awaiting_retest_since"),
            "weather_entity": data.get("weather_entity"),
            "weather_uv_sensor": data.get("weather_uv_sensor"),
            "weather_available": data.get("weather_available"),
            "weather_uv_today": data.get("weather_uv_today"),
            "weather_rain_probability_today": data.get("weather_rain_probability_today"),
            "weather_rain_amount_today": data.get("weather_rain_amount_today"),
            "weather_condition_today": data.get("weather_condition_today"),
            "weather_temperature_today": data.get("weather_temperature_today"),
            "weather_wind_speed_today": data.get("weather_wind_speed_today"),
            "weather_wind_speed_unit": data.get("weather_wind_speed_unit"),
            "weather_forecast_days": data.get("weather_forecast_days"),
            "weather_note": data.get("weather_note"),
        }

    @property
    def native_value(self):
        """Return the recommendation text."""
        return self.coordinator.data.get("recommendation")
