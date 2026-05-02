# Prompt Types

Every prompt has exactly **2 buttons**.

## TYPE 1: Physical Action

**Buttons:** ✓ Done / Skip (or ✓ Done / ❌ Can't do it)

```
┌─────────────────────────────┐
│ [TYPE 1] Decision             │
├─────────────────────────────┤
│                             │
│  Tap the NFC card           │
│                             │
│    [✓ Done]  [Skip]         │
│                             │
└─────────────────────────────┘
```

## TYPE 2: Verification

**Buttons:** Yes / No

```
┌─────────────────────────────┐
│ [TYPE 2] Verification       │
├─────────────────────────────┤
│                             │
│  Did it work?               │
│                             │
│     [Yes]  [No]             │
│                             │
└─────────────────────────────┘
```

**If NO → Problem Description:**

```
┌─────────────────────────────┐
│ [TYPE 1] Problem Description│
├─────────────────────────────┤
│                             │
│  What did you observe?      │
│                             │
│  ┌─────────────────────┐    │
│  │                     │    │
│  └─────────────────────┘    │
│                             │
│      [OK]  [Cancel]         │
│                             │
└─────────────────────────────┘
```

## All Methods

| Method | Type | Buttons |
|--------|------|---------|
| `_ask_yes_no()` | TYPE 2 | Yes / No |
| `_ask_yes_no_custom()` | TYPE 2 | Custom 2 |
| `_prompt_physical_action()` | TYPE 1 | ✓ Done / Skip |
| `_prompt_physical_action_with_result()` | TYPE 1 | ✓ Done / ❌ Can't do it |
| `_ask_input()` | TYPE 1 | OK / Cancel |
| `_ask_number()` | TYPE 2 | OK / Cancel |
| `_ask_yes_no_with_description()` | TYPE 2→1 | Yes/No → OK/Cancel |

## Removed

- ❌ List dialogs (checkboxes)
- ❌ Info/Error/Warning for decisions
- ❌ More than 2 buttons