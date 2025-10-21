# Tongdy Sensor Package

Complete sensor management system with support for real hardware, mock sensors, and comprehensive testing.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Mock Sensors](#mock-sensors)
- [Documentation](#documentation)

---

## 🚀 Quick Start

### With Real Hardware

```python
from Tongdy_sensor.sensor_poller import SensorPoller
from queue import Queue

queue = Queue()
poller = SensorPoller(polling_interval=60, ui_queue=queue)

poller.start()
# ... get data from queue ...
poller.stop()
```

### Without Hardware (Mock Sensors)

```python
from Tongdy_sensor.mock_sensor_poller import create_mock_poller
from queue import Queue

queue = Queue()
poller = create_mock_poller(
    ui_queue=queue,
    polling_interval=5,
    sensor_type='stable'
)

poller.start()
# ... works exactly the same! ...
poller.stop()
```

---

## ✨ Features

- ✅ **Real Hardware Support** - Tongdy CO2/Temp/Humidity sensors via Modbus
- ✅ **Mock Sensors** - Full development without physical hardware
- ✅ **Automatic Polling** - Background thread with configurable intervals
- ✅ **Error Handling** - Retry logic, timeout protection, graceful degradation
- ✅ **Thread Safety** - RS485 bus locking, concurrent access protection
- ✅ **Comprehensive Testing** - 43 tests with 96% code coverage
- ✅ **CI/CD Ready** - Tests run without hardware

---

## 📦 Installation

```bash
# Install dependencies
pip install minimalmodbus pyserial python-dotenv

# For testing
pip install -r tests/requirements-test.txt
```

---

## 💡 Usage

### Basic Sensor Reading

```python
from Tongdy_sensor.tongdy_sensor import TongdySensor

# Create sensor instance
sensor = TongdySensor(
    sensor_address=2,
    port="/dev/ttyUSB0",
    is_VOC=True
)

# Read values
data = sensor.read_values()
print(f"CO2: {data['co2']} ppm")
print(f"Temperature: {data['temperature']} °C")
print(f"Humidity: {data['humidity']} %")
```

### Automated Polling

```python
from Tongdy_sensor.sensor_poller import SensorPoller
from queue import Queue
import time

# Create queue for data
queue = Queue()

# Create poller (automatically creates sensors)
poller = SensorPoller(
    polling_interval=60,  # Poll every 60 seconds
    polling_jitter=(0.02, 0.08),  # Random delay between sensors
    ui_queue=queue
)

# Start polling
poller.start()

# Get data from queue
while True:
    if not queue.empty():
        data = queue.get()
        sensor_data = data['data']
        print(f"Sensor {sensor_data['sensor_id']}: "
              f"CO2={sensor_data['co2']}, "
              f"Temp={sensor_data['temperature']}, "
              f"RH={sensor_data['humidity']}")
    time.sleep(1)

# Stop when done
poller.stop()
```

### Error Handling

```python
from Tongdy_sensor.sensor_poller import SensorPoller

poller = SensorPoller()

try:
    if poller.start():
        print("Poller started successfully")
    else:
        print("Poller was already running")
except Exception as e:
    print(f"Failed to start poller: {e}")

# Stop with timeout handling
try:
    if poller.stop():
        print("Poller stopped successfully")
    else:
        print("Poller was already stopped")
except TimeoutError:
    print("Poller failed to stop within timeout!")
except Exception as e:
    print(f"Error stopping poller: {e}")
```

---

## 🧪 Testing

### Run All Tests

```bash
# Run tests
pytest Tongdy_sensor/tests/ -v

# Run with coverage
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=html
```

### Test Results

- **43 tests** - All passing ✅
- **96% code coverage** - Exceeds target ✅
- **No hardware required** - Uses mocks ✅
- **~16 seconds** - Fast execution ✅

### Test Structure

```
tests/
├── conftest.py              # Fixtures and test utilities
├── test_tongdy_sensor.py    # TongdySensor unit tests (12 tests)
├── test_sensor_poller.py    # SensorPoller unit tests (22 tests)
├── test_integration.py      # Integration tests (9 tests)
└── README.md                # Test documentation
```

See [TEST_IMPLEMENTATION_SUMMARY.md](TEST_IMPLEMENTATION_SUMMARY.md) for details.

---

## 🎨 Mock Sensors

### Why Mock Sensors?

- ✅ Develop without physical hardware
- ✅ Test on any machine (laptops, CI/CD servers)
- ✅ Simulate failures and edge cases
- ✅ Fast iteration and testing
- ✅ Demo software without sensors

### Quick Mock Sensor Demo

```bash
cd Tongdy_sensor
python demo_mock_sensors.py
```

### Mock Sensor Types

| Type | Characteristics | Use Case |
|------|----------------|----------|
| **Stable** | Minimal noise, no failures | UI development, basic testing |
| **Noisy** | Realistic noise & drift | Data filtering, averaging |
| **Unreliable** | 15% failure rate | Error handling, retry logic |
| **Extreme** | Edge case values | Validation, edge cases |

### Mock Sensor Usage

```python
from Tongdy_sensor.mock_sensor import MockSensorFactory

# Create different sensor types
stable = MockSensorFactory.create_stable_sensor(2, is_VOC=True)
noisy = MockSensorFactory.create_noisy_sensor(3, is_VOC=False)
unreliable = MockSensorFactory.create_unreliable_sensor(4)

# Use just like real sensors!
data = stable.read_values()
```

### Mock Poller

```python
from Tongdy_sensor.mock_sensor_poller import create_mock_poller
from queue import Queue

queue = Queue()
poller = create_mock_poller(
    ui_queue=queue,
    polling_interval=5,
    sensor_type='stable',
    num_sensors=2
)

poller.start()
# ... identical to real poller ...
poller.stop()
```

See [MOCK_SENSOR_GUIDE.md](MOCK_SENSOR_GUIDE.md) for complete documentation.

---

## 📚 Documentation

### Core Documentation

- **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** - Testing commands and tips
- **[TEST_IMPLEMENTATION_SUMMARY.md](TEST_IMPLEMENTATION_SUMMARY.md)** - Complete test details
- **[MOCK_SENSOR_GUIDE.md](MOCK_SENSOR_GUIDE.md)** - Mock sensor usage guide
- **[MOCK_IMPLEMENTATION_SUMMARY.md](MOCK_IMPLEMENTATION_SUMMARY.md)** - Mock implementation details

### Examples

- **`demo_mock_sensors.py`** - Quick mock sensor demo
- **`examples/example_mock_usage.py`** - 8 comprehensive examples

---

## 🏗️ Project Structure

```
Tongdy_sensor/
├── __init__.py                          # Package init
├── tongdy_sensor.py                     # Real sensor implementation
├── sensor_poller.py                     # Automated polling system
├── mock_sensor.py                       # Mock sensor implementation
├── mock_sensor_poller.py                # Mock poller utilities
├── demo_mock_sensors.py                 # Quick demo script
│
├── tests/                               # Test suite
│   ├── conftest.py                      # Pytest fixtures
│   ├── test_tongdy_sensor.py            # Sensor unit tests
│   ├── test_sensor_poller.py            # Poller unit tests
│   ├── test_integration.py              # Integration tests
│   ├── requirements-test.txt            # Test dependencies
│   └── README.md                        # Test documentation
│
├── examples/                            # Usage examples
│   └── example_mock_usage.py            # Mock sensor examples
│
└── Documentation/                       # Guides and summaries
    ├── QUICK_TEST_GUIDE.md
    ├── TEST_IMPLEMENTATION_SUMMARY.md
    ├── MOCK_SENSOR_GUIDE.md
    └── MOCK_IMPLEMENTATION_SUMMARY.md
```

---

## 🔧 API Reference

### TongdySensor

**Constructor:**
```python
TongdySensor(sensor_address, port, baudrate=19200, 
             timeout=1.5, is_VOC=False, pre_delay=0.03)
```

**Methods:**
- `read_values()` → `dict` - Read CO2, temp, humidity

**Properties:**
- `sensor_id` - Sensor ID/address
- `is_VOC` - Whether this is a VOC sensor

### SensorPoller

**Constructor:**
```python
SensorPoller(polling_interval=60, polling_jitter=(0.02, 0.08),
             ui_queue=Queue())
```

**Methods:**
- `start()` → `bool` - Start polling (True=success, False=already running)
- `stop()` → `bool` - Stop polling (True=success, False=already stopped)

**Properties:**
- `running` - Whether poller is running
- `sensors` - List of sensor instances
- `ui_queue` - Queue for data output

### MockTongdySensor

**Constructor:**
```python
MockTongdySensor(sensor_address, is_VOC=False, 
                 base_co2=None, noise_level=2.0,
                 should_fail_probability=0.0, ...)
```

**Methods:**
- `read_values()` → `dict` - Read simulated values
- `set_values(co2, temperature, humidity)` - Set specific values
- `simulate_failure(fail)` - Force failure/recovery
- `get_read_count()` → `int` - Get number of reads

---

## 🎯 Common Patterns

### Environment-Based Switching

```python
import os

# Use mock sensors in development
if os.getenv('USE_MOCK_SENSORS', 'false').lower() == 'true':
    from Tongdy_sensor.mock_sensor import MockTongdySensor as TongdySensor
else:
    from Tongdy_sensor.tongdy_sensor import TongdySensor

# Code works the same either way
sensor = TongdySensor(sensor_address=2, is_VOC=True)
```

### Context Manager Pattern

```python
from Tongdy_sensor.mock_sensor_poller import MockPollerContext

with MockPollerContext(sensor_type='stable') as (poller, queue):
    poller.start()
    # ... do work ...
    # Automatic cleanup on exit
```

### Error Recovery

```python
poller = SensorPoller()

# Start with retry
max_attempts = 3
for attempt in range(max_attempts):
    try:
        if poller.start():
            break
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(1)
```

---

## 🐛 Troubleshooting

### Tests Not Running

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Configure Python environment
python -m pytest Tongdy_sensor/tests/ -v
```

### Mock Sensors Not Working

```bash
# Run the demo to verify installation
python Tongdy_sensor/demo_mock_sensors.py
```

### Port Not Found (Real Sensors)

```python
# Check port availability
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
for port in ports:
    print(port.device)
```

---

## 📝 Contributing

When adding new features:

1. ✅ Write tests first (TDD)
2. ✅ Maintain >90% code coverage
3. ✅ Update documentation
4. ✅ Add examples if applicable
5. ✅ Run full test suite before committing

```bash
# Run tests
pytest Tongdy_sensor/tests/ -v

# Check coverage
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=term-missing
```

---

## 📄 License

[Add your license information here]

---

## 👥 Authors

[Add author information here]

---

## 🎉 Summary

This package provides:

- ✅ **Production-ready** sensor polling system
- ✅ **Complete test suite** (43 tests, 96% coverage)
- ✅ **Mock sensor system** for development without hardware
- ✅ **Comprehensive documentation** and examples
- ✅ **CI/CD ready** - tests run anywhere

**Get started:**
1. Run `python demo_mock_sensors.py` to see mock sensors in action
2. Read `MOCK_SENSOR_GUIDE.md` for development without hardware
3. See `examples/example_mock_usage.py` for more examples
4. Check `TEST_IMPLEMENTATION_SUMMARY.md` for testing details

**Happy coding! 🚀**
