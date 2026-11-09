"""Monitor device availability already reported to Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import label_registry as lr

from .const import CONF_IGNORE_LABEL, DEFAULT_LABEL_NAME, PLATFORMS
from .coordinator import AvailabilityCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create a shared exclusion label on first setup and start monitoring."""
    if not entry.data.get(CONF_IGNORE_LABEL):
        labels = lr.async_get(hass)
        label = labels.async_get_label_by_name(DEFAULT_LABEL_NAME)
        if label is None:
            label = labels.async_create(DEFAULT_LABEL_NAME, icon="mdi:eye-off")
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_IGNORE_LABEL: label.label_id}
        )
    coordinator = AvailabilityCoordinator(hass, entry)
    entry.runtime_data = coordinator
    await coordinator.async_restore()
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Persist incidents and stop the entities."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_save()
    return unloaded
