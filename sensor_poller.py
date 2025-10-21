import threading
import time
import random
import logging
import os

from dotenv import load_dotenv
from queue import Queue

try:
    from .tongdy_sensor import TongdySensor
    from .type_k_sensor import TypeKSensor
except ImportError:
    from tongdy_sensor import TongdySensor
    from type_k_sensor import TypeKSensor

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
port = os.getenv("MODBUS_PORT", "/dev/ttyUSB0")


# Sensor Poller class
class SensorPoller:

    def __init__(self,
                 polling_interval: int = 60,
                 polling_jitter: tuple = (0.02, 0.08),
                 ui_queue: Queue = Queue()):

        self.sensors = [
            TongdySensor(sensor_address=2, port=port, is_VOC=True),
            TongdySensor(sensor_address=3, port=port, is_VOC=False),
            TypeKSensor(sensor_address=51, port=port)
        ]

        self.polling_interval = polling_interval
        self.polling_jitter = polling_jitter
        self.ui_queue = ui_queue
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        """
        Start the sensor polling thread.
        Returns:
            True: Successfully started the polling thread
            False: Already running (thread is already active)
        Raises:
            Exception: If there's an error creating or starting the thread
        """
        if self.running:
            logger.info("SensorPoller already running, ignoring start")
            return False

        try:
            self.running = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("SensorPoller started successfully")
            return True
        except Exception as e:
            self.running = False
            logger.error(f"Failed to start SensorPoller: {e}")
            raise

    def stop(self) -> bool:
        """
        Stop the sensor polling thread.
        Returns:
            True: Successfully stopped the polling thread
            False: Already stopped (no active thread or not running)
        Raises:
            Exception: If error stopping thread or timeout occurs
        """
        if not self.running and not self.thread:
            logger.info("SensorPoller already stopped, ignoring stop")
            return False

        try:
            self.running = False
            self._stop_event.set()
            if self.thread:
                self.thread.join(timeout=10) 

                if self.thread.is_alive():
                    logger.error("Thread did not stop within 10 seconds")
                    raise TimeoutError(
                        "SensorPoller thread failed to stop"
                    )

                self.thread = None
                logger.info("SensorPoller stopped successfully")
                return True
            else:
                logger.info("SensorPoller stopped (no active thread)")
                return True

        except TimeoutError:
            raise
        except Exception as e:
            logger.error(f"Error stopping SensorPoller: {e}")
            raise

    def _run(self):
        next_poll = time.time()

        while self.running:
            for s in self.sensors:
                try:
                    vals = s.read_values() or {}
                except Exception as e:
                    logger.error(f"Unhandled error reading values from {getattr(s, 'sensor_address', 'Unknown')} : {e}")
                    logger.error(f"Defaulting to empty values for {getattr(s, 'sensor_address', 'Unknown')}")
                    vals = {"co2": None, "temperature": None, "humidity": None}

                co2 = vals.get("co2")
                temperature = vals.get("temperature")
                humidity = vals.get("humidity")

                self.ui_queue.put({
                    "type": "live_sensor_data",
                    "data": {
                        "co2": co2,
                        "temperature": temperature,
                        "humidity": humidity,
                        "sensor_id": s.sensor_id if hasattr(s, "sensor_id") else 0
                    }
                })

                if self.polling_jitter:
                    time.sleep(random.uniform(
                                self.polling_jitter[0],
                                self.polling_jitter[1]
                                ))

            next_poll = next_poll + self.polling_interval
            sleep_time = max(0, next_poll - time.time())
            if sleep_time > 0:
                self._stop_event.wait(timeout=sleep_time)
            else:
                next_poll = time.time()