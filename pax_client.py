from bleak import BleakClient, BleakError
from dataclasses import dataclass

import struct
from enum import Enum


class CurrentTrigger(Enum):
    BASE = 1
    LIGHT = 2
    HUMIDITY = 3
    AUTOMATIC_VENTILATION = 7

@dataclass
class PaxDevice:
    manufacturer: str | None
    model_number: str | None
    name: str | None
    sw_version: str | None
    hw_version: str | None


@dataclass
class PaxSensors:
    humidity: int
    temperature: int
    light: int
    fan_speed: int
    current_trigger: CurrentTrigger
    boost: bool
    unknown: int
    unknown2: int
    raw: str


class PaxClient:
    def __init__(self, device):
        self._device = device

    async def async_get_device_info(self) -> PaxDevice:
        async with BleakClient(self._device) as client:
            serial_number = await self._read_string(client, 11)
            model_number = await self._read_string(client, 13)
            hardware_revision = await self._read_string(client, 15)
            software_revision = await self._read_string(client, 19)
            manufacturer_name = await self._read_string(client, 21)
            name = await self._read_string(client, 28)

            return PaxDevice(
                manufacturer_name,
                model_number,
                name,
                software_revision,
                hardware_revision,
            )

    async def _read_string(self, client, handle):
        response = (await client.read_gatt_char(handle))
        return self._parse_string(response)

    def _parse_string(self, response):
        return response.decode("utf-8").split("\x00")[0]

    async def async_get_sensors(self) -> PaxSensors:
        async with BleakClient(self._device) as client:
            raw_sensors = await client.read_gatt_char(35)
            return self._parse_sensors_response(raw_sensors)

    def _parse_sensors_response(self, raw_sensors):
        (
                humidity,
                temperature,
                light,
                fan_speed,
                current_trigger,
                unknown,
                unknown2,
            ) = struct.unpack("HHHHBBH", raw_sensors)
        return PaxSensors(
                humidity,
                temperature,
                light,
                fan_speed,
                CurrentTrigger(current_trigger % 16),
                current_trigger >> 4 == 1,
                unknown,
                unknown2,
                raw_sensors.hex(),
            )
    
    async def get_pin(self) -> int:
        async with BleakClient(self._device) as client:
            return int.from_bytes(await client.read_gatt_char(24))
