# Physical Action Templates

Ready-to-use Zenity prompt templates for common physical interactions in firmware testing.

## NFC/RFID Card Templates

### Basic Card Present
```bash
zenity --info \
  --title="🔧 Step {N}: Present NFC Card" \
  --text="<b>Please tap the NFC card on the reader</b>\n\n📍 <b>Location:</b> The {COLOR} rectangular module\n   near the {LOCATION} of the {BOARD}\n\n⏱️  <b>Action:</b> Hold the card flat against the\n   reader surface for 1-2 seconds\n\n✓ <b>Expected:</b> {LED_COLOR} LED will light up\n   and you'll see 'Card detected' in the logs" \
  --width=450 \
  --height=300
```

### Card Removal
```bash
zenity --info \
  --title="🔧 Step {N}: Remove Card" \
  --text="<b>Please remove the NFC card from the reader</b>\n\n📍 <b>Location:</b> Lift card straight up from the\n   {READER_MODEL} module\n\n⏱️  <b>Action:</b> Remove the card completely\n\n✓ <b>Expected:</b> {LED_COLOR} LED will turn off\n   and you'll see 'Card removed' in the logs" \
  --width=450
```

### Specific Card Type
```bash
zenity --info \
  --title="🔧 Step {N}: Use {CARD_NAME}" \
  --text="<b>Please use the {CARD_COLOR} card</b>\n\n📍 <b>Card:</b> {CARD_NAME} ({CARD_TYPE})\n   Color: {CARD_COLOR}\n   Expected UID: {EXPECTED_UID}\n\n📍 <b>Location:</b> {READER_LOCATION}\n\n⏱️  <b>Action:</b> Tap and hold for {HOLD_TIME}s\n\n✓ <b>Expected:</b> {EXPECTED_RESULT}" \
  --width=450
```

### Card Sequence (Progress Dialog)
```bash
(
  echo "0"; echo "# Step 1: Remove any cards"
  zenity --info --title="Step 1/4" --text="Remove all cards from reader"
  
  echo "25"; echo "# Step 2: Present Card A"
  zenity --info --title="Step 2/4" --text="Tap the WHITE card"
  sleep 1
  
  echo "50"; echo "# Step 3: Remove and wait"
  zenity --info --title="Step 3/4" --text="Remove the card"
  sleep 2
  
  echo "75"; echo "# Step 4: Present Card B"
  zenity --info --title="Step 4/4" --text="Tap the BLUE card"
  
  echo "100"; echo "# Complete!"
) | zenity --progress --title="NFC Card Sequence" --percentage=0 --auto-close
```

### Card Distance Test
```bash
zenity --info \
  --title="🔧 Range Test: Maximum Distance" \
  --text="<b>Find the maximum reading distance</b>\n\n📍 <b>Setup:</b> Hold card {START_DISTANCE}cm from reader\n\n⏱️  <b>Action:</b> Slowly move card closer until\n   the LED lights up\n\n📏 <b>Task:</b> Note the distance when detection occurs\n\n💡 <b>Tip:</b> The PN532 typically reads within 5-10cm" \
  --width=450
```

## Rotary Encoder Templates

### Basic Rotation
```bash
zenity --info \
  --title="🔧 Step {N}: Rotate Encoder" \
  --text="<b>Rotate the encoder {DIRECTION} {CLICKS} clicks</b>\n\n📍 <b>Location:</b> The {COLOR} encoder on the {SIDE}\n   of the {PANEL_LOCATION}\n\n🔄 <b>Direction:</b> {DIRECTION} ({DIRECTION_ICON})\n\n🔢 <b>Count:</b> Exactly {CLICKS} detents (clicks)\n\n📊 <b>Values:</b> {CURRENT_VALUE} → {TARGET_VALUE}\n\n✓ <b>Expected:</b> You'll see position updates in the logs" \
  --width=450
```

### Encoder with Scale Input
```bash
VALUE=$(zenity --scale \
  --title="🔧 Set Encoder Position" \
  --text="<b>Rotate encoder to specific position</b>\n\n📍 Location: {ENCODER_LOCATION}\n\nSet to target value:" \
  --min-value={MIN} \
  --max-value={MAX} \
  --value={CURRENT} \
  --step=1 \
  --width=400)

if [ $? -eq 0 ]; then
  echo "User set encoder to: $VALUE"
fi
```

### Encoder Button Press
```bash
zenity --info \
  --title="🔧 Step {N}: Press Encoder Button" \
  --text="<b>{ACTION} the encoder button</b>\n\n📍 <b>Location:</b> Push the encoder shaft straight down\n\n⏱️  <b>Duration:</b> {DURATION} seconds\n\n✓ <b>Expected:</b> You'll feel a click and see\n   'Button pressed' in the logs" \
  --width=450
```

### Encoder Calibration
```bash
zenity --info \
  --title="🔧 Calibrate Encoder" \
  --text="<b>Set encoder to center position</b>\n\n📍 <b>Location:</b> {ENCODER_LOCATION}\n\n🎯 <b>Action:</b> Rotate encoder to find the center detent\n   (there should be a tactile 'home' position)\n\n📊 <b>Current:</b> Will be set to 50 (middle of 0-100 range)\n\n💡 <b>Tip:</b> If no detent, rotate to middle of travel" \
  --width=450
```

## Button Templates

### Simple Button Press
```bash
zenity --info \
  --title="🔧 Step {N}: Press Button" \
  --text="<b>Press the {BUTTON_NAME} button</b>\n\n📍 <b>Location:</b> {BUTTON_LOCATION}\n   Label: {BUTTON_LABEL}\n\n⏱️  <b>Action:</b> Quick press and release\n\n✓ <b>Expected:</b> {EXPECTED_RESULT}" \
  --width=450
```

### Button Hold
```bash
zenity --info \
  --title="🔧 Step {N}: Hold Button" \
  --text="<b>Press and hold {BUTTON_NAME}</b>\n\n📍 <b>Location:</b> {BUTTON_LOCATION}\n\n⏱️  <b>Duration:</b> Hold for exactly {HOLD_TIME} seconds\n\n⏰ <b>Timing:</b> I'll count down: 3... 2... 1...\n\n✓ <b>Expected:</b> {EXPECTED_RESULT}\n\n⚠️  <b>Note:</b> Don't release until I say!" \
  --width=450
```

### Button Combination
```bash
zenity --info \
  --title="🔧 Step {N}: Button Combo" \
  --text="<b>Press {BUTTON_A} + {BUTTON_B} together</b>\n\n📍 <b>Locations:</b>\n   • {BUTTON_A}: {LOCATION_A}\n   • {BUTTON_B}: {LOCATION_B}\n\n⏱️  <b>Action:</b> Press both simultaneously,\n   hold 1 second, then release\n\n✓ <b>Expected:</b> {EXPECTED_RESULT}" \
  --width=450
```

### Rapid Press Test
```bash
zenity --info \
  --title="🔧 Step {N}: Rapid Press Test" \
  --text="<b>Press button rapidly {COUNT} times</b>\n\n📍 <b>Location:</b> {BUTTON_LOCATION}\n\n⏱️  <b>Speed:</b> As fast as you can consistently\n\n🔢 <b>Count:</b> Exactly {COUNT} presses\n\n✓ <b>Expected:</b> All {COUNT} presses detected\n   (testing debounce logic)" \
  --width=450
```

## Hardware Reset/Power Templates

### Software Reset (AI Handles - No Prompt)
```python
# AI does this automatically - NO ZENITY PROMPT
subprocess.run(["idf.py", "monitor", "--port", port], ...)
# Or sends reset command via serial
```

### Hardware Power Cycle
```bash
zenity --info \
  --title="🔧 Hardware Reset Required" \
  --text="<b>Power cycle the device</b>\n\n⚠️  <b>Why:</b> {REASON}\n\n📍 <b>Action Required:</b>\n   1. 🔌 <b>Unplug</b> the USB cable\n   2. ⏱️  <b>Wait</b> {WAIT_TIME} seconds\n   3. 🔌 <b>Plug</b> the USB cable back in\n\n📟 <b>Then:</b> Watch for boot messages in the terminal\n\n✓ <b>Ready:</b> Click OK when you see 'boot:' messages" \
  --width=450 \
  --height=350
```

### Boot Mode Entry (ESP32)
```bash
zenity --info \
  --title="🔧 Enter Boot Mode" \
  --text="<b>Enter bootloader mode manually</b>\n\n📍 <b>Required for:</b> Flashing firmware\n\n🔘 <b>Buttons:</b>\n   • BOOT button: {BOOT_LOCATION}\n   • RST/EN button: {RST_LOCATION}\n\n⏱️  <b>Sequence:</b>\n   1. Press and hold BOOT button\n   2. Press and release RST button\n   3. Release BOOT button\n\n✓ <b>Expected:</b> Device enters download mode\n   (ready for flashing)" \
  --width=450
```

### USB Reconnect
```bash
zenity --info \
  --title="🔧 Reconnect USB" \
  --text="<b>Reconnect the USB cable</b>\n\n📍 <b>Action:</b>\n   1. Unplug USB from {DEVICE} or computer\n   2. Wait 2 seconds\n   3. Plug USB back in\n\n⚡ <b>Why:</b> {REASON}\n\n✓ <b>Ready:</b> Click OK when device reappears" \
  --width=400
```

## Sensor Triggering Templates

### Motion Sensor (PIR)
```bash
zenity --info \
  --title="🔧 Trigger Motion Sensor" \
  --text="<b>Wave hand to trigger PIR sensor</b>\n\n📍 <b>Location:</b> The dome-shaped white sensor\n   on the {BOARD_LOCATION}\n\n👋 <b>Action:</b> Wave your hand {DISTANCE}cm from sensor\n\n⏱️  <b>Timing:</b> Wave for 2-3 seconds\n\n✓ <b>Expected:</b> Red LED on sensor lights up\n   Log shows: 'Motion detected!'\n\n💡 <b>Tip:</b> PIR needs warm-up time after power-on" \
  --width=450
```

### Light Sensor (LDR/Photodiode)
```bash
zenity --info \
  --title="🔧 Test Light Sensor" \
  --text="<b>Cover and uncover light sensor</b>\n\n📍 <b>Location:</b> The small {COLOR} component\n   labeled {SENSOR_LABEL}\n\n🖐️  <b>Part 1:</b> Cover sensor completely with your hand\n   (should read low light)\n\n☀️  <b>Part 2:</b> Remove hand and shine phone flashlight\n   (should read high light)\n\n📊 <b>Expected:</b> Values changing in logs\n   Dark: ~0-100, Bright: ~3000+" \
  --width=450
```

### Temperature Sensor
```bash
zenity --info \
  --title="🔧 Test Temperature Sensor" \
  --text="<b>Warm up the temperature sensor</b>\n\n📍 <b>Location:</b> The small black chip labeled {CHIP}\n\n💨 <b>Action:</b> Gently blow warm air on the sensor\n   (like fogging a mirror)\n\n⏱️  <b>Duration:</b> 3-5 seconds of warm breath\n\n📈 <b>Expected:</b> Temperature reading increases\n   by 2-5°C in the logs\n\n⚠️  <b>Note:</b> Don't use hot air - just warm breath" \
  --width=450
```

### Hall/Magnetic Sensor
```bash
zenity --info \
  --title="🔧 Test Hall Sensor" \
  --text="<b>Move magnet near hall sensor</b>\n\n📍 <b>Location:</b> On-chip hall sensor (ESP32 internal)\n\n🧲 <b>Action:</b> Bring magnet close to ESP32 chip\n\n📏 <b>Distance:</b> Within 2-3 cm of the metal can\n\n🔄 <b>Test:</b> Move magnet toward and away repeatedly\n\n📊 <b>Expected:</b> Hall sensor values change significantly\n   (values jump when magnet is near)" \
  --width=450
```

### Pressure/Touch Sensor
```bash
zenity --info \
  --title="🔧 Test Pressure Sensor" \
  --text="<b>Press on the force sensor</b>\n\n📍 <b>Location:</b> The round {COLOR} pad labeled {LABEL}\n\n👆 <b>Test 1 - Light:</b> Gently tap the surface\n\n✊ <b>Test 2 - Medium:</b> Press firmly with finger\n\n✋ <b>Test 3 - Release:</b> Remove all pressure\n\n📊 <b>Expected:</b> Values change with pressure\n   Light: ~100-500, Firm: ~2000+" \
  --width=450
```

## Physical Configuration Templates

### Trim Pot Adjustment
```bash
VALUE=$(zenity --scale \
  --title="🔧 Adjust Trim Pot" \
  --text="<b>Turn the trim potentiometer</b>\n\n📍 Location: {POT_LOCATION}\n   (small blue square with screw head)\n\n🎯 Target: Set to {PERCENTAGE}%\n\nUse a small screwdriver to adjust:" \
  --min-value=0 \
  --max-value=100 \
  --value={CURRENT} \
  --step=5)
```

### Jumper/Switch Setting
```bash
zenity --info \
  --title="🔧 Configure Jumpers" \
  --text="<b>Set jumper to {POSITION} position</b>\n\n📍 <b>Location:</b> Jumper {JUMPER_NUMBER} near {COMPONENT}\n\n🔌 <b>Current:</b> {CURRENT_POSITION}\n🎯 <b>Target:</b> {TARGET_POSITION}\n\n✓ <b>Action:</b> Move jumper cap to {TARGET_PINS}\n\n💡 <b>Purpose:</b> {CONFIGURATION_PURPOSE}" \
  --width=450
```

### SD Card Insertion
```bash
zenity --info \
  --title="🔧 Insert SD Card" \
  --text="<b>Insert the SD card into the slot</b>\n\n📍 <b>Location:</b> SD card module on {BOARD_SIDE}\n\n💳 <b>Card:</b> {CARD_CAPACITY} {CARD_TYPE}\n\n📐 <b>Orientation:</b> Contacts facing {DIRECTION}\n   (label side facing {LABEL_DIRECTION})\n\n⏱️  <b>Action:</b> Push card in until it clicks\n\n✓ <b>Expected:</b> 'SD card mounted' in logs\n   or 'Card detected' message" \
  --width=450
```

## Multi-Step Test Sequences

### Complete NFC Test Sequence
```bash
#!/bin/bash
# complete_nfc_test.sh

STEPS=6
CURRENT=0

next_step() {
  CURRENT=$((CURRENT + 1))
  echo "$((CURRENT * 100 / STEPS))"
}

(
  echo "0"; echo "# NFC Reader Test Sequence"
  
  next_step; echo "# Step 1: Clear reader"
  zenity --info --title="Step $CURRENT/$STEPS" \
    --text="<b>Remove all cards from reader</b>\n\nEnsure no NFC cards are near the PN532 module"
  
  next_step; echo "# Step 2: Present Card A"
  zenity --info --title="Step $CURRENT/$STEPS" \
    --text="<b>Tap the WHITE card</b>\n\nHold on reader for 2 seconds"
  sleep 1
  
  next_step; echo "# Step 3: Remove Card A"
  zenity --info --title="Step $CURRENT/$STEPS" \
    --text="<b>Remove the white card</b>\n\nWait for 'Card removed' message"
  sleep 1
  
  next_step; echo "# Step 4: Present Card B"
  zenity --info --title="Step $CURRENT/$STEPS" \
    --text="<b>Tap the BLUE card</b>\n\nHold on reader for 2 seconds"
  sleep 1
  
  next_step; echo "# Step 5: Remove Card B"
  zenity --info --title="Step $CURRENT/$STEPS" \
    --text="<b>Remove the blue card</b>"
  
  next_step; echo "# Complete!"
  sleep 1
  
) | zenity --progress --title="NFC Test" --percentage=0 --auto-close

zenity --info --title="✓ Test Complete" \
  --text="<b>NFC reader test completed successfully!</b>\n\nBoth cards were detected and read correctly."
```

### Encoder Calibration Sequence
```bash
#!/bin/bash
# encoder_calibration.sh

zenity --info --title="Encoder Calibration" \
  --text="<b>Step 1: Find minimum</b>\n\nRotate encoder counter-clockwise to the hard stop"

zenity --info --title="Encoder Calibration" \
  --text="<b>Step 2: Find maximum</b>\n\nRotate encoder clockwise to the hard stop"

zenity --info --title="Encoder Calibration" \
  --text="<b>Step 3: Center position</b>\n\nRotate to middle position (halfway between stops)"

zenity --info --title="✓ Calibration Complete" \
  --text="<b>Encoder calibrated!</b>\n\nMin, max, and center positions recorded."
```

## Conditional Prompts

### Optional Physical Action
```bash
# Only prompt if software method failed
if software_reset_failed; then
  zenity --question --title="Hardware Reset?" \
    --text="<b>Software reset didn't work.</b>\n\nDo you want to power cycle the device?" \
    --ok-label="Power Cycle" --cancel-label="Skip"
  
  if [ $? -eq 0 ]; then
    zenity --info --title="Power Cycle" \
      --text="Please unplug USB, wait 3s, then plug back in"
  fi
fi
```

### Timeout-Based Prompt
```bash
# Prompt with timeout for non-critical actions
zenity --question --title="Test Sensor?" \
  --text="Wave hand in front of motion sensor?" \
  --timeout=10 \
  --ok-label="Done" --cancel-label="Skip"

if [ $? -eq 0 ]; then
  echo "User confirmed sensor test"
elif [ $? -eq 5 ]; then
  echo "Timeout - continuing without test"
else
  echo "User skipped sensor test"
fi
```

## Template Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `{N}` | Step number | "Step 2" |
| `{CARD_TYPE}` | Type of card | "MIFARE Classic", "NTAG213" |
| `{CARD_COLOR}` | Card color | "white", "blue" |
| `{CARD_NAME}` | Card identifier | "Card A", "Employee Badge" |
| `{EXPECTED_UID}` | Expected card UID | "0xA1B2C3D4" |
| `{READER_MODEL}` | Reader module | "PN532", "RC522" |
| `{READER_LOCATION}` | Physical location | "center of breadboard" |
| `{LED_COLOR}` | Indicator LED color | "blue", "green" |
| `{HOLD_TIME}` | Duration to hold | "2", "3" |
| `{DIRECTION}` | Rotation direction | "clockwise", "counter-clockwise" |
| `{DIRECTION_ICON}` | Arrow icon | "→", "←" |
| `{CLICKS}` | Number of detents | "3", "5" |
| `{CURRENT_VALUE}` | Current setting | "50%", "position 25" |
| `{TARGET_VALUE}` | Target setting | "80%", "position 55" |
| `{ENCODER_LOCATION}` | Where encoder is | "right side of panel" |
| `{BUTTON_NAME}` | Button identifier | "BOOT", "USER", "RST" |
| `{BUTTON_LOCATION}` | Button position | "near USB port" |
| `{BUTTON_LABEL}` | Text on button | "FLASH", "BOOT" |
| `{HOLD_TIME}` | Seconds to hold | "2", "3", "5" |
| `{DURATION}` | Action duration | "2 seconds" |
| `{WAIT_TIME}` | Wait duration | "3", "5" |
| `{REASON}` | Why action needed | "Clear persistent error state" |
| `{COLOR}` | Component color | "blue", "black", "white" |
| `{BOARD_LOCATION}` | Location on board | "top-left corner" |
| `{PANEL_LOCATION}` | Panel position | "front panel", "control board" |
| `{DISTANCE}` | Measurement | "5cm", "10cm" |
| `{EXPECTED_RESULT}` | What should happen | "Green LED lights up" |
| `{MIN}` | Minimum value | "0", "1" |
| `{MAX}` | Maximum value | "100", "255" |
| `{CURRENT}` | Current value | "50" |
| `{PERCENTAGE}` | Percentage value | "50%" |
| `{ACTION}` | Action description | "Press", "Hold", "Rotate" |
| `{CHIP}` | Chip identifier | "BME280", "MPU6050" |
| `{SENSOR_LABEL}` | Label on sensor | "LDR1", "PIR" |
| `{CARD_CAPACITY}` | SD card size | "16GB", "32GB" |
| `{JUMPER_NUMBER}` | Jumper identifier | "J1", "JP2" |
| `{POSITION}` | Jumper position | "USB", "EXT" |
| `{CONFIGURATION_PURPOSE}` | Why configure | "Enable external power" |
