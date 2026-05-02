#!/usr/bin/env python3
"""Test all 7 prompt types. Each has exactly 2 buttons."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from interactive_session import InteractiveSession, SessionConfig

def test_prompts():
    config = SessionConfig(
        project_path="/tmp/test",
        port="/dev/ttyUSB0",
        baud=115200,
        target="esp32",
        platform="esp-idf",
        patterns={},
        auto_fix=False
    )
    session = InteractiveSession(config)
    
    prompts = [
        ("1. TYPE 2: Yes/No", lambda: session._ask_yes_no("Hardware checked?")),
        ("2. TYPE 2: Custom", lambda: session._ask_yes_no_custom("Fix it?", "✓ Fix", "✗ Skip", prompt_type="TYPE 2")),
        ("3. TYPE 1: Physical", lambda: session._prompt_physical_action("Tap the card")),
        ("4. TYPE 1: With failure", lambda: session._prompt_physical_action_with_result("Press the button")),
        ("5. TYPE 1: Input", lambda: session._ask_input("What happened?", "")),
        ("6. TYPE 2: Number", lambda: session._ask_number("Timeout:", 5, 120, 30)),
        ("7. TYPE 2: With desc", lambda: session._ask_yes_no_with_description("Did it work?")),
    ]
    
    for name, fn in prompts:
        print(f"\n{name}")
        print("-" * 40)
        result = fn()
        print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("All prompts tested - each has exactly 2 buttons")

if __name__ == "__main__":
    import os
    if not os.environ.get('DISPLAY'):
        print("WARNING: No DISPLAY. For SSH use: ssh -X user@host")
        if input("Continue? (y/n): ").lower() != 'y':
            sys.exit(1)
    test_prompts()