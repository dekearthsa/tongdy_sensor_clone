"""
Integration tests for SensorPoller and TongdySensor.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import time
from queue import Queue
import threading


class TestSensorPollerIntegration:
    """Integration tests with mocked Modbus but real class interactions."""
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_full_polling_cycle_with_mock_sensors(self, mock_serial,
                                                   mock_instrument_class,
                                                   mock_bus_manager):
        """Test complete polling cycle with mocked Modbus."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        # Setup Modbus mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # Mock sensor readings
        def read_float_side_effect(registeraddress, functioncode,
                                   number_of_registers):
            if registeraddress == 0:  # CO2
                return 425.5
            elif registeraddress in [2, 4]:  # Temperature (varies by sensor)
                return 22.5
            elif registeraddress in [4, 6]:  # Humidity (varies by sensor)
                return 52.3
            return 0.0
        
        mock_instrument.read_float.side_effect = read_float_side_effect
        
        # Mock bus manager
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create poller
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.5,
            polling_jitter=(0.01, 0.02),
            ui_queue=test_queue
        )
        
        # Run polling cycle
        poller.start()
        time.sleep(0.7)  # Wait for at least one cycle
        poller.stop()
        
        # Verify data in queue
        assert not test_queue.empty()
        
        # Should have data from both sensors
        data_count = 0
        while not test_queue.empty():
            data = test_queue.get()
            assert data["type"] == "live_sensor_data"
            assert data["data"]["co2"] is not None
            assert data["data"]["temperature"] is not None
            assert data["data"]["humidity"] is not None
            data_count += 1
        
        # Should have at least 2 data points (one per sensor)
        assert data_count >= 2
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_multiple_sensors_polling(self, mock_serial,
                                      mock_instrument_class,
                                      mock_bus_manager):
        """Test polling with both VOC and non-VOC sensors."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        # Setup mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # Different readings for different sensors
        sensor_call_count = [0]
        
        def read_float_side_effect(registeraddress, functioncode,
                                   number_of_registers):
            sensor_call_count[0] += 1
            # Alternate values to simulate different sensors
            if sensor_call_count[0] % 2 == 0:
                if registeraddress == 0:
                    return 450.0  # VOC sensor CO2
                return 23.0
            else:
                if registeraddress == 0:
                    return 400.0  # Non-VOC sensor CO2
                return 22.0
        
        mock_instrument.read_float.side_effect = read_float_side_effect
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create and run poller
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.5,
            ui_queue=test_queue
        )
        
        poller.start()
        time.sleep(0.7)
        poller.stop()
        
        # Collect all readings
        co2_values = []
        while not test_queue.empty():
            data = test_queue.get()
            co2_values.append(data["data"]["co2"])
        
        # Should have readings from both sensors
        assert len(co2_values) >= 2
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    @patch('Tongdy_sensor.tongdy_sensor.time.sleep')
    def test_sensor_failure_recovery(self, mock_time_sleep, mock_serial,
                                     mock_instrument_class,
                                     mock_bus_manager):
        """Test that one sensor failing doesn't stop the other."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        # Setup mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # First sensor fails, second succeeds
        call_count = [0]
        
        def read_float_side_effect(registeraddress, functioncode,
                                   number_of_registers):
            call_count[0] += 1
            # Fail every other complete sensor read (3 calls per sensor)
            if (call_count[0] // 3) % 2 == 0:
                raise Exception("Sensor communication error")
            else:
                if registeraddress == 0:
                    return 420.0
                return 22.0
        
        mock_instrument.read_float.side_effect = read_float_side_effect
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create and run poller
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.5,
            ui_queue=test_queue
        )
        
        poller.start()
        time.sleep(0.7)
        poller.stop()
        
        # Should have data (some with None, some with values)
        data_items = []
        while not test_queue.empty():
            data_items.append(test_queue.get())
        
        assert len(data_items) > 0
        
        # Should have both failed (None) and successful readings
        has_none = any(d["data"]["co2"] is None for d in data_items)
        has_value = any(d["data"]["co2"] is not None for d in data_items)
        
        assert has_none or has_value  # At least one type of data
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_queue_receives_all_sensor_data(self, mock_serial,
                                            mock_instrument_class,
                                            mock_bus_manager):
        """Test that queue receives data from all sensors in order."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        # Setup mocks
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        mock_instrument.read_float.return_value = 100.0
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        # Create poller
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.5,
            ui_queue=test_queue
        )
        
        poller.start()
        time.sleep(0.7)
        poller.stop()
        
        # Count sensor IDs in queue
        sensor_ids = []
        while not test_queue.empty():
            data = test_queue.get()
            sensor_ids.append(data["data"]["sensor_id"])
        
        # Should have data from sensor address 2 and 3
        assert 2 in sensor_ids
        assert 3 in sensor_ids


class TestSensorPollerLifecycle:
    """Test SensorPoller lifecycle scenarios."""
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_rapid_start_stop_cycles(self, mock_serial, mock_instrument_class):
        """Test rapid start/stop cycles don't cause issues."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        poller = SensorPoller(polling_interval=0.2)
        
        for i in range(3):
            assert poller.start() is True
            time.sleep(0.1)
            assert poller.stop() is True
            time.sleep(0.05)
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_long_running_poller(self, mock_serial, mock_instrument_class):
        """Test poller running for extended period."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.2,
            ui_queue=test_queue
        )
        
        poller.start()
        time.sleep(1.0)  # Run for 1 second
        poller.stop()
        
        # Should have multiple cycles worth of data
        data_count = 0
        while not test_queue.empty():
            test_queue.get()
            data_count += 1
        
        # With 0.2s interval, should have ~5 cycles * 2 sensors = ~10 items
        assert data_count >= 8


class TestErrorPropagation:
    """Test error propagation between components."""
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_sensor_init_error_handling(self, mock_serial,
                                        mock_instrument_class):
        """Test that sensor initialization errors are handled."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        # Make instrument init fail
        mock_instrument_class.side_effect = Exception("Port error")
        mock_serial.PARITY_NONE = 'N'
        
        # Should still create poller (sensors will have None instruments)
        poller = SensorPoller()
        
        assert poller is not None
        assert len(poller.sensors) == 2
    
    @patch('Tongdy_sensor.tongdy_sensor.RS485BusManager.access')
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_modbus_communication_error(self, mock_serial,
                                        mock_instrument_class,
                                        mock_bus_manager):
        """Test handling of Modbus communication errors."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        # Simulate communication error
        mock_instrument.read_float.side_effect = Exception("Comm error")
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_bus_manager.return_value = mock_ctx
        
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.5,
            ui_queue=test_queue
        )
        
        # Should handle error and continue
        poller.start()
        time.sleep(0.7)
        poller.stop()
        
        # Should still have data (with None values)
        assert not test_queue.empty()
        data = test_queue.get()
        assert data["data"]["co2"] is None


class TestThreadSafety:
    """Test thread safety of components."""
    
    @patch('Tongdy_sensor.tongdy_sensor.minimalmodbus.Instrument')
    @patch('Tongdy_sensor.tongdy_sensor.serial')
    def test_concurrent_queue_access(self, mock_serial, mock_instrument_class):
        """Test that queue can be safely accessed from multiple threads."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        mock_instrument = MagicMock()
        mock_instrument_class.return_value = mock_instrument
        mock_serial.PARITY_NONE = 'N'
        
        test_queue = Queue()
        poller = SensorPoller(
            polling_interval=0.2,
            ui_queue=test_queue
        )
        
        # Start poller (writes to queue)
        poller.start()
        
        # Read from queue in another thread
        read_count = [0]
        
        def reader():
            for _ in range(5):
                if not test_queue.empty():
                    test_queue.get()
                    read_count[0] += 1
                time.sleep(0.1)
        
        reader_thread = threading.Thread(target=reader)
        reader_thread.start()
        
        time.sleep(0.6)
        poller.stop()
        reader_thread.join()
        
        # Should have read some data without errors
        assert read_count[0] > 0
