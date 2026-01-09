"""Test configuration."""
import os
import sys

# Set timezone to a valid IANA timezone
os.environ.setdefault("TZ", "America/Los_Angeles")

# Patch the US/Pacific timezone to work with newer zoneinfo
import pytest
from unittest.mock import patch
from zoneinfo import ZoneInfo


@pytest.fixture(autouse=True)
def patch_timezone():
    """Patch timezone handling to support legacy US/Pacific format."""
    original_get_time_zone = None

    try:
        from homeassistant.util import dt as dt_util
        original_get_time_zone = dt_util.get_time_zone

        def patched_get_time_zone(time_zone_str):
            """Get time zone, handling legacy US/Pacific format."""
            # Map legacy timezones to IANA timezones
            legacy_map = {
                "US/Pacific": "America/Los_Angeles",
                "US/Eastern": "America/New_York",
                "US/Central": "America/Chicago",
                "US/Mountain": "America/Denver",
            }

            # Use mapped timezone if it's a legacy format
            mapped_tz = legacy_map.get(time_zone_str, time_zone_str)
            return original_get_time_zone(mapped_tz)

        dt_util.get_time_zone = patched_get_time_zone
        yield
        dt_util.get_time_zone = original_get_time_zone
    except ImportError:
        yield
