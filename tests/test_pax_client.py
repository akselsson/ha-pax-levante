"""Tests for the PaxClient class."""

from unittest.mock import AsyncMock, MagicMock, patch
import struct

import pytest

from custom_components.pax_levante.pax_client import (
    BOOST_HANDLE,
    DEVICE_NAME_HANDLE,
    FAN_SENSITIVITY_HANDLE,
    FAN_SPEED_TARGETS_HANDLE,
    HARDWARE_REVISION_HANDLE,
    MANUFACTURER_NAME_HANDLE,
    MODEL_NUMBER_HANDLE,
    PIN_CHECK_HANDLE,
    PIN_READ_WRITE_HANDLE,
    SENSORS_HANDLE,
    SOFTWARE_REVISION_HANDLE,
    Boost,
    CurrentTrigger,
    FanSensitivity,
    FanSensitivitySetting,
    FanSpeedTarget,
    PaxClient,
    PaxDevice,
    PaxSensors,
)


def test_parse_string():
    response = bytearray(b"Pax Levante\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    expected_result = "Pax Levante"
    assert PaxClient._parse_string(response) == expected_result


def test_parse_sensors_response_BOOST():
    response = bytearray.fromhex("000062003002560917000000")
    expected_result = PaxSensors(
        humidity=0,
        temperature=98,
        light=560,
        fan_speed=2390,
        current_trigger=CurrentTrigger.BOOST,
        boost=True,
        unknown=0,
        raw="000062003002560917000000",
    )
    assert PaxClient._parse_sensors_response(response) == expected_result


def test_parse_sensors_response_AUTOMATIC_VENTILATION():
    response = bytearray.fromhex("0f00610022003d0907000000")
    expected_result = PaxSensors(
        humidity=15,
        temperature=97,
        light=34,
        fan_speed=2365,
        current_trigger=CurrentTrigger.AUTOMATIC_VENTILATION,
        boost=False,
        unknown=0,
        raw="0f00610022003d0907000000",
    )
    assert PaxClient._parse_sensors_response(response) == expected_result


@pytest.fixture
async def pax_client():
    # Setup code for creating a client instance
    client = PaxClient(None)  # Create an instance of PaxClient
    client._client = AsyncMock()  # Mock the _client attribute
    # You can add additional setup here if needed

    yield client  # This client will be used in the tests


async def test_async_check_pin(pax_client):
    pax_client._client.read_gatt_char.return_value = b"\x01"

    assert await pax_client.async_check_pin()

    pax_client._client.read_gatt_char.assert_called_once_with(PIN_CHECK_HANDLE)


async def test_async_get_fan_speed_targets(pax_client):
    pax_client._client.read_gatt_char.return_value = bytearray(b"`\t\xcc\x06\xb6\x03")

    assert await pax_client.async_get_fan_speed_targets() == FanSpeedTarget(
        2400, 1740, 950
    )

    pax_client._client.read_gatt_char.assert_called_once_with(FAN_SPEED_TARGETS_HANDLE)


# Additional tests for sensor parsing edge cases


def test_parse_sensors_response_BASE():
    """Test parsing sensors with BASE trigger."""
    response = bytearray.fromhex("2d00160096009c0501000000")
    expected_result = PaxSensors(
        humidity=45,
        temperature=22,
        light=150,
        fan_speed=1500,
        current_trigger=CurrentTrigger.BASE,
        boost=False,
        unknown=0,
        raw="2d00160096009c0501000000",
    )
    assert PaxClient._parse_sensors_response(response) == expected_result


def test_parse_sensors_response_LIGHT():
    """Test parsing sensors with LIGHT trigger."""
    response = bytearray.fromhex("0500620012003d0902000000")
    expected_result = PaxSensors(
        humidity=5,
        temperature=98,
        light=18,
        fan_speed=2365,
        current_trigger=CurrentTrigger.LIGHT,
        boost=False,
        unknown=0,
        raw="0500620012003d0902000000",
    )
    assert PaxClient._parse_sensors_response(response) == expected_result


def test_parse_sensors_response_HUMIDITY():
    """Test parsing sensors with HUMIDITY trigger."""
    response = bytearray.fromhex("5000600050006409003000000")
    expected_result = PaxSensors(
        humidity=80,
        temperature=96,
        light=80,
        fan_speed=2500,
        current_trigger=CurrentTrigger.HUMIDITY,
        boost=False,
        unknown=0,
        raw="5000600050006409003000000",
    )
    assert PaxClient._parse_sensors_response(response) == expected_result


# Context manager tests


async def test_context_manager_connect():
    """Test that context manager connects to device."""
    mock_ble_client = AsyncMock()

    with patch("custom_components.pax_levante.pax_client.BleakClient") as mock_bleak:
        mock_bleak.return_value = mock_ble_client

        async with PaxClient("AA:BB:CC:DD:EE:FF") as client:
            assert client._client == mock_ble_client
            mock_ble_client.connect.assert_called_once()


async def test_context_manager_disconnect():
    """Test that context manager disconnects from device."""
    mock_ble_client = AsyncMock()

    with patch("custom_components.pax_levante.pax_client.BleakClient") as mock_bleak:
        mock_bleak.return_value = mock_ble_client

        async with PaxClient("AA:BB:CC:DD:EE:FF") as client:
            pass

        mock_ble_client.disconnect.assert_called_once()


# Device info tests


async def test_async_get_device_info(pax_client):
    """Test getting device info."""
    pax_client._client.read_gatt_char.side_effect = [
        b"Levante\x00\x00\x00",  # model
        b"1.0\x00",  # hardware
        b"2.0.1\x00",  # software
        b"Pax\x00",  # manufacturer
        b"Pax Levante\x00",  # name
    ]

    device_info = await pax_client.async_get_device_info()

    assert device_info == PaxDevice(
        manufacturer="Pax",
        model_number="Levante",
        name="Pax Levante",
        sw_version="2.0.1",
        hw_version="1.0",
    )

    assert pax_client._client.read_gatt_char.call_count == 5
    pax_client._client.read_gatt_char.assert_any_call(MODEL_NUMBER_HANDLE)
    pax_client._client.read_gatt_char.assert_any_call(HARDWARE_REVISION_HANDLE)
    pax_client._client.read_gatt_char.assert_any_call(SOFTWARE_REVISION_HANDLE)
    pax_client._client.read_gatt_char.assert_any_call(MANUFACTURER_NAME_HANDLE)
    pax_client._client.read_gatt_char.assert_any_call(DEVICE_NAME_HANDLE)


# Sensors tests


async def test_async_get_sensors(pax_client):
    """Test getting sensor data."""
    sensor_data = bytearray.fromhex("2d00160096009c0501000000")
    pax_client._client.read_gatt_char.return_value = sensor_data

    sensors = await pax_client.async_get_sensors()

    assert sensors.humidity == 45
    assert sensors.temperature == 22
    assert sensors.light == 150
    assert sensors.fan_speed == 1500
    assert sensors.current_trigger == CurrentTrigger.BASE
    assert sensors.boost is False

    pax_client._client.read_gatt_char.assert_called_once_with(SENSORS_HANDLE)


# PIN tests


async def test_async_get_pin(pax_client):
    """Test getting PIN."""
    pax_client._client.read_gatt_char.return_value = b"\x00\x00\x04\xd2"  # 1234

    pin = await pax_client.async_get_pin()

    assert pin == 1234
    pax_client._client.read_gatt_char.assert_called_once_with(PIN_READ_WRITE_HANDLE)


async def test_async_set_pin_success(pax_client):
    """Test setting PIN successfully."""
    pax_client._client.read_gatt_char.return_value = b"\x01"  # PIN check returns True

    result = await pax_client.async_set_pin(5678)

    assert result is True
    pax_client._client.write_gatt_char.assert_called_once_with(
        PIN_READ_WRITE_HANDLE, b"\x00\x00\x16\x2e"
    )
    pax_client._client.read_gatt_char.assert_called_once_with(PIN_CHECK_HANDLE)


async def test_async_set_pin_failure(pax_client):
    """Test setting PIN with incorrect PIN."""
    pax_client._client.read_gatt_char.return_value = b"\x00"  # PIN check returns False

    result = await pax_client.async_set_pin(9999)

    assert result is False


async def test_async_check_pin_true(pax_client):
    """Test PIN check returns True."""
    pax_client._client.read_gatt_char.return_value = b"\x01"

    result = await pax_client.async_check_pin()

    assert result is True
    pax_client._client.read_gatt_char.assert_called_once_with(PIN_CHECK_HANDLE)


async def test_async_check_pin_false(pax_client):
    """Test PIN check returns False."""
    pax_client._client.read_gatt_char.return_value = b"\x00"

    result = await pax_client.async_check_pin()

    assert result is False


# Fan speed target tests


async def test_async_set_fan_speed_targets(pax_client):
    """Test setting fan speed targets."""
    targets = FanSpeedTarget(humidity=2000, light=1500, base=1000)

    await pax_client.async_set_fan_speed_targets(targets)

    pax_client._client.write_gatt_char.assert_called_once()
    call_args = pax_client._client.write_gatt_char.call_args
    assert call_args[0][0] == FAN_SPEED_TARGETS_HANDLE

    # Verify the packed data
    expected_data = struct.pack("<HHH", 2000, 1500, 1000)
    assert bytes(call_args[0][1]) == expected_data


# Fan sensitivity tests


async def test_async_get_fan_sensitivity_both_active(pax_client):
    """Test getting fan sensitivity when both are active."""
    # Both active with medium sensitivity (2)
    pax_client._client.read_gatt_char.return_value = b"\x01\x02\x01\x03"

    sensitivity = await pax_client.async_get_fan_sensitivity()

    assert sensitivity == FanSensitivitySetting(
        humidity=2,  # MEDIUM
        light=3,  # HIGH
    )
    pax_client._client.read_gatt_char.assert_called_once_with(FAN_SENSITIVITY_HANDLE)


async def test_async_get_fan_sensitivity_humidity_disabled(pax_client):
    """Test getting fan sensitivity when humidity is disabled."""
    # Humidity disabled (0), light active with low sensitivity (1)
    pax_client._client.read_gatt_char.return_value = b"\x00\x02\x01\x01"

    sensitivity = await pax_client.async_get_fan_sensitivity()

    assert sensitivity == FanSensitivitySetting(
        humidity=0,  # DISABLED
        light=1,  # LOW
    )


async def test_async_get_fan_sensitivity_both_disabled(pax_client):
    """Test getting fan sensitivity when both are disabled."""
    pax_client._client.read_gatt_char.return_value = b"\x00\x00\x00\x00"

    sensitivity = await pax_client.async_get_fan_sensitivity()

    assert sensitivity == FanSensitivitySetting(
        humidity=0,  # DISABLED
        light=0,  # DISABLED
    )


# Boost tests


async def test_async_get_boost(pax_client):
    """Test getting boost status."""
    # Active (1), fan_speed 2400, time left 900 seconds
    pax_client._client.read_gatt_char.return_value = struct.pack("<BHH", 1, 2400, 900)

    boost = await pax_client.async_get_boost()

    assert boost == Boost(active=True, fan_speed_target=2400, timeleft_seconds=900)
    pax_client._client.read_gatt_char.assert_called_once_with(BOOST_HANDLE)


async def test_async_get_boost_inactive(pax_client):
    """Test getting boost status when inactive."""
    pax_client._client.read_gatt_char.return_value = struct.pack("<BHH", 0, 0, 0)

    boost = await pax_client.async_get_boost()

    assert boost == Boost(active=False, fan_speed_target=0, timeleft_seconds=0)


async def test_async_set_boost_active_defaults(pax_client):
    """Test activating boost with default values."""
    await pax_client.async_set_boost(True)

    pax_client._client.write_gatt_char.assert_called_once()
    call_args = pax_client._client.write_gatt_char.call_args
    assert call_args[0][0] == BOOST_HANDLE

    # Verify defaults: active=True, fan_speed=2400, time=900
    expected_data = struct.pack("<BHH", True, 2400, 900)
    assert bytes(call_args[0][1]) == expected_data


async def test_async_set_boost_active_custom(pax_client):
    """Test activating boost with custom values."""
    await pax_client.async_set_boost(True, fan_speed_target=2200, timeleft_seconds=600)

    pax_client._client.write_gatt_char.assert_called_once()
    call_args = pax_client._client.write_gatt_char.call_args

    expected_data = struct.pack("<BHH", True, 2200, 600)
    assert bytes(call_args[0][1]) == expected_data


async def test_async_set_boost_deactivate(pax_client):
    """Test deactivating boost."""
    await pax_client.async_set_boost(False)

    pax_client._client.write_gatt_char.assert_called_once()
    call_args = pax_client._client.write_gatt_char.call_args

    # When deactivating, defaults to 0 for both fan_speed and time
    expected_data = struct.pack("<BHH", False, 0, 0)
    assert bytes(call_args[0][1]) == expected_data


async def test_async_set_boost_deactivate_with_params(pax_client):
    """Test deactivating boost but with custom params (edge case)."""
    await pax_client.async_set_boost(False, fan_speed_target=1000, timeleft_seconds=300)

    call_args = pax_client._client.write_gatt_char.call_args
    expected_data = struct.pack("<BHH", False, 1000, 300)
    assert bytes(call_args[0][1]) == expected_data
