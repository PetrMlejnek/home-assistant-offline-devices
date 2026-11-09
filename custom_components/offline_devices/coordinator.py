"""Adapt Home Assistant registries to the pure availability engine."""

from collections import defaultdict
from datetime import timedelta
import logging

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_GRACE, CONF_IGNORE_LABEL, DEFAULT_GRACE, DOMAIN, EVENT_CHANGED,
    OPERATIONAL_DOMAINS, STARTUP_GRACE,
)
from .engine import Device, Monitor, Reading, notification_payload

_LOGGER = logging.getLogger(__name__)


class AvailabilityCoordinator(DataUpdateCoordinator):
    """Read local state once a minute. No probing, credentials or cloud calls."""

    def __init__(self, hass, entry):
        super().__init__(
            hass, _LOGGER, name=DOMAIN, config_entry=entry,
            update_interval=timedelta(minutes=1),
        )
        settings = {**entry.data, **entry.options}
        self.ignore_label = settings.get(CONF_IGNORE_LABEL) or entry.data[CONF_IGNORE_LABEL]
        self.monitor = Monitor(
            startup_until=dt_util.utcnow().timestamp() + STARTUP_GRACE,
            grace=settings.get(CONF_GRACE, DEFAULT_GRACE),
        )
        self.notifications_enabled = False
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")

    async def async_restore(self):
        """Restore incidents and the switch without storing household data externally."""
        saved = await self._store.async_load()
        if not isinstance(saved, dict):
            return
        self.notifications_enabled = saved.get("notifications_enabled") is True
        rows = saved.get("devices", [])
        if isinstance(rows, list):
            self.monitor.rows = [
                row for row in rows if isinstance(row, dict)
                and isinstance(row.get("id"), str)
                and isinstance(row.get("incident"), bool)
                and isinstance(row.get("status"), str)
            ]

    def _saved_data(self):
        return {
            "devices": self.monitor.rows,
            "notifications_enabled": self.notifications_enabled,
        }

    async def async_save(self):
        await self._store.async_save(self._saved_data())

    async def async_set_notifications(self, enabled):
        self.notifications_enabled = enabled
        await self.async_save()
        self.async_update_listeners()

    def _snapshot(self, now):
        devices = dr.async_get(self.hass)
        entities = er.async_get(self.hass)
        areas = ar.async_get(self.hass)
        by_device = defaultdict(list)
        for entity in entities.entities.values():
            if (
                entity.device_id and entity.disabled_by is None
                and entity.hidden_by is None
                and entity.domain in OPERATIONAL_DOMAINS
                and self.ignore_label not in entity.labels
            ):
                state = self.hass.states.get(entity.entity_id)
                device_class = (
                    state.attributes.get("device_class") if state else
                    entity.device_class or entity.original_device_class
                )
                by_device[entity.device_id].append(Reading(
                    state=state.state if state else "unknown",
                    changed=state.last_changed.timestamp() if state else now,
                    connectivity=bool(
                        entity.domain == "binary_sensor" and device_class == "connectivity"
                    ),
                ))
        result = []
        for device in devices.devices.values():
            excluded = self.ignore_label in device.labels
            readings = tuple(by_device[device.id])
            bridge = device.manufacturer == "Zigbee2MQTT" and device.model == "Bridge"
            if not excluded and (
                device.disabled_by is not None
                or (device.entry_type == dr.DeviceEntryType.SERVICE and not bridge)
                or not readings
            ):
                continue
            integrations = sorted({
                entry.domain for entry_id in device.config_entries
                if (entry := self.hass.config_entries.async_get_entry(entry_id)) is not None
            })
            area = areas.async_get_area(device.area_id) if device.area_id else None
            result.append(Device(
                id=device.id, name=device.name_by_user or device.name or device.id,
                area=area.name if area else "", integrations=tuple(integrations),
                readings=readings, parent=device.via_device_id, excluded=excluded,
                bridge=bridge and "mqtt" in integrations,
            ))
        return result

    async def _async_update_data(self):
        now = dt_util.utcnow().timestamp()
        old_rows = self.monitor.rows
        data = self.monitor.update(self._snapshot(now), now)
        data["label_missing"] = lr.async_get(self.hass).async_get_label(self.ignore_label) is None
        if old_rows != self.monitor.rows:
            self._store.async_delay_save(self._saved_data, 10)
        payload = notification_payload(data)
        if self.notifications_enabled and not data["label_missing"] and payload:
            self.hass.bus.async_fire(EVENT_CHANGED, payload)
        return data
