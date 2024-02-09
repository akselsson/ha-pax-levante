from bleak import BleakClient, BleakError
from dataclasses import dataclass

import struct


@dataclass
class PaxSensors:
    fan_speed: int
    humidity: int
    temperature: int
    light: int
    current_trigger: int
    tbd: int
    raw: str


class PaxClient:
    def __init__(self, device):
        self._device = device

    async def async_get_sensors(self):
        async with BleakClient(self._device) as client:
            raw_sensors = await client.read_gatt_char(35)
            humidity, temperature, light, fan_speed, current_trigger, tbd = (
                struct.unpack("HHHHHH", raw_sensors)
            )
            return PaxSensors(
                fan_speed,
                humidity,
                temperature,
                light,
                current_trigger,
                tbd,
                raw_sensors.hex(),
            )
