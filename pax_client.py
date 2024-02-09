from bleak import BleakClient, BleakError
from dataclasses import dataclass

import struct
from enum import Enum


class CurrentTrigger(Enum):
    BASE = 1
    LIGHT = 2
    HUMIDITY = 3


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

    async def async_get_sensors(self):
        async with BleakClient(self._device) as client:
            raw_sensors = await client.read_gatt_char(35)
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
