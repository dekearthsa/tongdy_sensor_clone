"""
Examples of using Mock Sensors for Development and Testing
Run these examples to see how to use mock sensors without hardware.
"""

import time
import sys
from pathlib import Path
from queue import Queue

# Add parent directory to path so we can import the modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


# Example 1: Basic Mock Sensor Usage
def example_1_basic_mock_sensor():
    """Use a single mock sensor directly."""
    print("\n=== Example 1: Basic Mock Sensor ===")
    
    from mock_sensor import MockTongdySensor
    
    # Create a mock sensor (no hardware needed!)
    sensor = MockTongdySensor(sensor_address=2, is_VOC=True)
    
    # Read values multiple times
    for i in range(5):
        data = sensor.read_values()
        print(f"Read {i+1}: CO2={data['co2']} ppm, "
              f"Temp={data['temperature']}°C, "
              f"Humidity={data['humidity']}%")
        time.sleep(0.5)
    
    print(f"Total reads: {sensor.get_read_count()}")


# Example 2: Mock Sensor with Custom Values
def example_2_custom_values():
    """Set specific sensor values for testing."""
    print("\n=== Example 2: Custom Mock Values ===")
    
    from mock_sensor import MockTongdySensor
    
    sensor = MockTongdySensor(
        sensor_address=3,
        is_VOC=False,
        noise_level=0.1  # Very little noise
    )
    
    # Set specific values
    sensor.set_values(co2=800.0, temperature=25.0, humidity=60.0)
    
    # Read should be close to set values
    data = sensor.read_values()
    print(f"Set values - CO2=800, Temp=25, Humidity=60")
    print(f"Read values - CO2={data['co2']}, "
          f"Temp={data['temperature']}, "
          f"Humidity={data['humidity']}")


# Example 3: Mock Sensor Factory
def example_3_sensor_factory():
    """Use factory to create different sensor types."""
    print("\n=== Example 3: Mock Sensor Factory ===")
    
    from mock_sensor import MockSensorFactory
    
    # Create different types of sensors
    stable = MockSensorFactory.create_stable_sensor(2, is_VOC=True)
    noisy = MockSensorFactory.create_noisy_sensor(3, is_VOC=False)
    unreliable = MockSensorFactory.create_unreliable_sensor(4, is_VOC=False)
    
    sensors = [
        ("Stable", stable),
        ("Noisy", noisy),
        ("Unreliable", unreliable)
    ]
    
    print("\nReading from different sensor types:")
    for name, sensor in sensors:
        data = sensor.read_values()
        status = "OK" if data['co2'] is not None else "FAILED"
        print(f"{name:12} - Status: {status:6} - "
              f"CO2: {data['co2']}")


# Example 4: Simulate Sensor Failures
def example_4_simulate_failures():
    """Test error handling with simulated failures."""
    print("\n=== Example 4: Simulated Failures ===")
    
    from mock_sensor import MockTongdySensor
    
    sensor = MockTongdySensor(sensor_address=2, is_VOC=True)
    
    # Normal read
    print("Normal read:")
    data = sensor.read_values()
    print(f"  CO2: {data['co2']}")
    
    # Force failure
    sensor.simulate_failure(fail=True)
    print("\nForced failure:")
    data = sensor.read_values()
    print(f"  CO2: {data['co2']}")  # Should be None
    
    # Recover
    sensor.simulate_failure(fail=False)
    print("\nAfter recovery:")
    data = sensor.read_values()
    print(f"  CO2: {data['co2']}")  # Should have value again


# Example 5: Mock Poller (Full System)
def example_5_mock_poller():
    """Use the complete mock SensorPoller."""
    print("\n=== Example 5: Mock SensorPoller ===")
    
    from mock_sensor_poller import create_mock_poller
    
    # Create queue for data
    data_queue = Queue()
    
    # Create mock poller with stable sensors
    poller = create_mock_poller(
        ui_queue=data_queue,
        polling_interval=1,  # Poll every second
        sensor_type='stable',
        num_sensors=2
    )
    
    print(f"Created poller with {len(poller.sensors)} mock sensors")
    
    # Start polling
    print("Starting poller...")
    poller.start()
    
    # Let it run for 3 seconds
    time.sleep(3)
    
    # Stop polling
    print("Stopping poller...")
    poller.stop()
    
    # Display collected data
    print(f"\nCollected {data_queue.qsize()} data points:")
    count = 0
    while not data_queue.empty() and count < 5:
        data = data_queue.get()
        sensor_data = data['data']
        print(f"  Sensor {sensor_data['sensor_id']}: "
              f"CO2={sensor_data['co2']}, "
              f"Temp={sensor_data['temperature']}, "
              f"RH={sensor_data['humidity']}")
        count += 1
    
    if data_queue.qsize() > 0:
        print(f"  ... and {data_queue.qsize()} more")


# Example 6: Context Manager for Easy Testing
def example_6_context_manager():
    """Use context manager for automatic cleanup."""
    print("\n=== Example 6: Context Manager ===")
    
    from mock_sensor_poller import MockPollerContext
    
    # Automatically creates and cleans up poller
    with MockPollerContext(
        polling_interval=1,
        sensor_type='noisy',
        num_sensors=2
    ) as (poller, queue):
        
        print("Poller created and will auto-stop on exit")
        
        # Start polling
        poller.start()
        print("Polling...")
        time.sleep(2)
        
        # Get some data
        if not queue.empty():
            data = queue.get()
            print(f"Sample data: {data['data']}")
    
    print("Context exited - poller automatically stopped")


# Example 7: Testing Error Handling
def example_7_error_handling():
    """Test how your code handles sensor errors."""
    print("\n=== Example 7: Error Handling Test ===")
    
    from mock_sensor_poller import create_mock_poller
    
    # Create poller with unreliable sensors (15% failure rate)
    queue = Queue()
    poller = create_mock_poller(
        ui_queue=queue,
        polling_interval=0.5,
        sensor_type='unreliable',
        num_sensors=2
    )
    
    print("Testing with unreliable sensors (15% failure rate)...")
    poller.start()
    time.sleep(3)
    poller.stop()
    
    # Analyze results
    total_reads = 0
    failed_reads = 0
    
    while not queue.empty():
        data = queue.get()
        sensor_data = data['data']
        total_reads += 1
        if sensor_data['co2'] is None:
            failed_reads += 1
    
    print(f"Total reads: {total_reads}")
    print(f"Failed reads: {failed_reads}")
    print(f"Success rate: {(total_reads - failed_reads) / total_reads * 100:.1f}%")


# Example 8: Comparing Sensor Types
def example_8_compare_sensor_types():
    """Compare behavior of different sensor types."""
    print("\n=== Example 8: Compare Sensor Types ===")
    
    from mock_sensor import MockSensorFactory
    import statistics
    
    sensor_types = {
        'Stable': MockSensorFactory.create_stable_sensor(2),
        'Noisy': MockSensorFactory.create_noisy_sensor(3),
        'Extreme': MockSensorFactory.create_extreme_sensor(4)
    }
    
    # Collect readings from each type
    print("\nTaking 10 readings from each sensor type...\n")
    
    for name, sensor in sensor_types.items():
        readings = []
        for _ in range(10):
            data = sensor.read_values()
            if data['co2'] is not None:
                readings.append(data['co2'])
            time.sleep(0.05)
        
        if readings:
            avg = statistics.mean(readings)
            std_dev = statistics.stdev(readings) if len(readings) > 1 else 0
            print(f"{name:10} - Avg: {avg:7.2f}, "
                  f"StdDev: {std_dev:5.2f}, "
                  f"Range: {min(readings):.1f}-{max(readings):.1f}")


# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("Mock Sensor Usage Examples")
    print("=" * 60)
    
    # Run all examples
    examples = [
        example_1_basic_mock_sensor,
        example_2_custom_values,
        example_3_sensor_factory,
        example_4_simulate_failures,
        example_5_mock_poller,
        example_6_context_manager,
        example_7_error_handling,
        example_8_compare_sensor_types
    ]
    
    for example in examples:
        try:
            example()
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\nExamples interrupted by user")
            break
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
