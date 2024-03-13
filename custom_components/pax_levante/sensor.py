"""The Pax Levante fan integration."""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
import logging

# import SensorEntityDescription
import async_timeout
from homeassistant.components import bluetooth
from homeassistant.components.fan import FanEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import REVOLUTIONS_PER_MINUTE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import (
    CONNECTION_BLUETOOTH,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .pax_client import CurrentTrigger, PaxClient

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
        options=list(CurrentTrigger),
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
    coordinator = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.debug(
        "In setup sensor: %s, Address: %s, Coordinator: %s", entry, address, coordinator
    )

    async_add_entities(
        PaxSensorEntity(coordinator, SENSOR_MAPPING[key]) for key in SENSOR_MAPPING
    )
    return True


class PaxSensorEntity(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ):
        super().__init__(coordinator)

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{format_mac(coordinator.address)}_{entity_description.key}"
        )

        device_info = coordinator.device_info

        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            manufacturer=device_info.manufacturer,
            model=f"{device_info.name} {device_info.model_number}",
            name=device_info.name,
            sw_version=device_info.sw_version,
            hw_version=device_info.hw_version,
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
