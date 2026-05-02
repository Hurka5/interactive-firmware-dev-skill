---
name: interactive-firmware-dev
description: DEFAULT SKILL for ALL firmware testing. AI handles software (build, flash, config). User handles physical actions (tap cards, press buttons, rotate knobs) via Zenity prompts. Exactly 2 buttons per prompt. Supports ESP-IDF, Arduino, PlatformIO.
---

# Interactive Firmware Development

**AI handles software. User handles physical.**

## Quick Start

```bash
./scripts/interactive_session.py --project ./my_project --port /dev/ttyUSB0
```

## Core Principle

| AI Handles (No Prompts) | User Handles (Zenity Prompts) |
|------------------------|------------------------------|
| Build, flash, reset | Tap NFC cards |
| Config changes | Press buttons |
| Log analysis | Rotate encoders |
| Code fixes | Power cycle |

## Prompt Types (Exactly 2)

### TYPE 1: Physical Action
```
[TYPE 1] Decision

Tap the NFC card on the reader

[✓ Done]  [Skip]
```

### TYPE 2: Verification
```
[TYPE 2] Verification

Did the card read successfully?

[Yes]  [No]
```

**If NO → ask for description:**
```
[TYPE 1] Problem Description

What did you observe?

[OK]  [Cancel]
```

## Rules

1. **Exactly 2 buttons per prompt**
2. **One action per prompt** - no lists
3. **Physical verification > log verification** - ask user what they see
4. **Status messages to console** - only physical actions use Zenity
5. **Never use `input()`** - always use Zenity

## Example Session

```
[Console] Building firmware...
[Console] Flashing device...
[Console] Monitoring logs...

[Zenity] 👉 Tap the NFC card
[User taps card, clicks Done]

[Console] Card detected! UID: 0xA1B2C3D4
[Console] All tests passed
```

## Test All Prompts

```bash
python3 test_prompts.py
```

Shows all 7 prompt types with exactly 2 buttons each.