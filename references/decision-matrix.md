# Decision Matrix: Physical vs Software Actions

Clear guidelines for when to prompt the user (physical) vs when to handle automatically (software).

## Golden Rule

> **If the AI can do it via software/commands, it should.**
> **Only prompt for actions requiring human hands on hardware.**

## Software Actions (AI Handles Automatically)

### Build & Flash
| Situation | AI Action | User Prompt? |
|-----------|-----------|--------------|
| Build failed | Analyze error, fix code, rebuild | ❌ No |
| Flash failed | Retry with different baud rate | ❌ No |
| Wrong partition | Adjust partition table, rebuild | ❌ No |
| Missing component | Install component, rebuild | ❌ No |

### Configuration
| Situation | AI Action | User Prompt? |
|-----------|-----------|--------------|
| Wrong I2C address | Update config.h with correct address | ❌ No |
| Wrong pin mapping | Update pin definitions | ❌ No |
| Wrong Wi-Fi SSID | Update Wi-Fi config | ❌ No |
| Buffer too small | Increase buffer size in config | ❌ No |
| Wrong clock speed | Update frequency setting | ❌ No |

### Device Control
| Situation | AI Action | User Prompt? |
|-----------|-----------|--------------|
| Need to restart | Software reset via command | ❌ No |
| Monitor disconnected | Reconnect monitor automatically | ❌ No |
| Device not responding | Try software reset first | ❌ No |
| Need to enter boot mode | Use esptool.py --before default_reset | ❌ No |

### Code Fixes
| Situation | AI Action | User Prompt? |
|-----------|-----------|--------------|
| Null pointer crash | Add NULL check | ❌ No |
| Buffer overflow | Add bounds checking | ❌ No |
| Memory leak | Fix allocation/free | ❌ No |
| Race condition | Add synchronization | ❌ No |
| Wrong logic | Fix algorithm | ❌ No |

### Log Analysis
| Situation | AI Action | User Prompt? |
|-----------|-----------|--------------|
| Error detected | Analyze and suggest fix | ❌ No |
| Pattern found | Log and continue | ❌ No |
| Statistics needed | Parse and calculate | ❌ No |
| Trend analysis | Process log data | ❌ No |

## Physical Actions (Prompt User)

### Card/Token Interactions
| Situation | User Action | Prompt Type |
|-----------|-------------|-------------|
| Test NFC reading | Tap card on reader | ✅ Info dialog |
| Test card removal | Remove card from reader | ✅ Info dialog |
| Test different card | Present alternate card | ✅ Info dialog |
| Test card hold time | Hold card for X seconds | ✅ Info dialog |
| Test card distance | Move card closer/farther | ✅ Info dialog |
| Test multiple cards | Present cards in sequence | ✅ Progress dialog |
| Test RFID range | Move card to max distance | ✅ Info dialog |

### Encoder/Knob Interactions
| Situation | User Action | Prompt Type |
|-----------|-------------|-------------|
| Test encoder CW | Rotate clockwise X clicks | ✅ Info dialog |
| Test encoder CCW | Rotate counter-clockwise X clicks | ✅ Info dialog |
| Test encoder button | Press encoder button | ✅ Info dialog |
| Test encoder hold | Press and hold button | ✅ Info dialog |
| Calibrate encoder | Set to center position | ✅ Info dialog |
| Test encoder speed | Rotate fast then slow | ✅ Info dialog |
| Test detents | Count clicks in rotation | ✅ Info dialog |

### Button Interactions
| Situation | User Action | Prompt Type |
|-----------|-------------|-------------|
| Test button press | Press button A | ✅ Info dialog |
| Test button hold | Hold button for X seconds | ✅ Info dialog |
| Test button release | Release held button | ✅ Info dialog |
| Test combo | Press A+B together | ✅ Info dialog |
| Test debounce | Press button rapidly | ✅ Info dialog |
| Test long press | Hold 3+ seconds | ✅ Info dialog |
| Test double click | Press twice quickly | ✅ Info dialog |

### Hardware State Changes
| Situation | User Action | Prompt Type |
|-----------|-------------|-------------|
| Hard fault recovery | Power cycle device | ✅ Info dialog |
| Boot mode entry | Hold BOOT + press RST | ✅ Info dialog |
| USB reconnect | Unplug/replug USB | ✅ Info dialog |
| Peripheral connect | Plug in module | ✅ Info dialog |
| Peripheral disconnect | Unplug module | ✅ Info dialog |
| Switch position | Flip physical switch | ✅ Info dialog |
| Jumper change | Move jumper to new position | ✅ Info dialog |
| Battery test | Disconnect USB power | ✅ Info dialog |

### Sensor Triggering
| Situation | User Action | Prompt Type |
|-----------|-------------|-------------|
| Test PIR sensor | Wave hand in front | ✅ Info dialog |
| Test light sensor | Cover with hand | ✅ Info dialog |
| Test light sensor | Shine flashlight | ✅ Info dialog |
| Test temp sensor | Blow warm air | ✅ Info dialog |
| Test hall sensor | Move magnet near | ✅ Info dialog |
| Test pressure | Press on sensor | ✅ Info dialog |
| Test proximity | Move object close | ✅ Info dialog |
| Test sound | Clap or make noise | ✅ Info dialog |
| Test vibration | Tap or shake device | ✅ Info dialog |
| Test orientation | Tilt/rotate device | ✅ Info dialog |

### Physical Configuration
| Situation | User Action | Prompt Type |
|-----------|-------------|-------------|
| Adjust trim pot | Turn potentiometer | ✅ Scale dialog |
| Set dip switch | Configure switches | ✅ Info dialog |
| Select input | Press input select button | ✅ Info dialog |
| Calibrate sensor | Follow calibration procedure | ✅ Progress dialog |
| Set zero point | Position at reference | ✅ Info dialog |
| Mechanical adjust | Tighten/loosen screw | ✅ Info dialog |

## Edge Cases

### When Software Fails, Escalate to Physical

```
Software reset attempted → No response
    ↓
[Zenity] "Software reset failed. Please power cycle the device:"
         "1. Unplug USB"
         "2. Wait 3 seconds" 
         "3. Plug back in"
```

### When Physical is Optional

```
[Zenity --question --timeout=10]
"Wave hand in front of motion sensor to test?"
[Done] [Skip]

If timeout or Skip: Continue without test
If Done: Wait for trigger in logs
```

### When Both Are Needed

```
AI: Update config to enable sensor ✓ (software)
AI: Rebuild and flash ✓ (software)
[Zenity] "Please connect the sensor module to I2C pins" (physical)
User: [Clicks OK]
AI: Verify detection in logs ✓ (software)
```

## Prompt Templates by Category

### Card Interactions
```bash
# Present card
zenity --info \
  --title="🔧 Step N: Present Card" \
  --text="Please tap the <b>$CARD_TYPE</b> on the NFC reader.\n\n📍 Location: $LOCATION\n⏱️  Hold for: ${HOLD_TIME}s\n\nExpected: $EXPECTED_RESULT"

# Remove card  
zenity --info \
  --title="🔧 Step N: Remove Card" \
  --text="Please remove the card from the reader.\n\nExpected: $EXPECTED_RESULT"

# Card sequence
zenity --progress \
  --title="Card Test Sequence" \
  --text="Present cards in order..."
```

### Encoder Interactions
```bash
# Rotate
zenity --info \
  --title="🔧 Step N: Rotate Encoder" \
  --text="Rotate the encoder <b>$DIRECTION $CLICKS clicks</b>.\n\n📍 Location: $LOCATION\n\nCurrent: $CURRENT_VALUE → Target: $TARGET_VALUE"

# Press
zenity --info \
  --title="🔧 Step N: Press Button" \
  --text="<b>$ACTION</b> the encoder button.\n\n⏱️  Duration: ${DURATION}s"

# Scale for analog
zenity --scale \
  --title="🔧 Adjust Position" \
  --text="Set encoder to position:" \
  --min-value=$MIN --max-value=$MAX --value=$CURRENT
```

### Hardware Reset
```bash
zenity --info \
  --title="🔧 Hardware Reset Required" \
  --text="<b>Power cycle needed.</b>\n\n1. Unplug USB cable\n2. Wait ${WAIT_TIME}s\n3. Plug USB cable back in\n\n⚠️  $REASON"
```

### Sensor Triggering
```bash
zenity --info \
  --title="🔧 Trigger Sensor" \
  --text="<b>$ACTION</b>\n\n📍 Sensor: $SENSOR_NAME\n⏱️  $TIMING_INSTRUCTION\n\nExpected response: $EXPECTED"
```

## Anti-Patterns to Avoid

### ❌ Wrong: Asking for Software Actions
```
"Should I rebuild the firmware?"
"Do you want me to reset the device?"
"Can I change the I2C address?"
"Should I retry the flash?"
```

### ✅ Right: Just Do It
```
[AI rebuilds automatically when needed]
[AI resets device via command]
[AI updates config and rebuilds]
[AI retries with exponential backoff]
```

### ❌ Wrong: Vague Physical Instructions
```
"Do something with the card"
"Press the button"
"Move the thing"
```

### ✅ Right: Specific Physical Instructions
```
"Tap the white NFC card on the PN532 module (center of breadboard)"
"Press and hold the BOOT button (labeled 'BOOT' near USB port) for 2 seconds"
"Rotate the blue encoder 3 clicks clockwise until you feel the detents"
```

## Implementation Checklist

Before prompting user, verify:

- [ ] Is this something the AI **cannot** do via software?
- [ ] Is the instruction specific and actionable?
- [ ] Is the location clearly identified?
- [ ] Is the timing/action quantified?
- [ ] Is the expected result described?
- [ ] Is there a clear OK/Cancel choice?
- [ ] Would a diagram/photo help?

## Quick Reference Card

| If the AI needs to... | Then... |
|----------------------|---------|
| Change code/config | Do it automatically |
| Build/flash/reset | Do it automatically |
| Analyze logs | Do it automatically |
| Move a physical object | **Prompt user** |
| Press a physical button | **Prompt user** |
| Rotate a physical knob | **Prompt user** |
| Connect/disconnect hardware | **Prompt user** |
| Power cycle | **Prompt user** |
| Trigger a sensor | **Prompt user** |
