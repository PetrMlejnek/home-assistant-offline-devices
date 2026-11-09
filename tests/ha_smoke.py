"""Exercise a disposable real Home Assistant instance; never a user's server.

Run separately on Linux with Home Assistant 2026.11.1 / Python 3.14 installed.
This does not replace hardware or notification delivery testing.
"""

import asyncio
from pathlib import Path
import shutil
import tempfile

from homeassistant.bootstrap import async_from_config_dict
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.template import Template
from homeassistant.util.yaml import load_yaml


async def smoke(config_dir):
    hass = HomeAssistant(str(config_dir))
    await async_from_config_dict({
        "homeassistant": {"name": "Synthetic test home", "latitude": 0,
                          "longitude": 0, "elevation": 0, "unit_system": "metric",
                          "time_zone": "UTC"},
        "logger": {"default": "warning"},
    }, hass)
    try:
        result = await hass.config_entries.flow.async_init("offline_devices", context={"source": "user"})
        assert result["type"] == "form", result
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == "create_entry", result
        await hass.async_block_till_done()
        entry = result["result"]
        assert hass.states.get("sensor.offline_devices") is not None
        assert hass.states.get("switch.offline_devices_notifications").state == "off"
        dashboard = load_yaml(str(Path(__file__).resolve().parents[1] / "dashboards/device-availability.yaml"))
        for view in dashboard["views"]:
            for card in view["cards"]:
                if card["type"] == "markdown":
                    assert str(Template(card["content"], hass).async_render()).strip()
        coordinator = entry.runtime_data
        coordinator.monitor.startup_until = 0
        coordinator.monitor.grace = 0  # Timing boundaries have separate unit tests.

        devices, entities = dr.async_get(hass), er.async_get(hass)
        device = devices.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("offline_devices", "synthetic-test-socket")},
            name="Synthetic test socket",
        )
        entity = entities.async_get_or_create(
            "switch", "offline_devices", "synthetic-test-socket",
            config_entry=entry, device_id=device.id,
            suggested_object_id="synthetic_test_socket",
        )
        hass.states.async_set(entity.entity_id, "off")
        await coordinator.async_refresh()
        assert coordinator.data["monitored"] == 1
        assert coordinator.data["offline"] == 0

        events = []
        unsubscribe = hass.bus.async_listen("offline_devices_changed", lambda event: events.append(event.data))
        await hass.services.async_call("switch", "turn_on", {
            "entity_id": "switch.offline_devices_notifications"}, blocking=True)
        hass.states.async_set(entity.entity_id, "unavailable")
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(events) == 1, events
        assert events[0]["offline"][0]["name"] == "Synthetic test socket"
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(events) == 1, events

        devices.async_update_device(device.id, name_by_user="Renamed synthetic socket")
        await coordinator.async_refresh()
        assert coordinator.data["devices"][0]["name"] == "Renamed synthetic socket"
        devices.async_update_device(device.id, labels={coordinator.ignore_label})
        await coordinator.async_refresh()
        assert coordinator.data["excluded"] == 1
        devices.async_update_device(device.id, labels=set())
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(events) == 1, events

        await hass.services.async_call("switch", "turn_off", {
            "entity_id": "switch.offline_devices_notifications"}, blocking=True)
        hass.states.async_set(entity.entity_id, "on")
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(events) == 1, events
        await hass.services.async_call("switch", "turn_on", {
            "entity_id": "switch.offline_devices_notifications"}, blocking=True)
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get("switch.offline_devices_notifications").state == "on"

        duplicate = await hass.config_entries.flow.async_init("offline_devices", context={"source": "user"})
        assert duplicate["type"] == "abort", duplicate
        options = await hass.config_entries.options.async_init(entry.entry_id)
        assert options["type"] == "form", options
        options = await hass.config_entries.options.async_configure(options["flow_id"], {
            "ignore_label": entry.runtime_data.ignore_label, "offline_grace": 90})
        assert options["type"] == "create_entry", options
        await hass.async_block_till_done()
        assert entry.runtime_data.monitor.grace == 90
        unsubscribe()
        assert await hass.config_entries.async_unload(entry.entry_id)
        print("PASS: actual HA setup, registry scan, notification switch/events, exclusions, rename, reload, options and unload")
    finally:
        await hass.async_stop(force=True)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="offline-devices-smoke-") as temporary:
        config_dir = Path(temporary)
        shutil.copytree(root / "custom_components", config_dir / "custom_components")
        asyncio.run(smoke(config_dir))
