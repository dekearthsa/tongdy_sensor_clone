"""
Quick Demo: Mock Sensors Without Hardware

Run this script to see mock sensors in action!
Perfect for developers who don't have physical sensors.
"""

import time
from queue import Queue


def demo():
    """Quick demonstration of mock sensors."""
    print("=" * 60)
    print("MOCK SENSOR DEMO - No Hardware Required!")
    print("=" * 60)
    
    # Demo 1: Single Mock Sensor
    print("\n📊 Demo 1: Reading from a single mock sensor")
    print("-" * 60)
    
    from mock_sensor import MockTongdySensor
    
    sensor = MockTongdySensor(sensor_address=2, is_VOC=True)
    print(f"Created mock VOC sensor (ID: {sensor.sensor_id})")
    
    for i in range(3):
        data = sensor.read_values()
        print(f"  Read {i+1}: CO2={data['co2']:6.1f} ppm, "
              f"Temp={data['temperature']:4.1f}°C, "
              f"RH={data['humidity']:4.1f}%")
        time.sleep(0.5)
    
    # Demo 2: Mock SensorPoller
    print("\n🔄 Demo 2: Full SensorPoller with mock sensors")
    print("-" * 60)
    
    from mock_sensor_poller import create_mock_poller
    
    queue = Queue()
    poller = create_mock_poller(
        ui_queue=queue,
        polling_interval=1,
        sensor_type='stable',
        num_sensors=2
    )
    
    print(f"Created poller with {len(poller.sensors)} mock sensors")
    print("Starting poller for 3 seconds...")
    
    poller.start()
    time.sleep(3)
    poller.stop()
    
    print(f"\nCollected {queue.qsize()} data points:")
    
    # Show first few data points
    count = 0
    while not queue.empty() and count < 4:
        data = queue.get()
        sensor_data = data['data']
        print(f"  Sensor {sensor_data['sensor_id']}: "
              f"CO2={sensor_data['co2']:6.1f}, "
              f"Temp={sensor_data['temperature']:4.1f}, "
              f"RH={sensor_data['humidity']:4.1f}")
        count += 1
    
    # Demo 3: Different Sensor Types
    print("\n🎨 Demo 3: Comparing different sensor types")
    print("-" * 60)
    
    from mock_sensor import MockSensorFactory
    
    sensors = [
        ('Stable', MockSensorFactory.create_stable_sensor(2)),
        ('Noisy', MockSensorFactory.create_noisy_sensor(3)),
        ('Unreliable', MockSensorFactory.create_unreliable_sensor(4))
    ]
    
    print("\nReading from each sensor type:\n")
    for name, sensor in sensors:
        data = sensor.read_values()
        status = "✓ OK" if data['co2'] is not None else "✗ FAIL"
        co2_str = f"{data['co2']:6.1f}" if data['co2'] else "  None"
        print(f"  {name:12} {status:6} - CO2: {co2_str} ppm")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  • Use mock sensors for development without hardware")
    print("  • Test your code with different sensor behaviors")
    print("  • Run tests in CI/CD without physical sensors")
    print("\nSee MOCK_SENSOR_GUIDE.md for full documentation")
    print("Run examples/example_mock_usage.py for more examples")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
