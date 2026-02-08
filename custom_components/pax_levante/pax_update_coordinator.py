import copy
from datetime import timedelta
import logging

import async_timeout
from homeassistant.components import bluetooth
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .pax_client import FanSpeedTarget, PaxClient, PaxDevice, PaxSensors

_LOGGER = logging.getLogger(__name__)


class PaxUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, address, pin):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=65),
        )
        self.address = address
        self.device_info: PaxDevice | None = None
        self.sensors: PaxSensors | None = None
        self.fan_speed_targets: FanSpeedTarget | None = None
        self.pin = pin

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Updating data for %s", self.address)
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self.address
                )
                if not ble_device:
                    raise UpdateFailed(
                        f"Could not find device {self.address}"
                    )
                async with PaxClient(ble_device) as client:
                    _LOGGER.debug("Connected to device")
                    if self.device_info is None:
                        await client.async_log_services()
                        self.device_info = await client.async_get_device_info()
                        _LOGGER.debug("Fetched device info: %s", self.device_info)

                    self.sensors = await client.async_get_sensors()
                    _LOGGER.debug("Fetched sensors: %s", self.sensors)
                    self.fan_speed_targets = await client.async_get_fan_speed_targets()
                    _LOGGER.debug(
                        "Fetched fan speed targets: %s", self.fan_speed_targets
                    )
        except Exception as err:
            _LOGGER.warn("Pax sensor update error: %s", err)
            raise UpdateFailed(f"Unable to fetch data: {err}") from err
        _LOGGER.debug("Data updated")
        return self.sensors

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
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address
            )
            if not ble_device:
                raise UpdateFailed(f"Could not find device {self.address}")
            async with PaxClient(ble_device) as client:
                if not await client.async_set_pin(self.pin):
                    raise UpdateFailed(f"Unable to set pin.")
                await client.async_set_fan_speed_targets(targets)
                self.fan_speed_targets = await client.async_get_fan_speed_targets()
                self.fan_speed_targets = targets
                self.async_set_updated_data(self.sensors)
                return self.sensors

    async def async_set_boost(self, value):
        if self.pin == 0:
            raise UpdateFailed(f"Pin not set, unable to update fan speed targets")
        async with async_timeout.timeout(10):
            _LOGGER.debug("Setting boost: %s", value)
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address
            )
            if not ble_device:
                raise UpdateFailed(f"Could not find device {self.address}")
            async with PaxClient(ble_device) as client:
                if not await client.async_set_pin(self.pin):
                    raise UpdateFailed(f"Unable to set pin.")
                await client.async_set_boost(value)
                self.sensors = await client.async_get_sensors()
                self.async_set_updated_data(self.sensors)
                return self.sensors
