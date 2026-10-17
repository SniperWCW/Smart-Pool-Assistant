"""Shared entity base for Smart Pool Assistant."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartPoolCoordinator


class SmartPoolEntity(CoordinatorEntity[SmartPoolCoordinator]):
    """Base class that groups all entities of one config entry under one device."""

    def __init__(self, coordinator: SmartPoolCoordinator) -> None:
        """Initialize the entity and attach it to the Smart Pool Assistant device."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Smart Pool Assistant",
            manufacturer="SniperWCW",
            model="Smart Pool Assistant",
            entry_type=DeviceEntryType.SERVICE,
        )
