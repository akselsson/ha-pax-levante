"""Tests for the PaxClient class."""

from custom_components.pax_levante.pax_client import (
    CurrentTrigger,
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
