import logging
import async_timeout
from datetime import timedelta

from homeassistant.components import bluetooth

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .pax_client import PaxClient

_LOGGER = logging.getLogger(__name__)


class PaxUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, address):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.address = address

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Updating data for %s", self.address)
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self.address
                )
                async with PaxClient(ble_device) as client:
                    data = await PaxClient(ble_device).async_get_sensors()
                    _LOGGER.debug("Sensors: %s", data)
                    return data
        except Exception as err:
            _LOGGER.warn("Pax sensor update error: %s", err)
            raise UpdateFailed(f"Unable to fetch data: {err}") from err
