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
        PoolAssistantSensor(coordinator, "pH Senker", "ph_senker_total", "ml", "mdi:arrow-down-bold"),
        PoolAssistantSensor(coordinator, "pH Erhöher", "ph_erhoeher_total", "g", "mdi:arrow-up-bold"),
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
        return {
            "last_calculation": self.coordinator.data.get("last_calculation"),
            "last_measurement": self.coordinator.data.get("last_measurement"),
        }

    @property
    def native_value(self):
        """Return the recommendation text."""
        if self.coordinator.data.get("is_shock"):
            return "Stoßchlorung empfohlen"
        return "Werte im Zielbereich"