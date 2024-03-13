"""The Pax Levante fan integration."""

from __future__ import annotations

from collections import namedtuple
from dataclasses import asdict, dataclass
from datetime import timedelta
import logging

# import SensorEntityDescription
import async_timeout
from homeassistant.components import bluetooth
from homeassistant.components.number import NumberEntity, NumberEntityDescription
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
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .pax_client import CurrentTrigger, PaxClient
from .pax_update_coordinator import PaxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PaxFanSpeedEntityDescription(NumberEntityDescription):
    propertyKey: str

    has_entity_name: bool = True
    icon: str = "mdi:engine"
    mode: str = "auto"
    native_min_value: int = 950
    native_max_value: int = 2400
    native_step: int = 25
    native_unit_of_measurement: str = REVOLUTIONS_PER_MINUTE


ENTITIES = [
    PaxFanSpeedEntityDescription(
        key="fanspeed_target_humidity",
        translation_key="fanspeed_target_humidity",
        propertyKey="humidity",
    ),
    PaxFanSpeedEntityDescription(
        key="fanspeed_target_light",
        translation_key="fanspeed_target_light",
        propertyKey="light",
    ),
    PaxFanSpeedEntityDescription(
        key="fanspeed_target_base",
        translation_key="fanspeed_target_base",
        propertyKey="base",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    address = entry.unique_id
    coordinator = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.debug(
        "In setup number: %s, Address: %s, Coordinator: %s", entry, address, coordinator
    )

    async_add_entities(PaxFanSpeedEntity(coordinator, entity) for entity in ENTITIES)
    return True


class PaxFanSpeedEntity(CoordinatorEntity, NumberEntity):
    def __init__(
        self,
        coordinator: PaxUpdateCoordinator,
        entity_description: PaxFanSpeedEntityDescription,
    ):
        super().__init__(coordinator)

        _LOGGER.info(f"Creating PaxFanSpeedEntity: {entity_description}")

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{format_mac(coordinator.address)}_{entity_description.key}"
        )

        device_info = coordinator.device_info

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            manufacturer=device_info.manufacturer,
            model=f"{device_info.name} {device_info.model_number}",
            name=device_info.name,
            sw_version=device_info.sw_version,
            hw_version=device_info.hw_version,
        )

    @property
    def native_value(self) -> float | None:
        """Return number value."""
        try:
            return getattr(
                self.coordinator.fan_speed_targets, self.entity_description.propertyKey
            )
        except Exception as e:
            _LOGGER.error(
                f"Error getting native value for {self.entity_description.propertyKey}: {e}",
                exc_info=True,
            )
            return None

    async def async_set_native_value(self, value):
        await self.coordinator.async_set_fan_speed_target(
            self.entity_description.propertyKey, int(value)
        )

        self.async_schedule_update_ha_state(force_refresh=False)
