"""Switch tests for the pax_levante integration."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pax_levante.const import DOMAIN
from custom_components.pax_levante.pax_client import (
    CurrentTrigger,
    FanSpeedTarget,
    PaxDevice,
    PaxSensors,
)


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    return True


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


class MockClient:
    def __init__(self, bleDevice):
        self.bleDevice = bleDevice
        pass

    device = PaxDevice(
        manufacturer="Pax",
        model_number="Levante",
        name="Pax Levante",
        sw_version="1.0",
        hw_version="1.0",
    )

    sensors = PaxSensors(
        humidity=0,
        temperature=98,
        light=560,
        fan_speed=2390,
        current_trigger=CurrentTrigger.BOOST,
        boost=True,
        unknown=0,
        raw="000062003002560917000000",
    )

    fan_speed_targets = FanSpeedTarget(humidity=1, light=23, base=23)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def async_get_device_info(self):
        return self.device

    async def async_get_sensors(self):
        return self.sensors

    async def async_get_fan_speed_targets(self):
        return self.fan_speed_targets


async def test_switch(hass: HomeAssistant, enable_bluetooth: None):

    # mock bluetooth.async_ble_device_from_address
    ble_device = {"CONF_ADDRESS": "AA:BB:CC:DD:EE:FF"}
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        return_value=ble_device,
    ):
        with patch(
            "custom_components.pax_levante.pax_update_coordinator.PaxClient",
            new=MockClient,
        ) as client:

            entry = MockConfigEntry(
                domain=DOMAIN,
                data={
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    "pin": 1234,
                },
            )
            entry.add_to_hass(hass)

            await hass.config_entries.async_setup(entry.entry_id)

            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "on"

            client.sensors = PaxSensors(
                humidity=0,
                temperature=98,
                light=560,
                fan_speed=2390,
                current_trigger=CurrentTrigger.AUTOMATIC_VENTILATION,
                boost=False,
                unknown=0,
                raw="000062003002560917000000",
            )

            await hass.helpers.entity_component.async_update_entity(
                "switch.pax_levante_boost"
            )
            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "off"

            await hass.async_block_till_done()
