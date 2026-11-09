"""One persistent switch for all configured availability notifications."""

from homeassistant.components.switch import SwitchEntity

from .entity import OfflineDevicesEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([NotificationsSwitch(entry.runtime_data)])


class NotificationsSwitch(OfflineDevicesEntity, SwitchEntity):
    _attr_translation_key = "notifications"
    _attr_icon = "mdi:cellphone-message"

    def __init__(self, coordinator):
        super().__init__(coordinator, "notifications")
        self.entity_id = "switch.offline_devices_notifications"

    @property
    def is_on(self):
        return self.coordinator.notifications_enabled

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_notifications(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_notifications(False)
