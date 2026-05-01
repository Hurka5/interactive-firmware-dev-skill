# Interactive Firmware Development Skill

AI-assisted firmware development where you help by performing physical actions. The AI handles all the software work automatically and only asks for your help when it needs hands-on hardware interaction.

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
3. When the AI needs physical help, a popup appears asking you to:
   - Tap a card
   - Rotate a knob
   - Press a button
   - etc.
4. You perform the action and click OK
5. AI continues monitoring and may ask for more help as needed

## Example Session: NFC Card Testing

```
AI: Building firmware... ✓
AI: Flashing to device... ✓
AI: Starting monitor... ✓

[Popup] "Please ensure no NFC card is near the reader"
You: [Make sure no cards are present, click OK]

AI: Log: "NFC reader initialized. Waiting for card..."

[Popup] "Please tap the WHITE card on the reader"
You: [Tap the white card on the reader, click OK]

AI: Log: "Card detected! UID: 0xA1B2C3D4"
AI: Log: "Read successful"

[Popup] "Please remove the card"
You: [Remove the card, click OK]

AI: Log: "Card removed. Waiting..."

[Popup] "✓ Test complete!"
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
