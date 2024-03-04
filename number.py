"""The Pax Levante fan integration."""

from __future__ import annotations
from collections import namedtuple

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
    format_mac,
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

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import EntityCategory



from .pax_client import PaxClient, CurrentTrigger

import logging
import async_timeout
from datetime import timedelta

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

OptionsTuple = namedtuple('options', ['min_value', 'max_value', 'step'])
OPTIONS = {}
OPTIONS["fanspeed"] = OptionsTuple(950, 2400, 25)

PaxEntity = namedtuple('PaxEntity', ['key', 'entityName', 'units', 'deviceClass', 'category', 'icon', 'options'])
ENTITIES = [
    PaxEntity(
        "fanspeed_humidity",
        "Fanspeed Humidity",
        REVOLUTIONS_PER_MINUTE,
        None,
        EntityCategory.CONFIG,
        "mdi:engine",
        OPTIONS["fanspeed"],
    ),
    PaxEntity(
        "fanspeed_light",
        "Fanspeed Light",
        REVOLUTIONS_PER_MINUTE,
        None,
        EntityCategory.CONFIG,
        "mdi:engine",
        OPTIONS["fanspeed"],
    ),
    PaxEntity(
        "fanspeed_trickle",
        "Fanspeed Trickle",
        REVOLUTIONS_PER_MINUTE,
        None,
        EntityCategory.CONFIG,
        "mdi:engine",
        OPTIONS["fanspeed"],
    )
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    address = entry.unique_id
    coordinator = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.debug("In setup sensor: %s, Address: %s, Coordinator: %s", entry, address, coordinator)
 
    async_add_entities(
        PaxNumberEntity(coordinator, entity)
        for entity in ENTITIES
    )
    return True


class PaxNumberEntity(CoordinatorEntity, NumberEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entity_description: PaxEntity,
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

        """Number Entity properties"""
        self._attr_device_class = entity_description.deviceClass
        self._attr_mode = "box"
        self._attr_native_min_value = entity_description.options.min_value
        self._attr_native_max_value = entity_description.options.max_value
        self._attr_native_step = entity_description.options.step
        self._attr_native_unit_of_measurement = entity_description.units

    @property
    def native_value(self) -> float | None:
        """Return number value."""
        try:
            return int(self.coordinator.get_data(self._key))
        except:
            return None

    async def async_set_native_value(self, value):
        """Save old value"""
        old_value = self.coordinator.get_data(self._key)

        """ Write new value to our storage """
        self.coordinator.set_data(self._key, int(value))

        """ Write value to device """
        if not await self.coordinator.write_data(self._key):
            """Restore value"""
            self.coordinator.set_data(self._key, old_value)

        self.async_schedule_update_ha_state(force_refresh=False)
