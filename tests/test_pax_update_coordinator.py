"""Tests for the PaxUpdateCoordinator class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.pax_levante.pax_client import (
    CurrentTrigger,
    FanSpeedTarget,
    PaxDevice,
    PaxSensors,
)
from custom_components.pax_levante.pax_update_coordinator import PaxUpdateCoordinator


@pytest.fixture
def mock_device_info():
    """Return mock device info."""
    return PaxDevice(
        manufacturer="Pax",
        model_number="Levante",
        name="Pax Levante",
        sw_version="1.0.0",
        hw_version="1.0",
    )


@pytest.fixture
def mock_sensors():
    """Return mock sensor data."""
    return PaxSensors(
        humidity=45,
        temperature=22,
        light=150,
        fan_speed=1500,
        current_trigger=CurrentTrigger.BASE,
        boost=False,
        unknown=0,
        raw="2d00160096009c050001000000",
    )


@pytest.fixture
def mock_fan_speed_targets():
    """Return mock fan speed targets."""
    return FanSpeedTarget(humidity=2000, light=1500, base=950)


async def test_coordinator_initialization(hass: HomeAssistant):
    """Test coordinator initialization."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)

    assert coordinator.address == "AA:BB:CC:DD:EE:FF"
    assert coordinator.pin == 1234
    assert coordinator.device_info is None
    assert coordinator.sensors is None
    assert coordinator.fan_speed_targets is None
    assert coordinator.update_interval.total_seconds() == 65


async def test_async_update_data_success(
    hass: HomeAssistant, mock_device_info, mock_sensors, mock_fan_speed_targets
):
    """Test successful data update."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)

    mock_client = AsyncMock()
    mock_client.async_get_device_info.return_value = mock_device_info
    mock_client.async_get_sensors.return_value = mock_sensors
    mock_client.async_get_fan_speed_targets.return_value = mock_fan_speed_targets

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await coordinator._async_update_data()

        assert result == mock_sensors
        assert coordinator.device_info == mock_device_info
        assert coordinator.sensors == mock_sensors
        assert coordinator.fan_speed_targets == mock_fan_speed_targets
        mock_client.async_get_device_info.assert_called_once()
        mock_client.async_get_sensors.assert_called_once()
        mock_client.async_get_fan_speed_targets.assert_called_once()


async def test_async_update_data_subsequent_call_skips_device_info(
    hass: HomeAssistant, mock_device_info, mock_sensors, mock_fan_speed_targets
):
    """Test that device info is only fetched once."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info  # Already set

    mock_client = AsyncMock()
    mock_client.async_get_sensors.return_value = mock_sensors
    mock_client.async_get_fan_speed_targets.return_value = mock_fan_speed_targets

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await coordinator._async_update_data()

        assert result == mock_sensors
        mock_client.async_get_device_info.assert_not_called()
        mock_client.async_get_sensors.assert_called_once()
        mock_client.async_get_fan_speed_targets.assert_called_once()


async def test_async_update_data_timeout(hass: HomeAssistant):
    """Test timeout handling during update."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)

    mock_client = AsyncMock()
    mock_client.async_get_device_info.side_effect = TimeoutError("Connection timeout")

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(UpdateFailed, match="Unable to fetch data"):
            await coordinator._async_update_data()


async def test_async_update_data_connection_error(hass: HomeAssistant):
    """Test connection error handling during update."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.side_effect = Exception(
            "Connection failed"
        )

        with pytest.raises(UpdateFailed, match="Unable to fetch data"):
            await coordinator._async_update_data()


async def test_async_set_fan_speed_target_success(
    hass: HomeAssistant, mock_device_info, mock_sensors, mock_fan_speed_targets
):
    """Test successfully setting fan speed target."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors
    coordinator.fan_speed_targets = mock_fan_speed_targets

    new_targets = FanSpeedTarget(humidity=2200, light=1500, base=950)
    mock_client = AsyncMock()
    mock_client.async_set_pin.return_value = True
    mock_client.async_set_fan_speed_targets.return_value = True
    mock_client.async_get_fan_speed_targets.return_value = new_targets

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await coordinator.async_set_fan_speed_target("humidity", 2200)

        assert result == mock_sensors
        assert coordinator.fan_speed_targets.humidity == 2200
        mock_client.async_set_pin.assert_called_once_with(1234)
        mock_client.async_set_fan_speed_targets.assert_called_once()
        call_args = mock_client.async_set_fan_speed_targets.call_args[0][0]
        assert call_args.humidity == 2200
        assert call_args.light == 1500
        assert call_args.base == 950


async def test_async_set_fan_speed_target_no_pin(
    hass: HomeAssistant, mock_device_info, mock_sensors, mock_fan_speed_targets
):
    """Test setting fan speed target fails when PIN is 0."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 0)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors
    coordinator.fan_speed_targets = mock_fan_speed_targets

    with pytest.raises(UpdateFailed, match="Pin not set"):
        await coordinator.async_set_fan_speed_target("humidity", 2200)


async def test_async_set_fan_speed_target_no_current_targets(
    hass: HomeAssistant, mock_device_info, mock_sensors
):
    """Test setting fan speed target fails when current targets unavailable."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors
    coordinator.fan_speed_targets = None

    with pytest.raises(
        UpdateFailed, match="Unable to set fan speed targets, current target not available"
    ):
        await coordinator.async_set_fan_speed_target("humidity", 2200)


async def test_async_set_fan_speed_target_invalid_pin(
    hass: HomeAssistant, mock_device_info, mock_sensors, mock_fan_speed_targets
):
    """Test setting fan speed target fails with invalid PIN."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors
    coordinator.fan_speed_targets = mock_fan_speed_targets

    mock_client = AsyncMock()
    mock_client.async_set_pin.return_value = False

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(UpdateFailed, match="Unable to set pin"):
            await coordinator.async_set_fan_speed_target("humidity", 2200)


async def test_async_set_boost_success(
    hass: HomeAssistant, mock_device_info, mock_sensors
):
    """Test successfully setting boost."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors

    new_sensors = PaxSensors(
        humidity=45,
        temperature=22,
        light=150,
        fan_speed=2400,
        current_trigger=CurrentTrigger.BOOST,
        boost=True,
        unknown=0,
        raw="2d00160096006009011000000",
    )

    mock_client = AsyncMock()
    mock_client.async_set_pin.return_value = True
    mock_client.async_set_boost.return_value = True
    mock_client.async_get_sensors.return_value = new_sensors

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await coordinator.async_set_boost(True)

        assert result == new_sensors
        assert coordinator.sensors == new_sensors
        mock_client.async_set_pin.assert_called_once_with(1234)
        mock_client.async_set_boost.assert_called_once_with(True)
        mock_client.async_get_sensors.assert_called_once()


async def test_async_set_boost_no_pin(hass: HomeAssistant, mock_device_info, mock_sensors):
    """Test setting boost fails when PIN is 0."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 0)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors

    with pytest.raises(UpdateFailed, match="Pin not set"):
        await coordinator.async_set_boost(True)


async def test_async_set_boost_invalid_pin(
    hass: HomeAssistant, mock_device_info, mock_sensors
):
    """Test setting boost fails with invalid PIN."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors

    mock_client = AsyncMock()
    mock_client.async_set_pin.return_value = False

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(UpdateFailed, match="Unable to set pin"):
            await coordinator.async_set_boost(True)


async def test_async_set_boost_timeout(hass: HomeAssistant, mock_device_info, mock_sensors):
    """Test timeout handling when setting boost."""
    coordinator = PaxUpdateCoordinator(hass, "AA:BB:CC:DD:EE:FF", 1234)
    coordinator.device_info = mock_device_info
    coordinator.sensors = mock_sensors

    mock_client = AsyncMock()
    mock_client.async_set_pin.side_effect = TimeoutError("Connection timeout")

    with patch(
        "custom_components.pax_levante.pax_update_coordinator.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(Exception):
            await coordinator.async_set_boost(True)
