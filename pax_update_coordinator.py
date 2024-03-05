import copy
import logging
import async_timeout
from datetime import timedelta

from homeassistant.components import bluetooth

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .pax_client import PaxClient, FanSpeedTarget, PaxSensors

_LOGGER = logging.getLogger(__name__)


class PaxUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, address, device_info, pin):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.address = address
        self.device_info = device_info
        self.sensors: PaxSensors | None = None
        self.fan_speed_targets: FanSpeedTarget | None = None
        self.pin = pin

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Updating data for %s", self.address)
                async with PaxClient(self.address) as client:
                    self.sensors = await client.async_get_sensors()
                    self.fan_speed_targets = await client.async_get_fan_speed_targets()
                    _LOGGER.debug(
                        "Sensors: %s, Fan speeds: %s",
                        self.sensors,
                        self.fan_speed_targets,
                    )
                    return self.sensors
        except Exception as err:
            _LOGGER.warn("Pax sensor update error: %s", err)
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

    async def async_set_fan_speed_target(self, key: str, value: int):
        if self.pin == 0:
            raise UpdateFailed(f"Pin not set, unable to update fan speed targets")
        targets = copy.deepcopy(self.fan_speed_targets)
        if targets is None:
            raise UpdateFailed(
                f"Unable to set fan speed targets, current target not available"
            )

        setattr(targets, key, value)
        async with async_timeout.timeout(10):
            _LOGGER.debug("Setting fan speed targets: %s", targets)
            async with PaxClient(self.address) as client:
                if not await client.async_set_pin(self.pin):
                    raise UpdateFailed(f"Unable to set pin.")
                await client.async_set_fan_speed_targets(targets)
                self.fan_speed_targets = await client.async_get_fan_speed_targets()
                self.fan_speed_targets = targets
                self.async_set_updated_data(self.sensors)
                return self.sensors
