"""The Pax Levante fan integration."""
from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pax_client import PaxClient, PaxSensors

import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})

    hass.states.async_set('pax_levante.integration', 'setup')
    _LOGGER.info("In setup")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    address = entry.unique_id

    _LOGGER.info("In setup Entry: %s, Address: %s",entry, address)

    ble_device = bluetooth.async_ble_device_from_address(hass, address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Pax device with address {address}"
        )

    _LOGGER.info("Device: %s", ble_device)

    async def _async_update_method() -> PaxSensors:
        """Get data from Airthings BLE."""
        ble_device = bluetooth.async_ble_device_from_address(hass, address)

        try:
            data = await PaxClient(ble_device).async_get_sensors()
            _LOGGER.info("sensors: %s, fan_speed: %s", data, data.fan_speed)

        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

        return data
    
    #coordinator = DataUpdateCoordinator(
    #    hass,
    #    _LOGGER,
    #    name=DOMAIN,
    #    update_method=_async_update_method,
    #    update_interval=timedelta(seconds=60),
    #)

    #await coordinator.async_config_entry_first_refresh()

    #hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.states.async_set('pax_levante.integration', 'entry')

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Entry: %s",entry)
    hass.data[DOMAIN].pop(entry.entry_id)

    hass.states.async_set('pax_levante.integration','unloaded')


    return True