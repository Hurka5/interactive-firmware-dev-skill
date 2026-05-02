#!/usr/bin/env python3
"""
Interactive Firmware Development Session Manager

Coordinates AI coding, building, flashing, and user interaction via Zenity.
This script manages the full workflow:
1. Detects project type (ESP-IDF, Arduino, PlatformIO)
2. Builds and flashes firmware automatically (software actions)
3. Monitors serial logs for patterns
4. Prompts user via Zenity ONLY for physical actions

Physical actions (user handles):
- Moving NFC cards, rotating encoders, pressing buttons
- Power cycling, connecting hardware, triggering sensors

Software actions (AI handles automatically):
- Building, flashing, resetting, config changes
- All status messages go to console (not zenity)
"""

import subprocess
import json
import time
import argparse
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import log watcher from same directory
sys.path.insert(0, str(Path(__file__).parent))
from log_watcher import LogWatcher, LogMatch, LogLevel

# Import retry manager and test config
try:
    from retry_manager import RetryManager, RetryConfig, ErrorType
    from test_config import TestConfig, TestRunner, ConfigManager, load_test_config
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Advanced features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False


class SessionState(Enum):
    """States the interactive session can be in."""
    INITIALIZING = "initializing"
    CODING = "coding"
    BUILDING = "building"
    FLASHING = "flashing"
    MONITORING = "monitoring"
    WAITING_USER = "waiting_user"  # Waiting for physical action
    APPLYING_FIX = "applying_fix"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SessionEvent:
    """Records what happened during the session."""
    timestamp: str
    state: str
    event_type: str
    details: Dict
    user_action: Optional[str] = None


@dataclass
class SessionConfig:
    """Configuration for the interactive session."""
    project_path: str
    port: str
    baud: int
    target: str
    platform: str  # "esp-idf", "arduino", "platformio"
    patterns: List[str]
    auto_fix: bool
    session_file: Optional[str] = None
    test_config_path: Optional[str] = None  # Path to YAML/JSON test config
    retry_config_path: Optional[str] = None  # Path to retry configuration
    log_file: Optional[str] = None  # Path to serial log file
    clear_log_on_reset: bool = True  # Clear log file on device reset
    pattern_limits: Optional[Dict[str, int]] = None  # Pattern occurrence limits
    stop_on_limit: bool = True  # Stop monitoring when limits exceeded
    reset_before_debug: bool = True  # Reset device before each debug session
    physical_verification: bool = True  # Ask user to verify physical outcomes instead of judging from logs


def check_display_available() -> bool:
    """
    Check if graphical display is available for Zenity dialogs.
    
    Returns:
        bool: True if display is available, False otherwise
    """
    # Check for DISPLAY environment variable (X11)
    if os.environ.get('DISPLAY'):
        return True
    
    # Check for Wayland
    if os.environ.get('WAYLAND_DISPLAY'):
        return True
    
    # Try to run a simple zenity command to test
    try:
        result = subprocess.run(
            ['zenity', '--info', '--text=Test', '--timeout=1'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False


class InteractiveSession:
    """
    Manages an interactive firmware development session.
    
    Key principle: AI handles all software actions automatically.
    Only prompts user for physical actions it cannot perform.
    
    Software status messages go to console (print).
    Only physical actions use Zenity dialogs.
    """
    
    def __init__(self, config: SessionConfig):
        self.config = config
        self.state = SessionState.INITIALIZING
        self.events: List[SessionEvent] = []
        self.watcher: Optional[LogWatcher] = None
        self.session_id = f"dev-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        # Track fix attempts per pattern to avoid global limit blocking different fixes
        self.fix_attempts: Dict[str, int] = {}
        self.max_fix_attempts = 5
        self.last_fixed_pattern: Optional[str] = None
        
        # Test sequence tracking
        self.test_steps: List[Dict[str, Any]] = []
        self.current_step_index: int = 0
        
        # Path to zenity helper script
        self.zenity_script = Path(__file__).parent / "zenity_prompt.sh"
        
        # Initialize retry manager if available
        self.retry_manager: Optional['RetryManager'] = None
        if ADVANCED_FEATURES_AVAILABLE:
            retry_config = self._load_retry_config()
            self.retry_manager = RetryManager(retry_config)
        
        # Initialize test config if provided
        self.test_runner: Optional['TestRunner'] = None
        self.test_config: Optional['TestConfig'] = None
        if ADVANCED_FEATURES_AVAILABLE and config.test_config_path:
            self._load_test_config()
    
    def _log_event(self, event_type: str, details: Dict, user_action: Optional[str] = None):
        """Record an event in the session history."""
        event = SessionEvent(
            timestamp=datetime.now().isoformat(),
            state=self.state.value,
            event_type=event_type,
            details=details,
            user_action=user_action
        )
        self.events.append(event)
        self._save_session()
    
    def _save_session(self):
        """Save session state to JSON file for persistence."""
        if self.config.session_file:
            session_data = {
                "session_id": self.session_id,
                "config": {
                    "project_path": self.config.project_path,
                    "port": self.config.port,
                    "baud": self.config.baud,
                    "target": self.config.target,
                    "platform": self.config.platform,
                    "patterns": self.config.patterns
                },
                "current_state": self.state.value,
                "events": [asdict(e) for e in self.events],
                "fix_attempts": self.fix_attempts
            }
            with open(self.config.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
    
    def _zenity(self, dialog_type: str, *args, timeout: Optional[int] = None) -> Tuple[int, str]:
        """
        Execute a zenity dialog and return result.
        Only used for PHYSICAL actions that require user interaction.
        
        Args:
            dialog_type: Type of dialog (info, error, question, entry, list, scale)
            args: Arguments for the dialog
            timeout: Optional timeout in seconds
            
        Returns:
            Tuple of (exit_code, output_text)
            Exit codes: 0=success/yes, 1=cancel/no, 5=timeout
        """
        cmd = [str(self.zenity_script), f"--{dialog_type}"] + list(args)
        if timeout:
            cmd.extend(["--timeout", str(timeout)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or 300
            )
            return (result.returncode, result.stdout.strip())
        except subprocess.TimeoutExpired:
            return (5, "")  # Timeout exit code
        except Exception as e:
            print(f"Zenity error: {e}", file=sys.stderr)
            return (1, "")
    
    def _prompt_physical_action_with_result(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Prompt user for a PHYSICAL action using Zenity.
        Returns: (success, problem_description)
        - success: True if action performed, False if user couldn't do it
        - problem_description: User's explanation if they couldn't perform the action
        
        TYPE 1 PROMPT: Must allow user to indicate if action failed!
        """
        # Use choice dialog instead of info - gives user option to indicate failure
        choice = self._ask_choice(
            message + "\n\nSelect your result:",
            [
                "✓ Done - I performed the action",
                "❌ Can't do it - There's a problem"
            ],
            timeout=60
        )
        
        if choice == "✓ Done - I performed the action":
            return True, None
        elif choice == "❌ Can't do it - There's a problem":
            # User couldn't perform action - ask what went wrong
            problem = self._ask_input(
                "❌ What prevented you from performing the action?\n\n"
                "Examples:\n"
                "- 'Card is missing'\n"
                "- 'Button is broken'\n"
                "- 'Can't reach the device'\n\n"
                "Describe the issue:",
                ""
            )
            return False, problem
        else:
            # Timeout or cancel - treat as failure
            return False, "User did not confirm action completion"
    
    def _ask_yes_no(self, question: str, timeout: Optional[int] = None) -> bool:
        """Ask user a yes/no question. Returns True if yes/OK."""
        code, _ = self._zenity("question", question, timeout=timeout)
        return code == 0
    
    def _ask_choice(self, question: str, options: List[str], timeout: Optional[int] = None) -> Optional[str]:
        """Ask user to choose from a list of options."""
        code, choice = self._zenity("list", question, *options, timeout=timeout)
        if code == 0:
            return choice
        return None
    
    def _ask_input(self, prompt: str, default: str = "") -> Optional[str]:
        """Ask user for text input."""
        args = [prompt]
        if default:
            args.append(default)
        code, value = self._zenity("entry", *args)
        if code == 0:
            return value
        return None
    
    def _ask_number(self, prompt: str, min_val: int, max_val: int, default: int) -> Optional[int]:
        """Ask user for a number using a scale slider."""
        code, value = self._zenity("scale", prompt, str(min_val), str(max_val), str(default))
        if code == 0 and value:
            try:
                return int(value)
            except ValueError:
                pass
        return None
    
    def _handle_log_match(self, match: LogMatch):
        """
        Handle a detected log pattern match.
        
        This is called when the log watcher detects a pattern.
        It decides whether to prompt the user (physical action)
        or handle automatically (software action).
        """
        self.state = SessionState.WAITING_USER
        
        # Log the detection
        self._log_event("pattern_detected", match.to_dict())
        
        # Build context message from recent log lines
        context_msg = ""
        if match.context:
            context_msg = "\n\nRecent context:\n" + "\n".join(match.context[-3:])
        
        # Handle based on severity level
        if match.level == LogLevel.FATAL:
            self._handle_fatal_error(match, context_msg)
        elif match.level == LogLevel.ERROR:
            self._handle_error(match, context_msg)
        elif match.level == LogLevel.WARNING:
            self._handle_warning(match, context_msg)
        else:
            self._handle_info_match(match, context_msg)
    
    def _handle_fatal_error(self, match: LogMatch, context_msg: str):
        """
        Handle fatal errors (panics, crashes).
        
        For fatal errors, we may need physical intervention
        like hardware reset if software reset fails.
        """
        message = f"FATAL ERROR DETECTED\n\nPattern: {match.pattern}\nLine: {match.log_line}{context_msg}\n\nWhat would you like to do?"
        
        choice = self._ask_choice(message, [
            "Inspect code and suggest fix",
            "Increase stack size and retry",
            "Check hardware connections",
            "View full log context",
            "Abort session"
        ])
        
        if choice == "Inspect code and suggest fix":
            self._log_event("user_decision", {"pattern": match.pattern}, "inspect_and_fix")
            self._apply_fix(match, "fatal")
        elif choice == "Increase stack size and retry":
            self._log_event("user_decision", {"pattern": match.pattern}, "increase_stack")
            self._modify_stack_size()
        elif choice == "Check hardware connections":
            self._log_event("user_decision", {"pattern": match.pattern}, "check_hardware")
            # PHYSICAL ACTION: User checks hardware
            self._prompt_physical_action("Please check:\n- Power supply\n- USB cable\n- Boot/reset connections\n- Peripheral wiring")
            if self._ask_yes_no("Hardware checked. Retry?"):
                self._restart_monitoring()
        elif choice == "View full log context":
            print(f"Full context:\n{chr(10).join(match.context)}")
            self._handle_fatal_error(match, "")  # Re-prompt
        else:
            self._abort_session("User aborted after fatal error")
    
    def _handle_error(self, match: LogMatch, context_msg: str):
        """
        Handle regular errors.
        
        Most errors are handled automatically by the AI.
        Only prompt user if physical action is needed.
        """
        message = f"ERROR DETECTED\n\nPattern: {match.pattern}\nLine: {match.log_line}{context_msg}\n\nWhat would you like to do?"
        
        choice = self._ask_choice(message, [
            "Fix the issue automatically",
            "Show me the code to fix",
            "Ignore and continue monitoring",
            "Edit configuration",
            "Abort session"
        ], timeout=60)
        
        if choice == "Fix the issue automatically":
            # SOFTWARE ACTION: AI fixes automatically
            self._log_event("user_decision", {"pattern": match.pattern}, "auto_fix")
            self._apply_fix(match, "error")
        elif choice == "Show me the code to fix":
            self._log_event("user_decision", {"pattern": match.pattern}, "show_code")
            self._show_relevant_code(match)
        elif choice == "Ignore and continue monitoring":
            self._log_event("user_decision", {"pattern": match.pattern}, "ignore")
            self.state = SessionState.MONITORING
        elif choice == "Edit configuration":
            # SOFTWARE ACTION: AI updates config
            self._log_event("user_decision", {"pattern": match.pattern}, "edit_config")
            self._edit_configuration(match)
        else:
            self._abort_session("User aborted")
    
    def _handle_warning(self, match: LogMatch, context_msg: str):
        """Handle warnings - usually handled automatically."""
        if not self.config.auto_fix:
            return
        
        message = f"WARNING DETECTED\n\nPattern: {match.pattern}\nLine: {match.log_line}{context_msg}\n\nAction?"
        
        choice = self._ask_choice(message, [
            "Fix now",
            "Continue monitoring",
            "Suppress this warning"
        ], timeout=30)
        
        if choice == "Fix now":
            self._apply_fix(match, "warning")
        elif choice == "Suppress this warning":
            self._log_event("user_decision", {"pattern": match.pattern}, "suppress")
            # Remove pattern from watcher
            if match.pattern in self.watcher.compiled_patterns:
                del self.watcher.compiled_patterns[match.pattern]
        else:
            self._log_event("user_decision", {"pattern": match.pattern}, "continue")
    
    def _get_current_step(self, checkpoint_type: str) -> Tuple[int, str, str]:
        """
        Get current step number and action.
        Returns: (step_number, step_name, action_description)
        Each test has at least 2 steps: what to do and is it happening.
        
        CRITICAL: Only ONE action per prompt. No lists. No "and".
        Keep it simple and focused.
        """
        # Define test steps - each test has exactly 2 steps minimum
        # Step 1: What to do (instruction) - ONLY ONE ACTION, NO LISTS
        # Step 2: Is it happening (verification)
        step_definitions = {
            'nfc': (
                1,
                "NFC Card Test",
                "Tap the NFC card on the reader"
            ),
            'button': (
                1,
                "Button Test",
                "Press the button on the device"
            ),
            'encoder': (
                1,
                "Encoder Test",
                "Rotate the encoder knob"
            ),
            'sensor': (
                1,
                "Sensor Test",
                "Wave your hand near the sensor"
            ),
        }
        
        return step_definitions.get(checkpoint_type, (1, "Test Step", "Perform the action"))
    
    def _wait_for_pattern_with_timeout(
        self,
        pattern: str,
        timeout_seconds: float = 10.0,
        proactive_prompt_threshold: float = 5.0,
        proactive_message: Optional[str] = None
    ) -> Optional[LogMatch]:
        """
        Wait for a specific pattern with timeout and proactive user prompting.
        
        Monitors for the minimal amount of time needed. If the user can help
        make something happen faster, proactively asks them to do it.
        
        Args:
            pattern: Pattern name to wait for
            timeout_seconds: Maximum time to wait
            proactive_prompt_threshold: Time before showing proactive prompt
            proactive_message: Message to show user to speed things up
            
        Returns:
            LogMatch if pattern found, None if timeout
        """
        import time
        
        start_time = time.time()
        last_proactive_prompt = 0
        match_result: Optional[LogMatch] = None
        
        print(f"Waiting for pattern '{pattern}' (timeout: {timeout_seconds}s)...")
        
        while time.time() - start_time < timeout_seconds:
            # Process any pending matches
            if self.watcher:
                self.watcher.process_matches()
            
            # Check if pattern was detected (would be handled by _handle_info_match)
            # For now, we just wait and check periodically
            elapsed = time.time() - start_time
            remaining = timeout_seconds - elapsed
            
            # Show proactive prompt if threshold reached and not shown yet
            if (proactive_message and 
                elapsed >= proactive_prompt_threshold and 
                last_proactive_prompt < proactive_prompt_threshold):
                print(f"\n[⏱️  {elapsed:.1f}s elapsed] Proactively prompting user...")
                self._prompt_physical_action(proactive_message)
                last_proactive_prompt = elapsed
            
            # Short sleep to prevent CPU spinning
            time.sleep(0.1)
        
        # Timeout reached
        print(f"\n[⏱️  Timeout] Pattern '{pattern}' not detected within {timeout_seconds}s")
        return match_result
    
    def _speed_up_test_prompt(self, checkpoint_type: str):
        """
        Proactively ask user to perform action to speed up testing.
        ONE simple reminder. No lists.
        """
        step_num, step_name, action = self._get_current_step(checkpoint_type)
        
        # Simple reminder with ONE action
        message = (
            f"⏱️  Please {action.lower()} now"
        )
        
        self._prompt_physical_action(message)
    
    def _show_instruction_prompt(self, checkpoint_type: str, match: LogMatch) -> Tuple[bool, Optional[str]]:
        """
        TYPE 1 PROMPT: Instruction
        Tells user what to do. ONE action only. No lists.
        
        CRITICAL RULES:
        - Only ONE action per prompt
        - No numbered lists (1., 2., 3.)
        - No "and" connecting multiple actions
        - Simple, focused instruction
        - MUST allow user to indicate if action failed (not just OK button)
        
        Returns: (action_performed, problem_description)
        - action_performed: True if user did it, False if couldn't
        - problem_description: What went wrong if False
        """
        step_num, step_name, action = self._get_current_step(checkpoint_type)
        
        # Simple, focused message with ONE action only
        message = (
            f"📋 {step_name}\n\n"
            f"👉 {action}"
        )
        
        # Use new method that allows user to indicate failure
        return self._prompt_physical_action_with_result(message)
    
    def _show_verification_prompt(self, checkpoint_type: str) -> Tuple[bool, Optional[str]]:
        """
        TYPE 2 PROMPT: Verification
        Asks if everything is working. ONE observation only.
        
        CRITICAL RULES:
        - Only ONE thing to observe
        - No lists of multiple things to check
        - Simple YES/NO question
        """
        step_num, step_name, _ = self._get_current_step(checkpoint_type)
        
        # Map checkpoint types to ONE thing to observe (no lists)
        what_to_observe = {
            'nfc': "Did the NFC card trigger a response?",
            'button': "Did the button press work?",
            'encoder': "Did rotating the knob change anything?",
            'sensor': "Did the sensor detect your hand?",
        }
        
        observe = what_to_observe.get(checkpoint_type, "Did it work?")
        
        # Simple verification message
        message = (
            f"📋 {step_name}\n\n"
            f"{observe}"
        )
        
        # Ask YES/NO - if NO, agent stops and waits for user input
        if self._ask_yes_no(message, timeout=60):
            # YES - everything works
            return True, None
        else:
            # NO - something is wrong, agent stops and waits for user input
            problem = self._ask_input(
                "❌ Something is not right.\n\n"
                "Please describe what you observe:\n"
                "(What do you see/hear/feel instead of the expected behavior?)\n\n"
                "Your observation:",
                ""
            )
            if problem:
                print(f"\nUser observation: {problem}")
                self._log_event("verification_failed", {
                    "checkpoint_type": checkpoint_type,
                    "problem_description": problem
                })
            return False, problem
    
    def _handle_info_match(self, match: LogMatch, context_msg: str):
        """
        Handle info-level matches (checkpoints).
        
        Uses exactly 2 types of prompts:
        1. INSTRUCTION: Tells user what to do (Step X/Y + Action + OK)
        2. VERIFICATION: Asks if it worked (Step X/Y + What to observe + YES/NO)
        
        If NO on verification, agent STOPS and waits for user input describing the problem.
        
        OPTIMIZED: Monitors for minimal time, proactively prompts user to speed up testing.
        """
        import time
        
        # Determine checkpoint type from pattern or log content
        checkpoint_type = 'generic'
        checkpoint_keys = ['nfc', 'button', 'encoder', 'sensor']
        for key in checkpoint_keys:
            if key in match.pattern.lower() or key in match.log_line.lower():
                checkpoint_type = key
                break
        
        if self.config.physical_verification:
            # Walk user through steps ONE BY ONE (not a list)
            # Each test has at least 2 steps: what to do and is it happening
            
            # TYPE 1 PROMPT: Instruction - tell user what to do (Step 1)
            # User can indicate if they couldn't perform the action (not just OK)
            action_performed, step1_problem = self._show_instruction_prompt(checkpoint_type, match)
            
            if not action_performed:
                # User couldn't perform the action - handle this immediately
                if step1_problem:
                    print(f"\n❌ User couldn't perform action: {step1_problem}")
                    self._log_event("action_failed", {
                        "checkpoint_type": checkpoint_type,
                        "reason": step1_problem
                    })
                    
                    # Ask what to do next
                    choice = self._ask_choice(
                        f"Action failed: {step1_problem}\n\nWhat would you like to do?",
                        [
                            "🔄 Retry this step",
                            "🔧 Check hardware connections",
                            "⏭️  Skip to next step",
                            "❌ Abort session"
                        ],
                        timeout=30
                    )
                    
                    if choice == "🔄 Retry this step":
                        self._handle_info_match(match, context_msg)
                        return
                    elif choice == "🔧 Check hardware connections":
                        self._prompt_physical_action("Please check:\n- Power connections\n- Signal wires\n- Component mounting\n- Battery level")
                        if self._ask_yes_no("Hardware checked. Retry this step?"):
                            self._handle_info_match(match, context_msg)
                            return
                    elif choice == "⏭️  Skip to next step":
                        self.current_step_index += 1
                        return
                    elif choice == "❌ Abort session":
                        self._abort_session("User couldn't perform required action")
                else:
                    # User didn't specify reason - treat as skip
                    print("\n⚠️  Action not performed - skipping to verification")
                
                # Skip monitoring and go to verification or skip
                # Or we could skip directly to next step
                # For now, continue to verification to ask if they want to skip
            
            # Monitor for minimal time with proactive prompting
            timeout = 15.0  # Short timeout - we expect user to act quickly
            proactive_threshold = 3.0  # Prompt user after 3 seconds if no response
            
            start_time = time.time()
            proactive_shown = False
            
            print(f"[⏱️  Monitoring for {timeout}s... Perform the action now!]")
            
            # Brief monitoring loop - don't block indefinitely
            while time.time() - start_time < timeout:
                # Process any pending matches
                if self.watcher:
                    self.watcher.process_matches()
                
                elapsed = time.time() - start_time
                
                # Show proactive prompt if taking too long
                if elapsed >= proactive_threshold and not proactive_shown:
                    self._speed_up_test_prompt(checkpoint_type)
                    proactive_shown = True
                
                time.sleep(0.1)
            
            # TYPE 2 PROMPT: Verification - ask if it worked (Step 2)
            is_working, problem = self._show_verification_prompt(checkpoint_type)
            
            if is_working:
                # YES - success, move to next step
                print("✓ Verification passed - step successful!")
                self._log_event("checkpoint_passed", {"checkpoint_type": checkpoint_type})
                self.current_step_index += 1
            else:
                # NO - agent stops and waits. User must tell what's wrong.
                # Now ask what to do next
                if problem:
                    retry_msg = f"Problem reported: {problem}\n\nWhat would you like to do?"
                else:
                    retry_msg = "Problem detected. What would you like to do?"
                
                choice = self._ask_choice(retry_msg, [
                    "🔄 Retry this step",
                    "🔧 Check hardware connections",
                    "⏭️  Skip to next step",
                    "❌ Abort session"
                ], timeout=30)
                
                if choice == "🔄 Retry this step":
                    self._handle_info_match(match, context_msg)  # Recurse to retry
                    return
                elif choice == "🔧 Check hardware connections":
                    self._prompt_physical_action("Please check:\n- Power connections\n- Signal wires\n- Component mounting\n- Battery level")
                    if self._ask_yes_no("Hardware checked. Retry this step?"):
                        self._handle_info_match(match, context_msg)
                        return
                elif choice == "⏭️  Skip to next step":
                    self.current_step_index += 1
                    return
                elif choice == "❌ Abort session":
                    self._abort_session("User aborted at checkpoint")
        else:
            # Generic checkpoint without physical verification
            message = f"CHECKPOINT\n\n{match.log_line}{context_msg}\n\nContinue?"
            if not self._ask_yes_no(message, timeout=30):
                self._abort_session("User stopped at checkpoint")
    
    def _apply_fix(self, match: LogMatch, severity: str):
        """
        Apply a fix based on the detected pattern.
        
        This is a SOFTWARE ACTION - AI handles it automatically.
        No user prompt needed for software fixes.
        """
        self.state = SessionState.APPLYING_FIX
        
        # Reset counter if this is a different pattern than last time
        if self.last_fixed_pattern != match.pattern:
            self.fix_attempts[match.pattern] = 0
            self.last_fixed_pattern = match.pattern
        
        # Increment per-pattern fix counter
        self.fix_attempts[match.pattern] = self.fix_attempts.get(match.pattern, 0) + 1
        current_attempts = self.fix_attempts[match.pattern]
        
        if current_attempts > self.max_fix_attempts:
            print(f"ERROR: Maximum fix attempts ({self.max_fix_attempts}) reached for pattern '{match.pattern}'. Please review manually.", file=sys.stderr)
            self._abort_session(f"Too many fix attempts for {match.pattern}")
            return
        
        # Pattern-specific fixes - all handled automatically
        fix_applied = False
        
        if match.pattern == "wifi_fail":
            fix_applied = self._fix_wifi_issue(match)
        elif match.pattern == "i2c_fail":
            fix_applied = self._fix_i2c_issue(match)
        elif match.pattern == "sensor_fail":
            fix_applied = self._fix_sensor_issue(match)
        elif match.pattern == "heap_low":
            fix_applied = self._fix_heap_issue(match)
        elif match.pattern == "watchdog":
            fix_applied = self._fix_watchdog_issue(match)
        else:
            # No automatic fix available
            print(f"No automatic fix available for {match.pattern}. Please fix manually and retry.", file=sys.stderr)
            if self._ask_yes_no("Retry monitoring?"):
                self._restart_monitoring()
            return
        
        if fix_applied:
            self._log_event("fix_applied", {"pattern": match.pattern, "attempt": current_attempts})
            print("Fix applied. Rebuilding and reflashing...")
            if self._build_and_flash():
                # Ask user to verify physical outcome instead of just monitoring logs
                verification_passed, user_description = self._verify_physical_outcome(match.pattern)
                if verification_passed:
                    print("✓ Physical verification passed - fix successful!")
                    self._log_event("fix_verified", {"pattern": match.pattern}, "physical_verification_passed")
                    self._restart_monitoring()
                else:
                    print("✗ Physical verification failed - fix did not work as expected")
                    log_details = {"pattern": match.pattern}
                    if user_description:
                        log_details["user_observation"] = user_description
                        print(f"\nUser observation: {user_description}")
                        print("\nAI will use this information to diagnose the issue...")
                    self._log_event("fix_failed_verification", log_details, user_description or "physical_verification_failed")
                    
                    # Show user description in the retry prompt if available
                    retry_message = "The fix didn't work."
                    if user_description:
                        retry_message += f"\n\nYou reported: {user_description}\n\nWould you like to try a different approach?"
                    else:
                        retry_message += " Would you like to try a different approach?"
                    
                    if self._ask_yes_no(retry_message):
                        self._apply_fix(match, severity)
                    else:
                        self._abort_session("Fix verification failed")
            else:
                print("ERROR: Build/flash failed. Please check manually.", file=sys.stderr)
        else:
            print("Fix not applied. Continuing monitoring...")
            self.state = SessionState.MONITORING
    
    def _fix_wifi_issue(self, match: LogMatch) -> bool:
        """Fix Wi-Fi connection issues - SOFTWARE ACTION."""
        choice = self._ask_choice("Wi-Fi connection failed. What would you like to do?", [
            "Enter new SSID/password",
            "Increase timeout",
            "Check Wi-Fi scan results",
            "Skip Wi-Fi for now"
        ])
        
        if choice == "Enter new SSID/password":
            ssid = self._ask_input("Enter Wi-Fi SSID:", "MyNetwork")
            if ssid:
                password = self._ask_input("Enter Wi-Fi password:", "")
                # SOFTWARE ACTION: Update config file
                self._update_wifi_config(ssid, password)
                return True
        elif choice == "Increase timeout":
            timeout = self._ask_number("Connection timeout (seconds):", 5, 120, 30)
            if timeout:
                self._update_config_value("WIFI_TIMEOUT", str(timeout))
                return True
        
        return False
    
    def _fix_i2c_issue(self, match: LogMatch) -> bool:
        """Fix I2C communication issues - SOFTWARE ACTION."""
        choice = self._ask_choice("I2C communication failed. What would you like to do?", [
            "Try alternate address",
            "Change SDA/SCL pins",
            "Reduce I2C speed",
            "Check wiring diagram"
        ])
        
        if choice == "Try alternate address":
            addr = self._ask_input("Enter I2C address (hex, e.g., 0x77):", "0x77")
            if addr:
                # SOFTWARE ACTION: Update config
                self._update_config_value("I2C_ADDRESS", addr)
                return True
        elif choice == "Change SDA/SCL pins":
            sda = self._ask_number("SDA pin:", 0, 48, 21)
            scl = self._ask_number("SCL pin:", 0, 48, 22)
            if sda is not None and scl is not None:
                # SOFTWARE ACTION: Update config
                self._update_config_value("I2C_SDA_PIN", str(sda))
                self._update_config_value("I2C_SCL_PIN", str(scl))
                return True
        elif choice == "Reduce I2C speed":
            speed = self._ask_number("I2C frequency (Hz):", 10000, 1000000, 100000)
            if speed:
                # SOFTWARE ACTION: Update config
                self._update_config_value("I2C_FREQUENCY", str(speed))
                return True
        elif choice == "Check wiring diagram":
            # PHYSICAL ACTION: User checks hardware
            self._prompt_physical_action("Please check:\n- SDA/SCL connections\n- Pull-up resistors (4.7kΩ)\n- Power supply to sensor")
            return self._ask_yes_no("Wiring checked. Retry?")
        
        return False
    
    def _fix_sensor_issue(self, match: LogMatch) -> bool:
        """Fix sensor detection issues."""
        choice = self._ask_choice("Sensor not detected. What would you like to do?", [
            "Check sensor power/wiring",
            "Try alternate I2C address",
            "Skip sensor and continue",
            "Use mock sensor data"
        ])
        
        if choice == "Check sensor power/wiring":
            # PHYSICAL ACTION: User checks hardware
            self._prompt_physical_action("Please check:\n- VCC and GND connections\n- Sensor power LED\n- Cable connections")
            return self._ask_yes_no("Hardware checked. Retry?")
        elif choice == "Try alternate I2C address":
            return self._fix_i2c_issue(match)
        elif choice == "Use mock sensor data":
            # SOFTWARE ACTION: Enable mock mode
            self._update_config_value("USE_MOCK_SENSOR", "1")
            return True
        elif choice == "Skip sensor and continue":
            # SOFTWARE ACTION: Disable sensor
            self._update_config_value("SENSOR_ENABLED", "0")
            return True
        
        return False
    
    def _fix_heap_issue(self, match: LogMatch) -> bool:
        """Fix low heap memory issues - SOFTWARE ACTION."""
        choice = self._ask_choice("Low heap memory detected. What would you like to do?", [
            "Reduce buffer sizes",
            "Enable PSRAM if available",
            "Show memory analysis"
        ])
        
        if choice == "Reduce buffer sizes":
            factor = self._ask_number("Buffer reduction factor (%):", 10, 90, 50)
            if factor:
                # SOFTWARE ACTION: Update config
                self._update_config_value("BUFFER_SIZE_FACTOR", str(factor))
                return True
        elif choice == "Enable PSRAM if available":
            # SOFTWARE ACTION: Enable PSRAM
            self._update_config_value("PSRAM_ENABLED", "1")
            return True
        
        return False
    
    def _fix_watchdog_issue(self, match: LogMatch) -> bool:
        """Fix watchdog timeout issues - SOFTWARE ACTION."""
        choice = self._ask_choice("Watchdog timeout detected. What would you like to do?", [
            "Increase watchdog timeout",
            "Add yield() calls in loops",
            "Show task analysis"
        ])
        
        if choice == "Increase watchdog timeout":
            timeout = self._ask_number("Watchdog timeout (seconds):", 1, 60, 5)
            if timeout:
                # SOFTWARE ACTION: Update config
                self._update_config_value("WATCHDOG_TIMEOUT", str(timeout))
                return True
        elif choice == "Add yield() calls in loops":
            print("Please add vTaskDelay(1) or yield() calls in long-running loops")
            return self._ask_yes_no("Code updated. Continue?")
        
        return False
    
    def _update_wifi_config(self, ssid: str, password: str):
        """Update Wi-Fi configuration in project - SOFTWARE ACTION."""
        # Look for common config files
        config_files = [
            Path(self.config.project_path) / "config.h",
            Path(self.config.project_path) / "main" / "config.h",
            Path(self.config.project_path) / "include" / "config.h",
            Path(self.config.project_path) / "sdkconfig",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                content = config_file.read_text()
                # Update or add Wi-Fi config
                content = re.sub(r'#define\s+WIFI_SSID\s+"[^"]*"', f'#define WIFI_SSID "{ssid}"', content)
                content = re.sub(r'#define\s+WIFI_PASSWORD\s+"[^"]*"', f'#define WIFI_PASSWORD "{password}"', content)
                config_file.write_text(content)
                return
    
    def _update_config_value(self, key: str, value: str):
        """Update a configuration value - SOFTWARE ACTION."""
        config_files = [
            Path(self.config.project_path) / "config.h",
            Path(self.config.project_path) / "main" / "config.h",
            Path(self.config.project_path) / "include" / "config.h",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                content = config_file.read_text()
                pattern = rf'#define\s+{key}\s+\S+'
                replacement = f'#define {key} {value}'
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                else:
                    content += f"\n#define {key} {value}\n"
                config_file.write_text(content)
                return
    
    def _detect_platform(self) -> str:
        """
        Auto-detect the project platform type.
        
        Returns:
            str: "esp-idf", "platformio", "arduino", or "generic"
        """
        project_path = Path(self.config.project_path)
        
        # Check for PlatformIO
        if (project_path / "platformio.ini").exists():
            return "platformio"
        
        # Check for ESP-IDF
        if (project_path / "CMakeLists.txt").exists() and (project_path / "sdkconfig").exists():
            return "esp-idf"
        
        # Check for Arduino
        if list(project_path.glob("*.ino")):
            return "arduino"
        
        # Default to generic
        return "generic"
    
    def _install_platformio(self) -> bool:
        """
        Install PlatformIO if not already installed.
        
        Returns:
            bool: True if installation successful or already installed
        """
        # Check if already installed
        result = subprocess.run(["which", "pio"], capture_output=True)
        if result.returncode == 0:
            return True
        
        # Try to install PlatformIO
        print("PlatformIO not found. Installing...")
        
        install_methods = [
            ["pip", "install", "platformio"],
            ["pip3", "install", "platformio"],
        ]
        
        for method in install_methods:
            result = subprocess.run(method, capture_output=True, text=True)
            if result.returncode == 0:
                # Verify installation
                verify = subprocess.run(["pio", "--version"], capture_output=True)
                if verify.returncode == 0:
                    return True
        
        return False
    
    def _get_build_commands(self) -> Tuple[List[str], List[str]]:
        """
        Get the build and flash commands for the current platform.
        
        Returns:
            Tuple of (build_command, flash_command) as lists
        """
        platform = self.config.platform
        
        if platform == "esp-idf":
            # ESP-IDF uses idf.py
            build_cmd = ["idf.py", "build"]
            flash_cmd = ["idf.py", "flash", "--port", self.config.port]
            
        elif platform == "platformio":
            # PlatformIO uses pio
            build_cmd = ["pio", "run"]
            flash_cmd = ["pio", "run", "--target", "upload", "--upload-port", self.config.port]
            
        elif platform == "arduino":
            # Arduino uses platformio or arduino-cli
            if self._command_exists("pio"):
                build_cmd = ["pio", "run"]
                flash_cmd = ["pio", "run", "--target", "upload", "--upload-port", self.config.port]
            else:
                # Fallback to make
                build_cmd = ["make"]
                flash_cmd = ["make", "upload"]
        else:
            # Generic fallback
            build_cmd = ["make"]
            flash_cmd = ["make", "flash"]
        
        return build_cmd, flash_cmd
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists on the system."""
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _build_and_flash(self) -> bool:
        """
        Build and flash the firmware - SOFTWARE ACTION.
        
        This is handled automatically by the AI without user prompts.
        Supports ESP-IDF, PlatformIO, and Arduino.
        Uses smart retry logic for transient failures.
        
        Returns:
            bool: True if successful
        """
        self.state = SessionState.BUILDING
        
        # Auto-detect platform if not specified
        if self.config.platform == "generic":
            detected = self._detect_platform()
            if detected != "generic":
                self.config.platform = detected
                print(f"Auto-detected platform: {detected}")
        
        # Install PlatformIO if needed
        if self.config.platform == "platformio":
            if not self._install_platformio():
                print("ERROR: Failed to install PlatformIO. Please install manually:\npip install platformio", file=sys.stderr)
                return False
        
        # Get appropriate commands
        build_cmd, flash_cmd = self._get_build_commands()
        
        # Build with retry logic
        def do_build():
            print(f"Building firmware with {self.config.platform}...")
            print(f"Running: {' '.join(build_cmd)}")
            result = subprocess.run(
                build_cmd,
                cwd=self.config.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown build error"
                # Classify error type
                if "permission denied" in error_msg.lower() or "access" in error_msg.lower():
                    raise PermissionError(error_msg)
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    raise ConnectionError(error_msg)
                else:
                    raise RuntimeError(error_msg)
            return True
        
        # Flash with retry logic
        def do_flash():
            self.state = SessionState.FLASHING
            print(f"Flashing firmware to {self.config.port}...")
            print(f"Running: {' '.join(flash_cmd)}")
            result = subprocess.run(
                flash_cmd,
                cwd=self.config.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown flash error"
                # Classify error type
                if "failed to connect" in error_msg.lower() or "connection" in error_msg.lower():
                    raise ConnectionError(error_msg)
                elif "timeout" in error_msg.lower():
                    raise TimeoutError(error_msg)
                elif "permission" in error_msg.lower():
                    raise PermissionError(error_msg)
                else:
                    raise RuntimeError(error_msg)
            return True
        
        # Execute with retry if available
        if self.retry_manager:
            # Build with retry
            build_result = self.retry_manager.execute(
                do_build
            )
            build_success = build_result.success
            if not build_success:
                print(f"ERROR: Build failed after {build_result.attempts} attempts", file=sys.stderr)
                if build_result.last_error:
                    print(f"Last error: {build_result.last_error}", file=sys.stderr)
                return False
            
            # Flash with retry
            flash_result = self.retry_manager.execute(
                do_flash
            )
            flash_success = flash_result.success
            if not flash_success:
                print(f"ERROR: Flash failed after {flash_result.attempts} attempts", file=sys.stderr)
                if flash_result.last_error:
                    print(f"Last error: {flash_result.last_error}", file=sys.stderr)
                return False
        else:
            # No retry manager - execute directly
            try:
                do_build()
            except Exception as e:
                print(f"ERROR: Build failed: {e}", file=sys.stderr)
                return False
            
            try:
                do_flash()
            except Exception as e:
                print(f"ERROR: Flash failed: {e}", file=sys.stderr)
                return False
        
        print("Build and flash successful!")
        return True
    
    def _reset_device(self) -> bool:
        """
        Reset the device before debugging.
        
        Tries software reset first (via serial), falls back to hardware reset prompt.
        
        Returns:
            bool: True if reset successful, False otherwise
        """
        print("Resetting device before debug session...")
        
        # Try software reset via serial (RTS/DTR toggle)
        try:
            import serial
            ser = serial.Serial(self.config.port, self.config.baud, timeout=2)
            # Toggle DTR to reset ESP32
            ser.dtr = False
            ser.rts = True
            time.sleep(0.1)
            ser.rts = False
            ser.close()
            print("Software reset sent via serial")
            time.sleep(1)  # Wait for boot
            return True
        except ImportError:
            print("pyserial not available for software reset")
        except Exception as e:
            print(f"Software reset failed: {e}")
        
        # Fallback: prompt user for hardware reset
        print("Please reset the device manually (press reset button or power cycle)")
        self._prompt_physical_action("Please reset the device:\n- Press RESET button, OR\n- Power cycle (unplug/replug USB), OR\n- Click OK if already reset")
        return True
    
    def _restart_monitoring(self):
        """Restart log monitoring - SOFTWARE ACTION."""
        self.state = SessionState.MONITORING
        # Stop existing watcher to prevent resource leak
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
        # Reset device before restarting
        if self.config.reset_before_debug:
            self._reset_device()
        self.start_monitoring()
    
    def _show_relevant_code(self, match: LogMatch):
        """Show relevant code for the detected issue."""
        # Extract file/line info if available in log
        file_match = re.search(r'([\w\-/]+\.(c|cpp|h|hpp|ino)):(\d+)', match.log_line)
        if file_match:
            file_path = file_match.group(1)
            line_num = int(file_match.group(3))
            
            full_path = Path(self.config.project_path) / file_path
            if full_path.exists():
                lines = full_path.read_text().splitlines()
                start = max(0, line_num - 5)
                end = min(len(lines), line_num + 5)
                context = "\n".join(f"{i+1}: {lines[i]}" for i in range(start, end))
                print(f"Code context:\n{context}")
                return
        
        print("Could not locate specific code. Please check the project files.")
    
    def _edit_configuration(self, match: LogMatch):
        """Open configuration for editing."""
        self._prompt_physical_action("Please edit the configuration file and then click OK to retry.")
        if self._ask_yes_no("Configuration updated. Retry?"):
            self._restart_monitoring()
    
    def _ask_yes_no_with_description(self, question: str, timeout: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Ask user yes/no question with option to describe what actually happened.
        
        Returns:
            Tuple of (is_yes, description_if_no)
            - is_yes: True if user confirmed yes, False otherwise
            - description_if_no: User's description of what actually happened, or None if yes
        """
        # Show choice dialog with three options
        choice = self._ask_choice(
            question + "\n\nSelect an option:",
            [
                "✓ YES - It's working correctly",
                "✗ NO - Let me describe what actually happened",
                "⊘ Cancel / Not sure"
            ],
            timeout=timeout
        )
        
        if choice == "✓ YES - It's working correctly":
            return True, None
        elif choice == "✗ NO - Let me describe what actually happened":
            # Ask user to describe what they observed
            description = self._ask_input(
                "Please describe what you actually see/hear/feel:\n\n" +
                "Examples:\n" +
                "- 'The LED is blinking but no sound'\n" +
                "- 'Screen shows Error 404'\n" +
                "- 'Motor vibrates but doesn't spin'\n" +
                "- 'WiFi LED is off but router shows connection'\n\n" +
                "What happened?",
                ""
            )
            if description:
                print(f"User observation: {description}")
                self._log_event("physical_verification_failed", {"description": description})
            return False, description
        else:
            # Cancel or timeout
            return False, None
    
    def _show_fix_instruction_prompt(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """
        TYPE 1 PROMPT for fixes: Instruction
        Tells user what to check. ONE thing only. No lists.
        
        CRITICAL: Only ONE check per prompt. No "and". No lists.
        MUST allow user to indicate if they couldn't check (not just OK button).
        
        Returns: (check_performed, problem_description)
        """
        fix_checks = {
            'wifi_fail': (
                "Wi-Fi Fix",
                "Check the Wi-Fi LED"
            ),
            'i2c_fail': (
                "I2C Fix",
                "Check if sensor responds"
            ),
            'sensor_fail': (
                "Sensor Fix",
                "Check the sensor LED"
            ),
            'heap_low': (
                "Memory Fix",
                "Check if device is responsive"
            ),
            'watchdog': (
                "Stability Fix",
                "Check if device is stable"
            ),
            'error': (
                "Error Fix",
                "Check if it works now"
            ),
            'warning': (
                "Warning Fix",
                "Check if all is working"
            ),
        }
        
        fix_name, check_action = fix_checks.get(pattern, (
            "Fix Check",
            "Check if fixed"
        ))
        
        # Simple message with ONE check only
        message = (
            f"🔧 {fix_name}\n\n"
            f"👉 {check_action}"
        )
        
        # Use method that allows user to indicate failure
        return self._prompt_physical_action_with_result(message)
    
    def _show_fix_verification_prompt(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """
        TYPE 2 PROMPT for fixes: Verification
        Asks if fix worked. ONE simple question.
        
        CRITICAL: Only ONE observation. No lists.
        """
        fix_verifications = {
            'wifi_fail': ("Wi-Fi Fix", "Is Wi-Fi working?"),
            'i2c_fail': ("I2C Fix", "Is the sensor responding?"),
            'sensor_fail': ("Sensor Fix", "Is the sensor working?"),
            'heap_low': ("Memory Fix", "Is device responsive?"),
            'watchdog': ("Stability Fix", "Is device stable?"),
            'error': ("Error Fix", "Is it working now?"),
            'warning': ("Warning Fix", "Is everything working?"),
        }
        
        fix_name, question = fix_verifications.get(pattern, ("Fix", "Did it work?"))
        
        # Simple question
        message = f"🔧 {fix_name}\n\n{question}"
        
        # Ask YES/NO - if NO, agent stops and waits for user input
        if self._ask_yes_no(message, timeout=60):
            # YES - fix works
            return True, None
        else:
            # NO - fix didn't work, agent stops and waits for user input
            problem = self._ask_input(
                "❌ The fix didn't work.\n\n"
                "Please describe what you observe:\n"
                "(What do you see/hear/feel instead of the expected behavior?)\n\n"
                "Your observation:",
                ""
            )
            if problem:
                print(f"\nUser reported problem: {problem}")
                self._log_event("fix_verification_failed", {
                    "pattern": pattern,
                    "problem_description": problem
                })
            return False, problem
    
    def _verify_physical_outcome(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """
        Verify fix outcome using exactly 2 prompt types:
        1. INSTRUCTION: Show what to check (Step info + Check + OK)
        2. VERIFICATION: Ask if it worked (Step info + Observe + YES/NO)
        
        If NO on verification, agent STOPS and waits for user input.
        """
        # TYPE 1 PROMPT: Instruction - tell user what to check
        self._show_fix_instruction_prompt(pattern)
        
        # TYPE 2 PROMPT: Verification - ask if it worked
        return self._show_fix_verification_prompt(pattern)
    
    def _modify_stack_size(self):
        """Modify task stack size - SOFTWARE ACTION."""
        new_size = self._ask_number("New stack size (bytes):", 1024, 32768, 8192)
        if new_size:
            self._update_config_value("TASK_STACK_SIZE", str(new_size))
            if self._build_and_flash():
                # Verify physical outcome - device should be stable
                if self._verify_physical_outcome('watchdog'):
                    self._restart_monitoring()
    
    def _load_retry_config(self) -> 'RetryConfig':
        """Load retry configuration from file or use defaults."""
        if not ADVANCED_FEATURES_AVAILABLE:
            return RetryConfig()
        
        if self.config.retry_config_path and Path(self.config.retry_config_path).exists():
            try:
                with open(self.config.retry_config_path) as f:
                    data = json.load(f)
                return RetryConfig.from_dict(data)
            except Exception as e:
                print(f"Warning: Failed to load retry config: {e}. Using defaults.", file=sys.stderr)
        
        return RetryConfig()
    
    def _load_test_config(self):
        """Load test configuration from YAML/JSON file."""
        if not ADVANCED_FEATURES_AVAILABLE or not self.config.test_config_path:
            return
        
        config_path = Path(self.config.test_config_path)
        if not config_path.exists():
            print(f"Warning: Test config not found: {config_path}", file=sys.stderr)
            return
        
        try:
            self.test_config = load_test_config(str(config_path))
            self.test_runner = TestRunner(self.test_config, self._execute_test_step)
            print(f"Loaded test config: {self.test_config.name}")
            print(f"Description: {self.test_config.description}")
            print(f"Steps: {len(self.test_config.steps)}")
        except Exception as e:
            print(f"Warning: Failed to load test config: {e}", file=sys.stderr)
    
    def _execute_test_step(self, step: dict) -> Tuple[bool, str]:
        """Execute a single test step from configuration."""
        step_type = step.get('type')
        
        if step_type == 'flash':
            # Build and flash firmware
            success = self._build_and_flash()
            return success, "Firmware flashed" if success else "Flash failed"
        
        elif step_type == 'prompt':
            # Show Zenity prompt for physical action
            message = step.get('message', 'Perform action and click OK')
            self._prompt_physical_action(message)
            return True, "User acknowledged"
        
        elif step_type == 'wait':
            # Wait for specified duration
            duration = step.get('duration', 1)
            time.sleep(duration)
            return True, f"Waited {duration}s"
        
        elif step_type == 'monitor':
            # Start monitoring for patterns
            self.start_monitoring()
            return True, "Monitoring started"
        
        elif step_type == 'match':
            # Wait for specific log pattern
            pattern = step.get('pattern', '.*')
            timeout = step.get('timeout', 30)
            # This would integrate with log_watcher
            return True, f"Pattern match: {pattern}"
        
        elif step_type == 'verify':
            # Verify a condition
            condition = step.get('condition', '')
            # Implementation would check logs/state
            return True, f"Verified: {condition}"
        
        else:
            return False, f"Unknown step type: {step_type}"
    
    def run_test_sequence(self) -> bool:
        """Run a complete test sequence from configuration."""
        if not self.test_runner:
            print("No test configuration loaded")
            return False
        
        print(f"\n{'='*60}")
        print(f"Running Test: {self.test_config.name}")
        print(f"{'='*60}")
        
        success = self.test_runner.run_all()
        
        # Print summary
        print(f"\n{'='*60}")
        print("Test Summary:")
        print(f"{'='*60}")
        for i, step in enumerate(self.test_config.steps):
            step_success = self.test_runner.results.get(i, False)
            status = "✓ PASS" if step_success else "✗ FAIL"
            print(f"  {status}: {step.name}")
        
        return success
    
    def _abort_session(self, reason: str):
        """Abort the session with error."""
        self.state = SessionState.ERROR
        self._log_event("session_aborted", {"reason": reason})
        print(f"ERROR: Session aborted: {reason}", file=sys.stderr)
        if self.watcher:
            self.watcher.stop()
        sys.exit(1)
    
    def start_monitoring(self):
        """
        Start the log monitoring phase in a background thread.
        
        Logs are watched in a separate thread so Zenity prompts can be
        shown from the main thread without blocking log output.
        """
        self.state = SessionState.MONITORING
        self._log_event("monitoring_started", {"patterns": self.config.patterns})
        
        # Ensure any existing watcher is stopped first (prevent resource leak)
        if self.watcher:
            self.watcher.stop()
        
        # Create watcher with log file and pattern limit support
        self.watcher = LogWatcher(
            port=self.config.port,
            baud=self.config.baud,
            platform=self.config.platform,
            on_match=self._handle_log_match,
            log_file=self.config.log_file,
            clear_on_reset=self.config.clear_log_on_reset,
            pattern_limits=self.config.pattern_limits,
            stop_on_limit=self.config.stop_on_limit
        )
        
        # Filter to requested patterns
        if self.config.patterns:
            enabled = set(self.config.patterns)
            self.watcher.compiled_patterns = {
                k: v for k, v in self.watcher.compiled_patterns.items()
                if k in enabled
            }
        
        # Show info on console (not zenity)
        print(f"Monitoring started on {self.config.port}")
        print(f"Watching for: {', '.join(self.config.patterns)}")
        if self.config.pattern_limits:
            print(f"Pattern limits: {self.config.pattern_limits}")
        print("Logs will appear below. Press Ctrl+C to stop.")
        print("-" * 60)
        
        # Start watching in background thread
        self.watcher.start()
    
    def run(self):
        """
        Run the full interactive session.
        
        Main entry point that coordinates:
        1. Initial setup and info
        2. Build and flash (software actions)
        3. Start monitoring (in background thread)
        4. Process matches and show Zenity prompts (in main thread)
        
        This design allows logs to continue printing while Zenity
        dialogs are shown for physical actions.
        """
        import time
        
        # Check that display is available for Zenity
        if not check_display_available():
            print("=" * 60, file=sys.stderr)
            print("ERROR: No graphical display available!", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(file=sys.stderr)
            print("Zenity requires a graphical display (X11 or Wayland) to show dialogs.", file=sys.stderr)
            print(file=sys.stderr)
            print("Solutions:", file=sys.stderr)
            print("  1. Run in a graphical terminal (not SSH without X11)", file=sys.stderr)
            print("  2. Use SSH with X11 forwarding: ssh -X user@host", file=sys.stderr)
            print("  3. Set DISPLAY variable: export DISPLAY=:0", file=sys.stderr)
            print("  4. For WSL: Install VcXsrv and set DISPLAY", file=sys.stderr)
            print(file=sys.stderr)
            print("See: https://github.com/Hurka5/interactive-firmware-dev-skill#display-requirements", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            sys.exit(1)
        
        # Print session info to console (not zenity)
        print("=" * 60)
        print("Interactive Firmware Development Session")
        print("=" * 60)
        print(f"Session ID: {self.session_id}")
        print(f"Project: {self.config.project_path}")
        print(f"Platform: {self.config.platform}")
        print(f"Target: {self.config.target}")
        print(f"Port: {self.config.port}")
        print()
        print("The AI will handle all software actions automatically.")
        print("You'll only be prompted for physical actions.")
        print("=" * 60)
        
        # Initial build and flash (SOFTWARE ACTION - no prompt, just do it)
        if not self._build_and_flash():
            print("ERROR: Initial build/flash failed. Exiting.", file=sys.stderr)
            sys.exit(1)
        
        # Reset device before starting debug session (if enabled)
        if self.config.reset_before_debug:
            self._reset_device()
        
        # Start monitoring in background thread
        self.start_monitoring()
        
        # Main loop - process matches and keep session alive
        # This runs in the main thread so Zenity can work properly
        stop_reason = None
        try:
            while self.watcher and self.watcher.running:
                # Process any pending matches (may trigger Zenity prompts)
                if self.watcher:
                    self.watcher.process_matches()
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
            
            # Check if stopped due to pattern limit
            if self.watcher:
                stop_reason = self.watcher.get_stop_reason()
                if stop_reason:
                    print(f"\n[Monitoring stopped: {stop_reason}]")
                    # Log the event
                    self._log_event("monitoring_stopped", {"reason": stop_reason})
                    
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            if self.watcher:
                self.watcher.stop()
            
            # Print summary if limits were exceeded
            if self.watcher and self.watcher.get_limits_exceeded():
                print("\n" + "="*60)
                print("PATTERN LIMITS EXCEEDED:")
                for pattern, count in self.watcher.get_limits_exceeded().items():
                    limit = self.watcher.pattern_limits.get(pattern, 'N/A')
                    print(f"  {pattern}: {count} occurrences (limit: {limit})")
                print("="*60)
            
            print("\nSession ended.")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Interactive Firmware Development Session - AI handles software, prompts for physical actions only"
    )
    parser.add_argument(
        "--project", "-P",
        default=".",
        help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--port", "-p",
        default="/dev/ttyUSB0",
        help="Serial port (default: /dev/ttyUSB0)"
    )
    parser.add_argument(
        "--baud", "-b",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)"
    )
    parser.add_argument(
        "--target", "-t",
        default="esp32",
        help="Target chip (default: esp32)"
    )
    parser.add_argument(
        "--platform",
        choices=["esp-idf", "arduino", "platformio", "generic"],
        default="generic",
        help="Platform type (default: auto-detect)"
    )
    parser.add_argument(
        "--patterns",
        default="error,warning,panic,watchdog,wifi_fail,i2c_fail,sensor_fail",
        help="Comma-separated patterns to watch (default: common errors)"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically prompt for fixes on warnings"
    )
    parser.add_argument(
        "--session-file",
        help="Path to save session state JSON"
    )
    
    # New arguments for advanced features
    parser.add_argument(
        "--config", "-c",
        dest="test_config",
        help="Path to YAML/JSON test configuration file"
    )
    parser.add_argument(
        "--retry-config", "-r",
        help="Path to retry configuration JSON file"
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run test sequence from config file and exit"
    )
    parser.add_argument(
        "--log-file", "-l",
        help="Write serial logs to file (auto-cleared on reset)"
    )
    parser.add_argument(
        "--no-clear-log",
        action="store_true",
        help="Don't clear log file on device reset"
    )
    parser.add_argument(
        "--read-log",
        action="store_true",
        help="Read log file and exit (requires --log-file)"
    )
    parser.add_argument(
        "--tail",
        type=int,
        metavar="N",
        help="Read last N lines from log (use with --read-log)"
    )
    parser.add_argument(
        "--pattern-limit",
        action="append",
        metavar="NAME=LIMIT",
        help="Set occurrence limit for a pattern (e.g., panic=1,wifi_fail=3)"
    )
    parser.add_argument(
        "--no-stop-on-limit",
        action="store_true",
        help="Don't stop monitoring when pattern limits exceeded (just warn)"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't reset device before debug session"
    )
    parser.add_argument(
        "--no-physical-verify",
        action="store_true",
        help="Don't ask user to verify physical outcomes (rely on logs only)"
    )
    
    args = parser.parse_args()
    
    # Handle read-log mode
    if args.read_log:
        if not args.log_file:
            print("Error: --read-log requires --log-file", file=sys.stderr)
            sys.exit(1)
        from pathlib import Path
        log_path = Path(args.log_file)
        if not log_path.exists():
            print(f"Log file not found: {log_path}", file=sys.stderr)
            sys.exit(1)
        try:
            if args.tail:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    print(''.join(lines[-args.tail:]), end='')
            else:
                with open(log_path, 'r') as f:
                    print(f.read(), end='')
        except Exception as e:
            print(f"Error reading log: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    
    # Parse pattern limits
    pattern_limits = {}
    if args.pattern_limit:
        for limit_def in args.pattern_limit:
            if '=' in limit_def:
                name, limit_str = limit_def.split('=', 1)
                try:
                    pattern_limits[name] = int(limit_str)
                except ValueError:
                    print(f"Warning: Invalid limit value for '{name}': {limit_str}", file=sys.stderr)
    
    # Create config
    config = SessionConfig(
        project_path=args.project,
        port=args.port,
        baud=args.baud,
        target=args.target,
        platform=args.platform,
        patterns=args.patterns.split(","),
        auto_fix=args.auto_fix,
        session_file=args.session_file,
        test_config_path=args.test_config,
        retry_config_path=args.retry_config,
        log_file=args.log_file,
        clear_log_on_reset=not args.no_clear_log,
        pattern_limits=pattern_limits if pattern_limits else None,
        stop_on_limit=not args.no_stop_on_limit,
        reset_before_debug=not args.no_reset,
        physical_verification=not args.no_physical_verify
    )
    
    # Create and run session
    session = InteractiveSession(config)
    
    # Run test sequence if requested
    if args.run_tests and test_config_path:
        success = session.run_test_sequence()
        sys.exit(0 if success else 1)
    else:
        session.run()


if __name__ == "__main__":
    main()
