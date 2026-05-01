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

## ⚠️ CRITICAL: AI Uses Zenity, Firmware Code Does NOT

### What the AI Does (On the Computer)
The AI (running on your computer) uses **Zenity dialogs** to ask you for physical actions:
```
AI: [Shows Zenity popup] "Please tap the NFC card"
You: [Tap card, click OK]
AI: [Monitors logs] "Card detected!"
```

### What the Firmware Code Does (On the Device)
The firmware code you write should **ONLY interact with hardware** - NEVER with users:

**❌ WRONG - Firmware code should NOT do this:**
```cpp
// DON'T WRITE THIS IN FIRMWARE
Serial.println("Press button to continue...");  // ❌ NO!
while (!buttonPressed) { delay(100); }          // ❌ NO!
Serial.read();  // ❌ NO! Don't wait for user input
```

**✅ RIGHT - Firmware code should ONLY do this:**
```cpp
// CORRECT: Just read the hardware and report
void loop() {
    if (nfc.cardPresent()) {
        Serial.println("Card detected: " + nfc.readUID());
    }
    if (button.wasPressed()) {
        Serial.println("Button pressed");
    }
    // Just report state, don't prompt user
}
```

### The Flow
1. **AI writes firmware** that reads hardware and prints logs
2. **AI flashes firmware** to the device
3. **AI monitors logs** from the device
4. **AI shows Zenity popup** when physical action needed
5. **User performs action** (tap card, press button, etc.)
6. **AI sees result in logs** and continues

**The firmware code never prompts the user - only the AI does via Zenity!**

## ⚠️ CRITICAL: AI Must Use Zenity for ALL User Interaction

### The Rule
**The AI must use Zenity for ALL user interaction. NEVER use Python input() or CLI prompts.**

### ❌ WRONG - AI writing Python scripts with input()
```python
# DON'T WRITE THIS - Using Python input()
user_response = input("Press Enter when ready...")  # ❌ NEVER DO THIS

# DON'T WRITE THIS - Using getpass
import getpass
password = getpass.getpass("Enter password: ")  # ❌ NEVER DO THIS

# DON'T WRITE THIS - Using CLI prompts
print("Did you tap the card? (y/n): ")
response = sys.stdin.readline().strip()  # ❌ NEVER DO THIS
```

**WHY IT'S WRONG:**
- Python `input()` blocks and waits for terminal input
- User might not see the terminal prompt
- Zenity provides clear GUI popups that grab attention
- Terminal input is error-prone and user-unfriendly

### ✅ RIGHT - AI using Zenity for all interaction
```python
# CORRECT: Using Zenity via the helper script
import subprocess

# Show info dialog
subprocess.run(["./scripts/zenity_prompt.sh", "--info", 
                "Please tap the NFC card on the reader"])

# Ask yes/no question
result = subprocess.run(["./scripts/zenity_prompt.sh", "--question", 
                        "Did the LED light up?"], capture_output=True)
if result.returncode == 0:
    print("User said yes")

# Get text input
result = subprocess.run(["./scripts/zenity_prompt.sh", "--entry", 
                        "Enter WiFi SSID:", "MyNetwork"], 
                       capture_output=True, text=True)
ssid = result.stdout.strip()
```

### Summary Table

| Interaction Type | WRONG (Don't Use) | RIGHT (Use This) |
|-----------------|-------------------|------------------|
| Ask user to do something | `input("Press Enter...")` | `zenity --info` |
| Ask yes/no question | `input("Continue? (y/n): ")` | `zenity --question` |
| Get text input | `input("Enter name: ")` | `zenity --entry` |
| Select from options | `input("Choose 1-3: ")` | `zenity --list` |
| Get number input | `int(input("Enter value: "))` | `zenity --scale` |
| Show error | `print("Error!")` | `zenity --error` |

### The Golden Rule
**If the AI needs to interact with the user, it MUST use Zenity. No exceptions.**

- Firmware code: Only reads hardware, prints logs
- AI Python scripts: Use Zenity for ALL user interaction
- NEVER use: `input()`, `getpass`, `sys.stdin`, or any CLI prompts

## ⚠️ Zenity is ONLY for Physical Actions, NOT Status Messages

### The Rule
**Use Zenity ONLY when the user needs to perform a physical action. Status messages go to console.**

### ❌ WRONG - Using Zenity for status messages
```python
# DON'T DO THIS - Zenity for status
subprocess.run(["zenity", "--info", "--text=Building firmware..."])  # ❌ NO
subprocess.run(["zenity", "--info", "--text=Flashing device..."])    # ❌ NO
subprocess.run(["zenity", "--info", "--text=Starting monitor..."])   # ❌ NO
```

**WHY IT'S WRONG:**
- User doesn't need to see a popup for things the AI is doing
- Popups interrupt the user unnecessarily
- Console output is sufficient for status updates
- Zenity should only grab attention when user action is required

### ✅ RIGHT - Console for status, Zenity for physical actions
```python
# CORRECT: Status messages to console
print("Building firmware...")      # ✓ Console is fine
print("Flashing device...")          # ✓ Console is fine
print("Monitoring logs...")        # ✓ Console is fine

# CORRECT: Zenity ONLY for physical actions
subprocess.run(["./scripts/zenity_prompt.sh", "--info",
                "Please tap the NFC card on the reader"])  # ✓ Physical action

subprocess.run(["./scripts/zenity_prompt.sh", "--info",
                "Wait until you hear the music play, then click OK"])  # ✓ Context matters
```

### When to Use Zenity vs Console

| Situation | Use Console (print) | Use Zenity (popup) |
|-----------|---------------------|-------------------|
| Building firmware | ✓ `print("Building...")` | ❌ Don't popup |
| Flashing device | ✓ `print("Flashing...")` | ❌ Don't popup |
| Reading logs | ✓ `print("Reading...")` | ❌ Don't popup |
| Tap NFC card | ❌ Not a status | ✓ Zenity popup |
| Press button | ❌ Not a status | ✓ Zenity popup |
| Wait for music | ❌ Not a status | ✓ Zenity popup (context matters) |
| Rotate encoder | ❌ Not a status | ✓ Zenity popup |
| Power cycle | ❌ Not a status | ✓ Zenity popup |

### The Real Golden Rule
**Zenity is for PHYSICAL ACTIONS only. Everything else goes to console.**

## Quick Start

```bash
# Start interactive session - AI will only prompt for physical actions
./scripts/interactive_session.py --project ./nfc_project --port /dev/ttyUSB0

# Example: NFC card testing
# AI: [Console] "Building firmware..."
# AI: [Console] "Flashing device..."
# AI: [Console] "Monitoring logs..."
# AI: [Zenity] "Please tap the NFC card on the reader"  ← Only for physical action
# AI: [Console] "Card detected! UID: 0xA1B2C3D4"
# AI: [Zenity] "Please remove the card"  ← Only for physical action
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

## Prompt Philosophy: Trust but Verify

### Assume User Did the Action
**If the user clicked OK, assume they performed the action.** Don't ask "Did you do it?" - that's redundant.

**❌ WRONG - Don't ask if they did it:**
```
"Please tap the NFC card"
[User clicks OK]
"Did you actually tap the card?"  // ❌ DON'T ASK THIS
```

**✅ RIGHT - Assume they did it, check logs:**
```
"Please tap the NFC card"
[User clicks OK]
[AI checks logs for "Card detected"]
"Card detected! UID: 0xA1B2C3D4"  // ✓ Verify via logs
```

### Verify via Logs, Not Questions
The primary way to verify is by monitoring device logs, not by asking the user.

**❌ WRONG - Asking user to confirm:**
```
"Did the LED light up? (yes/no)"  // ❌ DON'T ASK - check logs instead
```

**✅ RIGHT - Check logs:**
```
[AI sees in logs: "Card detected"]
"Card detected successfully!"  // ✓ Verified via logs
```

### When to Question the User
Only ask follow-up questions if logs are ambiguous or unexpected:

**Scenario: Expected card detection but logs show nothing**
```
⚠️  No card detected in logs after prompt.

Possible reasons:
- Card not positioned correctly
- Wrong card type
- Reader not powered

❓ Which happened?
[ ] I tapped the card but no LED lit up
[ ] I couldn't tap the card yet (need more time)
[ ] The LED lit up but logs don't show detection
[ ] Something else
```

**Scenario: Unexpected behavior**
```
⚠️  Unexpected: Got "Card removed" instead of "Card detected"

❓ What happened?
[ ] I removed a card that was already there
[ ] I never tapped a card
[ ] Something else
```

### Keep Prompts Concise
Only say what matters. Remove fluff.

**❌ WRONG - Too verbose:**
```
🔧 TEST: NFC Card Detection

Testing if the PN532 reader can detect MIFARE Classic cards.

📋 What to do: Tap the WHITE card on the reader
⏱️  Timing: Hold for 2 seconds

✓ Expected: Blue LED lights up + log shows "Card detected"

This verifies the I2C communication and antenna are working.
```

**✅ RIGHT - Concise:**
```
🔧 TEST: Card Detection

📋 Tap the WHITE card on the reader
⏱️  Hold 2 seconds until LED lights up
```

**Even more concise (when context is clear):**
```
📋 Tap the white card
```

### When to Add Context
Add context only when it matters to the test:

**Needs context:**
```
📋 Wait until music plays, then click OK

⏱️  The device will play a test tone in 3-5 seconds
```

**Doesn't need context:**
```
📋 Tap the card  // User knows what to do from previous tests
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

### Direct Test Examples (Concise)

**Button Test**
```
🔧 TEST: Button Press

📋 Press the USER button once
⏱️  Quick click

[User clicks OK]
[AI sees in logs: "Button pressed!"]
✓ Button working
```

**Encoder Test**
```
🔧 TEST: Encoder Rotation

📋 Rotate the knob CLOCKWISE 3 clicks
🔄 → → →

[User clicks OK]
[AI sees in logs: Position 50 → 51 → 52 → 53]
✓ Clockwise rotation detected
```

**NFC Test with Timing Context**
```
🔧 TEST: NFC Read/Write

📋 Tap and HOLD the card
⏱️  Keep holding while I write and read...

[User holds card, clicks OK]
[AI sees in logs: "Write OK", "Read OK", "Data matches"]
✓ Read/write working
```

**Music/Sound Test (Needs Context)**
```
🔧 TEST: Audio Output

📋 Wait until you hear the beep, then click OK
⏱️  Sound will play in 2-3 seconds

[Sound plays, user clicks OK]
✓ Audio output working
```

📋 Step 3: You can remove the card

This verifies the full read/write communication chain.
```

## Workflow Integration

### Typical NFC Testing Session (Concise)

```
[Console] AI: Building firmware...
[Console] AI: Flashing to ESP32...
[Console] AI: Starting serial monitor...
[Console] AI: Monitoring logs...

[Zenity Popup] 🔧 TEST: Baseline - No Card Present

📋 Ensure no NFC cards are near the reader

User: [Clicks OK]

[Console] AI: Log: "NFC reader initialized. Waiting for card..."
[Console] AI: Log: "No card detected"

---

[Zenity Popup] 🔧 TEST: Card Detection

📋 Tap the WHITE card on the reader
⏱️  Hold 2 seconds until LED lights up

User: [Taps card, clicks OK]

[Console] AI: Log: "Card detected! UID: 0xA1B2C3D4"
[Console] AI: Log: "Type: MIFARE Classic 1K"
[Console] AI: ✓ Card detected successfully

---

[Zenity Popup] 🔧 TEST: Card Removal

📋 Remove the white card

User: [Removes card, clicks OK]

[Console] AI: Log: "Card removed"
[Console] AI: ✓ Removal detected

---

[Zenity Popup] 🔧 TEST: Different Card Type

📋 Tap the BLUE card

User: [Taps card, clicks OK]

[Console] AI: Log: "Card detected! UID: 0xE5F6A7B8"
[Console] AI: Log: "Type: NTAG213"
[Console] AI: Log: "NDEF: https://example.com"
[Console] AI: ✓ All tests passed

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
[Console] AI: Building firmware...
[Console] AI: Flashing...
[Console] AI: Starting monitor...
[Console] AI: Monitoring logs...

[Zenity Popup] 🔧 TEST: Encoder Center

📋 Rotate encoder to center position

User: [Rotates to center, clicks OK]

[Console] AI: Log: "Encoder position: 50 (center)"

---

[Zenity Popup] 🔧 TEST: Clockwise Rotation

📋 Rotate CLOCKWISE 5 clicks
🔄 → → → → →

User: [Rotates 5 clicks, clicks OK]

[Console] AI: Log: "Encoder: +1 (position: 51)"
[Console] AI: Log: "Encoder: +1 (position: 52)"
[Console] AI: Log: "Encoder: +1 (position: 53)"
[Console] AI: Log: "Encoder: +1 (position: 54)"
[Console] AI: Log: "Encoder: +1 (position: 55)"
[Console] AI: ✓ Clockwise detected

---

[Zenity Popup] 🔧 TEST: Counter-Clockwise

📋 Rotate COUNTER-CLOCKWISE 3 clicks
🔄 ← ← ←

User: [Rotates 3 clicks, clicks OK]

[Console] AI: Log: "Encoder: -1 (position: 54)"
[Console] AI: Log: "Encoder: -1 (position: 53)"
[Console] AI: Log: "Encoder: -1 (position: 52)"
[Console] AI: ✓ Counter-clockwise detected

---

[Zenity Popup] 🔧 TEST: Button Press

📋 Press the encoder button

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
[Console] AI: Building firmware...
[Console] AI: Flashing...
[Console] AI: Starting monitor...
[Console] AI: Monitoring logs...

[Zenity Popup] 🔧 TEST: Button Press Detection

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

## Common Mistakes to Avoid

### ❌ Mistake 1: Writing User Interaction Code in Firmware

**WRONG - Don't write code that waits for user input:**
```cpp
void setup() {
    Serial.begin(115200);
    Serial.println("Press any key to start...");  // ❌ DON'T DO THIS
    while (Serial.available() == 0) { }            // ❌ DON'T DO THIS
    Serial.read();                                 // ❌ DON'T DO THIS
}
```

**WHY IT'S WRONG:**
- The firmware runs on the embedded device without a keyboard
- The user can't interact with Serial input on most devices
- The AI uses Zenity on the computer to prompt the user, not the firmware

**RIGHT - Just start reading hardware immediately:**
```cpp
void setup() {
    Serial.begin(115200);
    nfc.begin();  // Just initialize hardware
    // Don't wait for user - start working immediately
}

void loop() {
    if (nfc.cardPresent()) {
        Serial.println("Card detected!");
    }
    // Just report what you see, don't ask for input
}
```

### ❌ Mistake 2: Firmware Prompting for Physical Actions

**WRONG - Don't make firmware ask for actions:**
```cpp
void loop() {
    Serial.println("Please tap the NFC card now");  // ❌ DON'T DO THIS
    delay(5000);                                     // ❌ DON'T DO THIS
    if (nfc.readCard()) {
        Serial.println("Card read successfully");
    }
}
```

**WHY IT'S WRONG:**
- The user might not see the Serial output in time
- The AI should handle all user prompts via Zenity
- The firmware should just continuously try to read

**RIGHT - Just try to read continuously:**
```cpp
void loop() {
    if (nfc.cardPresent()) {
        String uid = nfc.readUID();
        Serial.println("Card detected: " + uid);
    }
    // Just keep checking, AI will prompt user via Zenity when needed
    delay(100);
}
```

### ❌ Mistake 3: Blocking Waits in Firmware

**WRONG - Don't block waiting for hardware:**
```cpp
void loop() {
    Serial.println("Waiting for button press...");  // ❌ DON'T DO THIS
    while (!digitalRead(BUTTON_PIN)) {            // ❌ DON'T BLOCK
        delay(10);
    }
    Serial.println("Button pressed!");
}
```

**WHY IT'S WRONG:**
- Blocks other code from running
- Prevents the AI from seeing other log messages
- Makes the device unresponsive

**RIGHT - Use non-blocking checks:**
```cpp
void loop() {
    // Non-blocking button check
    if (button.wasPressed()) {
        Serial.println("Button pressed!");
    }
    
    // Other code can run here
    if (nfc.cardPresent()) {
        Serial.println("Card detected!");
    }
}
```

### Summary

| What | Who Handles It | How |
|------|---------------|-----|
| Prompt user for physical action | **AI** (on computer) | Zenity popup dialog |
| Read hardware state | **Firmware** (on device) | `digitalRead()`, `nfc.read()`, etc. |
| Report hardware state | **Firmware** (on device) | `Serial.println()` |
| Wait for user input | **AI** (on computer) | Zenity dialog + log monitoring |
| Wait for hardware | **Firmware** (on device) | Non-blocking polling in `loop()` |

**Remember:** The firmware code is "headless" - it only talks to hardware and prints logs. The AI is the "brain" that interprets logs and asks the user for help via Zenity.

## Resources

- **scripts/interactive_session.py** - Main session manager (physical actions only)
- **scripts/zenity_prompt.sh** - Zenity wrapper with physical action templates
- **references/physical-actions.md** - Physical action patterns and templates
- **references/decision-matrix.md** - When to prompt vs auto-handle
- **examples/nfc-testing-session.md** - Complete NFC test walkthrough
- **examples/encoder-testing-session.md** - Complete encoder test walkthrough
