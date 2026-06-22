"""Button platform for explicit PoolLab fetches."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_API_KEY, CONF_BLE_ADDRESS, DOMAIN
from .coordinator import SmartPoolCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: SmartPoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.config.get(CONF_BLE_ADDRESS) or coordinator.config.get(CONF_API_KEY):
        async_add_entities([PoolLabFetchButton(coordinator)])


class PoolLabFetchButton(CoordinatorEntity, ButtonEntity):
    """Trigger a one-shot PoolLab fetch."""

    def __init__(self, coordinator: SmartPoolCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "PoolLab Messwerte abrufen"
        self._attr_icon = "mdi:bluetooth-connect"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_poollab_fetch"
        self._attr_suggested_object_id = "poollab_messwerte_abrufen"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Expose the last manual fetch state on the button itself."""
        data = self.coordinator.data or {}
        attrs = {}

        if requested_at := data.get("last_poollab_fetch_requested_at"):
            attrs["last_fetch_requested_at"] = requested_at
        if completed_at := data.get("last_poollab_fetch_completed_at"):
            attrs["last_fetch_completed_at"] = completed_at
        if result := data.get("poollab_fetch_result"):
            attrs["last_fetch_result"] = result
        if error := data.get("poollab_fetch_error"):
            attrs["last_fetch_error"] = error
        if next_allowed := data.get("next_poollab_fetch_allowed_at"):
            attrs["next_fetch_allowed_at"] = next_allowed

        return attrs

    async def async_press(self) -> None:
        """Fetch PoolLab data exactly once."""
        _LOGGER.debug(
            "PoolLab fetch button pressed: entry_id=%s",
            self.coordinator.entry.entry_id,
        )
        await self.coordinator.async_fetch_poollab_measurements()
