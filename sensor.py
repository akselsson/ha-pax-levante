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


from .pax_client import PaxClient, PaxSensors

import logging
import async_timeout
from datetime import timedelta

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


FAN_SPEED = SensorEntityDescription(
    key="current_fan_speed",
    translation_key="current_fan_speed",
    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
    state_class=SensorStateClass.MEASUREMENT,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    address = entry.unique_id

    _LOGGER.info("In setup sensor: %s, Address: %s", entry, address)

    coordinator = PaxUpdateCoordinator(hass, address)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.states.async_set("pax_levante.integration", "sensor entry")

    async_add_entities([PaxFanEntity(coordinator, FAN_SPEED)])

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
                _LOGGER.info("Updated data for %s", self.address)
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self.address
                )
                data = await PaxClient(ble_device).async_get_sensors()
                _LOGGER.info("sensors: %s, fan_speed: %s", data, data.fan_speed)
                return data
        except Exception as err:
            _LOGGER.info("Update Error: %s", err)
            raise UpdateFailed(f"Unable to fetch data: {err}") from err


class PaxFanEntity(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.address}_{entity_description.key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info(
            "In coordinator update. Coordinator data: %s", self.coordinator.data
        )
        super()._handle_coordinator_update()
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        # self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Check if device and sensor is available in data."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.fan_speed is not None
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.coordinator.data.fan_speed
