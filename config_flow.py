from homeassistant import config_entries
from .const import DOMAIN

from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
)

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

import logging


_LOGGER = logging.getLogger(__name__)


class PaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfo):
        """Handle the bluetooth discovery step."""
        _LOGGER.debug(
            "Discovered BT device: %s, %s, %s, %s",
            discovery_info,
            discovery_info.name,
            discovery_info.address,
            discovery_info.service_uuids,
        )

        self.context["title_placeholders"] = {"name": discovery_info.name}

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=discovery_info.name, data={})
