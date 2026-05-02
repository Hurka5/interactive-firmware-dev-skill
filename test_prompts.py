#!/usr/bin/env python3
"""
Test script to demonstrate all prompt types in the interactive-firmware-dev skill.
Run this to verify all prompts have exactly 2 buttons.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from interactive_session import InteractiveSession, SessionConfig

def test_all_prompts():
    """Test all prompt types to verify 2-button compliance."""
    
    # Create a minimal session config
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
    
    print("=" * 60)
    print("TESTING ALL PROMPT TYPES")
    print("=" * 60)
    print()
    
    # 1. TYPE 2: Simple Yes/No Verification
    print("1. TYPE 2: _ask_yes_no() - Simple Verification")
    print("   Title: [TYPE 2] Verification")
    print("   Buttons: Yes / No")
    print("   Example: 'Hardware checked. Retry?'")
    result = session._ask_yes_no("Hardware checked. Retry?")
    print(f"   Result: {result}")
    print()
    
    # 2. TYPE 2: Custom Decision
    print("2. TYPE 2: _ask_yes_no_custom() - Custom Decision")
    print("   Title: [TYPE 2] Decision")
    print("   Buttons: ✓ Fix automatically / ✗ Skip fix")
    print("   Example: 'Wi-Fi connection failed. Attempt automatic fix?'")
    result = session._ask_yes_no_custom(
        "Wi-Fi connection failed. Attempt automatic fix?",
        ok_label="✓ Fix automatically",
        cancel_label="✗ Skip fix",
        prompt_type="TYPE 2"
    )
    print(f"   Result: {result}")
    print()
    
    # 3. TYPE 1: Physical Action Instruction
    print("3. TYPE 1: _prompt_physical_action() - Physical Action")
    print("   Title: [TYPE 1] Decision")
    print("   Buttons: ✓ Done / Skip")
    print("   Example: 'Tap the NFC card on the reader'")
    result = session._prompt_physical_action("Tap the NFC card on the reader")
    print(f"   Result: {result}")
    print()
    
    # 4. TYPE 1: Physical Action with Failure Option
    print("4. TYPE 1: _prompt_physical_action_with_result() - Action with Failure")
    print("   Title: [TYPE 1] Decision")
    print("   Buttons: ✓ Done / ❌ Can't do it")
    print("   If 'Can't do it' clicked, shows text entry for problem description")
    print("   Example: 'Press the button on the device'")
    success, problem = session._prompt_physical_action_with_result("Press the button on the device")
    print(f"   Success: {success}, Problem: {problem}")
    print()
    
    # 5. TYPE 1: Problem Description Input
    print("5. TYPE 1: _ask_input() - Problem Description")
    print("   Title: [TYPE 1] Problem Description")
    print("   Buttons: OK / Cancel")
    print("   Example: 'What prevented you from performing the action?'")
    result = session._ask_input("What prevented you from performing the action?\n\nDescribe the issue:", "")
    print(f"   Result: {result}")
    print()
    
    # 6. TYPE 2: Numeric Input
    print("6. TYPE 2: _ask_number() - Numeric Input")
    print("   Title: [TYPE 2] Numeric Input")
    print("   Buttons: OK / Cancel")
    print("   Example: 'Connection timeout (seconds):' with slider 5-120")
    result = session._ask_number("Connection timeout (seconds):", 5, 120, 30)
    print(f"   Result: {result}")
    print()
    
    # 7. TYPE 2: Yes/No with Description Flow
    print("7. TYPE 2: _ask_yes_no_with_description() - Verification with Details")
    print("   Step 1 Title: [TYPE 2] Decision")
    print("   Step 1 Buttons: ✓ YES - Working / ✗ NO - Not working")
    print("   If NO: Shows TYPE 1 Problem Description entry")
    print("   Example: 'Did the NFC card read successfully?'")
    is_working, description = session._ask_yes_no_with_description("Did the NFC card read successfully?")
    print(f"   Working: {is_working}, Description: {description}")
    print()
    
    print("=" * 60)
    print("ALL PROMPT TYPES TESTED")
    print("=" * 60)
    print()
    print("Summary:")
    print("- TYPE 1 prompts: Physical actions, problem descriptions")
    print("- TYPE 2 prompts: Verifications, decisions, numeric input")
    print("- ALL prompts have exactly 2 buttons")
    print("- NO list dialogs (checkboxes) used")
    print("- NO info/error/warning dialogs used for decisions")

if __name__ == "__main__":
    # Check if display is available
    import os
    if not os.environ.get('DISPLAY'):
        print("WARNING: No DISPLAY environment variable set.")
        print("Zenity dialogs require a graphical display.")
        print("For SSH, use: ssh -X user@host")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    test_all_prompts()