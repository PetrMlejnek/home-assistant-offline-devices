"""UI setup and options."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_GRACE, CONF_IGNORE_LABEL, DEFAULT_GRACE, DOMAIN


def options_schema(current):
    """Use a real label selector, so renaming a label preserves exclusions."""
    label_key = vol.Optional(CONF_IGNORE_LABEL)
    if current.get(CONF_IGNORE_LABEL):
        label_key = vol.Optional(CONF_IGNORE_LABEL, default=current[CONF_IGNORE_LABEL])
    return vol.Schema({
        label_key: selector.LabelSelector(selector.LabelSelectorConfig()),
        vol.Required(CONF_GRACE, default=current.get(CONF_GRACE, DEFAULT_GRACE)):
            vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
    })


class OfflineDevicesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Allow one monitor per Home Assistant instance."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Choose an existing exclusion label or let setup create one."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Online / Offline Devices", data=user_input)
        return self.async_show_form(step_id="user", data_schema=options_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OfflineDevicesOptionsFlow()


class OfflineDevicesOptionsFlow(config_entries.OptionsFlowWithReload):
    """Reload automatically after settings change."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema({**self.config_entry.data, **self.config_entry.options}),
        )
