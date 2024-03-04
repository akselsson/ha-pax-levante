"""The Pax Levante fan integration."""

from __future__ import annotations
import async_timeout

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

import logging
from .pax_client import PaxClient

from .pax_update_coordinator import PaxUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    address = entry.unique_id

    _LOGGER.debug("In setup Entry: %s, Address: %s", entry, address)

    ble_device = bluetooth.async_ble_device_from_address(hass, address)
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find Pax device with address {address}")

    _LOGGER.debug("Found device: %s", ble_device)
    
    async with async_timeout.timeout(10):
        async with PaxClient(ble_device) as client:
            device_info = await client.async_get_device_info()

            coordinator = PaxUpdateCoordinator(hass, address, device_info)
            await coordinator.async_config_entry_first_refresh()
            hass.data[DOMAIN][entry.entry_id] = coordinator

            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

            return True
