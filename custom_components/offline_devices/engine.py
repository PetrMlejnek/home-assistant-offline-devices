"""Pure availability rules. No network access or Home Assistant imports."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Reading:
    """One enabled operational entity's state."""

    state: str
    changed: float
    connectivity: bool = False


@dataclass(frozen=True)
class Device:
    """A sanitized projection of one device registry entry."""

    id: str
    name: str
    area: str = ""
    integrations: tuple[str, ...] = ()
    readings: tuple[Reading, ...] = ()
    parent: str | None = None
    bridge: bool = False
    excluded: bool = False


def classify(device: Device, now: float, grace: int) -> tuple[str, float]:
    """Prefer explicit connectivity; otherwise inspect operational entities."""
    if device.excluded:
        return "excluded", 0
    readings = device.readings
    connectivity = tuple(r for r in readings if r.connectivity)
    if connectivity:
        readings = connectivity
        if any(r.state == "on" for r in readings):
            return "online", 0
        if any(r.state not in {"off", "unavailable"} for r in readings):
            return "unknown", 0
    elif any(r.state not in {"unknown", "unavailable", ""} for r in readings):
        # A light/switch being "off" is an available device.
        return "online", 0
    elif not readings or any(r.state != "unavailable" for r in readings):
        return "unknown", 0
    since = max(r.changed for r in readings)
    return ("offline" if now - since >= grace else "pending"), since


def changes(old: list[dict], new: list[dict]) -> tuple[list[dict], list[dict]]:
    """Ignore first discovery, renames, deletions and exclusion changes."""
    previous = {row["id"]: row for row in old}
    offline, recovered = [], []
    for row in new:
        before = previous.get(row["id"])
        if not before or before.get("status") == "excluded":
            continue
        if row["status"] == "offline" and not before.get("incident", False):
            offline.append(row)
        elif row["status"] == "online" and before.get("incident", False):
            recovered.append(row)
    return offline, recovered


@dataclass
class Monitor:
    """Maintain incidents through temporary unknown and parent-blocked states."""

    startup_until: float
    grace: int = 300
    rows: list[dict[str, Any]] = field(default_factory=list)

    def update(self, devices: list[Device], now: float) -> dict[str, Any]:
        previous = {row["id"]: row for row in self.rows}
        # Track bridges separately, including excluded bridges. An excluded
        # bridge does not automatically exclude its children.
        blocked_parents = {
            d.id for d in devices if d.bridge
            and any(r.connectivity for r in d.readings)
            and not any(r.connectivity and r.state == "on" for r in d.readings)
        }
        rows = []
        for device in devices:
            status, since = classify(device, now, self.grace)
            if not device.excluded and device.parent in blocked_parents:
                status, since = "blocked", 0
            elif status == "offline" and now < self.startup_until:
                status = "pending"
            incident = previous.get(device.id, {}).get("incident", False)
            if status == "offline":
                incident = True
            elif status in {"online", "excluded"}:
                incident = False
            rows.append({
                "id": device.id, "name": device.name, "area": device.area,
                "integrations": ", ".join(device.integrations),
                "status": status, "since": since, "incident": incident,
            })
        rows.sort(key=lambda row: (row["name"].casefold(), row["id"]))
        offline, recovered = changes(self.rows, rows)
        self.rows = rows
        return {
            "devices": rows,
            "offline": sum(row["status"] == "offline" for row in rows),
            "monitored": sum(row["status"] != "excluded" for row in rows),
            "excluded": sum(row["status"] == "excluded" for row in rows),
            "warming_up": now < self.startup_until,
            "new_offline": offline if now >= self.startup_until else [],
            "recovered": recovered if now >= self.startup_until else [],
        }


def notification_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    """One combined event per scan; notification delivery is user-configured."""
    offline, recovered = data["new_offline"], data["recovered"]
    if not offline and not recovered:
        return None
    lines = []
    for label, rows in (("Offline", offline), ("Back online", recovered)):
        for row in rows:
            area = f" ({row['area']})" if row["area"] else ""
            lines.append(f"{label}: {row['name']}{area}")
    return {
        "title": "Home Assistant: device availability",
        "message": "\n".join(lines),
        "offline": offline,
        "recovered": recovered,
    }
