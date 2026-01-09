"""Tests for the Pax Levante config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfo
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.pax_levante.config_flow import PaxConfigFlow
from custom_components.pax_levante.const import DOMAIN


@pytest.fixture
def mock_bluetooth_service_info():
    """Return mock Bluetooth service info."""
    return BluetoothServiceInfo(
        name="Pax Levante",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=["12345678-1234-1234-1234-123456789012"],
        source="local",
    )


async def test_bluetooth_discovery(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test the bluetooth discovery flow."""
    flow = PaxConfigFlow()
    flow.hass = hass

    result = await flow.async_step_bluetooth(mock_bluetooth_service_info)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "add_device"
    assert flow.discovery_info == mock_bluetooth_service_info


async def test_bluetooth_discovery_sets_unique_id(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test that bluetooth discovery sets unique ID."""
    flow = PaxConfigFlow()
    flow.hass = hass

    await flow.async_step_bluetooth(mock_bluetooth_service_info)

    assert flow.unique_id == "AA:BB:CC:DD:EE:FF"


async def test_bluetooth_discovery_duplicate_aborts(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test that duplicate discovery aborts."""
    # First, create an existing entry
    entry = MagicMock()
    entry.unique_id = "AA:BB:CC:DD:EE:FF"

    flow = PaxConfigFlow()
    flow.hass = hass

    with patch.object(
        flow,
        "_async_current_entries",
        return_value=[entry],
    ):
        result = await flow.async_step_bluetooth(mock_bluetooth_service_info)

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_add_device_form_display(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test that the add device form displays correctly."""
    flow = PaxConfigFlow()
    flow.hass = hass
    flow.discovery_info = mock_bluetooth_service_info

    mock_client = AsyncMock()
    mock_client.async_get_pin.return_value = 1234

    with patch(
        "custom_components.pax_levante.config_flow.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await flow.async_step_add_device()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "add_device"
        assert "mac" in result["data_schema"].schema
        assert "pin" in result["data_schema"].schema
        mock_client.async_get_pin.assert_called_once()


async def test_add_device_form_default_values(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test that the add device form has correct default values."""
    flow = PaxConfigFlow()
    flow.hass = hass
    flow.discovery_info = mock_bluetooth_service_info

    mock_client = AsyncMock()
    mock_client.async_get_pin.return_value = 5678

    with patch(
        "custom_components.pax_levante.config_flow.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await flow.async_step_add_device()

        # Extract default values from schema
        schema_dict = {key.schema: key for key in result["data_schema"].schema}
        mac_key = [k for k in schema_dict.keys() if schema_dict[k] == "mac"][0]
        pin_key = [k for k in schema_dict.keys() if schema_dict[k] == "pin"][0]

        assert mac_key.default() == "AA:BB:CC:DD:EE:FF"
        assert pin_key.default() == 5678


async def test_add_device_submit_success(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test successful device addition."""
    flow = PaxConfigFlow()
    flow.hass = hass
    flow.discovery_info = mock_bluetooth_service_info

    user_input = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "pin": 1234,
    }

    result = await flow.async_step_add_device(user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Pax Levante"
    assert result["data"] == {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        "pin": 1234,
    }


async def test_add_device_submit_custom_values(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test device addition with custom MAC and PIN."""
    flow = PaxConfigFlow()
    flow.hass = hass
    flow.discovery_info = mock_bluetooth_service_info

    user_input = {
        "mac": "11:22:33:44:55:66",
        "pin": 9999,
    }

    result = await flow.async_step_add_device(user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_ADDRESS: "11:22:33:44:55:66",
        "pin": 9999,
    }


async def test_add_device_connection_error(
    hass: HomeAssistant, mock_bluetooth_service_info
):
    """Test handling of connection errors during PIN retrieval."""
    flow = PaxConfigFlow()
    flow.hass = hass
    flow.discovery_info = mock_bluetooth_service_info

    mock_client = AsyncMock()
    mock_client.async_get_pin.side_effect = Exception("Connection failed")

    with patch(
        "custom_components.pax_levante.config_flow.PaxClient"
    ) as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        with pytest.raises(Exception, match="Connection failed"):
            await flow.async_step_add_device()


async def test_flow_version():
    """Test that the flow has correct version."""
    flow = PaxConfigFlow()
    assert flow.VERSION == 1
    assert flow.MINOR_VERSION == 1


async def test_flow_domain():
    """Test that the flow has correct domain."""
    flow = PaxConfigFlow()
    assert flow.__class__.__dict__["domain"] == DOMAIN
