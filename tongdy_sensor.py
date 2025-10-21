import logging
import minimalmodbus
import serial
import time
import threading

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# MARK: RS485 BUS MANAGER
class RS485BusManager:
    """
    Bus manager for managing bus access (fixing timeout)
    Magic shenanigans from the depths of threading
    """

    _locks = {}
    _last_access = {}
    _global_lock = threading.Lock()

    @classmethod
    def _ensure_port(cls, port: str):
        with cls._global_lock:
            if port not in cls._locks:
                cls._locks[port] = threading.Lock()
                cls._last_access[port] = 0.0
            return cls._locks[port]

    @classmethod
    def access(cls, port: str, pre_delay: float = 0.03):
        lock = cls._ensure_port(port)

        class _Ctx:
            def __enter__(self_inner):
                lock.acquire()
                now = time.time()
                last = cls._last_access.get(port, 0.0)
                wait = pre_delay - (now - last)
                if wait > 0:
                    time.sleep(wait)
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                cls._last_access[port] = time.time()
                lock.release()
                return False

        return _Ctx()


# MARK: TONGDY SENSOR CLASS
class TongdySensor:
    def __init__(self,
                 sensor_address: int, 
                 port: str = "/dev/ttyUSB0",
                 baudrate: int = 19200,
                 timeout: float = 1.5,
                 is_VOC: bool = False,
                 pre_delay: float = 0.03):

        self.sensor_id = sensor_address
        self.sensor_address = sensor_address
        self.sensor_type = "tongdy"
        self.is_VOC = is_VOC
        self.pre_delay = pre_delay
        self.max_retries = 3    # maximum number of retries for reading
        self.retry_delay = 0.5  # delay between retries in seconds
        self.MODBUS_ADDRESS = self._get_address(self.is_VOC)

        try:
            self.instrument = minimalmodbus.Instrument(port=port, slaveaddress=sensor_address)
            self.instrument.serial.baudrate = baudrate
            self.instrument.serial.bytesize = 8
            self.instrument.serial.parity = serial.PARITY_NONE
            self.instrument.serial.stopbits = 1
            self.instrument.serial.timeout = timeout  # seconds
            self.instrument.mode = minimalmodbus.MODE_RTU
            self.instrument.clear_buffers_before_each_transaction = True
            self.instrument.close_port_after_each_call = False

            logger.info(f"Tongdy sensor connected on port {port} with address {sensor_address}")

        except Exception as e:
            logger.exception(f"Failed to initialize Tongdy sensor on port {port} with address {sensor_address}: {e}")
            self.instrument = None

    def read_values(self) -> dict:
        """
        Return a dictionary with CO2, temperature, and humidity readings.
        Returns:
        {
            "co2": int,          # CO2 concentration in ppm
            "temperature": float, # Temperature in °C 2 digit
            "humidity": float     # Relative Humidity in % 2 digit
        }
        """

        if not self.instrument:
            logger.error("Minimal MODBUS Instrument not initialized.")
            return {"co2": None, "temperature": None, "humidity": None}

        retries = 0
        while retries < self.max_retries:
            retries +=1
            try:
                with RS485BusManager.access(self.instrument.serial.port, self.pre_delay):

                    co2 = self.instrument.read_float(
                        registeraddress=self.MODBUS_ADDRESS["ADDR_CO2"],
                        functioncode=self.MODBUS_ADDRESS["FUNCTION_CODE"],
                        number_of_registers=2)

                    temperature = self.instrument.read_float(
                        registeraddress=self.MODBUS_ADDRESS["ADDR_TEMP"],
                        functioncode=self.MODBUS_ADDRESS["FUNCTION_CODE"],
                        number_of_registers=2)

                    humidity = self.instrument.read_float(
                        registeraddress=self.MODBUS_ADDRESS["ADDR_HUMID"],
                        functioncode=self.MODBUS_ADDRESS["FUNCTION_CODE"],
                        number_of_registers=2)

                logger.info(f"Sensor {self.sensor_id} Readings -")
                logger.info(f"CO2: {co2} ppm, Temperature: {temperature} °C, Humidity: {humidity} %")

                return {
                    "co2": round(co2, 2),
                    "temperature": round(temperature, 2),
                    "humidity": round(humidity, 2),
                    "sensor_id": self.sensor_id,
                    "sensor_type": self.sensor_type
                }
            except Exception as e:
                logger.error(f"Attempt {retries} - Failed to read from sensor {self.sensor_id}: {e}")
                time.sleep(self.retry_delay)

        # All attempts failed
        logger.error(f"All {self.max_retries} attempts failed for sensor {self.sensor_id}. Returning None values.")
        return {"co2": None, "temperature": None, "humidity": None}

    def _get_address(self, is_VOC: bool = False) -> dict:
        """Get the Modbus address of the sensor based on sensor type."""
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