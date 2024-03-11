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
FAN_SPEED_TARGETS_HANDLE = 42
FAN_SENSITIVITY_HANDLE = 44
BOOST_HANDLE = 50

# Constants for Sensor Data Parsing
BOOST_BIT_POSITION = 4  # The position of the boost flag in the current_trigger byte
TRIGGER_VALUE_MASK = 0xF  # Mask to extract the current trigger value


class CurrentTrigger(Enum):
    BASE = 1
    LIGHT = 2
    HUMIDITY = 3
    AUTOMATIC_VENTILATION = 7
    BOOST = 17


@dataclass
class FanSpeedTarget:
    humidity: int
    light: int
    base: int


class FanSensitivity(Enum):
    DISABLED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class FanSensitivitySetting:
    humidity: FanSensitivity
    light: FanSensitivity


@dataclass
class Boost:
    active: bool
    fan_speed_target: int
    timeleft_seconds: int


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

    async def async_get_fan_speed_targets(self) -> FanSpeedTarget:
        response = await self._client.read_gatt_char(FAN_SPEED_TARGETS_HANDLE)
        return FanSpeedTarget(*struct.unpack("<HHH", response))

    async def async_set_fan_speed_targets(self, targets: FanSpeedTarget) -> bool:
        return await self._client.write_gatt_char(
            FAN_SPEED_TARGETS_HANDLE,
            bytearray(
                struct.pack("<HHH", targets.humidity, targets.light, targets.base)
            ),
        )

    async def async_get_fan_sensitivity(self) -> FanSensitivitySetting:
        response = await self._client.read_gatt_char(FAN_SENSITIVITY_HANDLE)
        (
            humidity_active,
            humidity_sensitivity,
            prescense_active,
            prescense_sensitivity,
        ) = struct.unpack("<BBBB", response)
        return FanSensitivitySetting(
            0 if humidity_active == 0 else humidity_sensitivity,
            0 if prescense_active == 0 else prescense_sensitivity,
        )

    async def async_get_boost(self) -> bool:
        response = await self._client.read_gatt_char(BOOST_HANDLE)
        return Boost(*struct.unpack("<BHH", response))

    async def async_set_boost(
        self,
        active: bool,
        fan_speed_target: int | None = None,
        timeleft_seconds: int | None = None,
    ) -> bool:
        return await self._client.write_gatt_char(
            BOOST_HANDLE,
            bytearray(
                struct.pack(
                    "<BHH",
                    active,
                    fan_speed_target or (2400 if active else 0),
                    timeleft_seconds or (900 if active else 0),
                )
            ),
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
        ) = struct.unpack("<HHHHHH", raw_sensors)
        return PaxSensors(
            humidity,
            temperature,
            light,
            fan_speed,
            (
                CurrentTrigger.BOOST
                if current_trigger >> BOOST_BIT_POSITION == 1
                else CurrentTrigger(current_trigger & TRIGGER_VALUE_MASK)
            ),
            current_trigger >> BOOST_BIT_POSITION == 1,
            unknown,
            raw_sensors.hex(),
        )
