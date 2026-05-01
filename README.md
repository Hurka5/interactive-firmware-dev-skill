# Interactive Firmware Development Skill

**DEFAULT TESTING APPROACH for ALL firmware with hardware interactions.**

AI-assisted firmware development where you help by performing physical actions. The AI automatically uses this approach for any testing involving hardware - no need to ask specially.

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

**The AI automatically uses this approach whenever you mention hardware testing.**

Just say something like:
- "I have an NFC reader I want to test"
- "My button isn't working"
- "Help me test this encoder"

The AI will immediately start the interactive testing session.

```bash
# Or start manually
./scripts/interactive_session.py --project ./my_project --port /dev/ttyUSB0
```

**What happens automatically:**
1. AI detects you have hardware to test → starts interactive session
2. AI builds and flashes the firmware
3. AI monitors device logs in real-time
4. When physical action needed, popup appears with clear instructions
5. You perform the action and click OK
6. AI verifies via logs and continues testing
7. If something unexpected happens, AI asks what occurred and adapts

## Example Session: Context-Aware Testing

The AI explains what it's testing and why, so you understand the purpose of each action.

### NFC Card Testing (Concise)

```
[Console] AI: Building firmware...
[Console] AI: Flashing to device...
[Console] AI: Starting monitor...
[Console] AI: Monitoring logs...

[Popup] 🔧 TEST: Baseline

📋 Ensure no NFC cards are near the reader

You: [Click OK]

[Console] AI: Log: "NFC reader initialized. Waiting for card..."

---

[Popup] 🔧 TEST: Card Detection

📋 Tap the WHITE card
⏱️  Hold 2 seconds until LED lights up

You: [Tap card, click OK]

[Console] AI: Log: "Card detected! UID: 0xA1B2C3D4"
[Console] AI: ✓ Card detected

---

[Popup] 🔧 TEST: Card Removal

📋 Remove the white card

You: [Remove card, click OK]

[Console] AI: Log: "Card removed"
[Console] AI: ✓ Removal detected
```

### Error Recovery: When Things Go Wrong

If something unexpected happens, the AI asks what occurred:

```
[Popup] 🔧 TEST: Button Press

📋 Press the USER button

You: [Accidentally press RESET instead]

[Console] AI: Log: "Rebooting..."

⚠️  DEVICE RESET DETECTED

❓ Did you press RESET by mistake?
[ ] Yes, meant to press USER
[ ] No, device crashed on its own

You: [Select "Yes, meant to press USER"]

[Console] AI: Re-flashing firmware...

[Popup] 🔧 TEST: Button Press (Retry)

📋 Press the USER button (small black button, not RESET!)

You: [Press correct button, click OK]

[Console] AI: Log: "Button pressed!"
[Console] AI: ✓ Test passed
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
