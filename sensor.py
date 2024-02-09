"""The Pax Levante fan integration."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.device_registry import (
    CONNECTION_BLUETOOTH,
    DeviceInfo,
)

from dataclasses import asdict

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

# import SensorEntityDescription
from homeassistant.const import REVOLUTIONS_PER_MINUTE

from homeassistant.components.fan import FanEntity
from homeassistant.components.sensor import SensorEntity


from .pax_client import PaxClient, CurrentTrigger

import logging
import async_timeout
from datetime import timedelta

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_MAPPING: dict[str, SensorEntityDescription] = {
    "fan_speed": SensorEntityDescription(
        key="fan_speed",
        translation_key="fan_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "humidity": SensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "temperature": SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "light": SensorEntityDescription(
        key="light",
        translation_key="light",
        native_unit_of_measurement="lux",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "current_trigger": SensorEntityDescription(
        key="current_trigger",
        translation_key="current_trigger",
        device_class=SensorDeviceClass.ENUM,
        options=[CurrentTrigger.BASE, CurrentTrigger.LIGHT, CurrentTrigger.HUMIDITY],
    ),
    "boost": SensorEntityDescription(
        key="boost",
        translation_key="boost",
        device_class=SensorDeviceClass.ENUM,
        options=[True, False],
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    address = entry.unique_id

    _LOGGER.debug("In setup sensor: %s, Address: %s", entry, address)

    coordinator = PaxUpdateCoordinator(hass, address)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    async with async_timeout.timeout(10):
        device_info = await PaxClient(
            bluetooth.async_ble_device_from_address(hass, address)
        ).async_get_device_info()

        async_add_entities(
            PaxSensorEntity(coordinator, device_info, SENSOR_MAPPING[key])
            for key in SENSOR_MAPPING
        )
        return True


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
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                _LOGGER.debug("Updating data for %s", self.address)
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self.address
                )
                data = await PaxClient(ble_device).async_get_sensors()
                _LOGGER.debug("Sensors: %s", data)
                return data
        except Exception as err:
            _LOGGER.warn("Pax sensor update error: %s", err)
            raise UpdateFailed(f"Unable to fetch data: {err}") from err


class PaxSensorEntity(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
        entity_description: SensorEntityDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.address}_{entity_description.key}"
        _LOGGER.debug(
            "Creating entity: %s %s", self._attr_unique_id, self.entity_description
        )
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            manufacturer=device_info.manufacturer,
            model=device_info.model,
            name=device_info.name,
            sw_version=device_info.sw_version,
            hw_version=device_info.hw_version,
            serial_number=device_info.serial_number,
            suggested_area="Bathroom",
        )

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.key in asdict(self.coordinator.data)
        )

    @property
    def native_value(self) -> StateType:
        return asdict(self.coordinator.data)[self.entity_description.key]