# Installation Guide for Tongdy Sensor Project

## Quick Start

### 1. Create Virtual Environment (Recommended)

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

#### For Production Use:
```powershell
pip install -r requirements.txt
```

#### For Development/Testing:
```powershell
pip install -r requirements-dev.txt
```

This will install:
- **Core dependencies** (minimalmodbus, pyserial)
- **Testing framework** (pytest and plugins)
- **Code coverage tools**

### 3. Verify Installation

```powershell
# Check Python version (3.8+ required)
python --version

# Run tests to verify everything works
pytest tests/ -v

# Check code coverage
pytest tests/ --cov=. --cov-report=html
```

## Package Structure

```
Tongdy_sensor/
├── requirements.txt           # Core dependencies
├── requirements-dev.txt       # Development dependencies
├── sensor_poller.py          # Main polling class
├── tongdy_sensor.py          # Sensor communication
├── mock_sensor.py            # Mock sensor for testing
├── mock_sensor_poller.py     # Mock poller utilities
├── tests/
│   ├── requirements-test.txt # Test-specific dependencies
│   ├── conftest.py           # pytest fixtures
│   ├── test_tongdy_sensor.py
│   ├── test_sensor_poller.py
│   └── test_integration.py
└── examples/
    ├── demo_mock_sensors.py
    └── example_mock_usage.py
```

## Dependencies Explained

### Core Dependencies (`requirements.txt`)
- **minimalmodbus (>=2.1.1)**: Modbus RTU communication protocol
- **pyserial (>=3.5)**: Serial port (RS485/RS232) communication
- **python-dotenv (>=1.0.0)**: Environment variable management (optional)

### Development Dependencies (`requirements-dev.txt`)
- **pytest (>=8.0.0)**: Testing framework
- **pytest-mock (>=3.15.0)**: Mocking utilities for tests
- **pytest-cov (>=4.0.0)**: Code coverage measurement
- **pytest-timeout (>=2.4.0)**: Timeout protection for tests
- **pytest-xdist (>=3.8.0)**: Parallel test execution
- **coverage (>=7.0.0)**: Coverage reporting
- **colorama (>=0.4.6)**: Colored terminal output (Windows)

## Working Without Hardware

The project includes a complete mock sensor system for development without physical hardware:

```python
from mock_sensor import MockSensorFactory
from mock_sensor_poller import create_mock_poller

# Create mock poller with 2 sensors
poller = create_mock_poller(
    sensor_addresses=[2, 3],
    sensor_type='stable'
)

# Use just like real sensors!
poller.start()
# ... your code ...
poller.stop()
```

See `examples/example_mock_usage.py` for 8 detailed examples.

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`, make sure:
1. Virtual environment is activated
2. Dependencies are installed: `pip install -r requirements-dev.txt`
3. You're running from the correct directory

### Serial Port Issues (Windows)
- COM ports require administrator privileges on some systems
- Check Device Manager for available COM ports
- Install USB-to-RS485 adapter drivers if needed

### Test Failures
```powershell
# Run with verbose output
pytest tests/ -v -s

# Run specific test file
pytest tests/test_tongdy_sensor.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing
```

## Upgrading Dependencies

```powershell
# Upgrade all packages to latest versions
pip install --upgrade -r requirements-dev.txt

# Upgrade specific package
pip install --upgrade minimalmodbus

# Check for outdated packages
pip list --outdated
```

## Creating a Frozen Requirements File

For production deployment, create a frozen requirements file with exact versions:

```powershell
pip freeze > requirements-frozen.txt
```

This captures the exact versions currently installed for reproducible deployments.

## Additional Resources

- [MOCK_SENSOR_GUIDE.md](./documentation/MOCK_SENSOR_GUIDE.md) - Complete guide to mock sensors
- [QUICK_TEST_GUIDE.md](./documentation/QUICK_TEST_GUIDE.md) - Testing instructions
- [README.md](README.md) - Project overview
