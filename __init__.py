"""The Pax Levante fan integration."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    address = entry.unique_id

    _LOGGER.info("In setup Entry: %s, Address: %s", entry, address)

    ble_device = bluetooth.async_ble_device_from_address(hass, address)
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find Pax device with address {address}")

    _LOGGER.info("Device: %s", ble_device)

    hass.states.async_set("pax_levante.integration", "init_entry")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Entry: %s", entry)
    hass.data[DOMAIN].pop(entry.entry_id)

    hass.states.async_set("pax_levante.integration", "unloaded")

    return True
