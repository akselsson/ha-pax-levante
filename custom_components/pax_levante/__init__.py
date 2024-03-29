"""The Pax Levante fan integration."""

from __future__ import annotations

import logging

import async_timeout
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .pax_client import PaxClient
from .pax_update_coordinator import PaxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "number", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    address = entry.data[CONF_ADDRESS]

    _LOGGER.debug("In setup Entry: %s, Address: %s", entry, address)

    ble_device = bluetooth.async_ble_device_from_address(hass, address)
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find Pax device with address {address}")

    _LOGGER.info("Found device: %s", ble_device)

    coordinator = PaxUpdateCoordinator(hass, address, entry.data["pin"])
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
