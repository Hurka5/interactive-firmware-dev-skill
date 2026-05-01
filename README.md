# Interactive Firmware Development Skill

AI-assisted firmware development with Zenity prompts for **physical actions only**. The AI handles all software operations automatically and only asks the user to perform physical actions it cannot do itself.

## Core Principle

**AI handles software. User handles physical.**

| AI Handles (Automatically) | User Handles (Zenity Prompts) |
|---------------------------|------------------------------|
| Building firmware | Moving NFC cards |
| Flashing device | Rotating encoders |
| Software reset | Pressing buttons |
| Changing config | Power cycling |
| Analyzing logs | Connecting hardware |
| Applying fixes | Triggering sensors |

## Quick Start

```bash
# Start interactive session - AI only prompts for physical actions
./scripts/interactive_session.py --project ./my_project --port /dev/ttyUSB0

# Example: NFC testing
# AI: "Building... Flashing... Monitoring..."
# AI: [Zenity] "Please tap the NFC card on the reader"
# User: [Taps card, clicks OK]
# AI: "Card detected! UID: 0xA1B2C3D4"
# AI: [Zenity] "Please remove the card"
```

## Requirements

- **Zenity**: GTK dialog tool (`sudo apt-get install zenity`)
- **Python 3.7+**: For log watcher and session manager
- **ESP-IDF or Arduino**: Depending on your platform
- **Serial access**: User in `dialout` group

## Scripts

| Script | Purpose |
|--------|---------|
| `interactive_session.py` | Main session manager - coordinates coding, building, flashing, monitoring, **physical prompts only** |
| `log_watcher.py` | Log monitoring with pattern detection |
| `zenity_prompt.sh` | Zenity wrapper with physical action templates |

## Physical Action Categories

### 1. Card/Token Interactions
- Tap NFC/RFID card on reader
- Remove card from reader
- Present different card
- Hold card for X seconds
- Test card reading range

### 2. Encoder/Knob Interactions
- Rotate encoder clockwise X clicks
- Rotate encoder counter-clockwise X clicks
- Press encoder button
- Set encoder to specific position

### 3. Button Interactions
- Press button A
- Press and hold button B
- Press button combinations
- Rapid press testing

### 4. Hardware State Changes
- Power cycle device (unplug/replug)
- Enter boot mode (hold BOOT + press RST)
- Connect/disconnect peripherals
- Flip physical switches

### 5. Sensor Triggering
- Wave hand in front of motion sensor
- Cover/uncover light sensor
- Blow on temperature sensor
- Move magnet near hall sensor
- Press on pressure sensor

### 6. Physical Configuration
- Adjust trim potentiometer
- Change jumper positions
- Insert/remove SD cards
- Connect/disconnect cables

## When to Prompt vs Auto-Handle

### ❌ AI Handles Automatically (No Prompts)

```
"Building firmware..."                    → AI builds
"Flashing to device..."                   → AI flashes  
"Software reset..."                       → AI resets via command
"Updating I2C address in config..."       → AI edits file
"Retrying with new baud rate..."          → AI retries
"Analyzing crash log..."                  → AI parses
"Applying code fix..."                    → AI edits code
```

### ✅ AI Prompts User (Physical Only)

```
"Please tap the NFC card on the reader"
"Rotate the volume encoder clockwise 3 clicks"
"Press and hold the BOOT button for 2 seconds"
"Power cycle the device (unplug USB, wait 3s, replug)"
"Wave your hand in front of the PIR sensor"
"Connect the sensor module to the I2C pins"
```

## Zenity Dialog Examples

### Simple Physical Action
```bash
zenity --info \
  --title="🔧 Physical Action Required" \
  --text="Please tap the NFC card on the reader, then click OK."
```

### Detailed Physical Action
```bash
zenity --info \
  --title="🔧 Step 2 of 4: Rotate Encoder" \
  --text="<b>Physical Action Required</b>\n\nPlease rotate the volume encoder <b>clockwise 3 clicks</b>.\n\n📍 Location: Blue encoder on the right side\n⏱️  Timing: Rotate until you feel 3 detents" \
  --width=400
```

### Hardware Reset
```bash
zenity --info \
  --title="🔧 Hardware Reset Required" \
  --text="<b>Power cycle needed.</b>\n\n1. Unplug USB cable\n2. Wait 3 seconds\n3. Plug USB cable back in\n\n⚠️  Software reset failed - hardware power cycle required."
```

## Workflow Example: NFC Testing

```
AI: Building firmware... ✓
AI: Flashing to ESP32... ✓
AI: Starting monitor... ✓

[Zenity] "Step 1: Please ensure no NFC card is near the reader"
User: [Clicks OK]

AI: Log: "NFC reader initialized. Waiting for card..."

[Zenity] "Step 2: Please tap the WHITE card on the reader"
User: [Taps card, clicks OK]

AI: Log: "Card detected! UID: 0xA1B2C3D4"
AI: Log: "Read successful"

[Zenity] "Step 3: Please remove the card"
User: [Removes card, clicks OK]

AI: Log: "Card removed. Waiting..."

[Zenity] "✓ Test complete!"
```

## Resources

- **SKILL.md** - Main skill instructions for AI
- **references/decision-matrix.md** - When to prompt vs auto-handle
- **references/physical-action-templates.md** - Ready-to-use Zenity templates
- **references/log-patterns.md** - Common log patterns
- **examples/nfc-testing-session.md** - Complete NFC test walkthrough
- **examples/encoder-testing-session.md** - Complete encoder test walkthrough

## Decision Matrix Quick Reference

| Situation | Who Handles It |
|-----------|---------------|
| Build/flash/reset | AI (software) |
| Config changes | AI (software) |
| Log analysis | AI (software) |
| Code fixes | AI (software) |
| Move NFC card | **User (physical)** |
| Rotate encoder | **User (physical)** |
| Press button | **User (physical)** |
| Power cycle | **User (physical)** |
| Connect hardware | **User (physical)** |
| Trigger sensor | **User (physical)** |

## Trigger Phrases

Use this skill when you say:
- "Help me test this NFC reader - tell me when to tap cards"
- "Interactive testing for my rotary encoder project"
- "Develop firmware with prompts for physical actions"
- "Test my sensor project with step-by-step hardware interaction"
- "AI coding with human-in-the-loop for hardware testing"
- "Prompt me to move cards/rotate knobs/press buttons"

## License

MIT - See LICENSE file for details
