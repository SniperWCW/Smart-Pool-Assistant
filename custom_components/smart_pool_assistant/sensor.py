from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SmartPoolCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = SmartPoolCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    entities = [
        PoolChlorSensor(coordinator),
        PoolPHSensor(coordinator),
        PoolRecommendationSensor(coordinator),
    ]

    async_add_entities(entities)


class PoolChlorSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Pool Chlor"
    _attr_unique_id = "pool_chlor"
    _attr_native_unit_of_measurement = "mg/l"

    @property
    def native_value(self):
        return self.coordinator.data["chlor"]


class PoolPHSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Pool pH"
    _attr_unique_id = "pool_ph"

    @property
    def native_value(self):
        return self.coordinator.data["ph"]


class PoolRecommendationSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Pool Empfehlung"
    _attr_unique_id = "pool_recommendation"

    @property
    def native_value(self):
        chlor = self.coordinator.data["chlor"]
        grams = self.coordinator.data["chlor_grams"]

        if chlor < 0.5:
            return f"Stoßchlorung empfohlen: {grams}g"

        return f"Chlor nachdosieren: {grams}g"
