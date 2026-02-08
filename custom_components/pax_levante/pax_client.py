from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection
from dataclasses import dataclass
import logging
import struct
from enum import Enum

_LOGGER = logging.getLogger(__name__)

# Constants for GATT Characteristic UUIDs
# Standard Bluetooth SIG UUIDs
SERIAL_NUMBER_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
HARDWARE_REVISION_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
SOFTWARE_REVISION_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
MANUFACTURER_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"
# Pax-specific UUIDs (from pycalima / ha-pax_ble)
SENSORS_UUID = "528b80e8-c47a-4c0a-bdf1-916a7748f412"
PIN_READ_WRITE_UUID = "4cad343a-209a-40b7-b911-4d9b3df569b2"
PIN_CHECK_UUID = "d1ae6b70-ee12-4f6d-b166-d2063dcaffe1"
FAN_SPEED_TARGETS_UUID = "1488a757-35bc-4ec8-9a6b-9ecf1502778e"
FAN_SENSITIVITY_UUID = "e782e131-6ce1-4191-a8db-f4304d7610f1"
BOOST_UUID = "118c949c-28c8-4139-b0b3-36657fd055a9"

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
    def __init__(self, device, use_services_cache=True):
        self._device = device
        self._client = None
        self._use_services_cache = use_services_cache

    async def __aenter__(self):
        self._client = await establish_connection(
            BleakClient,
            self._device,
            self._device.name or "Pax Levante",
            use_services_cache=self._use_services_cache,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.disconnect()
        self._client = None

    async def async_get_device_info(self) -> PaxDevice:
        model_number = await self._read_string(self._client, MODEL_NUMBER_UUID)
        hardware_revision = await self._read_string(
            self._client, HARDWARE_REVISION_UUID
        )
        software_revision = await self._read_string(
            self._client, SOFTWARE_REVISION_UUID
        )
        manufacturer_name = await self._read_string(
            self._client, MANUFACTURER_NAME_UUID
        )
        name = await self._read_string(self._client, DEVICE_NAME_UUID)

        return PaxDevice(
            manufacturer_name,
            model_number,
            name,
            software_revision,
            hardware_revision,
        )

    async def async_get_sensors(self) -> PaxSensors:
        raw_sensors = await self._client.read_gatt_char(SENSORS_UUID)
        return self._parse_sensors_response(raw_sensors)

    async def async_get_pin(self) -> int:
        return int.from_bytes(
            await self._client.read_gatt_char(PIN_READ_WRITE_UUID), "big"
        )

    async def async_set_pin(self, pin) -> bool:
        await self._client.write_gatt_char(
            PIN_READ_WRITE_UUID, pin.to_bytes(4, byteorder="big")
        )
        return await self.async_check_pin()

    async def async_check_pin(self) -> bool:
        return (
            int.from_bytes(await self._client.read_gatt_char(PIN_CHECK_UUID), "big")
            == 1
        )

    async def async_get_fan_speed_targets(self) -> FanSpeedTarget:
        response = await self._client.read_gatt_char(FAN_SPEED_TARGETS_UUID)
        return FanSpeedTarget(*struct.unpack("<HHH", response))

    async def async_set_fan_speed_targets(self, targets: FanSpeedTarget) -> bool:
        return await self._client.write_gatt_char(
            FAN_SPEED_TARGETS_UUID,
            bytearray(
                struct.pack("<HHH", targets.humidity, targets.light, targets.base)
            ),
        )

    async def async_get_fan_sensitivity(self) -> FanSensitivitySetting:
        response = await self._client.read_gatt_char(FAN_SENSITIVITY_UUID)
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
        response = await self._client.read_gatt_char(BOOST_UUID)
        return Boost(*struct.unpack("<BHH", response))

    async def async_set_boost(
        self,
        active: bool,
        fan_speed_target: int | None = None,
        timeleft_seconds: int | None = None,
    ) -> bool:
        return await self._client.write_gatt_char(
            BOOST_UUID,
            bytearray(
                struct.pack(
                    "<BHH",
                    active,
                    fan_speed_target or (2400 if active else 0),
                    timeleft_seconds or (900 if active else 0),
                )
            ),
        )

    async def async_log_services(self):
        for service in self._client.services:
            _LOGGER.debug(
                "Service: %s (%s)", service.uuid, service.description
            )
            for char in service.characteristics:
                _LOGGER.debug(
                    "  Characteristic: %s (%s) | Properties: %s",
                    char.uuid,
                    char.description,
                    ", ".join(char.properties),
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
