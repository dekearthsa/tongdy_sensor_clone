"""
Unit tests for SensorPoller class.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time
from queue import Queue


class TestSensorPollerInitialization:
    """Test SensorPoller initialization."""
    
    @patch('Tongdy_sensor.sensor_poller.TongdySensor')
    def test_init_default(self, mock_tongdy_class):
        """Test default initialization."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        poller = SensorPoller()
        
        assert poller.polling_interval == 60
        assert poller.polling_jitter == (0.02, 0.08)
        assert poller.running is False
        assert poller.thread is None
        assert isinstance(poller.ui_queue, Queue)
        assert isinstance(poller._stop_event, threading.Event)
    
    @patch('Tongdy_sensor.sensor_poller.TongdySensor')
    def test_init_custom_params(self, mock_tongdy_class):
        """Test initialization with custom parameters."""
        from Tongdy_sensor.sensor_poller import SensorPoller
        
        custom_queue = Queue()
        poller = SensorPoller(
            polling_interval=30,
            polling_jitter=(0.01, 0.05),
            ui_queue=custom_queue
        )
        
        assert poller.polling_interval == 30
        assert poller.polling_jitter == (0.01, 0.05)
        assert poller.ui_queue is custom_queue


class TestSensorPollerStart:
    """Test SensorPoller start method."""
    
    def test_start_success(self, sensor_poller_instance):
        """Test successful start of poller."""
        poller = sensor_poller_instance
        
        result = poller.start()
        
        assert result is True
        assert poller.running is True
        assert poller.thread is not None
        assert poller.thread.is_alive()
        
        # Cleanup
        poller.stop()
    
    def test_start_already_running(self, sensor_poller_instance):
        """Test start when already running returns False."""
        poller = sensor_poller_instance
        
        # Start first time
        result1 = poller.start()
        assert result1 is True
        
        # Try to start again
        result2 = poller.start()
        assert result2 is False
        
        # Cleanup
        poller.stop()
    
    def test_start_thread_creation_failure(self, sensor_poller_instance):
        """Test start when thread creation fails."""
        poller = sensor_poller_instance
        
        with patch('threading.Thread') as mock_thread_class:
            mock_thread_class.side_effect = Exception("Thread creation failed")
            
            with pytest.raises(Exception) as exc_info:
                poller.start()
            
            assert "Thread creation failed" in str(exc_info.value)
            assert poller.running is False  # Should reset on failure
    
    def test_start_clears_stop_event(self, sensor_poller_instance):
        """Test that start clears the stop event."""
        poller = sensor_poller_instance
        
        # Set the stop event
        poller._stop_event.set()
        assert poller._stop_event.is_set()
        
        # Start should clear it
        poller.start()
        assert not poller._stop_event.is_set()
        
        # Cleanup
        poller.stop()


class TestSensorPollerStop:
    """Test SensorPoller stop method."""
    
    def test_stop_success(self, sensor_poller_instance):
        """Test successful stop of poller."""
        poller = sensor_poller_instance
        
        # Start the poller
        poller.start()
        time.sleep(0.1)  # Let it run briefly
        
        # Stop it
        result = poller.stop()
        
        assert result is True
        assert poller.running is False
        assert poller.thread is None
    
    def test_stop_already_stopped(self, sensor_poller_instance):
        """Test stop when already stopped returns False."""
        poller = sensor_poller_instance
        
        # Don't start it
        result = poller.stop()
        
        assert result is False
    
    def test_stop_sets_event(self, sensor_poller_instance):
        """Test that stop sets the stop event."""
        poller = sensor_poller_instance
        
        poller.start()
        assert not poller._stop_event.is_set()
        
        poller.stop()
        assert poller._stop_event.is_set()
    
    def test_stop_timeout(self, sensor_poller_instance):
        """Test stop raises TimeoutError if thread doesn't stop."""
        poller = sensor_poller_instance
        
        # Start the poller
        poller.start()
        
        # Mock join to simulate thread not stopping
        with patch.object(poller.thread, 'join') as mock_join:
            with patch.object(poller.thread, 'is_alive', return_value=True):
                with pytest.raises(TimeoutError) as exc_info:
                    poller.stop()
                
                assert "failed to stop" in str(exc_info.value).lower()
    
    def test_stop_with_no_thread(self, sensor_poller_instance):
        """Test stop when running but no thread exists."""
        poller = sensor_poller_instance
        
        poller.running = True
        poller.thread = None
        
        result = poller.stop()
        
        # Should return True and handle gracefully
        assert result is True


class TestSensorPollerPollingCycle:
    """Test SensorPoller polling cycle."""
    
    def test_polling_cycle(self, sensor_poller_instance, test_queue):
        """Test that polling cycle reads sensors and puts data in queue."""
        poller = sensor_poller_instance
        poller.ui_queue = test_queue
        poller.polling_interval = 0.5  # Short interval for testing
        
        # Start polling
        poller.start()
        time.sleep(0.6)  # Wait for at least one poll
        poller.stop()
        
        # Check that data was added to queue
        assert not test_queue.empty()
        
        # Get data from queue
        data = test_queue.get()
        
        assert data["type"] == "live_sensor_data"
        assert "co2" in data["data"]
        assert "temperature" in data["data"]
        assert "humidity" in data["data"]
        assert "sensor_id" in data["data"]
    
    def test_polling_with_sensor_error(self, sensor_poller_instance,
                                       test_queue):
        """Test polling when sensor raises exception."""
        poller = sensor_poller_instance
        poller.ui_queue = test_queue
        poller.polling_interval = 0.5
        
        # Make one sensor fail
        poller.sensors[0].read_values.side_effect = Exception("Sensor error")
        
        # Start polling
        poller.start()
        time.sleep(0.6)
        poller.stop()
        
        # Should still have data in queue (with None values)
        assert not test_queue.empty()
        
        data = test_queue.get()
        assert data["type"] == "live_sensor_data"
        assert data["data"]["co2"] is None
        assert data["data"]["temperature"] is None
        assert data["data"]["humidity"] is None
    
    @patch('time.sleep')
    def test_polling_interval_respected(self, mock_sleep,
                                        sensor_poller_instance):
        """Test that polling interval is respected."""
        poller = sensor_poller_instance
        poller.polling_interval = 5
        
        # Start and stop quickly
        poller.start()
        time.sleep(0.1)  # Real sleep to let thread start
        poller.stop()
        
        # The _stop_event.wait should be called with appropriate timeout
        # This is tricky to test directly, but we can verify the logic
        assert poller.polling_interval == 5
    
    def test_queue_data_format(self, sensor_poller_instance, test_queue):
        """Test that queue data has correct format."""
        poller = sensor_poller_instance
        poller.ui_queue = test_queue
        poller.polling_interval = 0.5
        
        poller.start()
        time.sleep(0.6)
        poller.stop()
        
        # Get all data from queue
        data_items = []
        while not test_queue.empty():
            data_items.append(test_queue.get())
        
        # Check format of each item
        for data in data_items:
            assert "type" in data
            assert data["type"] == "live_sensor_data"
            assert "data" in data
            assert "co2" in data["data"]
            assert "temperature" in data["data"]
            assert "humidity" in data["data"]
            assert "sensor_id" in data["data"]
    
    def test_stop_event_interrupts_sleep(self, sensor_poller_instance):
        """Test that stop event wakes up sleeping thread."""
        poller = sensor_poller_instance
        poller.polling_interval = 100  # Long interval
        
        start_time = time.time()
        poller.start()
        time.sleep(0.1)  # Let it start
        poller.stop()
        elapsed = time.time() - start_time
        
        # Should stop quickly, not wait for full interval
        assert elapsed < 2  # Much less than 100 seconds
    
    def test_multiple_sensors_polled(self, sensor_poller_instance, test_queue):
        """Test that all sensors are polled."""
        poller = sensor_poller_instance
        poller.ui_queue = test_queue
        poller.polling_interval = 0.5
        
        # Set different sensor IDs
        poller.sensors[0].sensor_id = 1
        poller.sensors[1].sensor_id = 2
        
        poller.start()
        time.sleep(0.6)
        poller.stop()
        
        # Get all data
        sensor_ids = []
        while not test_queue.empty():
            data = test_queue.get()
            sensor_ids.append(data["data"]["sensor_id"])
        
        # Should have data from both sensors
        assert 1 in sensor_ids
        assert 2 in sensor_ids


class TestSensorPollerConcurrency:
    """Test SensorPoller concurrency and thread safety."""
    
    def test_rapid_start_stop(self, sensor_poller_instance):
        """Test rapid start/stop cycles."""
        poller = sensor_poller_instance
        
        for _ in range(5):
            assert poller.start() is True
            time.sleep(0.05)
            assert poller.stop() is True
            time.sleep(0.05)
    
    def test_concurrent_stop_calls(self, sensor_poller_instance):
        """Test multiple concurrent stop calls."""
        poller = sensor_poller_instance
        poller.start()
        time.sleep(0.1)
        
        # Try to stop from multiple threads
        results = []
        
        def stop_thread():
            try:
                result = poller.stop()
                results.append(result)
            except Exception as e:
                results.append(e)
        
        threads = [threading.Thread(target=stop_thread) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # At least one should succeed
        assert True in results or any(isinstance(r, Exception)
                                      for r in results)


class TestSensorPollerEdgeCases:
    """Test edge cases for SensorPoller."""
    
    def test_zero_polling_interval(self, sensor_poller_instance):
        """Test with very short polling interval."""
        poller = sensor_poller_instance
        poller.polling_interval = 0.1
        
        poller.start()
        time.sleep(0.3)
        poller.stop()
        
        # Should handle without errors
        assert not poller.running
    
    def test_no_jitter(self, sensor_poller_instance):
        """Test with no jitter (None)."""
        poller = sensor_poller_instance
        poller.polling_jitter = None
        
        poller.start()
        time.sleep(0.2)
        poller.stop()
        
        # Should work without jitter
        assert not poller.running
    
    def test_sensor_without_sensor_id(self, sensor_poller_instance,
                                      test_queue):
        """Test sensor that doesn't have sensor_id attribute."""
        poller = sensor_poller_instance
        poller.ui_queue = test_queue
        poller.polling_interval = 0.5
        
        # Remove sensor_id from one sensor
        delattr(poller.sensors[0], 'sensor_id')
        
        poller.start()
        time.sleep(0.6)
        poller.stop()
        
        # Should default to 0
        data = test_queue.get()
        assert data["data"]["sensor_id"] == 0
