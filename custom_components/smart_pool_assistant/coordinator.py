from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN, CONF_CHLOR_SENSOR, CONF_PH_SENSOR, CONF_TEMP_SENSOR,
    CONF_POOL_VOLUME, CONF_CHLOR_TARGET, CONF_PH_TARGET,
    CONF_CHLOR_CONTENT, CONF_PH_DOWN_FACTOR, CONF_PH_UP_FACTOR
)


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
        def get_state_float(entity_id):
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                return 0.0
            try:
                return float(state.state)
            except ValueError:
                return 0.0

        # Sensordaten abrufen
        c_ist = get_state_float(self.entry.data[CONF_CHLOR_SENSOR])
        ph_ist = get_state_float(self.entry.data[CONF_PH_SENSOR])
        temp_ist = get_state_float(self.entry.data[CONF_TEMP_SENSOR])

        # Konfiguration laden
        volumen = self.entry.data[CONF_POOL_VOLUME]
        c_ziel = self.entry.data[CONF_CHLOR_TARGET]
        ph_ziel = self.entry.data[CONF_PH_TARGET]
        wirkstoff = self.entry.data[CONF_CHLOR_CONTENT]
        
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
            ph_senker_ml = round((ph_diff_abs * 10 * volumen) * (self.entry.data[CONF_PH_DOWN_FACTOR] / 100), 1)
        elif ph_diff > 0: # pH zu niedrig -> erhöhen
            ph_erhoeher_g = round((ph_diff_abs * 10 * volumen) * (self.entry.data[CONF_PH_UP_FACTOR] / 100), 1)

        return {
            "chlor_ist": c_ist,
            "ph_ist": ph_ist,
            "temp_ist": temp_ist,
            "chlor_dose": s_g,
            "chlor_pre": round(max(s_g * 0.3, 1.0), 1),
            "ph_senker_total": ph_senker_ml,
            "ph_erhoeher_total": ph_erhoeher_g,
            "ph_diff": ph_diff,
            "is_shock": c_ist < 0.5
        }
