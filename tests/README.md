# Tongdy Sensor Tests

This directory contains comprehensive tests for the Tongdy Sensor package.

## Test Structure

- **`conftest.py`** - Pytest fixtures and test configuration
- **`test_tongdy_sensor.py`** - Unit tests for TongdySensor class
- **`test_sensor_poller.py`** - Unit tests for SensorPoller class
- **`test_integration.py`** - Integration tests for complete system

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# From the Tongdy_sensor directory
pytest tests/

# Or from the project root
pytest Tongdy_sensor/tests/
```

### Run Specific Test Files

```bash
pytest tests/test_tongdy_sensor.py
pytest tests/test_sensor_poller.py
pytest tests/test_integration.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/test_tongdy_sensor.py::TestTongdySensorInitialization

# Run a specific test method
pytest tests/test_sensor_poller.py::TestSensorPollerStart::test_start_success
```

### Run with Coverage Report

```bash
pytest tests/ --cov=Tongdy_sensor --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run with Test Duration

```bash
pytest tests/ --durations=10
```

Shows the 10 slowest tests.

### Run in Parallel

```bash
pytest tests/ -n auto
```

Uses all available CPU cores.

## Test Categories

### Unit Tests

Tests individual components in isolation with mocked dependencies:

- `test_tongdy_sensor.py` - TongdySensor class
  - Initialization with various configurations
  - Reading values with mocked Modbus
  - Retry logic
  - Error handling
  - RS485BusManager thread safety

- `test_sensor_poller.py` - SensorPoller class
  - Start/stop functionality
  - Threading behavior
  - Polling cycles
  - Queue data format
  - Error handling

### Integration Tests

Tests component interactions with mocked hardware:

- `test_integration.py`
  - Full polling cycle
  - Multiple sensor coordination
  - Error recovery
  - Thread safety
  - Long-running scenarios

## Mock Data

All tests use mock data and do not require physical sensors. The mocks simulate:

- Modbus communication
- Serial port access
- Sensor readings (CO2, temperature, humidity)
- Communication errors and retries
- Thread timing and synchronization

## Test Coverage Goals

- **Overall Coverage**: >80%
- **Critical Paths**: 100%
  - Start/stop functionality
  - Error handling
  - Thread safety

## Continuous Integration

These tests are designed to run in CI/CD pipelines without hardware dependencies.

## Troubleshooting

### Tests Timeout

If tests timeout, it may be due to threading issues. Check:
- Ensure poller.stop() is called in test cleanup
- Use shorter polling intervals for tests
- Check for deadlocks in bus manager

### Import Errors

Make sure the parent directory is in the Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

Or install the package in development mode:
```bash
pip install -e ..
```

### Fixture Not Found

Ensure `conftest.py` is in the tests directory and properly formatted.

## Adding New Tests

When adding new tests:

1. Follow existing naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Mock external dependencies (Modbus, serial, etc.)
4. Include docstrings explaining what is tested
5. Test both success and failure cases
6. Clean up threads/resources in teardown

## Example Test

```python
def test_my_feature(sensor_poller_instance, test_queue):
    """Test description here."""
    poller = sensor_poller_instance
    
    # Setup
    poller.polling_interval = 0.5
    
    # Execute
    poller.start()
    time.sleep(0.6)
    poller.stop()
    
    # Assert
    assert not test_queue.empty()
    data = test_queue.get()
    assert data["type"] == "live_sensor_data"
```
