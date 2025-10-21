"""
Mock SensorPoller for Easy Testing

This module provides a pre-configured SensorPoller that uses mock sensors
instead of real hardware, making it easy for developers to test without
physical sensors.

Usage:
    from Tongdy_sensor.mock_sensor_poller import create_mock_poller
    from queue import Queue
    
    # Create a queue for receiving data
    data_queue = Queue()
    
    # Create mock poller (automatically uses mock sensors)
    poller = create_mock_poller(
        ui_queue=data_queue,
        polling_interval=5,
        sensor_type='stable'  # or 'noisy', 'unreliable', 'extreme'
    )
    
    # Use it just like the real poller
    poller.start()
    
    # Get data from queue
    while not data_queue.empty():
        data = data_queue.get()
        print(data)
    
    poller.stop()
"""

import logging
from queue import Queue
from typing import Literal, List

from sensor_poller import SensorPoller
from mock_sensor import MockTongdySensor, MockSensorFactory

logger = logging.getLogger(__name__)


def create_mock_poller(
    ui_queue: Queue = None,
    polling_interval: int = 60,
    polling_jitter: tuple = (0.02, 0.08),
    sensor_type: Literal['stable', 'noisy', 'unreliable', 'extreme'] = 'stable',
    num_sensors: int = 2,
    use_voc: bool = True
) -> SensorPoller:
    """
    Create a SensorPoller with mock sensors for testing.
    
    Args:
        ui_queue: Queue for sensor data (creates new one if None)
        polling_interval: Seconds between polls
        polling_jitter: Random jitter between sensor reads
        sensor_type: Type of mock sensors to create:
            - 'stable': Minimal noise, no failures
            - 'noisy': Realistic noise and drift
            - 'unreliable': Occasional failures (15% rate)
            - 'extreme': Extreme values for edge case testing
        num_sensors: Number of mock sensors to create
        use_voc: Whether to include a VOC sensor
    
    Returns:
        SensorPoller instance with mock sensors
    
    Example:
        >>> from queue import Queue
        >>> q = Queue()
        >>> poller = create_mock_poller(ui_queue=q, sensor_type='stable')
        >>> poller.start()
        >>> # ... get data from queue ...
        >>> poller.stop()
    """
    if ui_queue is None:
        ui_queue = Queue()
    
    # Create the poller
    poller = SensorPoller(
        polling_interval=polling_interval,
        polling_jitter=polling_jitter,
        ui_queue=ui_queue
    )
    
    # Replace sensors with mocks
    mock_sensors = create_mock_sensors(
        sensor_type=sensor_type,
        num_sensors=num_sensors,
        use_voc=use_voc
    )
    
    poller.sensors = mock_sensors
    
    logger.info(
        f"Created mock SensorPoller with {len(mock_sensors)} "
        f"{sensor_type} sensors"
    )
    
    return poller


def create_mock_sensors(
    sensor_type: str = 'stable',
    num_sensors: int = 2,
    use_voc: bool = True
) -> List[MockTongdySensor]:
    """
    Create a list of mock sensors.
    
    Args:
        sensor_type: Type of sensors ('stable', 'noisy', 'unreliable', 'extreme')
        num_sensors: Number of sensors to create
        use_voc: Whether first sensor should be VOC type
    
    Returns:
        List of MockTongdySensor instances
    """
    sensors = []
    
    # Factory method mapping
    factory_methods = {
        'stable': MockSensorFactory.create_stable_sensor,
        'noisy': MockSensorFactory.create_noisy_sensor,
        'unreliable': MockSensorFactory.create_unreliable_sensor,
        'extreme': MockSensorFactory.create_extreme_sensor
    }
    
    create_sensor = factory_methods.get(
        sensor_type,
        MockSensorFactory.create_stable_sensor
    )
    
    for i in range(num_sensors):
        # First sensor is VOC if requested, rest are non-VOC
        is_voc = (i == 0 and use_voc)
        sensor_address = i + 2  # Start at address 2
        
        sensor = create_sensor(
            sensor_address=sensor_address,
            is_VOC=is_voc
        )
        sensors.append(sensor)
        
        logger.info(
            f"Created mock sensor {sensor_address} "
            f"(VOC={is_voc}, type={sensor_type})"
        )
    
    return sensors


class MockPollerContext:
    """
    Context manager for easy mock poller usage in tests.
    
    Usage:
        with MockPollerContext(sensor_type='stable') as (poller, queue):
            poller.start()
            time.sleep(2)
            
            # Get data
            while not queue.empty():
                data = queue.get()
                print(data)
        # Poller automatically stopped when exiting context
    """
    
    def __init__(self,
                 polling_interval: int = 1,
                 sensor_type: str = 'stable',
                 num_sensors: int = 2):
        """
        Initialize context manager.
        
        Args:
            polling_interval: Seconds between polls
            sensor_type: Type of mock sensors
            num_sensors: Number of sensors
        """
        self.polling_interval = polling_interval
        self.sensor_type = sensor_type
        self.num_sensors = num_sensors
        self.queue = Queue()
        self.poller = None
    
    def __enter__(self):
        """Enter context - create and return poller and queue."""
        self.poller = create_mock_poller(
            ui_queue=self.queue,
            polling_interval=self.polling_interval,
            sensor_type=self.sensor_type,
            num_sensors=self.num_sensors
        )
        logger.info("Entered MockPollerContext")
        return self.poller, self.queue
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - stop poller if running."""
        if self.poller and self.poller.running:
            self.poller.stop()
            logger.info("MockPollerContext: Stopped poller")
        
        # Clear queue
        while not self.queue.empty():
            self.queue.get()
        
        logger.info("Exited MockPollerContext")
        return False  # Don't suppress exceptions
