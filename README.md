# Interactive Firmware Development Skill

AI-assisted firmware development where you help by performing physical actions. The AI handles all the software work automatically and only asks for your help when it needs hands-on hardware interaction.

## How It Works

**Important distinction:**
- The **AI** (running on your computer) shows popup dialogs using **Zenity** to ask for your help
- The **firmware code** (running on your device) only reads hardware and prints logs - it never interacts with you directly

```
┌─────────────────┐         ┌──────────────────┐
│   AI (Computer) │────────▶│  Zenity Popup    │
│                 │         │  "Tap the card"  │
│  - Monitors logs│         └────────┬─────────┘
│  - Shows popups │                  │
│  - Handles code │                  ▼
└─────────────────┘         ┌──────────────────┐
                            │     YOU          │
                            │  (Tap card)      │
                            └────────┬─────────┘
                                     │
┌─────────────────┐         ┌────────▼─────────┐
│ Firmware (Device)│◀──────│  NFC Reader      │
│                 │         │  detects card    │
│  - Reads NFC    │         └──────────────────┘
│  - Prints logs  │
│  - NO user input│
└─────────────────┘
```

The firmware code never prompts you - only the AI does via popup dialogs!

**Important:** The AI always uses **Zenity popup dialogs** (GUI windows) to ask for your input. The AI never uses terminal input or asks you to type responses in the console.

## Quick Install

```bash
# Install using npx skills add
npx skills add @hurka5/interactive-firmware-dev

# Or install globally
npm install -g @hurka5/interactive-firmware-dev

# Or clone from GitHub
git clone https://github.com/Hurka5/interactive-firmware-dev-skill.git
```

## What You Can Do To Help

During firmware development and testing, the AI will occasionally need your help with physical actions:

### 1. Card/Token Testing
- **Tap NFC/RFID cards** on the reader when asked
- **Remove cards** when the AI detects they're still present
- **Use different cards** (white card, blue card, etc.) for comparison testing
- **Hold cards** for specific durations to test detection timing

### 2. Encoder/Knob Testing
- **Rotate encoders** clockwise or counter-clockwise by specific numbers of clicks
- **Press encoder buttons** for testing button functionality
- **Set encoders to specific positions** for calibration

### 3. Button Testing
- **Press buttons** when prompted for input testing
- **Hold buttons** for duration tests (e.g., "hold for 2 seconds")
- **Press button combinations** for multi-button tests

### 4. Hardware State Changes
- **Power cycle devices** (unplug and replug USB) when software reset fails
- **Enter boot mode** by holding BOOT button and pressing RST
- **Connect or disconnect** peripherals and modules
- **Flip physical switches** for configuration changes

### 5. Sensor Triggering
- **Wave your hand** in front of motion/PIR sensors
- **Cover and uncover** light sensors with your hand
- **Shine a flashlight** on light sensors
- **Blow warm air** on temperature sensors
- **Move magnets** near hall effect sensors
- **Press** on pressure/force sensors

### 6. Physical Configuration
- **Adjust trim potentiometers** with a small screwdriver
- **Change jumper positions** on pin headers
- **Insert or remove** SD cards
- **Connect/disconnect** cables and modules

## Installation

### Prerequisites

1. **Zenity** - For the popup dialogs:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install zenity
   
   # Fedora
   sudo dnf install zenity
   
   # Arch
   sudo pacman -S zenity
   ```

2. **Python 3.7+** - Usually pre-installed:
   ```bash
   python3 --version
   ```

### Install the Skill

**Method 1: Using npx (recommended)**
```bash
npx skills add @hurka5/interactive-firmware-dev
```

**Method 2: Using npm**
```bash
npm install -g @hurka5/interactive-firmware-dev
```

**Method 3: Clone from GitHub**
```bash
git clone https://github.com/Hurka5/interactive-firmware-dev-skill.git
cd interactive-firmware-dev-skill
chmod +x scripts/*.py scripts/*.sh
```

## Quick Start

```bash
# Start a session - AI will prompt you when it needs physical help
./scripts/interactive_session.py --project ./my_project --port /dev/ttyUSB0
```

**What happens:**
1. AI builds and flashes the firmware automatically
2. AI starts monitoring the device logs
3. When the AI needs physical help, a popup appears explaining:
   - **What is being tested** (e.g., "Testing card detection")
   - **What action to take** (e.g., "Tap the white card")
   - **What to expect** (e.g., "Blue LED should light up")
   - **Why this matters** (e.g., "Verifies antenna coupling")
4. You perform the action and click OK
5. If something goes wrong, AI asks what happened and adapts the test
6. AI continues with the next test, explaining the purpose each time

## Example Session: Context-Aware Testing

The AI explains what it's testing and why, so you understand the purpose of each action.

### NFC Card Testing with Context

```
AI: Building firmware... ✓
AI: Flashing to device... ✓
AI: Starting monitor... ✓

[Popup] 🔧 TEST: Baseline - No Card Present

Establishing baseline: Verifying reader detects NO card when none present.

📋 Action: Ensure no NFC cards are near the reader (10cm away)
✓ Expected: Logs show "Waiting for card..." continuously

This confirms the reader isn't stuck detecting a phantom card.

You: [Make sure no cards are present, click OK]

AI: Log: "NFC reader initialized. Waiting for card..."

---

[Popup] 🔧 TEST: Card Detection - White Card (MIFARE Classic)

Testing if the reader detects MIFARE Classic cards and reads the UID.

📋 Action: Tap the WHITE card on the reader
⏱️  Hold for 2 seconds while I verify detection

✓ Expected: Blue LED lights up + log shows "Card detected! UID: 0x..."

This verifies antenna coupling and basic communication.

You: [Tap the white card, see LED light up, click OK]

AI: Log: "Card detected! UID: 0xA1B2C3D4"
AI: Log: "Type: MIFARE Classic 1K"
AI: Log: "Authentication successful"

---

[Popup] 🔧 TEST: Card Removal Detection

Testing if the reader detects when the card is removed.

📋 Action: REMOVE the white card completely
⏱️  Lift card 10cm away from reader

✓ Expected: Blue LED turns off + log shows "Card removed"

This verifies the presence detection loop is working.

You: [Remove the card, see LED turn off, click OK]

AI: Log: "Card removed"
```

### Error Recovery: When Things Go Wrong

If something unexpected happens, the AI asks what occurred so it can adapt:

```
[Popup] 🔧 TEST: Button Press Detection

Testing GPIO interrupt and debouncing for the USER button.

📋 Action: Press the USER button once
⏱️  Quick press and release

✓ Expected: Log shows "Button pressed!" then "Button released"

You: [Accidentally press RESET instead of USER button]

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

You: [Select "Pressed RESET by mistake"]

AI: Understood! You pressed RESET instead of USER. Let me restart the test.
AI: Re-flashing firmware... ✓

[Popup] 🔧 TEST: Button Press Detection (Retry)

Let's try again. The USER button is the small black button next to RESET.

📋 Action: Press the USER button (not RESET!)

You: [Press correct button, click OK]

AI: Log: "Button pressed!"
AI: Log: "Button released"

[Popup] ✓ TEST PASSED
```

## What the AI Handles (You Don't Need To Worry About)

The AI automatically handles all software tasks:
- Building firmware
- Flashing to device
- Software resets
- Configuration changes
- Log analysis
- Code fixes
- Installing tools (like PlatformIO)

**You only interact when a popup asks for physical help.**

## Supported Hardware

The AI works with:
- **ESP32** (all variants) via ESP-IDF or PlatformIO
- **Arduino** boards (ESP32, ESP8266, AVR, ARM)
- **Any PlatformIO project**

The AI auto-detects your project type.

## Command Reference

```bash
# Start a session (auto-detects project type)
./scripts/interactive_session.py --project ./my_project --port /dev/ttyUSB0

# Specify your serial port if different
./scripts/interactive_session.py --project ./my_project --port /dev/ttyACM0
```

## Tips

- **Keep the terminal visible** - you'll see what the AI is doing
- **Watch for popups** - that's when the AI needs your physical help
- **Be ready to interact** - have your cards, hands, or tools ready
- **Click OK promptly** after performing the action so the AI can continue

## License

MIT - See LICENSE file for details
