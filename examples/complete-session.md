# Example: Interactive ESP32 Development Session

This example demonstrates a complete interactive firmware development session using Zenity prompts.

## Scenario

Developing a weather station with ESP32 that reads from a BME280 sensor and sends data over Wi-Fi. During testing, various issues are encountered and resolved through AI-user interaction.

## Session Setup

```bash
# Start interactive session
./scripts/interactive_session.py \
  --project ./weather_station \
  --port /dev/ttyUSB0 \
  --target esp32s3 \
  --patterns "error,warning,panic,wifi_fail,i2c_fail,sensor_fail,heap_low"
```

## Phase 1: Initial Flash and Boot

### AI Action
```
Building firmware...
Flashing to /dev/ttyUSB0...
Starting monitor...
```

### Log Output
```
I (123) boot: ESP-IDF v5.0.2 2nd stage bootloader
I (124) boot: compile time 10:30:00
I (125) boot: chip revision: v0.1
I (126) boot.esp32s3: Boot SPI Speed : 80MHz
I (127) boot: Enabling RNG early entropy source...
I (128) boot: Partition Table:
I (129) boot: ## Label            Usage          Type ST Offset   Length
```

### Zenity Dialog
**Info**: "Firmware flashed successfully. Monitoring started on /dev/ttyUSB0"

## Phase 2: Wi-Fi Connection Issue

### Log Output
```
I (2345) wifi: wifi driver task: 3ffc9e88, prio:23, stack:6656, core=0
I (2350) wifi: wifi firmware version: 4c1b586
I (2355) wifi: config NVS flash: enabled
I (2360) wifi: config nano formating: disabled
I (2365) wifi: Init data frame dynamic rx buffer num: 32
I (2370) wifi: Init static rx buffer size: 1600
I (2375) wifi: Init static rx buffer num: 10
I (2380) wifi: Init dynamic rx buffer num: 32
I (2385) wifi_init: rx ba win: 6
I (2390) wifi_init: acceptcmode:0
I (2395) wifi: mode : sta (7c:df:a1:e0:00:00)
I (2400) wifi: STA_START
W (5678) wifi: Connection timeout after 10s
E (5680) main: Failed to connect to Wi-Fi
```

### Pattern Detected
- **Pattern**: `wifi_fail`
- **Level**: Error
- **Log**: `E (5680) main: Failed to connect to Wi-Fi`

### Zenity Dialog

```
┌─────────────────────────────────────────────────────────────┐
│  Wi-Fi Connection Failed                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Failed to connect to 'MyHomeNetwork'                       │
│                                                             │
│  Log: E (5680) main: Failed to connect to Wi-Fi             │
│       W (5678) wifi: Connection timeout after 10s            │
│                                                             │
│  What would you like to do?                                 │
│                                                             │
│  [ Retry with same credentials ]                            │
│  [ Enter new SSID/password ]                              │
│  [ Show Wi-Fi scan results ]                              │
│  [ Skip Wi-Fi for this session ]                          │
│  [ Abort session ]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Selection: "Enter new SSID/password"

### Zenity Entry Dialogs
```
Enter Wi-Fi SSID: [________________] [MyHomeNetwork]
Enter Wi-Fi password: [****************] []
```

### AI Action
```python
# Update config.h
#define WIFI_SSID "MyHomeNetwork"
#define WIFI_PASSWORD "correctpassword123"
```

### Result
```
I (2400) wifi: STA_START
I (3456) wifi: new:<11,0>, old:<1,0>, ap:<255,255>, sta:<11,0>
I (3460) wifi: state: init -> auth (b0)
I (3465) wifi: state: auth -> assoc (0)
I (3470) wifi: state: assoc -> run (10)
I (4500) wifi: connected with MyHomeNetwork, aid = 1
I (4505) wifi: security type: 3
I (4510) ip: 192.168.1.105
I (4515) main: Wi-Fi connected, IP: 192.168.1.105
```

## Phase 3: Sensor Detection Failure

### Log Output
```
I (5000) bme280: Initializing BME280 sensor...
E (5100) i2c: I2C device not found at 0x76
E (5105) bme280: Sensor not detected
E (5110) main: Failed to initialize BME280
```

### Pattern Detected
- **Pattern**: `sensor_fail` + `i2c_fail`
- **Level**: Error
- **Log**: `E (5100) i2c: I2C device not found at 0x76`

### Zenity Dialog

```
┌─────────────────────────────────────────────────────────────┐
│  Sensor Detection Failed                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BME280 sensor not detected at I2C address 0x76              │
│                                                             │
│  Log: E (5100) i2c: I2C device not found at 0x76         │
│       E (5105) bme280: Sensor not detected               │
│                                                             │
│  Possible causes:                                           │
│  • Wrong I2C address (try 0x77)                            │
│  • Wiring issue (SDA/SCL swapped or loose)               │
│  • Sensor not powered (check VCC/GND)                      │
│  • Pull-up resistors missing                              │
│                                                             │
│  What should I do?                                          │
│                                                             │
│  [ Try alternate address (0x77) ]                         │
│  [ Show wiring diagram ]                                    │
│  [ Skip sensor and continue ]                               │
│  [ Abort and fix hardware ]                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Selection: "Try alternate address (0x77)"

### AI Action
```python
# Update sensor configuration
#define BME280_I2C_ADDRESS 0x77  // Changed from 0x76
```

### Result
```
I (5000) bme280: Initializing BME280 sensor...
I (5050) bme280: Found BME280 at 0x77
I (5060) bme280: Chip ID: 0x60
I (5070) bme280: Calibration data loaded
I (5080) main: BME280 sensor initialized successfully
```

## Phase 4: Performance Warning

### Log Output (after running for 5 minutes)
```
W (300000) main: Heap low: 2048 bytes free
W (300001) main: Consider increasing buffer sizes
I (300010) bme280: Temperature: 23.5°C, Humidity: 45%
```

### Pattern Detected
- **Pattern**: `heap_low`
- **Level**: Warning
- **Log**: `W (300000) main: Heap low: 2048 bytes free`

### Zenity Dialog (30s timeout)

```
┌─────────────────────────────────────────────────────────────┐
│  WARNING: Low Heap Memory                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Heap low: 2048 bytes free                                  │
│                                                             │
│  This may indicate memory leaks or insufficient buffers.   │
│                                                             │
│  [ Fix now ]  [ Continue monitoring ]  [ Suppress ]       │
│                                                             │
│  (Auto-continues in 30 seconds...)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Selection: "Fix now"

### Zenity Scale Dialog
```
Set buffer reduction factor (%):

[==========|==========] 50%

Min: 10%    Current: 50%    Max: 90%

[ OK ]  [ Cancel ]
```

### AI Action
```python
# Reduce buffer sizes by 50%
#define SENSOR_BUFFER_SIZE 512   // Was 1024
#define WIFI_BUFFER_SIZE 1024    // Was 2048
```

### Result
```
I (100) main: Buffers resized
I (5000) main: Heap free: 8192 bytes
```

## Phase 5: Test Checkpoint

### Log Output
```
I (60000) TEST: Sensor calibration complete
I (60001) TEST: Current readings:
I (60002) TEST:   Temperature: 23.5°C
I (60003) TEST:   Humidity: 45%
I (60004) TEST:   Pressure: 1013.25 hPa
I (60005) CHECKPOINT: Verify readings are reasonable
```

### Pattern Detected
- **Pattern**: `CHECKPOINT:`
- **Level**: Info
- **Log**: `CHECKPOINT: Verify readings are reasonable`

### Zenity Question Dialog

```
┌─────────────────────────────────────────────────────────────┐
│  CHECKPOINT: Verify Sensor Readings                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Current sensor readings:                                   │
│  • Temperature: 23.5°C                                      │
│  • Humidity: 45%                                            │
│  • Pressure: 1013.25 hPa                                    │
│                                                             │
│  Do these values look reasonable for your environment?     │
│                                                             │
│                    [ Yes ]  [ No ]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Selection: "Yes"

### Result
Session continues to next phase (data upload testing).

## Phase 6: Fatal Error (Simulated)

### Log Output
```
I (120000) main: Sending data to server...
Guru Meditation Error: Core  0 panic'ed (LoadProhibited). 
Exception was unhandled.
Core  0 register dump:
PC      : 0x4008f5a4  PS      : 0x00060e30  
A0      : 0x800d0b8c  A1      : 0x3ffb5730  
A2      : 0x00000000  A3      : 0x00000000  
...
Backtrace: 0x4008f5a4:0x3ffb5730 0x400d0b89:0x3ffb5750
```

### Pattern Detected
- **Pattern**: `panic`
- **Level**: Fatal
- **Log**: `Guru Meditation Error: Core 0 panic'ed (LoadProhibited)`

### Zenity Dialog

```
┌─────────────────────────────────────────────────────────────┐
│  FATAL ERROR: ESP32 Panic Detected                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A fatal error occurred:                                    │
│                                                             │
│  Guru Meditation Error: Core 0 panic'ed                     │
│  (LoadProhibited)                                          │
│                                                             │
│  This typically indicates a null pointer dereference          │
│  or accessing invalid memory.                               │
│                                                             │
│  Backtrace:                                                 │
│  0x4008f5a4: http_send_data                               │
│  0x400d0b89: main_task                                     │
│                                                             │
│  What would you like to do?                                 │
│                                                             │
│  [ Inspect code around crash ]                            │
│  [ Increase stack size and retry ]                        │
│  [ Check hardware connections ]                           │
│  [ View full log context ]                                │
│  [ Abort session ]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Selection: "Inspect code around crash"

### AI Action
```
Analyzing code at http_send_data (main/http_client.c:45)...

Found issue:
  char *buffer = malloc(size);
  strcpy(buffer, data);  // <-- buffer may be NULL if malloc failed

Suggested fix:
  char *buffer = malloc(size);
  if (buffer == NULL) {
      ESP_LOGE(TAG, "Memory allocation failed");
      return ESP_ERR_NO_MEM;
  }
  strcpy(buffer, data);
```

### Zenity Dialog

```
┌─────────────────────────────────────────────────────────────┐
│  Suggested Fix                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  File: main/http_client.c:45                                │
│                                                             │
│  Issue: Null pointer dereference after malloc               │
│                                                             │
│  Suggested code:                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ char *buffer = malloc(size);                       │   │
│  │ if (buffer == NULL) {                              │   │
│  │     ESP_LOGE(TAG, "Memory allocation failed");    │   │
│  │     return ESP_ERR_NO_MEM;                         │   │
│  │ }                                                  │   │
│  │ strcpy(buffer, data);                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Apply this fix?                                            │
│                                                             │
│                    [ Yes ]  [ No ]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Selection: "Yes"

### AI Action
```
Applying fix to main/http_client.c...
Rebuilding firmware...
Flashing...
Restarting monitor...
```

### Result
```
I (120000) main: Sending data to server...
I (120010) http: Data sent successfully
I (120015) main: Next reading in 60 seconds...
```

## Session Summary

### Zenity Info Dialog (Session End)

```
┌─────────────────────────────────────────────────────────────┐
│  Session Complete                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Session ID: dev-20240115-103000                           │
│  Duration: 45 minutes                                       │
│                                                             │
│  Issues detected and resolved:                              │
│  ✓ Wi-Fi connection (wrong password)                        │
│  ✓ BME280 sensor (wrong I2C address)                        │
│  ✓ Low heap memory (reduced buffer sizes)                   │
│  ✓ Null pointer crash (added NULL check)                    │
│                                                             │
│  Session log saved to:                                      │
│  .weave/sessions/dev-20240115-103000.json                  │
│                                                             │
│                    [ OK ]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Takeaways

1. **Progressive Resolution**: Issues were resolved incrementally without starting over
2. **Contextual Prompts**: Each dialog provided relevant context (log lines, code, options)
3. **Safe Defaults**: The safest option was always prominent
4. **Timeouts**: Warnings auto-continued; fatal errors waited for user
5. **Session Persistence**: Full history saved for review and learning

## Command Reference

```bash
# Start a new session
./scripts/interactive_session.py --project ./my_project

# Resume from saved session
./scripts/interactive_session.py --session-file .weave/sessions/dev-20240115-103000.json

# Watch logs only (no interaction)
./scripts/log_watcher.py --port /dev/ttyUSB0 --patterns "error,warning"

# Manual zenity prompt
./scripts/zenity_prompt.sh --question "Continue testing?"
```
