from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture(name="enable_bluetooth")
async def mock_enable_bluetooth(
    hass: HomeAssistant,
    mock_bleak_scanner_start: MagicMock,
    mock_bluetooth_adapters: None,
):
    """Fixture to mock starting the bleak scanner."""
    entry = MockConfigEntry(domain="bluetooth", unique_id="00:00:00:00:00:01")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
