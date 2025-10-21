"""
Unit tests for TongdySensor class.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import minimalmodbus
import serial


class TestTongdySensorInitialization:
    """Test TongdySensor initialization."""
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_init_voc_sensor(self, mock_serial, mock_instrument_class):
        """Test initialization of VOC sensor with correct addresses."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        sensor = TongdySensor(
            sensor_address=2,
            port="/dev/ttyUSB0",
            is_VOC=True
        )
        
        assert sensor.sensor_id == 2
        assert sensor.sensor_address == 2
        assert sensor.is_VOC is True
        assert sensor.MODBUS_ADDRESS["ADDR_CO2"] == 0
        assert sensor.MODBUS_ADDRESS["ADDR_TEMP"] == 4
        assert sensor.MODBUS_ADDRESS["ADDR_HUMID"] == 6
        assert sensor.MODBUS_ADDRESS["FUNCTION_CODE"] == 4
        assert sensor.instrument is not None
        
        # Verify instrument was configured
        mock_instrument_class.assert_called_once_with(
            port="/dev/ttyUSB0",
            slaveaddress=2
        )
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_init_non_voc_sensor(self, mock_serial, mock_instrument_class):
        """Test initialization of non-VOC sensor with correct addresses."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        sensor = TongdySensor(
            sensor_address=3,
            port="/dev/ttyUSB0",
            is_VOC=False
        )
        
        assert sensor.sensor_id == 3
        assert sensor.sensor_address == 3
        assert sensor.is_VOC is False
        assert sensor.MODBUS_ADDRESS["ADDR_CO2"] == 0
        assert sensor.MODBUS_ADDRESS["ADDR_TEMP"] == 2
        assert sensor.MODBUS_ADDRESS["ADDR_HUMID"] == 4
        assert sensor.MODBUS_ADDRESS["FUNCTION_CODE"] == 4
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_init_custom_parameters(self, mock_serial, mock_instrument_class):
        """Test initialization with custom parameters."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        sensor = TongdySensor(
            sensor_address=5,
            port="/dev/ttyUSB1",
            baudrate=9600,
            timeout=2.0,
            is_VOC=True,
            pre_delay=0.05
        )
        
        assert sensor.pre_delay == 0.05
        assert mock_instrument.serial.baudrate == 9600
        assert mock_instrument.serial.timeout == 2.0
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_init_port_failure(self, mock_serial, mock_instrument_class):
        """Test initialization when port connection fails."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        mock_instrument_class.side_effect = Exception("Port not found")
        mock_serial.PARITY_NONE = 'N'
        
        sensor = TongdySensor(
            sensor_address=2,
            port="/dev/invalid",
            is_VOC=False
        )
        
        # Should handle exception and set instrument to None
        assert sensor.instrument is None


class TestTongdySensorReadValues:
    """Test TongdySensor read_values method."""
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_read_values_success(self, mock_serial, mock_instrument_class,
                                  mock_bus_manager):
        """Test successful reading of sensor values."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        # Setup mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # Mock read_float to return different values based on address
        def read_float_side_effect(registeraddress, functioncode,
                                   number_of_registers):
            if registeraddress == 0:  # CO2
                return 450.25
            elif registeraddress == 2:  # Temperature
                return 23.5
            elif registeraddress == 4:  # Humidity
                return 55.2
            return 0.0
        
        mock_instrument.read_float.side_effect = read_float_side_effect
        
        # Mock bus manager context
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create sensor and read values
        sensor = TongdySensor(sensor_address=3, is_VOC=False)
        result = sensor.read_values()
        
        assert result["co2"] == 450.25
        assert result["temperature"] == 23.5
        assert result["humidity"] == 55.2
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    @patch('Tongdy_sensor.tongdy_sensor.time.sleep')
    def test_read_values_retry_success(self, mock_sleep, mock_serial,
                                       mock_instrument_class,
                                       mock_bus_manager):
        """Test reading succeeds after retry."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        # Setup mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # First attempt fails, second succeeds
        attempt_count = [0]
        
        def read_float_side_effect(registeraddress, functioncode,
                                   number_of_registers):
            # Fail on first attempt (all 3 register reads)
            # Succeed on second attempt
            if attempt_count[0] == 0:
                raise Exception("Modbus read error")
            # Success on subsequent attempts
            if registeraddress == 0:
                return 400.0
            elif registeraddress == 2:
                return 22.0
            elif registeraddress == 4:
                return 50.0
            return 0.0
        
        mock_instrument.read_float.side_effect = read_float_side_effect
        
        # Mock bus manager context - track entry count
        call_count = [0]
        
        def mock_enter(*args):
            call_count[0] += 1
            if call_count[0] > 1:
                # After first failed attempt
                attempt_count[0] = 1
            return MagicMock()
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = mock_enter
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create sensor and read values
        sensor = TongdySensor(sensor_address=3, is_VOC=False)
        result = sensor.read_values()
        
        assert result["co2"] == 400.0
        assert result["temperature"] == 22.0
        assert result["humidity"] == 50.0
        assert mock_sleep.call_count >= 1  # Should have retried
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    @patch('Tongdy_sensor.tongdy_sensor.time.sleep')
    def test_read_values_all_retries_fail(self, mock_sleep, mock_serial,
                                          mock_instrument_class,
                                          mock_bus_manager):
        """Test reading fails after all retries."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        # Setup mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # All calls fail
        mock_instrument.read_float.side_effect = Exception("Modbus error")
        
        # Mock bus manager context
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create sensor and read values
        sensor = TongdySensor(sensor_address=3, is_VOC=False)
        result = sensor.read_values()
        
        assert result["co2"] is None
        assert result["temperature"] is None
        assert result["humidity"] is None
        assert mock_sleep.call_count == 3  # max_retries
    
    def test_read_values_no_instrument(self):
        """Test reading when instrument is None."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        with patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument') \
                as mock_inst:
            mock_inst.side_effect = Exception("Init failed")
            
            sensor = TongdySensor(sensor_address=3, is_VOC=False)
            result = sensor.read_values()
            
            assert result["co2"] is None
            assert result["temperature"] is None
            assert result["humidity"] is None


class TestTongdySensorHelperMethods:
    """Test TongdySensor helper methods."""
    
    def test_get_address_voc(self):
        """Test _get_address for VOC sensor."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        with patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument'):
            sensor = TongdySensor(sensor_address=2, is_VOC=True)
            addresses = sensor._get_address(is_VOC=True)
            
            assert addresses["ADDR_CO2"] == 0
            assert addresses["ADDR_TEMP"] == 4
            assert addresses["ADDR_HUMID"] == 6
            assert addresses["FUNCTION_CODE"] == 4
    
    def test_get_address_non_voc(self):
        """Test _get_address for non-VOC sensor."""
        from Tongdy_sensor.tongdy_sensor import TongdySensor
        
        with patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument'):
            sensor = TongdySensor(sensor_address=3, is_VOC=False)
            addresses = sensor._get_address(is_VOC=False)
            
            assert addresses["ADDR_CO2"] == 0
            assert addresses["ADDR_TEMP"] == 2
            assert addresses["ADDR_HUMID"] == 4
            assert addresses["FUNCTION_CODE"] == 4


class TestRS485BusManager:
    """Test RS485BusManager class."""
    
    def test_bus_manager_context(self):
        """Test bus manager context manager."""
        from Tongdy_sensor.tongdy_sensor import RS485BusManager
        
        port = "/dev/test"
        
        with RS485BusManager.access(port, pre_delay=0.01) as ctx:
            assert ctx is not None
            # Should acquire lock
            assert port in RS485BusManager._locks
    
    def test_bus_manager_thread_safety(self):
        """Test bus manager prevents concurrent access."""
        from Tongdy_sensor.tongdy_sensor import RS485BusManager
        import threading
        import time
        
        port = "/dev/test"
        access_log = []
        
        def access_bus(thread_id):
            with RS485BusManager.access(port, pre_delay=0.01):
                access_log.append(('enter', thread_id, time.time()))
                time.sleep(0.05)  # Simulate work
                access_log.append(('exit', thread_id, time.time()))
        
        # Create two threads
        t1 = threading.Thread(target=access_bus, args=(1,))
        t2 = threading.Thread(target=access_bus, args=(2,))
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Check that accesses didn't overlap
        assert len(access_log) == 4
        
        # Find enter/exit pairs
        thread_1_enter = next(t for t in access_log
                             if t[0] == 'enter' and t[1] == 1)[2]
        thread_1_exit = next(t for t in access_log
                            if t[0] == 'exit' and t[1] == 1)[2]
        thread_2_enter = next(t for t in access_log
                             if t[0] == 'enter' and t[1] == 2)[2]
        thread_2_exit = next(t for t in access_log
                            if t[0] == 'exit' and t[1] == 2)[2]
        
        # One thread should complete before the other starts
        assert (thread_1_exit <= thread_2_enter or
                thread_2_exit <= thread_1_enter)
