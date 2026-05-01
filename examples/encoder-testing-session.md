# Example: Rotary Encoder Testing with Physical Interaction

This example demonstrates testing a rotary encoder with volume control, where the AI handles all software and only prompts for physical knob rotations.

## Project Overview

**Hardware:** ESP32 + KY-040 Rotary Encoder Module  
**Goal:** Test encoder rotation, button press, and volume control  
**Approach:** AI handles software, prompts user to physically rotate encoder

## Session Start

```bash
./scripts/interactive_session.py \
  --project ./volume_controller \
  --port /dev/ttyUSB0 \
  --target esp32 \
  --patterns "encoder,rotary,volume,button,position"
```

## Phase 1: Software Setup (AI Handles Everything)

### AI Actions (No Prompts)
```
AI: Building firmware... ✓
AI: Flashing to ESP32... ✓
AI: Starting monitor... ✓
```

### Log Output
```
I (123) boot: ESP-IDF v5.0.2
I (500) main: Volume Controller Starting
I (510) encoder: GPIO initialized CLK:18 DT:19 SW:21
I (520) encoder: KY-040 module detected
I (530) volume: Initial volume: 50%
I (540) main: Ready - Current position: 50
```

## Phase 2: Physical Interaction - Encoder Testing

### Step 1: Set to Center Position

**AI detects:** Encoder initialized at position 50, needs calibration

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 1 of 5: Center the Encoder                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Set encoder to middle position.                            │
│                                                             │
│  📍 Location: The blue KY-040 module on the right side     │
│              of the breadboard                             │
│                                                             │
│  🎯 Action: Rotate the encoder knob to find the center     │
│            detent (tactile "home" position)                │
│                                                             │
│  💡 Tip: If no center detent, rotate to middle of travel  │
│                                                             │
│  Current reading: 50 (already centered)                    │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Ensures encoder is centered, clicks OK

**Log Output:**
```
I (1000) encoder: Position set to 50 (center)
I (1010) volume: Volume set to 50%
```

### Step 2: Rotate Clockwise 5 Clicks

**AI detects:** Centered, testing clockwise rotation

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 2 of 5: Rotate Clockwise                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Rotate the encoder CLOCKWISE 5 clicks.                     │
│                                                             │
│  📍 Location: The blue encoder module on the right         │
│                                                             │
│  🔄 Direction: Clockwise (right/forward)                    │
│     ⬆️                                                      │
│   ┌───┐                                                     │
│   │ ➡️ │  ← Rotate this way                                │
│   └───┘                                                     │
│     ⬇️                                                      │
│                                                             │
│  🔢 Count: Exactly 5 detents (clicks)                      │
│                                                             │
│  📊 Values: 50 → 55 (volume will increase)                │
│                                                             │
│  ✓ Expected: You'll feel 5 clicks and see position updates  │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Rotates encoder 5 clicks clockwise, clicks OK

**Log Output:**
```
I (2000) encoder: +1 (position: 51, volume: 51%)
I (2010) encoder: +1 (position: 52, volume: 52%)
I (2020) encoder: +1 (position: 53, volume: 53%)
I (2030) encoder: +1 (position: 54, volume: 54%)
I (2040) encoder: +1 (position: 55, volume: 55%)
I (2050) volume: Volume increased to 55%
```

**AI:** ✓ Clockwise rotation detected, 5 steps confirmed

### Step 3: Rotate Counter-Clockwise 3 Clicks

**AI detects:** Clockwise working, testing reverse

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 3 of 5: Rotate Counter-Clockwise                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Rotate the encoder COUNTER-CLOCKWISE 3 clicks.           │
│                                                             │
│  📍 Location: The blue encoder module                       │
│                                                             │
│  🔄 Direction: Counter-clockwise (left/backward)            │
│     ⬆️                                                      │
│   ┌───┐                                                     │
│   │ ⬅️ │  ← Rotate this way                                │
│   └───┘                                                     │
│     ⬇️                                                      │
│                                                             │
│  🔢 Count: Exactly 3 detents (clicks)                      │
│                                                             │
│  📊 Values: 55 → 52 (volume will decrease)                │
│                                                             │
│  ✓ Expected: Position decreases, volume goes down           │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Rotates 3 clicks counter-clockwise, clicks OK

**Log Output:**
```
I (3000) encoder: -1 (position: 54, volume: 54%)
I (3010) encoder: -1 (position: 53, volume: 53%)
I (3020) encoder: -1 (position: 52, volume: 52%)
I (3030) volume: Volume decreased to 52%
```

**AI:** ✓ Counter-clockwise rotation detected, direction working

### Step 4: Press Encoder Button

**AI detects:** Rotation working both directions, testing button

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 4 of 5: Press Button                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Press the encoder button.                                  │
│                                                             │
│  📍 Location: Push the encoder shaft straight DOWN         │
│              (it's also a button!)                          │
│                                                             │
│  ⏱️  Action: Quick press and release                        │
│                                                             │
│  ✓ Expected: You'll feel a click                            │
│              Log shows: 'Button pressed!'                   │
│              Volume will MUTE (toggle)                      │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Presses encoder button, clicks OK

**Log Output:**
```
I (4000) encoder: Button pressed!
I (4010) volume: MUTE toggled
I (4020) volume: Volume: 52% → MUTED
```

**AI:** ✓ Button press detected, mute function working

### Step 5: Set Specific Volume with Scale

**AI detects:** All basic functions working, testing precise control

**Zenity Prompt (Scale Dialog):**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 5 of 5: Set Specific Volume                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Rotate encoder to set volume to exactly 75%.               │
│                                                             │
│  📍 Location: The blue encoder on the right side          │
│                                                             │
│  🎯 Target: 75% volume                                      │
│                                                             │
│  Current: 52% (MUTED) → First press button to unmute!      │
│                                                             │
│  Set target volume:                                         │
│                                                             │
│  [========|==========] 75%                                 │
│                                                             │
│   0%        50%        100%                                  │
│                                                             │
│  Rotate encoder until the scale shows 75%,                │
│  then click OK.                                             │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** First presses button to unmute, then rotates to 75%, clicks OK

**Log Output:**
```
I (5000) encoder: Button pressed!
I (5010) volume: UNMUTED
I (5020) volume: Restored to 52%
I (5100) encoder: +1 (position: 53, volume: 53%)
I (5110) encoder: +1 (position: 54, volume: 54%)
...
I (5250) encoder: +1 (position: 75, volume: 75%)
I (5260) volume: Volume set to 75%
```

**AI:** ✓ Precise volume control achieved

## Session Complete

**Zenity Summary:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Encoder Test Complete                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Session ID: dev-20240115-150000                            │
│  Duration: 6 minutes                                        │
│                                                             │
│  Physical interactions completed:                           │
│  ✓ Step 1: Centered encoder at position 50                 │
│  ✓ Step 2: Rotated clockwise 5 clicks (50→55)             │
│  ✓ Step 3: Rotated counter-clockwise 3 clicks (55→52)       │
│  ✓ Step 4: Pressed button (mute toggle)                    │
│  ✓ Step 5: Set precise volume to 75%                       │
│                                                             │
│  Software actions (AI handled):                             │
│  • Built and flashed firmware                               │
│  • Monitored encoder interrupts                             │
│  • Tracked position changes                                 │
│  • Calculated volume levels                                 │
│  • Detected button presses                                  │
│  • Verified all state transitions                           │
│                                                             │
│  All tests PASSED ✓                                         │
│                                                             │
│                    [ OK ]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Advanced Test: Rapid Rotation

If needed, the AI can test rapid rotation:

**Zenity Prompt:**
```
🔧 Bonus Test: Rapid Rotation

Rotate the encoder back and forth rapidly for 5 seconds.

📍 Action: Spin the knob quickly clockwise and counter-clockwise

🎯 Purpose: Test debouncing and direction detection

Click START when ready, then click DONE after 5 seconds.

[ START ]  [ Skip ]
```

**Log Output:**
```
I (6000) encoder: Rapid rotation test started
I (6010) encoder: +1 (position: 76)
I (6020) encoder: +1 (position: 77)
I (6030) encoder: -1 (position: 76)
I (6040) encoder: +1 (position: 77)
I (6050) encoder: -1 (position: 76)
...
I (6500) encoder: Rapid rotation test complete
I (6510) encoder: Net change: +3 (76→79)
I (6520) encoder: Direction changes: 12 (debounce working)
```

## Error Scenario: Wrong Direction Detected

If the user rotates clockwise but logs show counter-clockwise:

**AI Response:**
```
⚠️  Direction Mismatch Detected

You rotated the encoder, but the direction detected was wrong.

Expected: Clockwise rotation → Position should increase
Detected: Position decreased (counter-clockwise behavior)

Possible causes:
• CLK and DT pins may be swapped
• Encoder wiring reversed

AI Action: Checking pin configuration...
[AI automatically checks and fixes config if needed]

If wiring is correct, the encoder may be defective.

[Retry test] [Check wiring] [Swap pins in config] [Abort]
```

Note: The AI would **automatically** check and fix the pin configuration in software before asking the user to retry - no need to prompt for a software fix!

## Key Points

### What AI Handled (Software)
- ✓ Building and flashing
- ✓ Monitoring GPIO interrupts
- ✓ Tracking encoder position
- ✓ Calculating volume from position
- ✓ Detecting button state
- ✓ Debouncing logic
- ✓ Direction interpretation

### What User Handled (Physical)
- ✓ Rotating the physical knob
- ✓ Pressing the physical button
- ✓ Setting specific positions

### No Unnecessary Prompts
The AI **never** asked:
- ❌ "Should I rebuild after the fix?" → Just rebuilt automatically
- ❌ "Do you want me to check the pin config?" → Checked automatically
- ❌ "Can I restart the monitor?" → Handled automatically

## Command Reference

```bash
# Start encoder testing session
./scripts/interactive_session.py \
  --project ./volume_controller \
  --port /dev/ttyUSB0 \
  --patterns "encoder,position,volume,button"

# Manual rotation prompt
./scripts/zenity_prompt.sh --info \
  "Rotate the encoder 3 clicks clockwise, then click OK"

# Scale dialog for precise setting
./scripts/zenity_prompt.sh --scale \
  "Set encoder position:" 0 100 50
```
