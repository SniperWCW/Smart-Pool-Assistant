from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN


class SmartPoolCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            logger=None,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

        self.entry = entry

    async def _async_update_data(self):
        chlor_entity = self.entry.data["chlor_sensor"]
        ph_entity = self.entry.data["ph_sensor"]

        chlor = float(self.hass.states.get(chlor_entity).state)
        ph = float(self.hass.states.get(ph_entity).state)

        chlor_target = self.entry.data["chlor_target"]
        ph_target = self.entry.data["ph_target"]
        volume = self.entry.data["pool_volume"]

        chlor_diff = max(chlor_target - chlor, 0)

        chlor_grams = round((chlor_diff * volume / 0.56), 1)

        ph_diff = ph_target - ph

        return {
            "chlor": chlor,
            "ph": ph,
            "chlor_target": chlor_target,
            "ph_target": ph_target,
            "chlor_grams": chlor_grams,
            "ph_diff": ph_diff,
        }
