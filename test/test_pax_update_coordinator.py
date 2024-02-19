import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pax_update_coordinator import (
    PaxUpdateCoordinator,
)


class TestPaxUpdateCoordinator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.address = "test_address"
        self.coordinator = PaxUpdateCoordinator(self.hass, self.address)

    def test_init(self):
        self.assertEqual(self.coordinator.hass, self.hass)
        self.assertEqual(self.coordinator.address, self.address)

    @patch(
        "your_module.async_timeout.timeout", new_callable=AsyncMock
    )  # replace with your actual module
    @patch(
        "your_module.bluetooth.async_ble_device_from_address",
        new_callable=AsyncMock,
    )  # replace with your actual module
    @patch(
        "your_module.PaxClient", new_callable=AsyncMock
    )  # replace with your actual module
    async def test_async_update_data(
        self, mock_pax_client, mock_ble_device, mock_timeout
    ):
        mock_pax_client.return_value.async_get_sensors = AsyncMock(
            return_value="test_data"
        )
        data = await self.coordinator._async_update_data()
        self.assertEqual(data, "test_data")
        mock_timeout.assert_called_once_with(10)
        mock_ble_device.assert_called_once_with(self.hass, self.address)
        mock_pax_client.assert_called_once_with(mock_ble_device.return_value)

    @patch(
        "your_module.async_timeout.timeout", new_callable=AsyncMock
    )  # replace with your actual module
    @patch(
        "your_module.bluetooth.async_ble_device_from_address",
        new_callable=AsyncMock,
    )  # replace with your actual module
    @patch(
        "your_module.PaxClient", new_callable=AsyncMock
    )  # replace with your actual module
    async def test_async_update_data_exception(
        self, mock_pax_client, mock_ble_device, mock_timeout
    ):
        mock_pax_client.return_value.async_get_sensors = AsyncMock(
            side_effect=Exception("test_error")
        )
        with self.assertRaises(Exception):
            await self.coordinator._async_update_data()
        mock_timeout.assert_called_once_with(10)
        mock_ble_device.assert_called_once_with(self.hass, self.address)
        mock_pax_client.assert_called_once_with(mock_ble_device.return_value)
