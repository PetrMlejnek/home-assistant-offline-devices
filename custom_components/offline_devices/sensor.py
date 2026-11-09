"""A count and a dynamic inventory for native dashboard cards."""

from homeassistant.components.sensor import SensorEntity

from .entity import OfflineDevicesEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([OfflineDevicesSensor(entry.runtime_data)])


class OfflineDevicesSensor(OfflineDevicesEntity, SensorEntity):
    _attr_translation_key = "offline_count"
    _attr_icon = "mdi:lan-disconnect"

    def __init__(self, coordinator):
        super().__init__(coordinator, "offline_count")
        # Stable initial ID for the supplied dashboard; a registry rename still wins.
        self.entity_id = "sensor.offline_devices"

    @property
    def native_value(self):
        return self.coordinator.data["offline"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            key: data[key] for key in
            ("devices", "monitored", "excluded", "warming_up", "label_missing")
        } | {"ignore_label": self.coordinator.ignore_label, "schema_version": 1}
