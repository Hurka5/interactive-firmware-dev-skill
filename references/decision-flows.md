# Decision Flows Reference

Pre-defined decision trees for common firmware issues encountered during interactive development.

## Fatal Error Flows

### Guru Meditation / Core Panic

```
DETECTED: Guru Meditation Error
│
├─→ [1] Inspect code around crash location
│   └─→ Show stack trace and register dump
│   └─→ Identify offending line
│   └─→ Suggest fix (null check, bounds check, etc.)
│   └─→ Apply fix → Rebuild → Retest
│
├─→ [2] Increase stack size and retry
│   └─→ Ask: New stack size? (default: 2x current)
│   └─→ Update config → Rebuild → Retest
│
├─→ [3] Check hardware connections
│   └─→ Show checklist dialog
│   └─→ Wait for user confirmation
│   └─→ Retry or abort
│
└─→ [4] Abort session
    └─→ Save session state
    └─→ Show summary
```

### Stack Overflow

```
DETECTED: Stack overflow in task X
│
├─→ [1] Increase task stack size
│   └─→ Current: Y bytes
│   └─→ Suggest: 2x current
│   └─→ Apply → Rebuild → Retest
│
├─→ [2] Analyze stack usage
│   └─→ Enable stack monitoring
│   └─→ Show high-water mark
│   └─→ Identify heavy functions
│
├─→ [3] Check for recursion
│   └─→ Search for recursive calls
│   └─→ Suggest iterative alternative
│
└─→ [4] Abort and review manually
```

### Assert Failed

```
DETECTED: assert failed: condition
│
├─→ [1] Show assertion location
│   └─→ File:line information
│   └─→ Context code
│   └─→ Explain assertion purpose
│
├─→ [2] Fix the root cause
│   └─→ Analyze call stack
│   └─→ Identify invalid parameter/state
│   └─→ Apply fix
│
└─→ [3] Disable assertion (not recommended)
    └─→ Warning about consequences
    └─→ Require explicit confirmation
```

## Communication Error Flows

### I2C NACK / Timeout

```
DETECTED: I2C communication error
│
├─→ [1] Try alternate I2C address
│   └─→ Common alternatives: 0x76→0x77, 0x50→0x51
│   └─→ Scan bus for devices
│   └─→ Update address → Retest
│
├─→ [2] Change SDA/SCL pins
│   └─→ Show pinout diagram
│   └─→ Ask: New SDA pin? (default: 21)
│   └─→ Ask: New SCL pin? (default: 22)
│   └─→ Update pins → Retest
│
├─→ [3] Reduce I2C speed
│   └─→ Current: X Hz
│   └─→ Suggest: 100kHz or 50kHz
│   └─→ Update speed → Retest
│
├─→ [4] Check pull-up resistors
│   └─→ Show wiring diagram
│   └─→ Explain 4.7kΩ pull-ups
│   └─→ Wait for hardware check
│
├─→ [5] Skip this device
│   └─→ Disable in config
│   └─→ Continue with reduced functionality
│
└─→ [6] Abort and fix hardware
```

### SPI Communication Error

```
DETECTED: SPI communication error
│
├─→ [1] Check pin configuration
│   └─→ MOSI, MISO, SCK, CS pins
│   └─→ Show current vs expected
│   └─→ Allow pin remapping
│
├─→ [2] Verify chip select
│   └─→ CS active level (high/low)
│   └─→ CS timing
│   └─→ Update CS config
│
├─→ [3] Reduce SPI speed
│   └─→ Current: X MHz
│   └─→ Suggest: 10MHz or 1MHz
│
├─→ [4] Check mode/polarity
│   └─→ Mode 0,1,2,3
│   └─→ Show device datasheet requirements
│
└─→ [5] Skip device or abort
```

### Wi-Fi Connection Failed

```
DETECTED: Wi-Fi connection timeout/failed
│
├─→ [1] Retry with same credentials
│   └─→ Immediate retry
│   └─→ Increase timeout
│
├─→ [2] Enter new credentials
│   └─→ Ask: SSID
│   └─→ Ask: Password (hidden)
│   └─→ Update config → Retry
│
├─→ [3] Show Wi-Fi scan results
│   └─→ Scan for networks
│   └─→ Present list to user
│   └─→ User selects → Enter password
│
├─→ [4] Check Wi-Fi configuration
│   └─→ Show current config
│   └─→ Verify security mode
│   └─→ Check static IP settings
│
├─→ [5] Skip Wi-Fi for this session
│   └─→ Disable Wi-Fi init
│   └─→ Continue offline mode
│
└─→ [6] Abort session
```

## Sensor/Device Error Flows

### Sensor Not Found

```
DETECTED: Sensor not detected
│
├─→ [1] Check wiring/power
│   └─→ Show wiring diagram
│   └─→ Checklist: VCC, GND, SDA, SCL
│   └─→ Wait for confirmation
│
├─→ [2] Try alternate address
│   └─→ Scan I2C bus
│   └─→ Show found devices
│   └─→ Try alternate addresses
│
├─→ [3] Use mock/simulated data
│   └─→ Enable mock mode
│   └─→ Generate synthetic data
│   └─→ Continue development
│
├─→ [4] Skip sensor
│   └─→ Disable in config
│   └─→ Continue without sensor
│
└─→ [5] Abort and fix hardware
```

## Memory Error Flows

### Low Heap Memory

```
DETECTED: Heap low / Out of memory
│
├─→ [1] Reduce buffer sizes
│   └─→ Show current buffer allocations
│   └─→ Suggest reductions
│   └─→ Apply → Rebuild → Retest
│
├─→ [2] Enable PSRAM
│   └─→ Check if chip has PSRAM
│   └─→ Enable in sdkconfig
│   └─→ Move large buffers to PSRAM
│
├─→ [3] Optimize memory usage
│   └─→ Show heap trace
│   └─→ Identify large allocations
│   └─→ Suggest optimizations
│
├─→ [4] Increase task priorities
│   └─→ Prevent memory fragmentation
│   └─→ Adjust FreeRTOS config
│
└─→ [5] Continue with caution
```

### Task Watchdog Triggered

```
DETECTED: Task watchdog timeout
│
├─→ [1] Increase watchdog timeout
│   └─→ Current: X seconds
│   └─→ Suggest: 2x current
│   └─→ Update → Retest
│
├─→ [2] Add yield/delay in loops
│   └─→ Identify blocking loop
│   └─→ Add vTaskDelay(1) or yield()
│   └─→ Apply fix → Retest
│
├─→ [3] Move work to separate task
│   └─→ Split long operation
│   └─→ Use queue/worker pattern
│
├─→ [4] Optimize the blocking code
│   └─→ Profile the task
│   └─→ Optimize hot paths
│
└─→ [5] Disable watchdog (not recommended)
```

## Update/OTA Flows

### OTA Update Failed

```
DETECTED: OTA image validation failed
│
├─→ [1] Check image integrity
│   └─→ Verify download completed
│   └─→ Check checksum/signature
│   └─→ Retry download
│
├─→ [2] Verify partition layout
│   └─→ Show current partitions
│   └─→ Check OTA partition size
│   └─→ Verify compatibility
│
├─→ [3] Check network stability
│   └─→ Test connection
│   └─→ Retry with resume
│
├─→ [4] Rollback to previous
│   └─→ Activate previous OTA slot
│   └─→ Reboot to known-good
│
└─→ [5] Abort and investigate
```

## Test Checkpoint Flows

### User Verification Required

```
DETECTED: TEST: or CHECKPOINT: marker
│
├─→ [1] Show checkpoint info
│   └─→ Display test description
│   └─→ Show expected behavior
│   └─→ Show actual reading/state
│
├─→ [2] Ask user to verify
│   └─→ "Does the LED blink?"
│   └─→ "Is the sensor reading reasonable?"
│   └─→ Yes/No response
│
├─→ [3] If NO: Debug
│   └─→ Show relevant code
│   └─→ Suggest checks
│   └─→ Apply fix → Retest
│
└─→ [4] If YES: Continue
    └─→ Log success
    └─→ Proceed to next checkpoint
```

## Decision Prompt Design Guidelines

### Information Hierarchy

1. **What happened**: Clear description of the detected issue
2. **Context**: Relevant log lines and recent history
3. **Options**: 2-4 specific actions (not open-ended)
4. **Default**: Safest option should be prominent

### Option Ordering

```
Recommended order:
1. Fix automatically (if safe)
2. Show me the code
3. Skip/ignore for now
4. Abort session
```

### Timeout Handling

```python
# Critical errors: No timeout (wait for user)
# Warnings: 30-60 second timeout
# Info/Checkpoints: 10-30 second timeout

TIMEOUTS = {
    'fatal': None,      # Wait indefinitely
    'error': 60,        # 1 minute
    'warning': 30,      # 30 seconds
    'info': 10,         # 10 seconds
}
```

### Dialog Text Templates

**Fatal Error Template:**
```
FATAL ERROR: {pattern_name}

Detected: {log_line}

Context:
{context_lines}

This error typically indicates:
{explanation}

What would you like to do?
[Inspect code] [Increase stack] [Check hardware] [Abort]
```

**Error Template:**
```
ERROR: {pattern_name}

{log_line}

Recent activity:
{context}

Options:
[Fix automatically] [Show code] [Ignore] [Edit config] [Abort]
```

**Warning Template:**
```
WARNING: {pattern_name}

{log_line}

This may indicate: {explanation}

[Fix now] [Continue] [Suppress]
(Auto-continues in 30s)
```

**Checkpoint Template:**
```
CHECKPOINT: {description}

Current state: {state_info}

Please verify: {verification_question}

[Yes, continue] [No, debug] [Stop session]
```
