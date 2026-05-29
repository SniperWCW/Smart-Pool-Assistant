import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN


class SmartPoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Smart Pool Assistant",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("chlor_sensor"):
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),

                vol.Required("ph_sensor"):
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),

                vol.Optional("temp_sensor"):
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),

                vol.Optional("usage_boolean"):
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="input_boolean")
                    ),

                vol.Required("pool_volume", default=0.96):
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.1,
                            max=100,
                            step=0.01,
                            mode="box"
                        )
                    ),

                vol.Required("chlor_target", default=1.5):
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.1,
                            max=5,
                            step=0.1,
                            mode="box"
                        )
                    ),

                vol.Required("ph_target", default=7.2):
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=6.8,
                            max=7.6,
                            step=0.1,
                            mode="slider"
                        )
                    ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
