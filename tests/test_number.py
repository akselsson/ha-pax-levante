"""Number entity tests for the pax_levante integration."""

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


async def test_number_entities_created(hass: HomeAssistant, enable_bluetooth: None):
    """Test that all number entities are created."""
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

            # Verify all 3 number entities were created
            assert hass.states.get("number.pax_levante_fanspeed_target_humidity") is not None
            assert hass.states.get("number.pax_levante_fanspeed_target_light") is not None
            assert hass.states.get("number.pax_levante_fanspeed_target_base") is not None


async def test_number_humidity_target_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test humidity fan speed target state."""
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

            state = hass.states.get("number.pax_levante_fanspeed_target_humidity")
            assert state.state == "2000"
            assert state.attributes.get("unit_of_measurement") == "rpm"
            assert state.attributes.get("min") == 950
            assert state.attributes.get("max") == 2400
            assert state.attributes.get("step") == 25


async def test_number_light_target_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test light fan speed target state."""
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

            state = hass.states.get("number.pax_levante_fanspeed_target_light")
            assert state.state == "1500"
            assert state.attributes.get("unit_of_measurement") == "rpm"


async def test_number_base_target_state(hass: HomeAssistant, enable_bluetooth: None):
    """Test base fan speed target state."""
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

            state = hass.states.get("number.pax_levante_fanspeed_target_base")
            assert state.state == "950"
            assert state.attributes.get("unit_of_measurement") == "rpm"


async def test_number_set_value(hass: HomeAssistant, enable_bluetooth: None):
    """Test setting a number value."""
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

            # Set new value
            await hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": "number.pax_levante_fanspeed_target_humidity",
                    "value": 2200,
                },
                blocking=True,
            )

            # Update mock data to reflect the change
            mock_client_class.fan_speed_targets = FanSpeedTarget(
                humidity=2200, light=1500, base=950
            )

            # Force state update
            await hass.helpers.entity_component.async_update_entity(
                "number.pax_levante_fanspeed_target_humidity"
            )

            state = hass.states.get("number.pax_levante_fanspeed_target_humidity")
            assert state.state == "2200"


async def test_number_unique_id(hass: HomeAssistant, enable_bluetooth: None):
    """Test that number entities have correct unique IDs."""
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

            entity_humidity = entity_registry.async_get(
                "number.pax_levante_fanspeed_target_humidity"
            )
            assert entity_humidity is not None
            assert entity_humidity.unique_id == "aa:bb:cc:dd:ee:ff_fanspeed_target_humidity"

            entity_light = entity_registry.async_get(
                "number.pax_levante_fanspeed_target_light"
            )
            assert entity_light is not None
            assert entity_light.unique_id == "aa:bb:cc:dd:ee:ff_fanspeed_target_light"

            entity_base = entity_registry.async_get(
                "number.pax_levante_fanspeed_target_base"
            )
            assert entity_base is not None
            assert entity_base.unique_id == "aa:bb:cc:dd:ee:ff_fanspeed_target_base"


async def test_number_device_info(hass: HomeAssistant, enable_bluetooth: None):
    """Test that number entities have correct device info."""
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

            entity = entity_registry.async_get("number.pax_levante_fanspeed_target_humidity")
            assert entity is not None

            device = device_registry.async_get(entity.device_id)
            assert device is not None
            assert device.manufacturer == "Pax"
            assert device.model == "Pax Levante Levante"


async def test_number_multiple_set_values(hass: HomeAssistant, enable_bluetooth: None):
    """Test setting multiple number values."""
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

            # Set humidity target
            await hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": "number.pax_levante_fanspeed_target_humidity",
                    "value": 2100,
                },
                blocking=True,
            )

            mock_client_class.fan_speed_targets = FanSpeedTarget(
                humidity=2100, light=1500, base=950
            )
            await hass.helpers.entity_component.async_update_entity(
                "number.pax_levante_fanspeed_target_humidity"
            )

            # Set light target
            await hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": "number.pax_levante_fanspeed_target_light",
                    "value": 1800,
                },
                blocking=True,
            )

            mock_client_class.fan_speed_targets = FanSpeedTarget(
                humidity=2100, light=1800, base=950
            )
            await hass.helpers.entity_component.async_update_entity(
                "number.pax_levante_fanspeed_target_light"
            )

            # Verify both changes
            state_humidity = hass.states.get("number.pax_levante_fanspeed_target_humidity")
            assert state_humidity.state == "2100"

            state_light = hass.states.get("number.pax_levante_fanspeed_target_light")
            assert state_light.state == "1800"
