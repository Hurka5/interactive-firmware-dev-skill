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
        self.fix_attempts = 0
        self.max_fix_attempts = 5
        
        # Path to zenity helper script
        self.zenity_script = Path(__file__).parent / "zenity_prompt.sh"
    
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
    
    def _prompt_physical_action(self, message: str):
        """
        Prompt user for a PHYSICAL action using Zenity.
        This is the ONLY case where we use Zenity dialogs.
        """
        self._zenity("info", message)
    
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
    
    def _handle_info_match(self, match: LogMatch, context_msg: str):
        """
        Handle info-level matches (checkpoints).
        
        These often require physical user action like:
        - "Tap card now"
        - "Press button"
        - "Remove card"
        """
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
        self.fix_attempts += 1
        
        if self.fix_attempts > self.max_fix_attempts:
            print(f"ERROR: Maximum fix attempts ({self.max_fix_attempts}) reached. Please review manually.", file=sys.stderr)
            self._abort_session("Too many fix attempts")
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
            self._log_event("fix_applied", {"pattern": match.pattern, "attempt": self.fix_attempts})
            print("Fix applied. Rebuilding and reflashing...")
            if self._build_and_flash():
                self._restart_monitoring()
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
        
        # Build
        print(f"Building firmware with {self.config.platform}...")
        print(f"Running: {' '.join(build_cmd)}")
        result = subprocess.run(
            build_cmd, 
            cwd=self.config.project_path, 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print(f"ERROR: Build failed:\n{result.stderr[-500:]}", file=sys.stderr)
            return False
        
        # Flash
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
            print(f"ERROR: Flash failed:\n{result.stderr[-500:]}", file=sys.stderr)
            return False
        
        print("Build and flash successful!")
        return True
    
    def _restart_monitoring(self):
        """Restart log monitoring - SOFTWARE ACTION."""
        self.state = SessionState.MONITORING
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
    
    def _modify_stack_size(self):
        """Modify task stack size - SOFTWARE ACTION."""
        new_size = self._ask_number("New stack size (bytes):", 1024, 32768, 8192)
        if new_size:
            self._update_config_value("TASK_STACK_SIZE", str(new_size))
            if self._build_and_flash():
                self._restart_monitoring()
    
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
        
        # Create watcher
        self.watcher = LogWatcher(
            port=self.config.port,
            baud=self.config.baud,
            platform=self.config.platform,
            on_match=self._handle_log_match
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
        
        # Start monitoring in background thread
        self.start_monitoring()
        
        # Main loop - process matches and keep session alive
        # This runs in the main thread so Zenity can work properly
        try:
            while self.watcher and self.watcher.running:
                # Process any pending matches (may trigger Zenity prompts)
                if self.watcher:
                    self.watcher.process_matches()
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            if self.watcher:
                self.watcher.stop()
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
    
    args = parser.parse_args()
    
    # Create config
    config = SessionConfig(
        project_path=args.project,
        port=args.port,
        baud=args.baud,
        target=args.target,
        platform=args.platform,
        patterns=args.patterns.split(","),
        auto_fix=args.auto_fix,
        session_file=args.session_file
    )
    
    # Create and run session
    session = InteractiveSession(config)
    session.run()


if __name__ == "__main__":
    main()
