import logging

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfo
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import DOMAIN
from .pax_client import CurrentTrigger, PaxClient

_LOGGER = logging.getLogger(__name__)


class PaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1
    discovery_info = None

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfo):
        """Handle the bluetooth discovery step."""
        _LOGGER.debug(
            "Discovered Pax Fan Bluetooth device: %s, %s, %s, %s",
            discovery_info,
            discovery_info.name,
            discovery_info.address,
            discovery_info.service_uuids,
        )

        self.discovery_info = discovery_info

        await self.async_set_unique_id(self.discovery_info.address)
        self._abort_if_unique_id_configured()

        return await self.async_step_add_device()

    async def async_step_add_device(self, user_input=None) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.info(
            f"In async_step_add_device. Address: {self.discovery_info.address}"
        )

        if user_input is not None:
            return self.async_create_entry(
                title=self.discovery_info.name,
                data={CONF_ADDRESS: user_input["mac"], "pin": user_input["pin"]},
            )

        async with PaxClient(self.discovery_info.device) as client:
            pin = await client.async_get_pin()

            data_schema = vol.Schema(
                {
                    vol.Required("mac", default=self.discovery_info.address): str,
                    vol.Optional("pin", default=pin): int,
                }
            )
            errors = {}
            return self.async_show_form(
                step_id="add_device", data_schema=data_schema, errors=errors
            )
