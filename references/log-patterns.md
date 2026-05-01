# Log Patterns Reference

Common log patterns for firmware development organized by platform and severity.

## ESP-IDF Patterns

### Fatal Errors (Require Immediate Action)

| Pattern | Regex | Example | Typical Cause |
|---------|-------|---------|---------------|
| Guru Meditation | `Guru Meditation` | `Guru Meditation Error: Core 0 panic'ed (LoadProhibited)` | Memory access violation, null pointer |
| Stack Overflow | `Stack overflow` | `***ERROR*** A stack overflow in task main` | Task stack too small |
| Abort | `abort\(\)` | `abort() was called at PC 0x4008...` | Assertion failure, unhandled exception |
| Core Panic | `Core \d+ panic` | `Core 0 panic'ed (IntegerDivideByZero)` | Arithmetic error, illegal instruction |
| Assert Failed | `assert.*failed` | `assert failed: xQueueGiveMutexRecursive` | FreeRTOS assertion |

### Errors (Should Be Fixed)

| Pattern | Regex | Example | Typical Cause |
|---------|-------|---------|---------------|
| ESP Error | `E \(\d+\)` | `E (1234) main: Failed to initialize I2C` | General error with tag |
| Wi-Fi Fail | `wifi:.*failed` | `wifi: Association refused` | Connection rejected |
| Wi-Fi Timeout | `wifi:.*timeout` | `wifi: Connection timeout` | Network unreachable |
| I2C NACK | `I2C.*NACK` | `I2C: NACK received` | Device not responding |
| I2C Timeout | `I2C.*timeout` | `I2C: Timeout waiting for bus` | Bus stuck or device missing |
| SPI Error | `SPI.*error` | `SPI: Device not found` | SPI device not responding |
| Sensor Fail | `sensor.*not found` | `BMP280 sensor not found at 0x76` | Wrong address or wiring |
| OTA Fail | `ota:.*fail` | `OTA: Image validation failed` | Corrupt image or wrong partition |
| NVS Fail | `nvs:.*fail` | `NVS: Namespace not found` | NVS not initialized |
| Flash Fail | `flash.*fail` | `Flash: Erase failed` | Flash corruption or protection |

### Warnings (Should Be Reviewed)

| Pattern | Regex | Example | Typical Cause |
|---------|-------|---------|---------------|
| ESP Warning | `W \(\d+\)` | `W (5678) wifi: Beacon timeout` | General warning |
| Heap Low | `heap.*low` | `Heap low: 1024 bytes free` | Memory pressure |
| Task Watchdog | `Task watchdog` | `Task watchdog got triggered` | Task blocking too long |
| Interrupt WDT | `WDT timeout` | `Interrupt watchdog timeout` | ISR taking too long |
| Wi-Fi Disconnect | `wifi:.*disconnect` | `wifi: Disconnected from AP` | Connection lost |
| Deprecated | `deprecated` | `Function xyz is deprecated` | Using old API |
| Buffer Overflow | `buffer.*overflow` | `Buffer overflow detected` | String/buffer too long |
| Power Warning | `power.*low` | `Battery voltage low` | Power supply issue |

### Information (Checkpoints)

| Pattern | Regex | Example | Purpose |
|---------|-------|---------|---------|
| ESP Info | `I \(\d+\)` | `I (9012) main: Starting application` | General info |
| Boot Message | `boot:` | `boot: ESP-IDF v4.4` | Boot information |
| Wi-Fi Connect | `wifi:.*connected` | `wifi: Connected to MyAP` | Connection success |
| IP Address | `ip:.*address` | `ip: 192.168.1.100` | Network config |
| OTA Progress | `ota:.*progress` | `OTA: 50% complete` | Update status |
| Test Point | `TEST:` | `TEST: Sensor reading 25.5C` | Test checkpoint |
| Checkpoint | `CHECKPOINT:` | `CHECKPOINT: Init complete` | Progress marker |

## Arduino Patterns

### Errors

| Pattern | Regex | Example |
|---------|-------|---------|
| Error | `error\|Error\|ERROR` | `Error: Sensor not found` |
| Exception | `Exception` | `Exception (28): LoadProhibited` |
| Panic | `panic\|Reset` | `ets Jan 8 2013,rst cause:2` |
| Failed | `failed\|Failed\|FAIL` | `Connection failed` |
| Timeout | `timeout\|Timeout` | `Read timeout` |

### Warnings

| Pattern | Regex | Example |
|---------|-------|---------|
| Warning | `warning\|Warning\|WARNING` | `Warning: Low memory` |
| Deprecated | `deprecated` | `Function deprecated` |
| Overflow | `overflow` | `Buffer overflow` |

## Pattern Categories by Use Case

### Development/Debugging

```python
DEBUG_PATTERNS = [
    'panic', 'watchdog', 'assert_fail',  # Fatal
    'error', 'wifi_fail', 'i2c_fail',    # Errors
    'warning', 'heap_low',                  # Warnings
]
```

### Hardware Bring-Up

```python
HARDWARE_PATTERNS = [
    'sensor_fail', 'i2c_fail', 'spi_fail',  # Hardware errors
    'wifi_fail', 'ble_fail',                 # Wireless errors
    'power_warning',                         # Power issues
]
```

### Production Monitoring

```python
PRODUCTION_PATTERNS = [
    'panic', 'watchdog', 'assert_fail',  # Critical
    'ota_fail', 'nvs_fail',               # Update/storage
    'heap_low',                           # Memory
]
```

### Testing/Validation

```python
TEST_PATTERNS = [
    'error', 'warning',                    # Issues
    'TEST:', 'CHECKPOINT:',                # Test markers
    'wifi:.*connected', 'ip:.*address',    # Success markers
]
```

## Custom Pattern Examples

### Application-Specific

```python
# Custom patterns for a weather station
CUSTOM_PATTERNS = {
    'sensor_reading_error': r'BME280.*read.*fail',
    'sd_card_error': r'SD.*card.*error',
    'low_battery': r'Battery.*below.*20%',
    'data_upload_fail': r'Upload.*fail',
}
```

### Communication Protocols

```python
# MQTT patterns
MQTT_PATTERNS = {
    'mqtt_connect': r'mqtt:.*connected',
    'mqtt_disconnect': r'mqtt:.*disconnected',
    'mqtt_publish_fail': r'mqtt:.*publish.*fail',
    'mqtt_subscribe': r'mqtt:.*subscribed',
}

# HTTP patterns
HTTP_PATTERNS = {
    'http_200': r'HTTP.*200',
    'http_404': r'HTTP.*404',
    'http_500': r'HTTP.*500',
    'http_timeout': r'HTTP.*timeout',
}
```

## Pattern Priority Levels

### Immediate Action Required
1. Guru Meditation / Core panic
2. Stack overflow
3. Assert failed
4. Watchdog timeout

### Should Fix Soon
1. I2C/SPI communication errors
2. Sensor not found
3. Wi-Fi connection failures
4. Memory allocation failures

### Monitor and Review
1. Heap warnings
2. Deprecated API usage
3. Buffer warnings
4. Power warnings

### Information Only
1. Successful connections
2. Progress indicators
3. Test checkpoints
4. Boot messages

## Pattern Matching Tips

### Case Insensitivity
All patterns should use case-insensitive matching:
```python
re.compile(pattern, re.IGNORECASE)
```

### Anchoring
Use word boundaries for precise matching:
```python
r'\berror\b'  # Matches "error" but not "terror"
```

### Context Capture
Include surrounding context in matches:
```python
# Good: Captures the full error message
r'E \(\d+\) \w+: (.+)'

# Better: Also captures the tag
r'E \(\d+\) (\w+): (.+)'
```

### Multiple Variants
Account for different log formats:
```python
# ESP-IDF style
r'E \(\d+\)'

# Arduino style  
r'\[ERROR\]'

# Generic
r'^ERROR'
```
