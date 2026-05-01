# Example: NFC Card Testing with Physical Interaction

This example demonstrates a complete interactive firmware development session for an NFC reader project, focusing on **physical actions** the AI cannot perform.

## Project Overview

**Hardware:** ESP32 + PN532 NFC Module  
**Goal:** Test NFC card reading functionality  
**Approach:** AI handles all software, prompts user only for physical card interactions

## Session Start

```bash
./scripts/interactive_session.py \
  --project ./nfc_reader \
  --port /dev/ttyUSB0 \
  --target esp32 \
  --patterns "nfc,pn532,card,uid,error"
```

## Phase 1: Software Setup (AI Handles Everything)

### AI Actions (No Prompts)
```
AI: Analyzing project structure... ✓
AI: Checking dependencies... ✓
AI: Building firmware... ✓
   → Compiling main/nfc_task.c
   → Compiling components/pn532/pn532.c
   → Linking project.elf
AI: Build successful

AI: Flashing firmware to /dev/ttyUSB0... ✓
   → Erasing flash...
   → Writing at 0x00010000... (10%)
   → Writing at 0x00020000... (50%)
   → Writing at 0x00030000... (100%)
AI: Flash successful

AI: Starting serial monitor... ✓
```

### Log Output
```
I (123) boot: ESP-IDF v5.0.2 2nd stage bootloader
I (124) boot: compile time 14:30:00
I (500) main: NFC Reader Test Starting
I (510) pn532: I2C initialized on SDA:21 SCL:22
I (520) pn532: PN532 module found at 0x24
I (530) pn532: Firmware version: 1.6
I (540) main: NFC reader ready - waiting for cards
```

## Phase 2: Physical Interaction - Card Testing

### Step 1: Clear Reader

**AI detects:** Reader initialized, ready for testing

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 1 of 6: Clear Reader                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Please ensure no NFC cards are near the reader.            │
│                                                             │
│  📍 Location: The white rectangular PN532 module           │
│              near the center of the breadboard             │
│                                                             │
│  ⏱️  Action: Remove any cards currently on or near        │
│              the reader (at least 10cm away)              │
│                                                             │
│  ✓ Expected: Logs show 'Waiting for card...'               │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Clicks OK

**Log Output:**
```
I (1000) main: Waiting for card...
I (1100) main: No card detected (baseline established)
```

### Step 2: Present Card A (White Card)

**AI detects:** Baseline established, ready for first card test

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 2 of 6: Present Card A                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Please tap the WHITE card on the NFC reader.              │
│                                                             │
│  📍 Card: Card A (MIFARE Classic 1K)                        │
│     Expected UID: 0xA1B2C3D4                                │
│                                                             │
│  📍 Location: The white rectangular PN532 module          │
│              near the center of the breadboard             │
│                                                             │
│  ⏱️  Action: Hold the card flat against the reader         │
│              surface for 1-2 seconds                      │
│                                                             │
│  ✓ Expected: Blue LED lights up                             │
│              Logs show: 'Card detected! UID: ...'           │
│                                                             │
│         [ NFC CARD ]                                        │
│            |                                                │
│            v                                                │
│    ┌───────────────┐                                       │
│    │  PN532 MODULE │                                       │
│    │   [ANTENNA]   │                                       │
│    └───────────────┘                                       │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Taps white card on reader, clicks OK

**Log Output:**
```
I (2500) pn532: Card detected!
I (2510) pn532: UID: 0xA1B2C3D4
I (2520) pn532: Card type: MIFARE Classic 1K
I (2530) pn532: Authentication successful
I (2540) pn532: Read 16 bytes from block 4
I (2550) main: Card A read successfully - Data: Hello World
```

**AI:** ✓ Card A detected and read correctly

### Step 3: Remove Card A

**AI detects:** Card A successfully read, needs removal test

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 3 of 6: Remove Card A                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Please remove the WHITE card from the reader.             │
│                                                             │
│  📍 Action: Lift the card straight up and away from        │
│             the reader (at least 10cm)                    │
│                                                             │
│  ✓ Expected: Blue LED turns off                             │
│              Logs show: 'Card removed'                      │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Removes card, clicks OK

**Log Output:**
```
I (3500) pn532: Card removed
I (3510) main: Waiting for next card...
```

### Step 4: Present Card B (Blue Card - Different Type)

**AI detects:** Removal detection working, testing different card type

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 4 of 6: Present Card B                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Please use the BLUE card now.                              │
│                                                             │
│  📍 Card: Card B (NTAG213 - different type!)                │
│     Expected UID: 0xE5F6A7B8                                │
│     Expected NDEF message                                   │
│                                                             │
│  📍 Location: Same PN532 module (center of breadboard)     │
│                                                             │
│  ⏱️  Action: Tap and hold for 2 seconds                     │
│                                                             │
│  ✓ Expected: Blue LED lights up                             │
│              Logs show different card type                  │
│              NDEF message should be read                    │
│                                                             │
│                    [ OK ]  [ Cancel ]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Taps blue card, clicks OK

**Log Output:**
```
I (4500) pn532: Card detected!
I (4510) pn532: UID: 0xE5F6A7B8
I (4520) pn532: Card type: NTAG213 (different from previous!)
I (4530) pn532: NDEF message found
I (4540) pn532: NDEF content: 'https://example.com/nfc-test'
I (4550) main: Card B read successfully - URL extracted
```

**AI:** ✓ Different card type detected and handled correctly

### Step 5: Range Test

**AI detects:** Both card types working, testing detection range

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 5 of 6: Range Test                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Find the maximum reading distance.                         │
│                                                             │
│  📍 Setup: Hold the WHITE card 15cm from the reader        │
│                                                             │
│  📏 Action: Slowly move the card closer to the reader      │
│            until the blue LED lights up                   │
│                                                             │
│  🎯 Task: Note the distance when detection occurs          │
│                                                             │
│  💡 Tip: The PN532 typically reads within 5-10cm           │
│                                                             │
│  What distance did the card read at?                        │
│                                                             │
│                    [ 5cm ]  [ 10cm ]  [ Other ]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Tests range, selects "10cm"

**AI:** Logs the range test result for documentation

### Step 6: Multiple Rapid Reads

**AI detects:** Range established, testing rapid detection

**Zenity Prompt:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Step 6 of 6: Rapid Read Test                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Test rapid card detection.                                 │
│                                                             │
│  ⏱️  Action: Tap the WHITE card 5 times in succession      │
│            (as fast as you can while still reading)       │
│                                                             │
│  🔢 Count: Exactly 5 taps                                   │
│                                                             │
│  ✓ Expected: All 5 taps detected in logs                   │
│                                                             │
│                    [ OK when done ]  [ Cancel ]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User:** Taps card 5 times rapidly, clicks OK

**Log Output:**
```
I (6000) pn532: Card detected! UID: 0xA1B2C3D4
I (6100) pn532: Card removed
I (6150) pn532: Card detected! UID: 0xA1B2C3D4
I (6250) pn532: Card removed
I (6300) pn532: Card detected! UID: 0xA1B2C3D4
I (6400) pn532: Card removed
I (6450) pn532: Card detected! UID: 0xA1B2C3D4
I (6550) pn532: Card removed
I (6600) pn532: Card detected! UID: 0xA1B2C3D4
I (6700) pn532: Card removed
I (6750) main: 5 rapid reads successful - debounce working
```

## Session Complete

**Zenity Summary:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✓ NFC Reader Test Complete                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Session ID: dev-20240115-143000                            │
│  Duration: 8 minutes                                          │
│                                                             │
│  Physical interactions completed:                           │
│  ✓ Step 1: Cleared reader                                   │
│  ✓ Step 2: Presented Card A (MIFARE Classic)               │
│  ✓ Step 3: Removed Card A                                   │
│  ✓ Step 4: Presented Card B (NTAG213)                      │
│  ✓ Step 5: Range test (10cm max distance)                  │
│  ✓ Step 6: Rapid read test (5/5 successful)              │
│                                                             │
│  Software actions (AI handled):                             │
│  • Built firmware                                           │
│  • Flashed to ESP32                                         │
│  • Monitored logs                                           │
│  • Detected all card events                                 │
│  • Analyzed card types                                      │
│  • Verified NDEF parsing                                    │
│                                                             │
│  Session log saved to:                                      │
│  .weave/sessions/dev-20240115-143000.json                  │
│                                                             │
│                    [ OK ]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Points

### What AI Handled (Software)
- ✓ Building and flashing firmware
- ✓ Starting serial monitor
- ✓ Detecting card events in logs
- ✓ Analyzing card types and data
- ✓ Verifying NDEF message parsing
- ✓ Counting successful reads

### What User Handled (Physical)
- ✓ Moving cards to/from reader
- ✓ Testing different card types
- ✓ Finding max detection range
- ✓ Performing rapid tap test

### No Unnecessary Prompts
The AI **never** asked:
- ❌ "Should I build the firmware?" → Just built it
- ❌ "Do you want me to reset the device?" - Software reset handled automatically
- ❌ "Can I change the I2C address?" → Would fix config automatically if needed
- ❌ "Should I retry the flash?" → Would retry automatically on failure

## Error Scenario: Card Not Detected

If the card wasn't detected, the AI would:

1. **Software checks first (no prompt):**
   - Check I2C configuration
   - Verify PN532 initialization
   - Check for firmware errors

2. **Only if software checks pass, then prompt:**
   ```
   🔧 Card Not Detected
   
   The PN532 is initialized but no card is being detected.
   
   Software checks passed:
   ✓ I2C communication OK
   ✓ PN532 responding
   ✓ Antenna enabled
   
   Please check physically:
   📍 Is the card on the correct side of the reader?
   📍 Is the card within 10cm?
   📍 Try a different card
   
   [Retry] [Try different card] [Check wiring] [Abort]
   ```

## Command Reference

```bash
# Start NFC testing session
./scripts/interactive_session.py \
  --project ./nfc_reader \
  --port /dev/ttyUSB0 \
  --patterns "pn532,card,uid,ndef"

# Manual card present prompt
./scripts/zenity_prompt.sh --info \
  "Please tap the NFC card on the reader, then click OK"

# Multi-step card sequence
./scripts/zenity_prompt.sh --list "Select card to test:" \
  "White Card (MIFARE)" "Blue Card (NTAG)" "Skip test"
```
