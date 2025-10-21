# Quick Test Reference Guide

## 🚀 Common Commands

### Run All Tests
```bash
pytest Tongdy_sensor/tests/ -v
```

### Run with Coverage
```bash
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=html
```

### Run Specific Test File
```bash
pytest Tongdy_sensor/tests/test_tongdy_sensor.py -v
pytest Tongdy_sensor/tests/test_sensor_poller.py -v
pytest Tongdy_sensor/tests/test_integration.py -v
```

### Run Specific Test Class
```bash
pytest Tongdy_sensor/tests/test_sensor_poller.py::TestSensorPollerStart -v
```

### Run Specific Test
```bash
pytest Tongdy_sensor/tests/test_sensor_poller.py::TestSensorPollerStart::test_start_success -v
```

### Run Tests in Parallel
```bash
pytest Tongdy_sensor/tests/ -n auto
```

### Run with Detailed Output
```bash
pytest Tongdy_sensor/tests/ -vv -s
```

---

## 📊 Test Results (Current)

- **Total Tests**: 43
- **Passing**: 43 (100%)
- **Code Coverage**: 96%
- **Execution Time**: ~16 seconds

---

## 📁 Test Organization

| File | Tests | Purpose |
|------|-------|---------|
| `test_tongdy_sensor.py` | 12 | TongdySensor unit tests |
| `test_sensor_poller.py` | 22 | SensorPoller unit tests |
| `test_integration.py` | 9 | Integration tests |

---

## 🎯 What Each Test File Covers

### test_tongdy_sensor.py
- Sensor initialization (VOC/non-VOC)
- Modbus communication (mocked)
- Retry logic
- Error handling
- Address mapping
- RS485 bus manager

### test_sensor_poller.py
- Start/stop functionality
- Thread lifecycle
- Polling cycles
- Queue operations
- Error handling
- Concurrency
- Edge cases

### test_integration.py
- End-to-end polling
- Multiple sensor coordination
- Error recovery
- Thread safety
- Long-running scenarios

---

## 🔍 Debugging Failed Tests

### Show Full Traceback
```bash
pytest Tongdy_sensor/tests/ -v --tb=long
```

### Show Only Failed Tests
```bash
pytest Tongdy_sensor/tests/ --lf
```

### Show Print Statements
```bash
pytest Tongdy_sensor/tests/ -v -s
```

### Stop on First Failure
```bash
pytest Tongdy_sensor/tests/ -x
```

---

## 📈 Coverage Commands

### Terminal Report
```bash
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=term-missing
```

### HTML Report (Better visualization)
```bash
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=html
# Then open: htmlcov/index.html
```

### XML Report (For CI/CD)
```bash
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=xml
```

---

## ✅ Pre-Commit Checklist

Before committing code:

```bash
# 1. Run all tests
pytest Tongdy_sensor/tests/ -v

# 2. Check coverage
pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=term-missing

# 3. Run linting (if configured)
# flake8 Tongdy_sensor/
# black Tongdy_sensor/

# 4. Ensure all tests pass
echo "All tests should be passing!"
```

---

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'pytest'"
**Solution:**
```bash
pip install -r tests/requirements-test.txt
```

### Issue: "ModuleNotFoundError: No module named 'minimalmodbus'"
**Solution:**
```bash
pip install minimalmodbus pyserial python-dotenv
```

### Issue: Tests timeout or hang
**Solution:**
- Check if `poller.stop()` is called in cleanup
- Verify threading Event is properly set
- Use `pytest --timeout=30` to set global timeout

### Issue: Import errors in tests
**Solution:**
```bash
# From project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or install in development mode
pip install -e .
```

---

## 🎨 Adding New Tests

### Template for New Test
```python
def test_my_new_feature(sensor_poller_instance, test_queue):
    """Brief description of what this tests."""
    # Arrange
    poller = sensor_poller_instance
    poller.polling_interval = 0.5
    
    # Act
    poller.start()
    time.sleep(0.6)
    poller.stop()
    
    # Assert
    assert not test_queue.empty()
    data = test_queue.get()
    assert data["type"] == "live_sensor_data"
```

### Steps to Add Test
1. Determine which file (unit or integration)
2. Add to appropriate test class
3. Use fixtures from `conftest.py`
4. Follow naming convention: `test_<feature>_<scenario>`
5. Add docstring explaining what's tested
6. Run test to verify it passes
7. Check coverage improved

---

## 📚 Documentation

- **Full Details**: See `TEST_IMPLEMENTATION_SUMMARY.md`
- **Test Docs**: See `tests/README.md`
- **Fixtures**: See `tests/conftest.py`

---

## 🎯 Test Quality Metrics

Current metrics:
- ✅ Code coverage: 96%
- ✅ All tests passing: 100%
- ✅ Execution time: ~16s
- ✅ No flaky tests
- ✅ No hardware dependencies

Goals:
- Maintain >90% coverage
- Keep execution time <30s
- Zero flaky tests
- All tests independent

---

## 🔄 Continuous Integration

For CI/CD pipelines, use:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r Tongdy_sensor/tests/requirements-test.txt
    pip install minimalmodbus pyserial python-dotenv
    pytest Tongdy_sensor/tests/ --cov=Tongdy_sensor --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v2
```

---

## 💡 Tips

1. **Run tests often** - Catch issues early
2. **Check coverage** - Ensure new code is tested
3. **Use fixtures** - Don't repeat setup code
4. **Mock external deps** - Keep tests fast and reliable
5. **Descriptive names** - Make failures easy to understand
6. **One assertion focus** - Each test should verify one thing
7. **Clean up resources** - Prevent test pollution
8. **Test edge cases** - Not just happy paths

---

## 📞 Need Help?

- Check `tests/README.md` for detailed documentation
- Review `conftest.py` for available fixtures
- Look at existing tests for examples
- Run with `-vv -s` for detailed output
