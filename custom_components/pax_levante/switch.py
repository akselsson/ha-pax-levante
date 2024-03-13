"""The Pax Levante fan integration."""

from __future__ import annotations

from collections import namedtuple
from dataclasses import asdict, dataclass
from datetime import timedelta
import logging

# import SensorEntityDescription
import async_timeout
from homeassistant.components import bluetooth
from homeassistant.components.number import NumberEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
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
class PaxFanSpeedBoostDescription(SwitchEntityDescription):
    has_entity_name: bool = True


ENTITIES = [
    PaxFanSpeedBoostDescription(
        key="boost",
        translation_key="boost",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    address = entry.unique_id
    coordinator = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.debug(
        "In setup switch: %s, Address: %s, Coordinator: %s", entry, address, coordinator
    )

    async_add_entities(PaxBoostEntity(coordinator, entity) for entity in ENTITIES)
    return True


class PaxBoostEntity(CoordinatorEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: PaxUpdateCoordinator,
        entity_description: PaxFanSpeedBoostDescription,
    ):
        super().__init__(coordinator)

        _LOGGER.info(f"Creating PaxBoostEntity: {entity_description}")

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{format_mac(coordinator.address)}_{entity_description.key}"
        )

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            manufacturer=coordinator.device_info.manufacturer,
            model=f"{coordinator.device_info.name} {coordinator.device_info.model_number}",
            name=coordinator.device_info.name,
            sw_version=coordinator.device_info.sw_version,
            hw_version=coordinator.device_info.hw_version,
        )

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self.coordinator.sensors.boost

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("Enabling Boost Mode")
        await self.coordinator.async_set_boost(True)

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("Disabling Boost Mode")
        await self.coordinator.async_set_boost(False)
