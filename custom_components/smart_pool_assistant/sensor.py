"""Sensor platform for Smart Pool Assistant."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
        PoolAssistantSensor(coordinator, "Filter Reinigung Fällig", "days_since_filter_clean", "Tage", "mdi:filter-outline"),
        PoolAssistantSensor(coordinator, "Filter Wechsel Fällig", "days_since_filter_replace", "Tage", "mdi:filter-cog-outline"),
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
            "chlor_ist": data.get("chlor_ist"),
            "ph_ist": data.get("ph_ist"),
            "temp_ist": data.get("temp_ist"),
            "chlor_target": data.get("chlor_target"),
            "ph_target": data.get("ph_target"),
            "chlor_dose": data.get("chlor_dose"),
            "chlor_pre": data.get("chlor_pre"),
            "days_since_filter_clean": data.get("days_since_filter_clean"),
            "filter_clean_status": data.get("filter_clean_status"),
            "filter_clean_interval": data.get("filter_clean_interval"),
            "days_since_filter_replace": data.get("days_since_filter_replace"),
            "filter_replace_status": data.get("filter_replace_status"),
            "filter_replace_interval": data.get("filter_replace_interval"),
            "ph_senker_total": data.get("ph_senker_total"),
            "ph_erhoeher_total": data.get("ph_erhoeher_total"),
            "history": data.get("history"),
            "is_shock": data.get("is_shock"),
            "pool_covered": data.get("pool_covered"),
            "usage_mode": data.get("usage_mode"),
            "data_source": data.get("data_source"),
        }

    @property
    def native_value(self):
        """Return the recommendation text."""
        if self.coordinator.data.get("is_shock"):
            return "Stoßchlorung empfohlen"
        return "Werte im Zielbereich"
