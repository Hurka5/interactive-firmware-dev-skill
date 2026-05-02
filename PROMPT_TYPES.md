# Prompt Type Reference Guide

This document shows all prompt types used in the interactive-firmware-dev skill.
**Every prompt has exactly 2 buttons.**

---

## TYPE 1 Prompts: Physical Actions & Problem Description

Used when the user needs to perform a physical action or describe a problem.

### 1. Simple Physical Action
**Method:** `_prompt_physical_action()`

```
┌─────────────────────────────────────────┐
│ [TYPE 1] Decision                       │
├─────────────────────────────────────────┤
│                                         │
│  Tap the NFC card on the reader         │
│                                         │
│         [✓ Done]    [Skip]              │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** ✓ Done / Skip

---

### 2. Physical Action with Failure Option
**Method:** `_prompt_physical_action_with_result()`

```
┌─────────────────────────────────────────┐
│ [TYPE 1] Decision                       │
├─────────────────────────────────────────┤
│                                         │
│  Press the button on the device         │
│                                         │
│      [✓ Done]    [❌ Can't do it]       │
│                                         │
└─────────────────────────────────────────┘
```

**If "❌ Can't do it" clicked, shows:**

```
┌─────────────────────────────────────────┐
│ [TYPE 1] Problem Description            │
├─────────────────────────────────────────┤
│                                         │
│  What prevented you from performing     │
│  the action?                            │
│                                         │
│  Describe the issue:                    │
│  ┌─────────────────────────────────┐    │
│  │ Button is broken                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│              [OK]    [Cancel]           │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** ✓ Done / ❌ Can't do it → then OK / Cancel

---

### 3. Problem Description Entry
**Method:** `_ask_input()`

```
┌─────────────────────────────────────────┐
│ [TYPE 1] Problem Description            │
├─────────────────────────────────────────┤
│                                         │
│  What did you observe?                  │
│                                         │
│  Examples:                              │
│  - 'LED blinking but no sound'          │
│  - 'Screen shows error'                 │
│  - 'No response at all'                 │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │                                  │    │
│  └─────────────────────────────────┘    │
│                                         │
│              [OK]    [Cancel]           │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** OK / Cancel

---

## TYPE 2 Prompts: Verifications & Decisions

Used when asking the user to verify something or make a decision.

### 4. Simple Yes/No Verification
**Method:** `_ask_yes_no()`

```
┌─────────────────────────────────────────┐
│ [TYPE 2] Verification                   │
├─────────────────────────────────────────┤
│                                         │
│  Hardware checked. Retry?               │
│                                         │
│              [Yes]    [No]              │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** Yes / No

---

### 5. Custom Decision
**Method:** `_ask_yes_no_custom()`

```
┌─────────────────────────────────────────┐
│ [TYPE 2] Decision                       │
├─────────────────────────────────────────┤
│                                         │
│  Wi-Fi connection failed.               │
│  Attempt automatic fix?                 │
│                                         │
│   [✓ Fix automatically]  [✗ Skip fix]   │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** ✓ Fix automatically / ✗ Skip fix

---

### 6. Numeric Input
**Method:** `_ask_number()`

```
┌─────────────────────────────────────────┐
│ [TYPE 2] Numeric Input                  │
├─────────────────────────────────────────┤
│                                         │
│  Connection timeout (seconds):          │
│                                         │
│  5 [────────●──────────────] 120        │
│            30                           │
│                                         │
│              [OK]    [Cancel]           │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** OK / Cancel

---

### 7. Verification with Description Flow
**Method:** `_ask_yes_no_with_description()`

**Step 1:**
```
┌─────────────────────────────────────────┐
│ [TYPE 2] Decision                       │
├─────────────────────────────────────────┤
│                                         │
│  Did the NFC card read successfully?    │
│                                         │
│  [✓ YES - Working]  [✗ NO - Not working]│
│                                         │
└─────────────────────────────────────────┘
```

**If "✗ NO" clicked, Step 2:**
```
┌─────────────────────────────────────────┐
│ [TYPE 1] Problem Description            │
├─────────────────────────────────────────┤
│                                         │
│  What did you observe?                  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Card not detected               │    │
│  └─────────────────────────────────┘    │
│                                         │
│              [OK]    [Cancel]           │
│                                         │
└─────────────────────────────────────────┘
```

**Buttons:** ✓ YES - Working / ✗ NO - Not working → then OK / Cancel

---

## Summary Table

| Method | Type | Title | Buttons | Use Case |
|--------|------|-------|---------|----------|
| `_ask_yes_no()` | TYPE 2 | [TYPE 2] Verification | Yes / No | Simple verification |
| `_ask_yes_no_custom()` | TYPE 1/2 | [TYPE 1/2] Decision | Custom 2 | Decision with context |
| `_prompt_physical_action()` | TYPE 1 | [TYPE 1] Decision | ✓ Done / Skip | Simple physical action |
| `_prompt_physical_action_with_result()` | TYPE 1 | [TYPE 1] Decision | ✓ Done / ❌ Can't do it | Physical action with failure option |
| `_ask_input()` | TYPE 1 | [TYPE 1] Problem Description | OK / Cancel | Text input |
| `_ask_number()` | TYPE 2 | [TYPE 2] Numeric Input | OK / Cancel | Numeric input |
| `_ask_yes_no_with_description()` | TYPE 2 → TYPE 1 | [TYPE 2] Decision → [TYPE 1] Problem Description | ✓ YES / ✗ NO → OK / Cancel | Verification with details |

---

## What Was Removed

The following dialog types are **NOT used** for user decisions:

- ❌ `--list` (checkboxes/radio buttons) - Was causing the confusing UI you encountered
- ❌ `--info` (single OK button) - Not suitable for decisions
- ❌ `--error` (single OK button) - Not suitable for decisions  
- ❌ `--warning` (single OK button) - Not suitable for decisions

All decisions now use exactly 2 buttons.