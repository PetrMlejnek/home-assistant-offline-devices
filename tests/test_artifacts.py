"""Validate shipped YAML, JSON, Python syntax and dashboard templates."""

import ast
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from jinja2 import Environment, StrictUndefined
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/offline_devices"


class BlueprintLoader(yaml.SafeLoader):
    pass


BlueprintLoader.add_constructor("!input", lambda loader, node: {"input": loader.construct_scalar(node)})


class ArtifactTests(unittest.TestCase):
    def test_all_python_parses(self):
        for path in COMPONENT.glob("*.py"):
            with self.subTest(file=path.name):
                ast.parse(path.read_text(encoding="utf-8"))

    def test_metadata_and_translations(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], "offline_devices")
        self.assertTrue(manifest["config_flow"])
        self.assertEqual(manifest["requirements"], [])
        self.assertEqual(len(list((ROOT / "custom_components").iterdir())), 1)
        strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))

        def paths(value, prefix=""):
            return {p for key, child in value.items() for p in
                    (paths(child, prefix + key + ".") if isinstance(child, dict) else {prefix + key})}

        for language in ("en", "cs"):
            translation = json.loads((COMPONENT / f"translations/{language}.json").read_text(encoding="utf-8"))
            self.assertEqual(paths(strings), paths(translation))

    def test_blueprint_has_no_fixed_recipient(self):
        blueprint = yaml.load((ROOT / "blueprints/availability_notifications.yaml").read_text(), Loader=BlueprintLoader)
        self.assertEqual(blueprint["triggers"][0]["event_type"], "offline_devices_changed")
        self.assertEqual(blueprint["actions"][-1]["sequence"], {"input": "notification_actions"})
        self.assertNotIn("default", blueprint["blueprint"]["input"]["notification_actions"])
        self.assertEqual(blueprint["actions"][0], {
            "condition": "state", "entity_id": {"input": "notification_switch"}, "state": "on"})

    def test_dashboard_templates_render_offline_unknown_and_empty_states(self):
        dashboard = yaml.safe_load((ROOT / "dashboards/device-availability.yaml").read_text(encoding="utf-8"))
        env = Environment(undefined=StrictUndefined)
        env.filters["timestamp_custom"] = lambda value, fmt, local: datetime.fromtimestamp(value, timezone.utc).strftime(fmt)
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for status in ("online", "offline", "pending", "unknown", "blocked", "excluded", None):
            rows = [] if status is None else [{"name": "Synthetic socket", "area": "Test room",
                                              "integrations": "mqtt", "status": status, "since": 100}]
            attrs = {"devices": rows, "monitored": 1, "excluded": 0, "warming_up": False,
                     "label_missing": False, "ignore_label": "test_label"}
            state = SimpleNamespace(state="0" if status else "unavailable", attributes=attrs, last_reported=now)

            class States:
                sensor = SimpleNamespace(offline_devices=state)

                def __call__(self, entity_id):
                    return state.state

            context = {"states": States(), "state_attr": lambda entity, attr: attrs.get(attr),
                       "label_name": lambda label: "Test exclusion label", "now": lambda: now,
                       "as_timestamp": lambda value: value.timestamp()}
            for view in dashboard["views"]:
                for card in view["cards"]:
                    if card["type"] == "markdown":
                        with self.subTest(status=status, card=card["title"]):
                            rendered = env.from_string(card["content"]).render(context)
                            self.assertTrue(rendered.strip())


if __name__ == "__main__":
    unittest.main()
