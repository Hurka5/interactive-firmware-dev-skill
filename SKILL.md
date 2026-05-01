---
name: interactive-firmware-dev
description: AI-assisted interactive firmware development using Zenity dialogs for PHYSICAL user actions. Supports ESP-IDF, Arduino, and PlatformIO. The AI automatically detects when physical intervention is needed during debugging/testing (e.g., moving NFC cards, rotating encoders, pressing buttons, connecting hardware). The AI handles all software actions (reset, flash, config changes, PlatformIO install) automatically without bothering the user. No trigger phrases needed - the AI knows when to prompt based on log patterns and test flow.
---

# Interactive Firmware Development - Physical Actions

AI-assisted firmware development with real-time log monitoring and Zenity-based prompts for **physical actions only**. The AI automatically detects when physical intervention is needed during debugging and testing - no trigger phrases required. The AI handles all software operations autonomously and only asks the user to perform physical actions it cannot do.

## Supported Platforms

- **ESP-IDF**: ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C6
- **Arduino**: ESP32, ESP8266, AVR, ARM  
- **PlatformIO**: Universal embedded development (auto-detected, auto-installed if needed)

## Core Principle

**AI handles software. User handles physical.**

### AI Handles (No Prompts)
- Building and flashing firmware
- Resetting the device (software reset)
- Changing configuration values
- Installing PlatformIO (if needed)
- Restarting monitoring
- Analyzing logs and code
- Applying code fixes

### User Handles (Zenity Prompts)
- Moving NFC cards to/from reader
- Rotating knobs/encoders
- Pressing physical buttons
- Connecting/disconnecting cables
- Power cycling (unplug/replug)
- Changing physical switch positions
- Inserting/removing SD cards
- Adjusting trim pots
- Triggering sensors manually

## Quick Start

```bash
# Start interactive session - AI will only prompt for physical actions
./scripts/interactive_session.py --project ./nfc_project --port /dev/ttyUSB0

# Example: NFC card testing
# AI: "Building firmware..."
# AI: "Resetting device..."
# AI: [Zenity] "Please tap the NFC card on the reader, then click OK"
# AI: "Card detected! UID: 0xA1B2C3D4"
# AI: [Zenity] "Please remove the card, then click OK"
```

## Physical Action Categories

### 1. Card/Token Interactions
- Tap NFC/RFID card on reader
- Remove card from reader
- Present different card ("Use the blue card now")
- Hold card for X seconds
- Tap card multiple times

### 2. Encoder/Knob Interactions
- Rotate encoder clockwise X clicks
- Rotate encoder counter-clockwise X clicks
- Press encoder button
- Set encoder to specific position

### 3. Button Interactions
- Press button A
- Press and hold button B for X seconds
- Release button
- Press button combination

### 4. Hardware State Changes
- Power cycle the device (unplug and replug)
- Connect USB cable
- Disconnect USB cable
- Flip physical switch
- Press reset button (hardware reset)
- Insert SD card
- Remove SD card

### 5. Sensor Triggering
- Wave hand in front of motion sensor
- Cover light sensor
- Shine light on sensor
- Blow on temperature sensor
- Move magnet near hall sensor
- Press on pressure sensor

### 6. Physical Configuration
- Adjust trim potentiometer
- Change jumper position
- Select different input source
- Connect/disconnect peripheral

## When to Prompt vs Auto-Handle

### Always Auto-Handle (Software Actions)
```
❌ WRONG: "Should I reset the device?"
✅ RIGHT: [AI resets device automatically via command]

❌ WRONG: "Do you want me to rebuild the firmware?"
✅ RIGHT: [AI rebuilds automatically when needed]

❌ WRONG: "Should I change the I2C address in config?"
✅ RIGHT: [AI updates config.h and rebuilds]

❌ WRONG: "PlatformIO is not installed, should I install it?"
✅ RIGHT: [AI installs PlatformIO automatically via pip]
```

### Always Prompt (Physical Actions)
```
✅ RIGHT: "Please tap the NFC card on the reader"
✅ RIGHT: "Rotate the volume encoder clockwise 3 clicks"
✅ RIGHT: "Press and hold the BOOT button for 2 seconds"
✅ RIGHT: "Power cycle the device (unplug USB, wait 3s, replug)"
✅ RIGHT: "Wave your hand in front of the PIR sensor"
```

## Physical Action Prompt Design

### Template Structure
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 PHYSICAL ACTION REQUIRED                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step {N} of {Total}: {Action Title}                       │
│                                                             │
│  Please perform this physical action:                       │
│                                                             │
│  {Clear, specific instruction with details}               │
│                                                             │
│  📍 Location: {Where on the device/board}                 │
│  ⏱️  Timing: {How long or when}                            │
│                                                             │
│  [Optional: ASCII diagram or photo reference]             │
│                                                             │
│  Click OK when done, or Cancel to skip this step.        │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Example Prompts

**NFC Card Testing:**
```
🔧 PHYSICAL ACTION REQUIRED

Step 2 of 5: Present NFC Card

Please tap the NFC card on the reader module.

📍 Location: The white rectangular PN532 module 
            near the center of the breadboard
⏱️  Timing: Hold the card on the reader for 1-2 seconds

Expected: Blue LED will light up when card is detected

         [ NFC CARD ]
            |
            v
    ┌───────────────┐
    │  PN532 MODULE │
    │   [ANTENNA]   │
    └───────────────┘

Click OK when the card is on the reader.
```

**Rotary Encoder:**
```
🔧 PHYSICAL ACTION REQUIRED

Step 3 of 4: Adjust Volume

Please rotate the volume encoder.

📍 Location: The blue rotary encoder on the right side
            of the control panel
⏱️  Action: Rotate CLOCKWISE exactly 3 detents (clicks)

Current volume: 50%
Target volume: 80%

    ⬆️
  ┌───┐
  │ ⬆️ │  ← Rotate this way
  └───┘
    ⬇️

Click OK after rotating 3 clicks clockwise.
```

**Hardware Reset:**
```
🔧 PHYSICAL ACTION REQUIRED

Step 1 of 3: Hardware Reset

Please power cycle the device.

📍 Location: USB cable connected to the ESP32 devkit
⏱️  Action: 
   1. Unplug the USB cable
   2. Wait 3 seconds
   3. Plug the USB cable back in

⚠️  Note: This is a hardware power cycle, not a software reset
   which I could do automatically. Physical reset is needed
   to clear the persistent error state.

Click OK when the device has rebooted (you'll see the boot messages).
```

## Workflow Integration

### Typical NFC Testing Session

```
AI: Building firmware... ✓
AI: Flashing to ESP32... ✓
AI: Starting serial monitor... ✓

[Zenity] "Step 1: Please ensure no NFC card is near the reader"
User: [Clicks OK]

AI: Log: "NFC reader initialized. Waiting for card..."

[Zenity] "Step 2: Please tap Card A (the white card) on the reader"
User: [Taps card, clicks OK]

AI: Log: "Card detected! UID: 0xA1B2C3D4, Type: MIFARE Classic"
AI: Log: "Authentication successful"
AI: Log: "Read 16 bytes from block 4"

[Zenity] "Step 3: Please remove the card from the reader"
User: [Removes card, clicks OK]

AI: Log: "Card removed. Waiting..."

[Zenity] "Step 4: Please tap Card B (the blue card) on the reader"
User: [Taps card, clicks OK]

AI: Log: "Card detected! UID: 0xE5F6G7H8, Type: NTAG213"
AI: Log: "Read NDEF message: 'https://example.com'"

[Zenity] "✓ Test complete! Both cards working correctly."
```

### Typical Encoder Testing Session

```
AI: Building firmware... ✓
AI: Flashing... ✓
AI: Starting monitor... ✓

[Zenity] "Step 1: Set encoder to middle position (rotate to center detent)"
User: [Adjusts, clicks OK]

AI: Log: "Encoder position: 50 (center)"

[Zenity] "Step 2: Rotate encoder clockwise 5 clicks"
User: [Rotates, clicks OK]

AI: Log: "Encoder: +1 (position: 51)"
AI: Log: "Encoder: +1 (position: 52)"
AI: Log: "Encoder: +1 (position: 53)"
AI: Log: "Encoder: +1 (position: 54)"
AI: Log: "Encoder: +1 (position: 55)"

[Zenity] "Step 3: Press the encoder button"
User: [Presses, clicks OK]

AI: Log: "Button pressed!"
AI: Log: "Selected option: 55"

[Zenity] "✓ Encoder test passed!"
```

## Decision Matrix: Prompt or Auto?

| Situation | Action | Prompt User? |
|-----------|--------|--------------|
| Build failed | Rebuild with fix | ❌ No - AI does it |
| Flash failed | Retry flash | ❌ No - AI retries |
| Device stuck | Software reset | ❌ No - AI resets |
| Device stuck (hard fault) | Hardware power cycle | ✅ Yes - User unplugs |
| NFC not detected | Check I2C config | ❌ No - AI updates config |
| NFC not detected | Ask user to tap card | ✅ Yes - User moves card |
| Wrong card detected | Update expected UID | ❌ No - AI updates test |
| Wrong card detected | Ask user to use different card | ✅ Yes - User swaps card |
| Encoder not responding | Check pin config | ❌ No - AI fixes pins |
| Encoder not responding | Ask user to rotate it | ✅ Yes - User rotates |
| Wi-Fi fail | Update credentials | ❌ No - AI updates config |
| Wi-Fi fail | Check antenna connection | ✅ Yes - User checks hardware |
| Low memory | Reduce buffer size | ❌ No - AI optimizes |
| Low memory | Ask about PSRAM chip | ✅ Yes - User checks hardware |
| Panic/crash | Analyze and fix code | ❌ No - AI debugs |
| Panic/crash | Hardware power cycle | ✅ Yes - User resets |
| PlatformIO missing | Install PlatformIO | ❌ No - AI installs via pip |

## Physical Action Patterns

### Pattern: Card Presence Test
```python
# AI detects card should be present but isn't
if "Waiting for card..." in log and timeout_reached:
    zenity_info("Please tap the NFC card on the reader")
    # AI waits for card detection in logs
    # No software action needed - user provides the physical card
```

### Pattern: Card Removal Test
```python
# AI detects card should be removed
if "Card still present" in log and test_phase == "removal":
    zenity_info("Please remove the NFC card from the reader")
    # AI waits for removal detection
```

### Pattern: Encoder Range Test
```python
# AI needs user to rotate encoder through range
zenity_info("Rotate encoder fully clockwise, then click OK")
# AI verifies all positions logged
zenity_info("Now rotate fully counter-clockwise, then click OK")
# AI verifies reverse direction
```

### Pattern: Button Debounce Test
```python
# AI needs user to press button multiple times
for i in range(5):
    zenity_info(f"Press button {i+1} of 5, then click OK")
    # AI verifies each press detected correctly
```

### Pattern: Hardware Reset
```python
# AI detects need for hardware reset (not software)
if persistent_error_requires_hardware_reset:
    zenity_info(
        "Hardware reset required.\n\n"
        "1. Unplug USB cable\n"
        "2. Wait 3 seconds\n" 
        "3. Plug USB cable back in\n\n"
        "Click OK when device has rebooted"
    )
    # AI waits for boot messages
```

## Zenity Dialog Types for Physical Actions

### Simple Confirmation
```bash
zenity --info \
  --title="🔧 Physical Action Required" \
  --text="Please tap the NFC card on the reader, then click OK."
```

### With Details
```bash
zenity --info \
  --title="Step 2 of 4: Rotate Encoder" \
  --text="<b>Physical Action Required</b>\n\nPlease rotate the volume encoder <b>clockwise 3 clicks</b>.\n\n📍 Location: Blue encoder on the right side\n⏱️  Timing: Rotate until you feel 3 detents" \
  --width=400
```

### With Timeout (for optional actions)
```bash
zenity --question \
  --title="Physical Action" \
  --text="Wave hand in front of motion sensor?" \
  --timeout=10 \
  --ok-label="Done" \
  --cancel-label="Skip"
```

### Progress for Multi-Step
```bash
(
  echo "25"; echo "# Step 1: Remove card"
  zenity --info --text="Please remove the NFC card"
  echo "50"; echo "# Step 2: Wait..."
  sleep 2
  echo "75"; echo "# Step 3: Present new card"
  zenity --info --text="Please tap the blue card"
  echo "100"
) | zenity --progress --title="NFC Test Sequence"
```

## Resources

- **scripts/interactive_session.py** - Main session manager (physical actions only)
- **scripts/zenity_prompt.sh** - Zenity wrapper with physical action templates
- **references/physical-actions.md** - Physical action patterns and templates
- **references/decision-matrix.md** - When to prompt vs auto-handle
- **examples/nfc-testing-session.md** - Complete NFC test walkthrough
- **examples/encoder-testing-session.md** - Complete encoder test walkthrough
