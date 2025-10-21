"""
Mock Sensor Implementation for Testing Without Hardware

This module provides a mock implementation of TongdySensor that simulates
realistic sensor behavior without requiring physical hardware or Modbus
connections.

Usage:
    # Simple usage - replace real sensor
    from Tongdy_sensor.mock_sensor import MockTongdySensor
    
    sensor = MockTongdySensor(sensor_address=2, is_VOC=True)
    data = sensor.read_values()
    print(data)  # {'co2': 425.3, 'temperature': 22.5, 'humidity': 55.2}
    
    # Advanced usage - with custom behavior
    sensor = MockTongdySensor(
        sensor_address=3,
        is_VOC=False,
        base_co2=400.0,
        should_fail_probability=0.1,  # 10% failure rate
        noise_level=5.0  # Add realistic noise
    )
"""

import random
import time
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class MockTongdySensor:
    """
    Mock implementation of TongdySensor for testing without hardware.
    
    This mock sensor simulates realistic sensor behavior including:
    - Realistic sensor values with noise
    - Gradual value changes over time
    - Configurable failure modes
    - Retry logic simulation
    - VOC vs non-VOC sensor differences
    """
    
    def __init__(self,
                 sensor_address: int,
                 port: str = "/dev/ttyUSB0",
                 baudrate: int = 19200,
                 timeout: float = 1.5,
                 is_VOC: bool = False,
                 pre_delay: float = 0.03,
                 # Mock-specific parameters
                 base_co2: float = None,
                 base_temperature: float = None,
                 base_humidity: float = None,
                 noise_level: float = 2.0,
                 drift_rate: float = 0.1,
                 should_fail_probability: float = 0.0,
                 simulate_delay: bool = True):
        """
        Initialize mock sensor.
        
        Args:
            sensor_address: Modbus address (used as sensor_id)
            port: Port name (ignored in mock)
            baudrate: Baudrate (ignored in mock)
            timeout: Timeout (ignored in mock)
            is_VOC: Whether this is a VOC sensor
            pre_delay: Delay before reading (ignored in mock)
            base_co2: Base CO2 value (default varies by sensor type)
            base_temperature: Base temperature (default: 22.0)
            base_humidity: Base humidity (default: 50.0)
            noise_level: Amount of random noise to add
            drift_rate: Rate of gradual value drift
            should_fail_probability: Probability (0-1) of simulated failure
            simulate_delay: Whether to simulate read delay
        """
        # Standard sensor properties
        self.sensor_id = sensor_address
        self.sensor_address = sensor_address
        self.is_VOC = is_VOC
        self.pre_delay = pre_delay
        self.max_retries = 3
        self.retry_delay = 0.5
        self.MODBUS_ADDRESS = self._get_address(self.is_VOC)
        
        # Mock sensor is always "connected"
        self.instrument = True  # Non-None to indicate connected
        
        # Mock-specific properties
        self.noise_level = noise_level
        self.drift_rate = drift_rate
        self.should_fail_probability = should_fail_probability
        self.simulate_delay = simulate_delay
        
        # Base values - VOC sensors typically read higher
        if base_co2 is None:
            self.base_co2 = 450.0 if is_VOC else 400.0
        else:
            self.base_co2 = base_co2
            
        self.base_temperature = base_temperature or 22.0
        self.base_humidity = base_humidity or 50.0
        
        # Current values (start at base)
        self._current_co2 = self.base_co2
        self._current_temperature = self.base_temperature
        self._current_humidity = self.base_humidity
        
        # Tracking
        self._read_count = 0
        self._last_read_time = time.time()
        
        logger.info(
            f"Mock Tongdy sensor created with address {sensor_address} "
            f"(VOC={is_VOC})"
        )
    
    def read_values(self) -> Dict[str, Optional[float]]:
        """
        Simulate reading sensor values.
        
        Returns:
            Dictionary with co2, temperature, and humidity readings,
            or None values if simulated failure occurs.
        """
        self._read_count += 1
        
        # Simulate random failures
        if random.random() < self.should_fail_probability:
            logger.error(
                f"Mock sensor {self.sensor_id} simulating failure "
                f"(read #{self._read_count})"
            )
            return {
                "co2": None,
                "temperature": None,
                "humidity": None
            }
        
        # Simulate read delay
        if self.simulate_delay:
            time.sleep(random.uniform(0.01, 0.05))
        
        # Update values with drift and noise
        self._update_values()
        
        # Get current values with noise
        co2 = self._add_noise(self._current_co2, self.noise_level)
        temperature = self._add_noise(
            self._current_temperature,
            self.noise_level * 0.1
        )
        humidity = self._add_noise(
            self._current_humidity,
            self.noise_level * 0.5
        )
        
        # Clamp to realistic ranges
        co2 = max(300, min(5000, co2))
        temperature = max(-10, min(50, temperature))
        humidity = max(0, min(100, humidity))
        
        # Round to realistic precision
        result = {
            "co2": round(co2, 2),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2)
        }
        
        logger.info(
            f"Mock sensor {self.sensor_id} readings - "
            f"CO2: {result['co2']} ppm, "
            f"Temp: {result['temperature']} °C, "
            f"Humidity: {result['humidity']} %"
        )
        
        return result
    
    def _update_values(self):
        """Update internal values with gradual drift."""
        time_since_last_read = time.time() - self._last_read_time
        self._last_read_time = time.time()
        
        # Gradual drift toward base values
        drift_factor = self.drift_rate * time_since_last_read
        
        self._current_co2 += random.uniform(-1, 1) * drift_factor
        self._current_temperature += random.uniform(-0.1, 0.1) * drift_factor
        self._current_humidity += random.uniform(-0.5, 0.5) * drift_factor
        
        # Slowly drift back to base values
        self._current_co2 += (self.base_co2 - self._current_co2) * 0.01
        self._current_temperature += (
            (self.base_temperature - self._current_temperature) * 0.01
        )
        self._current_humidity += (
            (self.base_humidity - self._current_humidity) * 0.01
        )
    
    def _add_noise(self, value: float, noise_amount: float) -> float:
        """Add random noise to a value."""
        return value + random.uniform(-noise_amount, noise_amount)
    
    def _get_address(self, is_VOC: bool = False) -> dict:
        """Get the Modbus address mapping (same as real sensor)."""
        if is_VOC:
            return {
                "ADDR_CO2": 0,
                "ADDR_TEMP": 4,
                "ADDR_HUMID": 6,
                "FUNCTION_CODE": 4
            }
        else:
            return {
                "ADDR_CO2": 0,
                "ADDR_TEMP": 2,
                "ADDR_HUMID": 4,
                "FUNCTION_CODE": 4
            }
    
    # Convenience methods for testing
    
    def set_values(self, co2: float = None, temperature: float = None,
                   humidity: float = None):
        """
        Manually set sensor values for testing.
        
        Args:
            co2: CO2 value in ppm
            temperature: Temperature in Celsius
            humidity: Humidity percentage
        """
        if co2 is not None:
            self._current_co2 = co2
            self.base_co2 = co2
        if temperature is not None:
            self._current_temperature = temperature
            self.base_temperature = temperature
        if humidity is not None:
            self._current_humidity = humidity
            self.base_humidity = humidity
        
        logger.info(
            f"Mock sensor {self.sensor_id} values set to: "
            f"CO2={co2}, Temp={temperature}, Humidity={humidity}"
        )
    
    def simulate_failure(self, fail: bool = True):
        """
        Force the sensor to fail or recover.
        
        Args:
            fail: If True, next read will fail. If False, will succeed.
        """
        self.should_fail_probability = 1.0 if fail else 0.0
        logger.info(
            f"Mock sensor {self.sensor_id} failure mode: {fail}"
        )
    
    def get_read_count(self) -> int:
        """Get the number of times read_values was called."""
        return self._read_count
    
    def reset_read_count(self):
        """Reset the read counter."""
        self._read_count = 0


class MockSensorFactory:
    """
    Factory for creating mock sensors with various scenarios.
    """
    
    @staticmethod
    def create_stable_sensor(sensor_address: int,
                            is_VOC: bool = False) -> MockTongdySensor:
        """
        Create a stable sensor with minimal noise and no failures.
        
        Perfect for basic integration testing.
        """
        return MockTongdySensor(
            sensor_address=sensor_address,
            is_VOC=is_VOC,
            noise_level=0.5,
            drift_rate=0.05,
            should_fail_probability=0.0,
            simulate_delay=False
        )
    
    @staticmethod
    def create_noisy_sensor(sensor_address: int,
                           is_VOC: bool = False) -> MockTongdySensor:
        """
        Create a sensor with realistic noise and drift.
        
        Good for testing filtering and data validation.
        """
        return MockTongdySensor(
            sensor_address=sensor_address,
            is_VOC=is_VOC,
            noise_level=5.0,
            drift_rate=0.3,
            should_fail_probability=0.0,
            simulate_delay=True
        )
    
    @staticmethod
    def create_unreliable_sensor(sensor_address: int,
                                is_VOC: bool = False) -> MockTongdySensor:
        """
        Create a sensor that occasionally fails.
        
        Good for testing error handling and retry logic.
        """
        return MockTongdySensor(
            sensor_address=sensor_address,
            is_VOC=is_VOC,
            noise_level=3.0,
            drift_rate=0.2,
            should_fail_probability=0.15,  # 15% failure rate
            simulate_delay=True
        )
    
    @staticmethod
    def create_extreme_sensor(sensor_address: int,
                             is_VOC: bool = False) -> MockTongdySensor:
        """
        Create a sensor with extreme values.
        
        Good for testing edge cases and value validation.
        """
        sensor = MockTongdySensor(
            sensor_address=sensor_address,
            is_VOC=is_VOC,
            base_co2=2500.0,  # Very high
            base_temperature=35.0,
            base_humidity=85.0,
            noise_level=10.0,
            drift_rate=0.5,
            should_fail_probability=0.0
        )
        return sensor
    
    @staticmethod
    def create_custom_sensor(sensor_address: int,
                            is_VOC: bool = False,
                            **kwargs) -> MockTongdySensor:
        """
        Create a sensor with custom parameters.
        
        Args:
            sensor_address: Sensor address
            is_VOC: Whether this is a VOC sensor
            **kwargs: Any MockTongdySensor parameters
        """
        return MockTongdySensor(
            sensor_address=sensor_address,
            is_VOC=is_VOC,
            **kwargs
        )
