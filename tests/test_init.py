"""Test the setup of the component."""

from homeassistant.setup import async_setup_component
import pytest

from custom_components.pax_levante.const import DOMAIN


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    return True


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_async_setup(hass, enable_bluetooth):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True
