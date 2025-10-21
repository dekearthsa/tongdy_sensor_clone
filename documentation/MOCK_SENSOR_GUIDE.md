# Mock Sensor Guide for Development Without Hardware

This guide explains how to use mock sensors for testing and development without physical hardware.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Mock Sensor Types](#mock-sensor-types)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Testing Scenarios](#testing-scenarios)
- [Integration Examples](#integration-examples)

---

## 🚀 Quick Start

### Simple Mock Sensor

```python
from Tongdy_sensor.mock_sensor import MockTongdySensor

# Create a mock sensor (no hardware needed!)
sensor = MockTongdySensor(sensor_address=2, is_VOC=True)

# Read values just like a real sensor
data = sensor.read_values()
print(data)
# {'co2': 450.25, 'temperature': 22.5, 'humidity': 55.2}
```

### Mock SensorPoller (Complete System)

```python
from Tongdy_sensor.mock_sensor_poller import create_mock_poller
from queue import Queue
import time

# Create a queue for data
data_queue = Queue()

# Create a fully functional poller with mock sensors
poller = create_mock_poller(
    ui_queue=data_queue,
    polling_interval=5,
    sensor_type='stable'
)

# Use it exactly like the real poller!
poller.start()
time.sleep(10)
poller.stop()

# Get the data
while not data_queue.empty():
    data = data_queue.get()
    print(data)
```

---

## 🎨 Mock Sensor Types

We provide 4 pre-configured sensor types for different testing scenarios:

### 1. **Stable Sensors** (Default)
- ✅ Minimal noise (±0.5)
- ✅ No failures
- ✅ Fast reads (no delay simulation)
- **Use for**: Basic integration testing, UI development

```python
from Tongdy_sensor.mock_sensor import MockSensorFactory

sensor = MockSensorFactory.create_stable_sensor(2, is_VOC=True)
```

### 2. **Noisy Sensors**
- 📊 Realistic noise (±5.0)
- 📊 Gradual drift
- 📊 Simulated read delays
- **Use for**: Testing data filtering, averaging algorithms

```python
sensor = MockSensorFactory.create_noisy_sensor(3, is_VOC=False)
```

### 3. **Unreliable Sensors**
- ⚠️ 15% failure rate
- ⚠️ Moderate noise (±3.0)
- ⚠️ Simulated delays
- **Use for**: Testing error handling, retry logic

```python
sensor = MockSensorFactory.create_unreliable_sensor(4, is_VOC=False)
```

### 4. **Extreme Sensors**
- 🔥 Very high values (CO2: 2500 ppm, Temp: 35°C)
- 🔥 High noise (±10.0)
- 🔥 Fast drift
- **Use for**: Testing edge cases, value validation

```python
sensor = MockSensorFactory.create_extreme_sensor(5, is_VOC=True)
```

---

## 💡 Basic Usage

### Creating a Mock Sensor

```python
from Tongdy_sensor.mock_sensor import MockTongdySensor

# Basic creation
sensor = MockTongdySensor(
    sensor_address=2,
    is_VOC=True,
    base_co2=450.0,
    base_temperature=22.0,
    base_humidity=50.0
)

# Read values
data = sensor.read_values()
print(f"CO2: {data['co2']} ppm")
print(f"Temperature: {data['temperature']} °C")
print(f"Humidity: {data['humidity']} %")
```

### Setting Custom Values

```python
# Set specific values for testing
sensor.set_values(co2=800.0, temperature=25.0, humidity=60.0)

# Next read will be close to these values (with some noise)
data = sensor.read_values()
```

### Simulating Failures

```python
# Make sensor fail
sensor.simulate_failure(fail=True)
data = sensor.read_values()
# Returns: {'co2': None, 'temperature': None, 'humidity': None}

# Make it work again
sensor.simulate_failure(fail=False)
data = sensor.read_values()
# Returns: Normal values
```

---

## 🔧 Advanced Usage

### Custom Mock Sensor Configuration

```python
from Tongdy_sensor.mock_sensor import MockTongdySensor

sensor = MockTongdySensor(
    sensor_address=2,
    is_VOC=True,
    base_co2=500.0,              # Base CO2 value
    base_temperature=23.0,        # Base temperature
    base_humidity=55.0,           # Base humidity
    noise_level=3.0,              # Amount of random noise
    drift_rate=0.2,               # Rate of value drift
    should_fail_probability=0.1,  # 10% chance of failure
    simulate_delay=True           # Add realistic delays
)
```

### Creating Multiple Mock Sensors

```python
from Tongdy_sensor.mock_sensor_poller import create_mock_sensors

# Create a list of mock sensors
sensors = create_mock_sensors(
    sensor_type='noisy',
    num_sensors=4,
    use_voc=True  # First sensor will be VOC
)

# Use them in your code
for sensor in sensors:
    data = sensor.read_values()
    print(f"Sensor {sensor.sensor_id}: CO2={data['co2']}")
```

### Using Context Manager (Recommended for Tests)

```python
from Tongdy_sensor.mock_sensor_poller import MockPollerContext
import time

# Automatically handles start/stop and cleanup
with MockPollerContext(
    polling_interval=1,
    sensor_type='stable',
    num_sensors=2
) as (poller, queue):
    
    poller.start()
    time.sleep(5)
    
    # Process data
    while not queue.empty():
        data = queue.get()
        print(data)
    
# Poller automatically stopped when exiting context
```

---

## 🧪 Testing Scenarios

### Scenario 1: Test UI Without Hardware

```python
from Tongdy_sensor.mock_sensor_poller import create_mock_poller
from queue import Queue
import time

def update_ui(data):
    """Your UI update function."""
    sensor_data = data['data']
    print(f"Updating UI: CO2={sensor_data['co2']}")

# Create mock poller
queue = Queue()
poller = create_mock_poller(
    ui_queue=queue,
    polling_interval=2,
    sensor_type='stable'
)

poller.start()

# Simulate UI loop
for _ in range(10):
    if not queue.empty():
        data = queue.get()
        update_ui(data)
    time.sleep(0.5)

poller.stop()
```

### Scenario 2: Test Error Recovery

```python
from Tongdy_sensor.mock_sensor import MockTongdySensor

sensor = MockTongdySensor(sensor_address=2, is_VOC=True)

def read_with_retry(sensor, max_retries=3):
    """Your retry logic."""
    for attempt in range(max_retries):
        data = sensor.read_values()
        if data['co2'] is not None:
            return data
        print(f"Attempt {attempt + 1} failed, retrying...")
    return None

# Test with unreliable sensor
sensor.simulate_failure(fail=True)
result = read_with_retry(sensor)
print(f"Result: {result}")

# Test recovery
sensor.simulate_failure(fail=False)
result = read_with_retry(sensor)
print(f"After recovery: {result}")
```

### Scenario 3: Test Data Averaging

```python
from Tongdy_sensor.mock_sensor import MockSensorFactory
import statistics

# Create noisy sensor
sensor = MockSensorFactory.create_noisy_sensor(2, is_VOC=True)

# Collect multiple readings
readings = []
for _ in range(10):
    data = sensor.read_values()
    if data['co2'] is not None:
        readings.append(data['co2'])
    time.sleep(0.1)

# Calculate average
avg_co2 = statistics.mean(readings)
std_dev = statistics.stdev(readings)

print(f"Average CO2: {avg_co2:.2f} ppm")
print(f"Std Deviation: {std_dev:.2f}")
```

### Scenario 4: Test Edge Cases

```python
from Tongdy_sensor.mock_sensor import MockSensorFactory

# Test with extreme values
sensor = MockSensorFactory.create_extreme_sensor(2, is_VOC=True)

data = sensor.read_values()

# Your validation logic
def validate_reading(data):
    if data['co2'] > 2000:
        print(f"WARNING: High CO2 detected! {data['co2']} ppm")
        return False
    return True

validate_reading(data)
```

---

## 🔄 Integration Examples

### Drop-in Replacement for Real Sensors

Your existing code doesn't need to change! Just swap the import:

**Before (with real hardware):**
```python
from Tongdy_sensor.tongdy_sensor import TongdySensor

sensor = TongdySensor(sensor_address=2, port="/dev/ttyUSB0", is_VOC=True)
data = sensor.read_values()
```

**After (with mock):**
```python
from Tongdy_sensor.mock_sensor import MockTongdySensor as TongdySensor

sensor = TongdySensor(sensor_address=2, is_VOC=True)
data = sensor.read_values()
# Same interface, no hardware needed!
```

### Environment-Based Switching

```python
import os

# Automatically use mock sensors in development
if os.getenv('USE_MOCK_SENSORS', 'false').lower() == 'true':
    from Tongdy_sensor.mock_sensor import MockTongdySensor as TongdySensor
else:
    from Tongdy_sensor.tongdy_sensor import TongdySensor

# Your code works the same either way
sensor = TongdySensor(sensor_address=2, is_VOC=True)
data = sensor.read_values()
```

### Mock Poller in Your Application

```python
import os
from queue import Queue

# Choose poller based on environment
if os.getenv('USE_MOCK_SENSORS', 'false').lower() == 'true':
    from Tongdy_sensor.mock_sensor_poller import create_mock_poller
    
    queue = Queue()
    poller = create_mock_poller(
        ui_queue=queue,
        polling_interval=60,
        sensor_type='stable'
    )
else:
    from Tongdy_sensor.sensor_poller import SensorPoller
    
    queue = Queue()
    poller = SensorPoller(
        polling_interval=60,
        ui_queue=queue
    )

# Rest of your code is identical
poller.start()
# ... your application logic ...
poller.stop()
```

---

## 📝 Running the Examples

We've provided comprehensive examples in `examples/example_mock_usage.py`:

```bash
cd Tongdy_sensor
python examples/example_mock_usage.py
```

This will run 8 different examples showing:
1. Basic mock sensor usage
2. Custom values
3. Sensor factory
4. Simulated failures
5. Full mock poller
6. Context manager
7. Error handling
8. Comparing sensor types

---

## 🎯 Best Practices

### ✅ DO:
- Use **stable** sensors for basic testing and UI development
- Use **noisy** sensors to test filtering and averaging
- Use **unreliable** sensors to test error handling
- Use **extreme** sensors to test edge cases and validation
- Use the context manager for automatic cleanup
- Set `USE_MOCK_SENSORS` environment variable for easy switching

### ❌ DON'T:
- Don't use mock sensors in production (they're for testing only)
- Don't forget to test with real hardware before deployment
- Don't assume mock behavior exactly matches hardware
- Don't mix mock and real sensors in the same poller

---

## 🔍 Troubleshooting

### Mock sensor returns None values
```python
# Check if failure is simulated
sensor.should_fail_probability  # Should be 0.0 for stable

# Force success
sensor.simulate_failure(fail=False)
```

### Values don't match expectations
```python
# Reduce noise for more predictable values
sensor = MockTongdySensor(
    sensor_address=2,
    is_VOC=True,
    noise_level=0.1  # Very low noise
)

# Or set exact values
sensor.set_values(co2=450.0, temperature=22.0, humidity=50.0)
```

### Poller not collecting data
```python
# Make sure poller is started
poller.start()

# Check that queue is being read
print(f"Queue size: {queue.qsize()}")

# Verify sensors are in poller
print(f"Number of sensors: {len(poller.sensors)}")
```

---

## 📚 API Reference

### MockTongdySensor

**Methods:**
- `read_values()` - Read sensor values (returns dict)
- `set_values(co2, temperature, humidity)` - Set custom values
- `simulate_failure(fail)` - Force failure/recovery
- `get_read_count()` - Get number of reads
- `reset_read_count()` - Reset read counter

**Properties:**
- `sensor_id` - Sensor ID
- `is_VOC` - Whether this is a VOC sensor
- `base_co2`, `base_temperature`, `base_humidity` - Base values

### MockSensorFactory

**Methods:**
- `create_stable_sensor(address, is_VOC)` - Stable sensor
- `create_noisy_sensor(address, is_VOC)` - Noisy sensor
- `create_unreliable_sensor(address, is_VOC)` - Unreliable sensor
- `create_extreme_sensor(address, is_VOC)` - Extreme values sensor
- `create_custom_sensor(address, is_VOC, **kwargs)` - Custom config

### create_mock_poller()

**Parameters:**
- `ui_queue` - Queue for data (optional)
- `polling_interval` - Seconds between polls
- `polling_jitter` - Random delay between sensors
- `sensor_type` - 'stable', 'noisy', 'unreliable', or 'extreme'
- `num_sensors` - Number of sensors to create
- `use_voc` - Whether to include a VOC sensor

**Returns:** SensorPoller with mock sensors

---

## 💡 Tips for Developers

1. **Start with stable sensors** - Get your basic functionality working
2. **Progress to noisy sensors** - Test data handling and filtering
3. **Test with unreliable sensors** - Verify error handling works
4. **Validate with extreme sensors** - Check edge case handling
5. **Use environment variables** - Easy switching between mock and real
6. **Document which sensor type** - In tests, specify which type you're using
7. **Test different scenarios** - Don't just test happy paths

---

## 🚀 Next Steps

- Run `examples/example_mock_usage.py` to see all features in action
- Replace real sensors with mocks in your development environment
- Write tests using the mock sensors
- Use context managers for clean test code
- Set up environment-based switching for production vs development

**Happy testing without hardware! 🎉**
