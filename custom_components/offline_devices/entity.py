"""Common integration device."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class OfflineDevicesEntity(CoordinatorEntity):
    """Represent the monitor as a service, which is excluded from its own scan."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Online / Offline Devices",
            entry_type=DeviceEntryType.SERVICE,
        )
