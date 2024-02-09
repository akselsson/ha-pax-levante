"""The Pax Levante fan integration."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.fan import FanEntity


from .pax_client import PaxClient, PaxSensors

import logging
import async_timeout
from datetime import timedelta

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    address = entry.unique_id

    _LOGGER.info("In setup sensor: %s, Address: %s", entry, address)

    coordinator = PaxUpdateCoordinator(hass, address)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.states.async_set("pax_levante.integration", "sensor entry")

    async_add_entities([PaxFanEntity(coordinator)])

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
            _LOGGER.info("Updated Error: %s", err)
            raise UpdateFailed(f"Unable to fetch data: {err}") from err


class PaxFanEntity(FanEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info(
            "In coordinator update. Coordinator data: %s", self.coordinator.data
        )
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        # self.async_write_ha_state()
