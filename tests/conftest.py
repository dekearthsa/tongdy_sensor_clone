"""
Pytest configuration and shared fixtures for Tongdy Sensor tests.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from queue import Queue
import threading


# MARK: Mock Data Fixtures
@pytest.fixture
def mock_sensor_data_voc():
    """Typical sensor readings for VOC sensor."""
    return {
        "co2": 450.25,
        "temperature": 23.5,
        "humidity": 55.2
    }


@pytest.fixture
def mock_sensor_data_non_voc():
    """Typical sensor readings for non-VOC sensor."""
    return {
        "co2": 425.0,
        "temperature": 22.8,
        "humidity": 58.7
    }


@pytest.fixture
def mock_sensor_data_extreme():
    """Edge case sensor readings."""
    return {
        "co2": 5000.0,
        "temperature": 35.0,
        "humidity": 95.0
    }


@pytest.fixture
def mock_sensor_data_failed():
    """Failed sensor readings."""
    return {
        "co2": None,
        "temperature": None,
        "humidity": None
    }


# MARK: Modbus Mocking Fixtures
@pytest.fixture
def mock_minimalmodbus_instrument():
    """Mock minimalmodbus.Instrument."""
    mock_instrument = MagicMock()
    mock_instrument.serial = MagicMock()
    mock_instrument.serial.port = "/dev/ttyUSB0"
    mock_instrument.serial.baudrate = 19200
    mock_instrument.serial.bytesize = 8
    mock_instrument.serial.timeout = 1.5
    
    # Mock read_float to return different values
    mock_instrument.read_float = MagicMock()
    
    return mock_instrument


@pytest.fixture
def mock_rs485_bus_manager():
    """Mock RS485BusManager context manager."""
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


# MARK: TongdySensor Fixtures
@pytest.fixture
def mock_tongdy_sensor():
    """Mock TongdySensor instance."""
    mock_sensor = MagicMock()
    mock_sensor.sensor_id = 1
    mock_sensor.sensor_address = 1
    mock_sensor.is_VOC = False
    mock_sensor.read_values = MagicMock(return_value={
        "co2": 400.0,
        "temperature": 22.0,
        "humidity": 50.0
    })
    return mock_sensor


@pytest.fixture
def mock_tongdy_sensor_voc():
    """Mock VOC TongdySensor instance."""
    mock_sensor = MagicMock()
    mock_sensor.sensor_id = 2
    mock_sensor.sensor_address = 2
    mock_sensor.is_VOC = True
    mock_sensor.read_values = MagicMock(return_value={
        "co2": 450.0,
        "temperature": 23.5,
        "humidity": 55.0
    })
    return mock_sensor


# MARK: Queue Fixtures
@pytest.fixture
def test_queue():
    """Fresh Queue for each test."""
    return Queue()


# MARK: SensorPoller Fixtures
@pytest.fixture
def mock_sensor_list(mock_tongdy_sensor, mock_tongdy_sensor_voc):
    """List of mock sensors."""
    return [mock_tongdy_sensor, mock_tongdy_sensor_voc]


@pytest.fixture
def sensor_poller_instance(test_queue, mock_sensor_list):
    """SensorPoller instance with mocked sensors.
    
    Note: This requires patching during import or modifying SensorPoller
    to accept sensors as a parameter.
    """
    from Tongdy_sensor.sensor_poller import SensorPoller
    
    poller = SensorPoller(
        polling_interval=1,
        polling_jitter=(0.01, 0.02),
        ui_queue=test_queue
    )
    # Replace sensors with mocks
    poller.sensors = mock_sensor_list
    
    return poller


# MARK: Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_threads():
    """Ensure all threads are cleaned up after each test."""
    yield
    # Wait a bit for threads to finish
    import time
    time.sleep(0.1)
    
    # Check for any lingering daemon threads
    active_threads = threading.enumerate()
    for thread in active_threads:
        if thread.daemon and thread.is_alive() and thread != threading.main_thread():
            # Try to join with short timeout
            thread.join(timeout=0.5)


# MARK: Patch Helpers
@pytest.fixture
def patch_minimalmodbus():
    """Patch minimalmodbus module."""
    with patch('Tongdy_sensor.tongdy_sensor.minimalmodbus') as mock_mm:
        yield mock_mm


@pytest.fixture
def patch_serial():
    """Patch serial module."""
    with patch('Tongdy_sensor.tongdy_sensor.serial') as mock_serial:
        yield mock_serial


@pytest.fixture
def patch_time_sleep():
    """Patch time.sleep to speed up tests."""
    with patch('time.sleep', return_value=None) as mock_sleep:
        yield mock_sleep
