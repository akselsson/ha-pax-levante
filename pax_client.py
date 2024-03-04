from bleak import BleakClient, BleakError
from dataclasses import dataclass
import struct
from enum import Enum

# Constants for GATT Characteristic Handles
SERIAL_NUMBER_HANDLE = 11
MODEL_NUMBER_HANDLE = 13
HARDWARE_REVISION_HANDLE = 15
SOFTWARE_REVISION_HANDLE = 19
MANUFACTURER_NAME_HANDLE = 21
DEVICE_NAME_HANDLE = 28
SENSORS_HANDLE = 35
PIN_READ_WRITE_HANDLE = 24
PIN_CHECK_HANDLE = 26

# Constants for Sensor Data Parsing
BOOST_BIT_POSITION = 4  # The position of the boost flag in the current_trigger byte
TRIGGER_VALUE_MASK = 0xF  # Mask to extract the current trigger value


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
        self._client = None

    async def __aenter__(self):
        self._client = BleakClient(self._device)
        await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.disconnect()
        self._client = None

    async def async_get_device_info(self) -> PaxDevice:
        serial_number = await self._read_string(self._client, SERIAL_NUMBER_HANDLE)
        model_number = await self._read_string(self._client, MODEL_NUMBER_HANDLE)
        hardware_revision = await self._read_string(
            self._client, HARDWARE_REVISION_HANDLE
        )
        software_revision = await self._read_string(
            self._client, SOFTWARE_REVISION_HANDLE
        )
        manufacturer_name = await self._read_string(
            self._client, MANUFACTURER_NAME_HANDLE
        )
        name = await self._read_string(self._client, DEVICE_NAME_HANDLE)

        return PaxDevice(
            manufacturer_name,
            model_number,
            name,
            software_revision,
            hardware_revision,
        )

    async def async_get_sensors(self) -> PaxSensors:
        raw_sensors = await self._client.read_gatt_char(SENSORS_HANDLE)
        return self._parse_sensors_response(raw_sensors)

    async def async_get_pin(self) -> int:
        return int.from_bytes(
            await self._client.read_gatt_char(PIN_READ_WRITE_HANDLE), "big"
        )

    async def async_set_pin(self, pin) -> bool:
        await self._client.write_gatt_char(
            PIN_READ_WRITE_HANDLE, pin.to_bytes(4, byteorder="big")
        )
        return await self.async_check_pin()

    async def async_check_pin(self) -> bool:
        return (
            int.from_bytes(await self._client.read_gatt_char(PIN_CHECK_HANDLE), "big")
            == 1
        )

    async def _read_string(self, client, handle) -> str:
        response = await client.read_gatt_char(handle)
        return self._parse_string(response)

    @staticmethod
    def _parse_string(response: bytes) -> str:
        return response.decode("utf-8").split("\x00")[0]

    @staticmethod
    def _parse_sensors_response(raw_sensors: bytes) -> PaxSensors:
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
            CurrentTrigger(current_trigger & TRIGGER_VALUE_MASK),
            current_trigger >> BOOST_BIT_POSITION == 1,
            unknown,
            unknown2,
            raw_sensors.hex(),
        )
