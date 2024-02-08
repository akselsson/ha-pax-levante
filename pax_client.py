from bleak import BleakClient, BleakError

import struct

class PaxSensors:
    fan_speed: int
    humidity: int
    temperature: int

class PaxClient:
    def __init__(self, device):
        self._device = device

    async def async_get_sensors(self):
        async with BleakClient(self._device) as client:
            raw_sensors = await client.read_gatt_char(35)
            humidity, temperature, light, fan_speed, current_trigger, tbd = struct.unpack(
                "HHHHHH", await client.read_gatt_char(35)
            )
            return PaxSensors(fan_speed, humidity, temperature)