# CLAUDE.md - AI Assistant Guide for ha-pax-levante

## Project Overview

This repository contains a **Home Assistant custom component** that integrates **Pax Levante Bluetooth ventilation fans** into Home Assistant. The integration provides local polling control over fan speed, sensors (humidity, temperature, light), and boost mode.

**Key Facts:**
- **Platform**: Home Assistant Custom Component (HACS compatible)
- **Communication**: Bluetooth Low Energy (BLE) via Bleak library
- **Language**: Python 3.11+
- **Integration Type**: Local polling (no cloud dependency)
- **Discovery**: Automatic Bluetooth discovery
- **Domain**: `pax_levante`

## Repository Structure

```
ha-pax-levante/
├── custom_components/
│   └── pax_levante/           # Main integration code
│       ├── __init__.py        # Integration setup and entry point
│       ├── config_flow.py     # Configuration flow for device setup
│       ├── const.py           # Constants (just DOMAIN)
│       ├── pax_client.py      # BLE client for Pax device communication
│       ├── pax_update_coordinator.py  # Data update coordinator
│       ├── sensor.py          # Sensor entities (humidity, temp, light, fan_speed, etc.)
│       ├── number.py          # Number entities (fan speed targets)
│       ├── switch.py          # Switch entities (boost mode)
│       ├── manifest.json      # Integration metadata
│       ├── strings.json       # UI strings
│       └── translations/
│           └── en.json        # English translations
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_init.py
│   ├── test_pax_client.py
│   ├── test_switch.py
│   └── bandit.yaml
├── .github/workflows/         # CI/CD
│   ├── pythonpackage.yaml     # Main test workflow
│   └── hassfest.yaml          # Home Assistant validation
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── setup.cfg                  # Tool configurations (pytest, flake8, isort, mypy)
├── requirements.txt           # Runtime dependencies
├── requirements.test.txt      # Test dependencies
├── hacs.json                  # HACS metadata
└── README.md                  # User documentation
```

## Architecture Overview

### Core Components

1. **PaxClient** (`pax_client.py`): Low-level BLE communication
   - Async context manager for BLE connections
   - GATT characteristic handles for device attributes
   - Data parsing for sensor values, fan settings, boost mode
   - Data classes: `PaxDevice`, `PaxSensors`, `FanSpeedTarget`, `Boost`, `FanSensitivitySetting`
   - Enums: `CurrentTrigger`, `FanSensitivity`

2. **PaxUpdateCoordinator** (`pax_update_coordinator.py`): Data coordination
   - Inherits from `DataUpdateCoordinator`
   - 65-second polling interval (line 20)
   - Manages device info, sensors, and fan speed targets
   - Handles PIN authentication for write operations
   - Methods: `_async_update_data()`, `async_set_fan_speed_target()`, `async_set_boost()`

3. **Platform Entities**:
   - **Sensors** (`sensor.py`): fan_speed, humidity, temperature, light, current_trigger, boost
   - **Numbers** (`number.py`): fanspeed_target_humidity, fanspeed_target_light, fanspeed_target_base
   - **Switches** (`switch.py`): boost toggle

4. **Config Flow** (`config_flow.py`): Bluetooth discovery and setup
   - Automatic discovery via `async_step_bluetooth()`
   - PIN configuration during setup
   - Unique ID based on MAC address

### Data Flow

```
Bluetooth Device
    ↓
PaxClient (BLE Communication)
    ↓
PaxUpdateCoordinator (65s polling)
    ↓
Entity Updates (Sensors, Numbers, Switches)
    ↓
Home Assistant UI
```

## Development Conventions

### Code Style

1. **Python Version**: 3.11+ (see `.github/workflows/pythonpackage.yaml:11`)
2. **Formatting**: Black (line length: 88)
3. **Import Order**: isort with Home Assistant conventions (setup.cfg:38-56)
4. **Type Hints**: Required (Python 3.7+ annotations)
5. **Linting**: flake8 with specific ignores (E501, W503, E203, D103, D202, W504)
6. **Security**: Bandit scanning enabled
7. **Async**: All I/O operations must be async

### Import Conventions

Order (from `setup.cfg:52`):
```python
from __future__ import annotations  # Always first

# Standard library
import logging
from datetime import timedelta

# Third-party
import async_timeout
from bleak import BleakClient, BleakError

# Home Assistant
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

# Local
from .const import DOMAIN
from .pax_client import PaxClient
```

### Entity Patterns

All entities follow this structure:
- Inherit from `CoordinatorEntity` and appropriate entity base class
- Use `entity_description` for metadata
- Unique ID format: `{MAC_ADDRESS}_{entity_key}`
- Device info with Bluetooth connection
- Override `native_value` for sensors, `is_on` for switches

### Logging

Use module-level logger:
```python
_LOGGER = logging.getLogger(__name__)
```

Log levels:
- `debug`: Connection events, data updates
- `info`: Device discovery, entity creation
- `warning`: Recoverable errors
- `error`: Unrecoverable errors

### Error Handling

- Use `UpdateFailed` for coordinator errors
- Use `ConfigEntryNotReady` for setup failures
- Always include context in error messages
- Use `async_timeout.timeout(10)` for BLE operations

## Testing

### Test Structure

- **Framework**: pytest with pytest-homeassistant-custom-component
- **Async Mode**: Auto (setup.cfg:15)
- **Coverage**: Enabled with exclusions for common patterns
- **Location**: `tests/` directory

### Running Tests

```bash
# Install dependencies
pip install -r requirements.test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components

# Run specific test file
pytest tests/test_pax_client.py
```

### Test Patterns

1. **Unit Tests**: Test individual functions (e.g., `test_parse_string()`)
2. **Mock BLE**: Use `AsyncMock` for `_client` attribute
3. **Fixtures**: Use pytest fixtures for client setup
4. **Async Tests**: All async functions use `async def test_...()`

Example:
```python
@pytest.fixture
async def pax_client():
    client = PaxClient(None)
    client._client = AsyncMock()
    yield client

async def test_async_check_pin(pax_client):
    pax_client._client.read_gatt_char.return_value = b"\x01"
    assert await pax_client.async_check_pin()
```

### Mocking Bluetooth

In tests, Bluetooth must be mocked to avoid hardware dependencies:
```python
from unittest.mock import AsyncMock, patch

# Mock bluetooth module
with patch('homeassistant.components.bluetooth'):
    # Test code here
```

## Git Workflow

### Branch Strategy

- **Main branch**: Production-ready code
- **Feature branches**: Named `claude/feature-name-{session-id}`
- All development happens on feature branches
- PRs are required for merging to main

### Commit Messages

Follow conventional commits style:
```
type: brief description

Longer explanation if needed

Examples:
- feat: add humidity sensitivity configuration
- fix: correct fan speed parsing for boost mode
- test: add tests for config flow
- docs: update README with installation steps
- refactor: simplify sensor entity creation
```

### Pre-commit Hooks

The repository uses pre-commit hooks (`.pre-commit-config.yaml`):
- **pyupgrade**: Upgrade to Python 3.7+ syntax
- **black**: Auto-format code
- **codespell**: Spell checking
- **flake8**: Linting with docstring checks
- **bandit**: Security scanning
- **isort**: Import sorting
- **mypy**: Type checking

Install hooks:
```bash
pip install pre-commit
pre-commit install
```

## Home Assistant Integration Specifics

### Manifest Requirements

The `manifest.json` defines integration metadata:
- **domain**: Must match directory name
- **dependencies**: `["bluetooth_adapters"]`
- **config_flow**: `true` (UI configuration)
- **iot_class**: `"local_polling"`
- **bluetooth**: Discovery configuration with `local_name`

### Entry Setup Flow

1. User adds integration or auto-discovery triggers
2. `config_flow.py:async_step_bluetooth()` handles discovery
3. `config_flow.py:async_step_add_device()` collects MAC and PIN
4. `__init__.py:async_setup_entry()` creates coordinator and platforms
5. Platform `async_setup_entry()` functions create entities

### Coordinator Pattern

The coordinator (`PaxUpdateCoordinator`) centralizes data updates:
- Single BLE connection per update cycle
- All entities listen to coordinator updates
- Reduces BLE traffic and battery drain
- Provides consistent data across entities

### Device Info

All entities must provide consistent device info:
```python
DeviceInfo(
    connections={(CONNECTION_BLUETOOTH, coordinator.address)},
    manufacturer=device_info.manufacturer,
    model=f"{device_info.name} {device_info.model_number}",
    name=device_info.name,
    sw_version=device_info.sw_version,
    hw_version=device_info.hw_version,
)
```

## Key Files to Understand

### 1. `pax_client.py` (216 lines)

**Purpose**: BLE protocol implementation for Pax Levante fans

**Critical Constants** (lines 7-18):
- GATT characteristic handles for device communication
- Must match device firmware specification

**Data Classes**:
- `PaxSensors`: Current sensor readings
- `FanSpeedTarget`: RPM targets for humidity/light/base modes
- `Boost`: Boost mode state and settings

**Key Methods**:
- `async_get_sensors()`: Read sensor data (line 116)
- `async_set_fan_speed_targets()`: Write fan speed settings (line 141)
- `async_set_boost()`: Toggle boost mode (line 166)
- `_parse_sensors_response()`: Parse binary sensor data (line 193)

**Parsing Logic** (line 207-210):
Boost mode uses bit shifting to detect boost flag in `current_trigger` byte

### 2. `pax_update_coordinator.py` (83 lines)

**Purpose**: Coordinate data updates across all entities

**Update Interval**: 65 seconds (line 20)
- Chosen to avoid synchronization with other integrations
- Reduces BLE connection frequency

**PIN Authentication**: Required for write operations (lines 51-52, 72-73)
- Must be set during config flow
- Validated before each write operation

**Important**: Lines 66-67 show redundant assignment (potential bug to watch)

### 3. Platform Files (`sensor.py`, `number.py`, `switch.py`)

**Common Pattern**:
1. Define entity descriptions with translation keys
2. `async_setup_entry()` creates entities from coordinator
3. Entity class inherits `CoordinatorEntity` + platform base
4. Override appropriate properties/methods

**Sensor Entity** (`sensor.py`):
- Read-only entities
- Use `@property native_value` (line 131)
- Check availability via coordinator data (line 123)

**Number Entity** (`number.py`):
- Configurable fan speeds (950-2400 RPM in 25 RPM steps)
- Use `async_set_native_value()` (line 131)
- Call coordinator's `async_set_fan_speed_target()`

**Switch Entity** (`switch.py`):
- Boost mode toggle
- Implement `async_turn_on()` and `async_turn_off()` (lines 102-108)
- Call coordinator's `async_set_boost()`

## Common Tasks for AI Assistants

### Adding a New Sensor

1. Define sensor in `pax_client.py` if new BLE data needed
2. Add to `SENSOR_MAPPING` in `sensor.py`
3. Create translation key in `strings.json` and `translations/en.json`
4. Add test in `tests/test_pax_client.py` if parsing logic added
5. Update coordinator if new data fetching required

### Modifying BLE Communication

1. **IMPORTANT**: Changes to GATT handles must match device firmware
2. Update constants in `pax_client.py` (lines 7-18)
3. Modify parsing logic if data format changes
4. Add unit tests for new parsing functions
5. Test with actual device before committing

### Adding Configuration Options

1. Update `config_flow.py` data schema
2. Store in entry.data during `async_create_entry()`
3. Access via `entry.data[key]` in `__init__.py`
4. Update coordinator if configuration affects updates

### Debugging Connection Issues

Check these in order:
1. Bluetooth discovery: `_LOGGER.debug` in `config_flow.py:26`
2. Device connection: `_LOGGER.debug` in `pax_update_coordinator.py:31-33`
3. Data updates: `_LOGGER.debug` in `pax_update_coordinator.py:38-42`
4. Entity states: Add logging in entity classes

### Performance Optimization

Current update interval: 65 seconds
- Avoid reducing below 30 seconds (BLE connection overhead)
- Consider caching device info (only fetched if None, line 34)
- Batch multiple writes in coordinator methods
- Use `async_set_updated_data()` to push updates immediately

## CI/CD Pipeline

### GitHub Actions Workflows

1. **Python Package** (`.github/workflows/pythonpackage.yaml`):
   - Runs on every push
   - Python 3.11 matrix
   - Installs test dependencies
   - Runs pytest

2. **HACS/Hassfest** (`.github/workflows/hassfest.yaml`):
   - Validates Home Assistant integration requirements
   - Checks manifest.json structure
   - Verifies HACS compatibility

### Local Pre-push Checklist

```bash
# 1. Run tests
pytest

# 2. Check code style
black custom_components tests --check
isort custom_components tests --check
flake8 custom_components

# 3. Run type checker
mypy custom_components

# 4. Run pre-commit hooks
pre-commit run --all-files
```

## Dependencies

### Runtime (`requirements.txt`)
- `homeassistant==2024.3.1`: Home Assistant core
- `async-timeout==4.0.3`: Timeout handling
- **Note**: Bleak is included via Home Assistant's bluetooth component

### Testing (`requirements.test.txt`)
- Inherits from `requirements.txt`
- `pytest`: Test framework
- `pytest-homeassistant-custom-component==0.13.108`: HA test fixtures
- `pyserial==3.5`: Serial communication mocking
- `pyudev==0.24.1`: Device management mocking

## Troubleshooting Guide

### Test Failures Related to Bluetooth

**Issue**: Tests fail with Bluetooth import errors

**Solution**: Mock the bluetooth component:
```python
from unittest.mock import patch

@patch('homeassistant.components.bluetooth')
def test_something(mock_bluetooth):
    # Test code
```

See `tests/test_switch.py` for examples.

### Type Checking Errors

**Issue**: mypy reports errors

**Solution**: Check `setup.cfg:58-66` for mypy configuration
- `ignore_errors = true` is set (intentional for HA compatibility)
- Focus on actual runtime errors, not type warnings

### Import Order Issues

**Issue**: isort or pre-commit fails on imports

**Solution**: Follow the order in `setup.cfg:38-56`:
1. `from __future__ import annotations`
2. Standard library
3. Third-party
4. Home Assistant imports
5. Local imports (`.const`, `.pax_client`, etc.)

### BLE Connection Timeout

**Issue**: Update coordinator fails with timeout

**Solution**:
- Default timeout is 10 seconds (line 30 in coordinator)
- Check device is in range and powered
- Verify no other app is connected to device
- BLE allows only one connection at a time

## Important Notes for AI Assistants

### Do's ✓

1. **Always read existing files before modifying** them
2. **Follow Home Assistant entity patterns** strictly
3. **Add logging** for debugging (use appropriate levels)
4. **Write unit tests** for new parsing logic
5. **Use async/await** for all I/O operations
6. **Update translations** when adding entities
7. **Check coordinator data availability** before accessing
8. **Use context managers** for PaxClient connections
9. **Handle UpdateFailed exceptions** properly
10. **Test with pre-commit hooks** before committing

### Don'ts ✗

1. **Don't modify GATT handles** without device specification
2. **Don't reduce update interval** below 30 seconds without testing
3. **Don't block the event loop** with synchronous I/O
4. **Don't skip error handling** for BLE operations
5. **Don't forget PIN authentication** for write operations
6. **Don't create entities without coordinator** data
7. **Don't use hardcoded MAC addresses** in tests
8. **Don't modify manifest.json** without validating against HA schema
9. **Don't add emoji** unless explicitly requested
10. **Don't over-engineer** - keep solutions simple

### Critical Files - Modify with Caution

- `pax_client.py`: BLE protocol implementation (must match device firmware)
- `manifest.json`: Breaking changes affect installation
- `pax_update_coordinator.py`: Changes affect all entities
- GATT handle constants: Must match device specification exactly

### Safe to Modify

- Entity descriptions (SENSOR_MAPPING, ENTITIES)
- Translation strings (strings.json, translations/)
- Test files (tests/)
- Documentation (README.md, this file)
- Logging statements

## Quick Reference

### File Locations

| Component | File | Line Reference |
|-----------|------|----------------|
| Domain constant | `const.py` | 1 |
| Entry setup | `__init__.py` | 23-43 |
| BLE client | `pax_client.py` | 81-216 |
| Coordinator | `pax_update_coordinator.py` | 14-83 |
| Config flow | `config_flow.py` | 16-65 |
| Sensor entities | `sensor.py` | 41-133 |
| Number entities | `number.py` | 58-137 |
| Switch entity | `switch.py` | 51-109 |
| Update interval | `pax_update_coordinator.py` | 20 |
| GATT handles | `pax_client.py` | 7-18 |

### Common Coordinator Access Patterns

```python
# In entity classes:
self.coordinator.data              # Current sensor data (PaxSensors)
self.coordinator.device_info       # Device info (PaxDevice)
self.coordinator.fan_speed_targets # Fan speed targets (FanSpeedTarget)
self.coordinator.address           # Device MAC address

# Update methods:
await self.coordinator.async_set_fan_speed_target(key, value)
await self.coordinator.async_set_boost(active)
await self.coordinator.async_request_refresh()
```

### Translation Keys

All user-facing strings must have translation keys:
- `strings.json`: Default translations (used by HA core)
- `translations/en.json`: English translations (used by frontend)
- Format: `entity.{domain}.{entity_key}.{attribute}`

## Version Information

- **Integration Version**: 0.1.0 (manifest.json:20)
- **Home Assistant**: 2024.3.1+
- **Python**: 3.11+
- **Config Flow Version**: 1.1 (config_flow.py:19-20)

## External Resources

- **Documentation**: https://github.com/akselsson/ha-pax-levante
- **HACS**: Compatible (see hacs.json)
- **Home Assistant Docs**: https://developers.home-assistant.io/
- **Bluetooth Integration**: https://www.home-assistant.io/integrations/bluetooth/

---

**Last Updated**: 2026-01-09 (Generated by Claude)

This guide should be updated whenever significant architectural changes are made to the codebase.
