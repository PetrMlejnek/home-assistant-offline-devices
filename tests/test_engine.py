"""Behavioral tests using synthetic household devices only."""

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "availability_engine", ROOT / "custom_components/offline_devices/engine.py"
)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
Device, Reading, Monitor = engine.Device, engine.Reading, engine.Monitor


def device(key="plug", state="on", changed=0, **kwargs):
    return Device(key, key.title(), readings=(Reading(state, changed),), **kwargs)


class AvailabilityTests(unittest.TestCase):
    def test_off_switch_is_online(self):
        self.assertEqual(engine.classify(device(state="off"), 1000, 300)[0], "online")

    def test_offline_threshold_boundary(self):
        d = device(state="unavailable", changed=100)
        self.assertEqual(engine.classify(d, 399, 300), ("pending", 100))
        self.assertEqual(engine.classify(d, 400, 300), ("offline", 100))

    def test_last_operational_entity_to_fail_sets_threshold(self):
        d = replace(device(), readings=(Reading("unavailable", 0), Reading("unavailable", 900)))
        self.assertEqual(engine.classify(d, 1000, 300), ("pending", 900))

    def test_partial_entity_failure_does_not_mark_whole_device_offline(self):
        d = replace(device(), readings=(Reading("unavailable", 0), Reading("22", 10)))
        self.assertEqual(engine.classify(d, 1000, 300)[0], "online")

    def test_unknown_and_empty_are_not_confirmed_outages(self):
        for readings in ((), (Reading("unknown", 0),), (Reading("", 0),),
                         (Reading("unknown", 0), Reading("unavailable", 0))):
            with self.subTest(readings=readings):
                self.assertEqual(engine.classify(replace(device(), readings=readings), 1000, 300)[0], "unknown")

    def test_explicit_connectivity_overrides_retained_sensor_value(self):
        d = replace(device(), readings=(Reading("off", 0, True), Reading("22", 0)))
        self.assertEqual(engine.classify(d, 1000, 300)[0], "offline")

    def test_unknown_connectivity_remains_uncertain(self):
        d = replace(device(), readings=(Reading("unknown", 0, True), Reading("off", 0, True)))
        self.assertEqual(engine.classify(d, 1000, 300)[0], "unknown")

    def test_any_connected_interface_means_online(self):
        d = replace(device(), readings=(Reading("on", 0, True), Reading("off", 0, True)))
        self.assertEqual(engine.classify(d, 1000, 300)[0], "online")

    def test_exclusion_wins_over_offline(self):
        self.assertEqual(engine.classify(device(state="unavailable", excluded=True), 1000, 300)[0], "excluded")

    def test_multiple_zigbee_bridges_only_block_their_own_children(self):
        bridge_a = replace(device("bridge_a", bridge=True), readings=(Reading("off", 0, True),))
        bridge_b = replace(device("bridge_b", bridge=True), readings=(Reading("on", 0, True),))
        monitor = Monitor(0)
        data = monitor.update([bridge_a, bridge_b, device("a", parent="bridge_a"),
                               device("b", parent="bridge_b"), device("wifi")], 1000)
        statuses = {r["id"]: r["status"] for r in data["devices"]}
        self.assertEqual(statuses, {"bridge_a": "offline", "bridge_b": "online",
                                    "a": "blocked", "b": "online", "wifi": "online"})

    def test_excluded_bridge_still_blocks_children(self):
        bridge = replace(device("bridge", bridge=True, excluded=True), readings=(Reading("off", 0, True),))
        data = Monitor(0).update([bridge, device("child", parent="bridge")], 1000)
        self.assertEqual({r["status"] for r in data["devices"]}, {"blocked", "excluded"})

    def test_missing_bridge_connectivity_does_not_block_children(self):
        data = Monitor(0).update([device("bridge", bridge=True), device("child", parent="bridge")], 1000)
        self.assertTrue(all(r["status"] == "online" for r in data["devices"]))

    def test_startup_delays_new_outage(self):
        monitor = Monitor(1300)
        d = device(state="unavailable")
        first = monitor.update([d], 1000)
        self.assertTrue(first["warming_up"])
        self.assertEqual(first["devices"][0]["status"], "pending")
        self.assertEqual(first["new_offline"], [])
        ready = monitor.update([d], 1300)
        self.assertEqual(len(ready["new_offline"]), 1)

    def test_discovery_is_silent(self):
        data = Monitor(0).update([device(state="unavailable")], 1000)
        self.assertEqual(data["offline"], 1)
        self.assertEqual(data["new_offline"], [])

    def test_outage_not_repeated_and_recovery_once(self):
        monitor = Monitor(0)
        monitor.update([device()], 1000)
        self.assertEqual(len(monitor.update([device(state="unavailable")], 1300)["new_offline"]), 1)
        self.assertEqual(monitor.update([device(state="unavailable")], 1360)["new_offline"], [])
        self.assertEqual(len(monitor.update([device()], 1400)["recovered"]), 1)
        self.assertEqual(monitor.update([device()], 1460)["recovered"], [])

    def test_unknown_does_not_split_an_incident(self):
        monitor = Monitor(0)
        monitor.update([device()], 1000)
        monitor.update([device(state="unavailable")], 1300)
        unknown = monitor.update([device(state="unknown")], 1400)
        self.assertTrue(unknown["devices"][0]["incident"])
        self.assertEqual(monitor.update([device(state="unavailable")], 1500)["new_offline"], [])
        self.assertEqual(len(monitor.update([device()], 1600)["recovered"]), 1)

    def test_parent_outage_does_not_split_child_incident(self):
        monitor = Monitor(0)
        bridge = replace(device("bridge", bridge=True), readings=(Reading("on", 0, True),))
        child = device("child", parent="bridge", state="unavailable")
        monitor.update([bridge, replace(child, readings=(Reading("on", 0),))], 1000)
        monitor.update([bridge, child], 1300)
        monitor.update([replace(bridge, readings=(Reading("off", 0, True),)), child], 1400)
        self.assertEqual(monitor.update([bridge, child], 1500)["new_offline"], [])

    def test_rename_updates_inventory_without_notification(self):
        monitor = Monitor(0)
        d = device(state="unavailable")
        monitor.update([d], 1000)
        data = monitor.update([replace(d, name="Renamed socket", area="Workshop")], 1100)
        self.assertEqual(data["devices"][0]["name"], "Renamed socket")
        self.assertEqual(data["devices"][0]["area"], "Workshop")
        self.assertIsNone(engine.notification_payload(data))

    def test_excluding_and_reincluding_does_not_notify(self):
        monitor = Monitor(0)
        d = device(state="unavailable")
        monitor.update([d], 1000)
        excluded = monitor.update([replace(d, excluded=True)], 1100)
        self.assertEqual((excluded["monitored"], excluded["excluded"]), (0, 1))
        self.assertIsNone(engine.notification_payload(excluded))
        self.assertIsNone(engine.notification_payload(monitor.update([d], 1200)))

    def test_removal_is_not_a_recovery(self):
        monitor = Monitor(0)
        monitor.update([device(state="unavailable")], 1000)
        self.assertIsNone(engine.notification_payload(monitor.update([], 1100)))

    def test_restored_incident_survives_startup(self):
        before = Monitor(0)
        before.update([device(state="unavailable")], 1000)
        after = Monitor(2300, rows=before.rows)
        self.assertIsNone(engine.notification_payload(after.update([device(state="unavailable")], 2000)))
        self.assertIsNone(engine.notification_payload(after.update([device(state="unavailable")], 2300)))

    def test_recovery_during_startup_is_silent(self):
        before = Monitor(0)
        before.update([device(state="unavailable")], 1000)
        after = Monitor(2300, rows=before.rows)
        self.assertIsNone(engine.notification_payload(after.update([device()], 2000)))

    def test_grouped_notification_has_real_newline(self):
        monitor = Monitor(0)
        monitor.update([device("a"), device("b", state="unavailable")], 1000)
        data = monitor.update([device("a", state="unavailable"), device("b")], 1300)
        payload = engine.notification_payload(data)
        self.assertEqual(payload["message"], "Offline: A\nBack online: B")
        self.assertEqual(len(payload["offline"]), 1)
        self.assertEqual(len(payload["recovered"]), 1)


if __name__ == "__main__":
    unittest.main()
