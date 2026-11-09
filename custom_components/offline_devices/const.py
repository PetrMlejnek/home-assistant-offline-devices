"""Shared constants."""

DOMAIN = "offline_devices"
EVENT_CHANGED = "offline_devices_changed"
CONF_IGNORE_LABEL = "ignore_label"
CONF_GRACE = "offline_grace"
DEFAULT_GRACE = 300
STARTUP_GRACE = 300
DEFAULT_LABEL_NAME = "Do not monitor availability"
PLATFORMS = ["sensor", "switch"]

OPERATIONAL_DOMAINS = frozenset({
    "alarm_control_panel", "binary_sensor", "camera", "climate", "cover",
    "fan", "humidifier", "lawn_mower", "light", "lock", "media_player",
    "sensor", "siren", "switch", "vacuum", "valve", "water_heater",
})
