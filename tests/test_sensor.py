"""Sensor tests for the pax_levante integration."""

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
    """Mock PaxClient for testing."""

    def __init__(self, bleDevice):
        self.bleDevice = bleDevice

    device = PaxDevice(
        manufacturer="Pax",
        model_number="Levante",
        name="Pax Levante",
        sw_version="1.0",
        hw_version="1.0",
    )

    sensors = PaxSensors(
        humidity=45,
        temperature=22,
        light=150,
        fan_speed=1500,
        current_trigger=CurrentTrigger.BASE,
        boost=False,
        unknown=0,
        raw="2d00160096009c0501000000",
    )

    fan_speed_targets = FanSpeedTarget(humidity=2000, light=1500, base=950)

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


async def test_sensor_entities_created(hass: HomeAssistant, enable_bluetooth: None):
    """Test that all sensor entities are created."""
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

            # Verify all 6 sensor entities were created
            assert hass.states.get("sensor.pax_levante_fan_speed") is not None
            assert hass.states.get("sensor.pax_levante_humidity") is not None
            assert hass.states.get("sensor.pax_levante_temperature") is not None
            assert hass.states.get("sensor.pax_levante_light") is not None
            assert hass.states.get("sensor.pax_levante_current_trigger") is not None
            assert hass.states.get("sensor.pax_levante_boost") is not None


async def test_sensor_fan_speed_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test fan speed sensor state."""
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

            state = hass.states.get("sensor.pax_levante_fan_speed")
            assert state.state == "1500"
            assert state.attributes.get("unit_of_measurement") == "rpm"


async def test_sensor_humidity_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test humidity sensor state."""
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

            state = hass.states.get("sensor.pax_levante_humidity")
            assert state.state == "45"
            assert state.attributes.get("unit_of_measurement") == "%"


async def test_sensor_temperature_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test temperature sensor state."""
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

            state = hass.states.get("sensor.pax_levante_temperature")
            assert state.state == "22"
            assert state.attributes.get("unit_of_measurement") == "°C"


async def test_sensor_light_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test light sensor state."""
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

            state = hass.states.get("sensor.pax_levante_light")
            assert state.state == "150"
            assert state.attributes.get("unit_of_measurement") == "lux"


async def test_sensor_current_trigger_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test current trigger sensor state."""
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

            state = hass.states.get("sensor.pax_levante_current_trigger")
            assert state.state == "CurrentTrigger.BASE"


async def test_sensor_boost_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test boost sensor state."""
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

            state = hass.states.get("sensor.pax_levante_boost")
            assert state.state == "False"


async def test_sensor_state_updates(hass: HomeAssistant, enable_bluetooth: None):
    """Test that sensor states update when coordinator data changes."""
    ble_device = {"CONF_ADDRESS": "AA:BB:CC:DD:EE:FF"}

    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        return_value=ble_device,
    ):
        with patch(
            "custom_components.pax_levante.pax_update_coordinator.PaxClient",
            new=MockClient,
        ) as mock_client_class:
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

            # Initial state
            state = hass.states.get("sensor.pax_levante_humidity")
            assert state.state == "45"

            # Update mock data
            mock_client_class.sensors = PaxSensors(
                humidity=60,
                temperature=25,
                light=200,
                fan_speed=2000,
                current_trigger=CurrentTrigger.HUMIDITY,
                boost=False,
                unknown=0,
                raw="3c00190000c8000d0803000000",
            )

            # Trigger update
            await hass.helpers.entity_component.async_update_entity(
                "sensor.pax_levante_humidity"
            )

            state = hass.states.get("sensor.pax_levante_humidity")
            assert state.state == "60"


async def test_sensor_device_info(hass: HomeAssistant, enable_bluetooth: None):
    """Test that sensor entities have correct device info."""
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
            entity = entity_registry.async_get("sensor.pax_levante_fan_speed")

            assert entity is not None
            assert entity.unique_id == "aa:bb:cc:dd:ee:ff_fan_speed"


async def test_sensor_availability(hass: HomeAssistant, enable_bluetooth: None):
    """Test sensor availability logic."""
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

            # Initially available
            state = hass.states.get("sensor.pax_levante_fan_speed")
            assert state.state != "unavailable"
