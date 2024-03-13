"""Tests for the PaxClient class."""

from unittest.mock import AsyncMock

import pytest

from custom_components.pax_levante.pax_client import (
    FAN_SPEED_TARGETS_HANDLE,
    PIN_CHECK_HANDLE,
    CurrentTrigger,
    FanSpeedTarget,
    PaxClient,
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
