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


async def test_switch_turn_on(hass: HomeAssistant, enable_bluetooth: None):
    """Test turning boost switch on."""
    ble_device = {"CONF_ADDRESS": "AA:BB:CC:DD:EE:FF"}

    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        return_value=ble_device,
    ):
        with patch(
            "custom_components.pax_levante.pax_update_coordinator.PaxClient",
            new=MockClient,
        ) as client:
            # Start with boost off
            client.sensors = PaxSensors(
                humidity=0,
                temperature=98,
                light=560,
                fan_speed=1500,
                current_trigger=CurrentTrigger.BASE,
                boost=False,
                unknown=0,
                raw="000062003002dc050001000000",
            )

            entry = MockConfigEntry(
                domain=DOMAIN,
                data={
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    "pin": 1234,
                },
            )
            entry.add_to_hass(hass)

            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "off"

            # Turn on boost
            await hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": "switch.pax_levante_boost"},
                blocking=True,
            )

            # Update mock to reflect boost on
            client.sensors = PaxSensors(
                humidity=0,
                temperature=98,
                light=560,
                fan_speed=2400,
                current_trigger=CurrentTrigger.BOOST,
                boost=True,
                unknown=0,
                raw="000062003002600917000000",
            )

            await hass.helpers.entity_component.async_update_entity(
                "switch.pax_levante_boost"
            )

            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "on"


async def test_switch_turn_off(hass: HomeAssistant, enable_bluetooth: None):
    """Test turning boost switch off."""
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
            await hass.async_block_till_done()

            # Initial state is boost on
            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "on"

            # Turn off boost
            await hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": "switch.pax_levante_boost"},
                blocking=True,
            )

            # Update mock to reflect boost off
            client.sensors = PaxSensors(
                humidity=0,
                temperature=98,
                light=560,
                fan_speed=1500,
                current_trigger=CurrentTrigger.BASE,
                boost=False,
                unknown=0,
                raw="000062003002dc050001000000",
            )

            await hass.helpers.entity_component.async_update_entity(
                "switch.pax_levante_boost"
            )

            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "off"


async def test_switch_toggle(hass: HomeAssistant, enable_bluetooth: None):
    """Test toggling boost switch."""
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
            await hass.async_block_till_done()

            # Initial state is boost on
            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "on"

            # Toggle boost (should turn off)
            await hass.services.async_call(
                "switch",
                "toggle",
                {"entity_id": "switch.pax_levante_boost"},
                blocking=True,
            )

            client.sensors = PaxSensors(
                humidity=0,
                temperature=98,
                light=560,
                fan_speed=1500,
                current_trigger=CurrentTrigger.BASE,
                boost=False,
                unknown=0,
                raw="000062003002dc050001000000",
            )

            await hass.helpers.entity_component.async_update_entity(
                "switch.pax_levante_boost"
            )

            state = hass.states.get("switch.pax_levante_boost")
            assert state.state == "off"


async def test_switch_unique_id(hass: HomeAssistant, enable_bluetooth: None):
    """Test that switch entity has correct unique ID."""
    ble_device = {"CONF_ADDRESS": "AA:BB:CC:DD:EE:FF"}

    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        return_value=ble_device,
    ):
        with patch(
            "custom_components.pax_levante.pax_update_coordinator.PaxClient",
            new=MockClient,
        ):
            entry = MockConfigEntry(
                domain=DOMAIN,
                data={
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    "pin": 1234,
                },
            )
            entry.add_to_hass(hass)

            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

            # Get entity registry
            entity_registry = hass.helpers.entity_registry.async_get(hass)
            entity = entity_registry.async_get("switch.pax_levante_boost")

            assert entity is not None
            assert entity.unique_id == "aa:bb:cc:dd:ee:ff_boost"


async def test_switch_device_info(hass: HomeAssistant, enable_bluetooth: None):
    """Test that switch entity has correct device info."""
    ble_device = {"CONF_ADDRESS": "AA:BB:CC:DD:EE:FF"}

    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        return_value=ble_device,
    ):
        with patch(
            "custom_components.pax_levante.pax_update_coordinator.PaxClient",
            new=MockClient,
        ):
            entry = MockConfigEntry(
                domain=DOMAIN,
                data={
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    "pin": 1234,
                },
            )
            entry.add_to_hass(hass)

            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

            # Get device registry
            device_registry = hass.helpers.device_registry.async_get(hass)
            entity_registry = hass.helpers.entity_registry.async_get(hass)

            entity = entity_registry.async_get("switch.pax_levante_boost")
            assert entity is not None

            device = device_registry.async_get(entity.device_id)
            assert device is not None
            assert device.manufacturer == "Pax"
            assert device.model == "Pax Levante Levante"
