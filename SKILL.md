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

## Direct Testing Approach

The AI should be direct and context-aware when asking for physical actions. Always explain WHAT is being tested and WHY.

### Principle: Test with Purpose

Every prompt should clearly state:
1. **What action** to perform
2. **What is being tested** (the purpose)
3. **What to expect** (so user knows if it worked)

### Context-Aware Prompts

**❌ BAD: Vague prompt**
```
"Please tap the card"
```

**✅ GOOD: Context-aware prompt**
```
🔧 TEST: NFC Card Detection

I'm testing if the PN532 reader can detect MIFARE Classic cards.

📋 What to do: Tap the WHITE card on the reader
⏱️  Timing: Hold for 2 seconds

✓ Expected: Blue LED lights up + log shows "Card detected"

This verifies the I2C communication and antenna are working.
```

### Testing with Timing/Sequence

When testing sequences (like tap-and-remove), explain the full flow:

```
🔧 TEST: Card Presence Detection

Testing the reader's ability to detect when cards arrive and leave.

📋 Step 1: Tap the card and HOLD it
⏱️  Keep holding while I verify detection...

✓ Expected: "Card detected" in logs

[User clicks OK after seeing detection]

---

🔧 TEST: Card Removal Detection

Now testing if the reader detects when the card is removed.

📋 Step 2: REMOVE the card now
⏱️  Remove completely (10cm away)

✓ Expected: "Card removed" in logs

This tests the presence detection loop.
```

### Error Recovery: Ask What Happened

When something unexpected occurs, the AI should ask the user for context:

**Scenario: Expected card detection but nothing happened**
```
⚠️  UNEXPECTED RESULT

I expected the card to be detected, but no detection occurred.

Possible causes:
- Card not positioned correctly
- Wrong card type
- Reader not powered
- Communication error

❓ What happened on your end?
[ ] I tapped the card but no LED lit up
[ ] I couldn't tap the card yet
[ ] The LED lit but logs don't show detection
[ ] Something else happened (please describe)

This helps me determine if it's a hardware or software issue.
```

**Scenario: Unexpected reset detected**
```
⚠️  DEVICE RESET DETECTED

The device rebooted unexpectedly during the test.

❓ Did you:
[ ] Press the reset button intentionally
[ ] Power cycle the device
[ ] Disconnect/reconnect USB
[ ] None of the above - it reset on its own

This helps me distinguish between intentional actions and crashes.
```

**Scenario: Wrong input detected**
```
⚠️  UNEXPECTED INPUT

I detected a button press, but I was waiting for an encoder rotation.

❓ Did you:
[ ] Press the button by mistake
[ ] Press the button intentionally to test something
[ ] The device has only one input (button, not encoder)
[ ] Something else

This helps me adapt the test to your actual hardware.
```

### Direct Test Examples

**Button Test (Direct)**
```
🔧 TEST: Button Input

Testing GPIO button debouncing and detection.

📋 Action: Press the USER button once
⏱️  Quick press and release (like a click)

✓ Expected: Log shows "Button pressed" and "Button released"

This verifies the interrupt and debounce logic.
```

**Encoder Test (Direct with Context)**
```
🔧 TEST: Encoder Clockwise Rotation

Testing encoder direction detection.

📋 Action: Rotate the knob CLOCKWISE 3 clicks
🔄 Direction: → (right/forward)

✓ Expected: Logs show position increasing (e.g., 50 → 51 → 52 → 53)

This verifies the CLK/DT pin decoding.
```

**NFC Communication Test (Context-Rich)**
```
🔧 TEST: NFC Read/Write Communication

Testing if I can read and write data to the MIFARE card.

📋 Step 1: Tap and HOLD the card
💾 I'm writing test data to block 4...
✓ Write successful

📋 Step 2: Keep holding - now reading back...
✓ Read successful - data matches!

📋 Step 3: You can remove the card

This verifies the full read/write communication chain.
```

## Workflow Integration

### Typical NFC Testing Session (Context-Aware)

```
AI: Building firmware... ✓
AI: Flashing to ESP32... ✓
AI: Starting serial monitor... ✓

[Zenity] 🔧 TEST: Baseline - No Card Present

Establishing baseline: Verifying reader detects NO card when none present.

📋 Action: Ensure no NFC cards are near the reader (10cm away)
✓ Expected: Logs show "Waiting for card..." continuously

This confirms the reader isn't stuck detecting a phantom card.

User: [Ensures no cards, clicks OK]

AI: Log: "NFC reader initialized. Waiting for card..."
AI: Log: "No card detected (baseline established)"

---

[Zenity] 🔧 TEST: Card Detection - White Card (MIFARE Classic)

Testing if the reader detects MIFARE Classic cards and reads the UID.

📋 Action: Tap the WHITE card on the reader
⏱️  Hold for 2 seconds while I verify detection

✓ Expected: 
  - Blue LED lights up
  - Log shows: "Card detected! UID: 0x..."
  - Log shows: "Type: MIFARE Classic"

This verifies antenna coupling and basic communication.

User: [Taps white card, sees LED, clicks OK]

AI: Log: "Card detected! UID: 0xA1B2C3D4"
AI: Log: "Type: MIFARE Classic 1K"
AI: Log: "Authentication successful"
AI: Log: "Read 16 bytes from block 4"

---

[Zenity] 🔧 TEST: Card Removal Detection

Testing if the reader detects when the card is removed.

📋 Action: REMOVE the white card completely
⏱️  Lift card 10cm away from reader

✓ Expected: Blue LED turns off + log shows "Card removed"

This verifies the presence detection loop is working.

User: [Removes card, sees LED off, clicks OK]

AI: Log: "Card removed"
AI: Log: "Waiting for next card..."

---

[Zenity] 🔧 TEST: Card Detection - Blue Card (NTAG213)

Testing a different card type (NTAG213) to verify protocol handling.

📋 Action: Tap the BLUE card on the reader
⏱️  Hold for 2 seconds

✓ Expected: 
  - Blue LED lights up
  - Log shows: "Type: NTAG213"
  - Log shows NDEF message content

This verifies the reader handles different NFC types correctly.

User: [Taps blue card, clicks OK]

AI: Log: "Card detected! UID: 0xE5F6A7B8"
AI: Log: "Type: NTAG213"
AI: Log: "NDEF message found"
AI: Log: "NDEF content: 'https://example.com'"

---

[Zenity] ✓ ALL TESTS PASSED

Both card types detected and read correctly:
- ✓ MIFARE Classic: UID read, data block read
- ✓ NTAG213: UID read, NDEF message read
- ✓ Presence detection: Arrival and departure both detected

The NFC reader is working correctly!
```

### Typical Encoder Testing Session (Context-Aware)

```
AI: Building firmware... ✓
AI: Flashing... ✓
AI: Starting monitor... ✓

[Zenity] 🔧 TEST: Encoder Center Position

Calibrating encoder - finding the middle position for reference.

📋 Action: Rotate encoder to find the center detent
🎯 Target: Middle of rotation range (will be set as position 50)

✓ Expected: You feel a tactile "click" or resistance at center

This establishes a known starting point for directional tests.

User: [Rotates to center, clicks OK]

AI: Log: "Encoder position: 50 (center)"
AI: Log: "Center position calibrated"

---

[Zenity] 🔧 TEST: Clockwise Rotation Detection

Testing if clockwise rotation increases the position value.

📋 Action: Rotate encoder CLOCKWISE exactly 5 clicks
🔄 Direction: → (right/forward)
📊 Current: 50 → Expected: 55

✓ Expected: Logs show position increasing by 1 each click:
  "Encoder: +1 (position: 51)"
  "Encoder: +1 (position: 52)"
  ...through 55

This verifies the CLK/DT pin decoding for clockwise direction.

User: [Rotates 5 clicks CW, clicks OK]

AI: Log: "Encoder: +1 (position: 51)"
AI: Log: "Encoder: +1 (position: 52)"
AI: Log: "Encoder: +1 (position: 53)"
AI: Log: "Encoder: +1 (position: 54)"
AI: Log: "Encoder: +1 (position: 55)"

---

[Zenity] 🔧 TEST: Counter-Clockwise Rotation Detection

Testing if counter-clockwise rotation decreases the position value.

📋 Action: Rotate encoder COUNTER-CLOCKWISE exactly 3 clicks
🔄 Direction: ← (left/backward)
📊 Current: 55 → Expected: 52

✓ Expected: Logs show position decreasing by 1 each click:
  "Encoder: -1 (position: 54)"
  "Encoder: -1 (position: 53)"
  "Encoder: -1 (position: 52)"

This verifies direction detection is working both ways.

User: [Rotates 3 clicks CCW, clicks OK]

AI: Log: "Encoder: -1 (position: 54)"
AI: Log: "Encoder: -1 (position: 53)"
AI: Log: "Encoder: -1 (position: 52)"

---

[Zenity] 🔧 TEST: Encoder Button Press

Testing the integrated push-button on the encoder shaft.

📋 Action: Press the encoder button (push the shaft down)
⏱️  Quick press and release (like a mouse click)

✓ Expected: Log shows "Button pressed!" and "Button released"

This verifies the SW (switch) pin connection and debouncing.

User: [Presses button, clicks OK]

AI: Log: "Button pressed!"
AI: Log: "Button released"
AI: Log: "Selected option: 52"

---

[Zenity] ✓ ALL TESTS PASSED

Encoder functionality verified:
- ✓ Center position calibration
- ✓ Clockwise rotation: 5 steps detected correctly
- ✓ Counter-clockwise rotation: 3 steps detected correctly
- ✓ Direction detection: Both directions working
- ✓ Button press: Detected and debounced correctly

The encoder is working correctly!
```

### Error Recovery Example: When Things Go Wrong

```
AI: Building firmware... ✓
AI: Flashing... ✓
AI: Starting monitor... ✓

[Zenity] 🔧 TEST: Button Press Detection

Testing GPIO interrupt and debouncing for the USER button.

📋 Action: Press the USER button once
⏱️  Quick press and release

✓ Expected: Log shows "Button pressed!" then "Button released"

User: [Accidentally presses RESET instead of USER button]

AI: Log: "ets Jun  8 2016 00:22:57"
AI: Log: "rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)"
AI: Log: "Rebooting..."

⚠️  DEVICE RESET DETECTED

The device rebooted unexpectedly during the button test.

❓ Did you:
[ ] Press the RESET button by mistake (meant to press USER)
[ ] Press RESET intentionally to restart the test
[ ] The device crashed on its own
[ ] Something else happened

This helps me distinguish between intentional actions and crashes.

User: [Selects "Pressed RESET by mistake"]

AI: Understood! You pressed RESET instead of USER. Let me restart the test.
AI: Re-flashing firmware... ✓

[Zenity] 🔧 TEST: Button Press Detection (Retry)

Let's try again. The USER button is the small black button next to the RESET button.

📋 Action: Press the USER button (not RESET!)
   USER button location: [diagram showing board]

User: [Presses correct button, clicks OK]

AI: Log: "Button pressed!"
AI: Log: "Button released"

[Zenity] ✓ TEST PASSED

Button detection working correctly!
```

### Error Recovery Example: Wrong Input Detected

```
AI: Monitoring logs...

[Zenity] 🔧 TEST: Encoder Rotation

Testing encoder clockwise rotation.

📋 Action: Rotate the encoder CLOCKWISE 3 clicks
📊 Current position: 50

User: [Rotates counter-clockwise instead]

AI: Log: "Encoder: -1 (position: 49)"
AI: Log: "Encoder: -1 (position: 48)"
AI: Log: "Encoder: -1 (position: 47)"

⚠️  UNEXPECTED ROTATION DIRECTION

I expected clockwise rotation (position increasing), 
but detected counter-clockwise (position decreasing).

❓ What happened:
[ ] I rotated the wrong way by mistake
[ ] The encoder is wired backwards (CLK/DT swapped)
[ ] I rotated correctly but logs show wrong direction
[ ] Something else

User: [Selects "Rotated wrong way by mistake"]

AI: No problem! Let's try again.

[Zenity] 🔧 TEST: Encoder Rotation (Retry)

Rotate the encoder CLOCKWISE (to the right) 3 clicks.

📋 Action: Rotate RIGHT → → → 3 clicks
📊 Current position: 47 → Expected: 50

User: [Rotates correctly, clicks OK]

AI: Log: "Encoder: +1 (position: 48)"
AI: Log: "Encoder: +1 (position: 49)"
AI: Log: "Encoder: +1 (position: 50)"

[Zenity] ✓ TEST PASSED

Clockwise rotation detected correctly!
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
