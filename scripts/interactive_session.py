#!/usr/bin/env python3
"""
Interactive Firmware Development Session Manager
Coordinates AI coding, building, flashing, and user interaction via Zenity.
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
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum

# Import log watcher
sys.path.insert(0, str(Path(__file__).parent))
from log_watcher import LogWatcher, LogMatch, LogLevel


class SessionState(Enum):
    """Session states."""
    INITIALIZING = "initializing"
    CODING = "coding"
    BUILDING = "building"
    FLASHING = "flashing"
    MONITORING = "monitoring"
    WAITING_USER = "waiting_user"
    APPLYING_FIX = "applying_fix"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SessionEvent:
    """Session event record."""
    timestamp: str
    state: str
    event_type: str
    details: Dict
    user_action: Optional[str] = None


@dataclass
class SessionConfig:
    """Session configuration."""
    project_path: str
    port: str
    baud: int
    target: str
    platform: str
    patterns: List[str]
    auto_fix: bool
    session_file: Optional[str] = None


class InteractiveSession:
    """Manages an interactive firmware development session."""
    
    def __init__(self, config: SessionConfig):
        self.config = config
        self.state = SessionState.INITIALIZING
        self.events: List[SessionEvent] = []
        self.watcher: Optional[LogWatcher] = None
        self.session_id = f"dev-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.fix_attempts = 0
        self.max_fix_attempts = 5
        
        # Zenity script path
        self.zenity_script = Path(__file__).parent / "zenity_prompt.sh"
    
    def _log_event(self, event_type: str, details: Dict, user_action: Optional[str] = None):
        """Log a session event."""
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
        """Save session state to file."""
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
    
    def _zenity(self, dialog_type: str, *args, timeout: Optional[int] = None) -> tuple:
        """Execute a zenity dialog and return result."""
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
    
    def _show_info(self, message: str):
        """Show info dialog."""
        self._zenity("info", message)
    
    def _show_error(self, message: str):
        """Show error dialog."""
        self._zenity("error", message)
    
    def _ask_yes_no(self, question: str, timeout: Optional[int] = None) -> bool:
        """Ask yes/no question."""
        code, _ = self._zenity("question", question, timeout=timeout)
        return code == 0
    
    def _ask_choice(self, question: str, options: List[str], timeout: Optional[int] = None) -> Optional[str]:
        """Ask user to choose from list."""
        code, choice = self._zenity("list", question, *options, timeout=timeout)
        if code == 0:
            return choice
        return None
    
    def _ask_input(self, prompt: str, default: str = "") -> Optional[str]:
        """Ask for text input."""
        args = [prompt]
        if default:
            args.append(default)
        code, value = self._zenity("entry", *args)
        if code == 0:
            return value
        return None
    
    def _ask_number(self, prompt: str, min_val: int, max_val: int, default: int) -> Optional[int]:
        """Ask for numeric input via scale."""
        code, value = self._zenity("scale", prompt, str(min_val), str(max_val), str(default))
        if code == 0 and value:
            try:
                return int(value)
            except ValueError:
                pass
        return None
    
    def _handle_log_match(self, match: LogMatch):
        """Handle a detected log pattern match."""
        self.state = SessionState.WAITING_USER
        
        # Log the detection
        self._log_event("pattern_detected", match.to_dict())
        
        # Build context message
        context_msg = ""
        if match.context:
            context_msg = "\n\nRecent context:\n" + "\n".join(match.context[-3:])
        
        # Handle based on severity
        if match.level == LogLevel.FATAL:
            self._handle_fatal_error(match, context_msg)
        elif match.level == LogLevel.ERROR:
            self._handle_error(match, context_msg)
        elif match.level == LogLevel.WARNING:
            self._handle_warning(match, context_msg)
        else:
            self._handle_info_match(match, context_msg)
    
    def _handle_fatal_error(self, match: LogMatch, context_msg: str):
        """Handle fatal error (panic, crash)."""
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
            self._show_info("Please check:\n- Power supply\n- USB cable\n- Boot/reset connections\n- Peripheral wiring")
            if self._ask_yes_no("Hardware checked. Retry?"):
                self._restart_monitoring()
        elif choice == "View full log context":
            self._show_info(f"Full context:\n{chr(10).join(match.context)}")
            self._handle_fatal_error(match, "")  # Re-prompt
        else:
            self._abort_session("User aborted after fatal error")
    
    def _handle_error(self, match: LogMatch, context_msg: str):
        """Handle regular error."""
        message = f"ERROR DETECTED\n\nPattern: {match.pattern}\nLine: {match.log_line}{context_msg}\n\nWhat would you like to do?"
        
        choice = self._ask_choice(message, [
            "Fix the issue automatically",
            "Show me the code to fix",
            "Ignore and continue monitoring",
            "Edit configuration",
            "Abort session"
        ], timeout=60)
        
        if choice == "Fix the issue automatically":
            self._log_event("user_decision", {"pattern": match.pattern}, "auto_fix")
            self._apply_fix(match, "error")
        elif choice == "Show me the code to fix":
            self._log_event("user_decision", {"pattern": match.pattern}, "show_code")
            self._show_relevant_code(match)
        elif choice == "Ignore and continue monitoring":
            self._log_event("user_decision", {"pattern": match.pattern}, "ignore")
            self.state = SessionState.MONITORING
        elif choice == "Edit configuration":
            self._log_event("user_decision", {"pattern": match.pattern}, "edit_config")
            self._edit_configuration(match)
        else:
            self._abort_session("User aborted")
    
    def _handle_warning(self, match: LogMatch, context_msg: str):
        """Handle warning."""
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
        """Handle info-level match (checkpoint, etc)."""
        message = f"CHECKPOINT\n\n{match.log_line}{context_msg}\n\nContinue?"
        if not self._ask_yes_no(message, timeout=30):
            self._abort_session("User stopped at checkpoint")
    
    def _apply_fix(self, match: LogMatch, severity: str):
        """Apply a fix based on the detected pattern."""
        self.state = SessionState.APPLYING_FIX
        self.fix_attempts += 1
        
        if self.fix_attempts > self.max_fix_attempts:
            self._show_error(f"Maximum fix attempts ({self.max_fix_attempts}) reached. Please review manually.")
            self._abort_session("Too many fix attempts")
            return
        
        # Pattern-specific fixes
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
            # Generic fix - ask user what to do
            self._show_info(f"No automatic fix available for {match.pattern}. Please fix manually and retry.")
            if self._ask_yes_no("Retry monitoring?"):
                self._restart_monitoring()
            return
        
        if fix_applied:
            self._log_event("fix_applied", {"pattern": match.pattern, "attempt": self.fix_attempts})
            self._show_info("Fix applied. Rebuilding and reflashing...")
            if self._build_and_flash():
                self._restart_monitoring()
            else:
                self._show_error("Build/flash failed. Please check manually.")
        else:
            self._show_info("Fix not applied. Continuing monitoring...")
            self.state = SessionState.MONITORING
    
    def _fix_wifi_issue(self, match: LogMatch) -> bool:
        """Fix Wi-Fi connection issues."""
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
                # Update config file
                self._update_wifi_config(ssid, password)
                return True
        elif choice == "Increase timeout":
            timeout = self._ask_number("Connection timeout (seconds):", 5, 120, 30)
            if timeout:
                self._update_config_value("WIFI_TIMEOUT", str(timeout))
                return True
        
        return False
    
    def _fix_i2c_issue(self, match: LogMatch) -> bool:
        """Fix I2C communication issues."""
        choice = self._ask_choice("I2C communication failed. What would you like to do?", [
            "Try alternate address",
            "Change SDA/SCL pins",
            "Reduce I2C speed",
            "Check wiring diagram"
        ])
        
        if choice == "Try alternate address":
            addr = self._ask_input("Enter I2C address (hex, e.g., 0x77):", "0x77")
            if addr:
                self._update_config_value("I2C_ADDRESS", addr)
                return True
        elif choice == "Change SDA/SCL pins":
            sda = self._ask_number("SDA pin:", 0, 48, 21)
            scl = self._ask_number("SCL pin:", 0, 48, 22)
            if sda is not None and scl is not None:
                self._update_config_value("I2C_SDA_PIN", str(sda))
                self._update_config_value("I2C_SCL_PIN", str(scl))
                return True
        elif choice == "Reduce I2C speed":
            speed = self._ask_number("I2C frequency (Hz):", 10000, 1000000, 100000)
            if speed:
                self._update_config_value("I2C_FREQUENCY", str(speed))
                return True
        
        return False
    
    def _fix_sensor_issue(self, match: LogMatch) -> bool:
        """Fix sensor detection issues."""
        choice = self._ask_choice("Sensor not detected. What would you like to do?", [
            "Check sensor power/wiring",
            "Try alternate I2C address",
            "Skip sensor and continue",
            "Use mock sensor data"
        ])
        
        if choice == "Try alternate I2C address":
            return self._fix_i2c_issue(match)
        elif choice == "Use mock sensor data":
            self._update_config_value("USE_MOCK_SENSOR", "1")
            return True
        elif choice == "Skip sensor and continue":
            self._update_config_value("SENSOR_ENABLED", "0")
            return True
        
        return False
    
    def _fix_heap_issue(self, match: LogMatch) -> bool:
        """Fix low heap memory issues."""
        choice = self._ask_choice("Low heap memory detected. What would you like to do?", [
            "Reduce buffer sizes",
            "Increase task stack sizes",
            "Enable PSRAM if available",
            "Show memory analysis"
        ])
        
        if choice == "Reduce buffer sizes":
            factor = self._ask_number("Buffer reduction factor (%):", 10, 90, 50)
            if factor:
                self._update_config_value("BUFFER_SIZE_FACTOR", str(factor))
                return True
        elif choice == "Enable PSRAM if available":
            self._update_config_value("PSRAM_ENABLED", "1")
            return True
        
        return False
    
    def _fix_watchdog_issue(self, match: LogMatch) -> bool:
        """Fix watchdog timeout issues."""
        choice = self._ask_choice("Watchdog timeout detected. What would you like to do?", [
            "Increase watchdog timeout",
            "Add yield() calls in loops",
            "Show task analysis"
        ])
        
        if choice == "Increase watchdog timeout":
            timeout = self._ask_number("Watchdog timeout (seconds):", 1, 60, 5)
            if timeout:
                self._update_config_value("WATCHDOG_TIMEOUT", str(timeout))
                return True
        elif choice == "Add yield() calls in loops":
            self._show_info("Please add vTaskDelay(1) or yield() calls in long-running loops")
            return self._ask_yes_no("Code updated. Continue?")
        
        return False
    
    def _update_wifi_config(self, ssid: str, password: str):
        """Update Wi-Fi configuration in project."""
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
        """Update a configuration value."""
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
    
    def _build_and_flash(self) -> bool:
        """Build and flash the firmware."""
        self.state = SessionState.BUILDING
        
        # Determine build command
        if self.config.platform == "esp-idf":
            build_cmd = ["idf.py", "build"]
            flash_cmd = ["idf.py", "flash", "--port", self.config.port]
        else:
            # Arduino or other platforms
            build_cmd = ["make"]  # Adjust as needed
            flash_cmd = ["make", "upload"]  # Adjust as needed
        
        # Build
        self._show_info("Building firmware...")
        result = subprocess.run(build_cmd, cwd=self.config.project_path, capture_output=True, text=True)
        if result.returncode != 0:
            self._show_error(f"Build failed:\n{result.stderr[-500:]}")
            return False
        
        # Flash
        self.state = SessionState.FLASHING
        self._show_info("Flashing firmware...")
        result = subprocess.run(flash_cmd, cwd=self.config.project_path, capture_output=True, text=True)
        if result.returncode != 0:
            self._show_error(f"Flash failed:\n{result.stderr[-500:]}")
            return False
        
        self._show_info("Build and flash successful!")
        return True
    
    def _restart_monitoring(self):
        """Restart log monitoring."""
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
                self._show_info(f"Code context:\n{context}")
                return
        
        self._show_info("Could not locate specific code. Please check the project files.")
    
    def _edit_configuration(self, match: LogMatch):
        """Open configuration for editing."""
        self._show_info("Please edit the configuration file and then click OK to retry.")
        # Could open editor here if desired
        if self._ask_yes_no("Configuration updated. Retry?"):
            self._restart_monitoring()
    
    def _modify_stack_size(self):
        """Modify task stack size."""
        new_size = self._ask_number("New stack size (bytes):", 1024, 32768, 8192)
        if new_size:
            self._update_config_value("TASK_STACK_SIZE", str(new_size))
            if self._build_and_flash():
                self._restart_monitoring()
    
    def _abort_session(self, reason: str):
        """Abort the session."""
        self.state = SessionState.ERROR
        self._log_event("session_aborted", {"reason": reason})
        self._show_error(f"Session aborted: {reason}")
        if self.watcher:
            self.watcher.stop()
        sys.exit(1)
    
    def start_monitoring(self):
        """Start the log monitoring phase."""
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
        
        # Show info
        self._show_info(f"Monitoring started on {self.config.port}\nWatching for: {', '.join(self.config.patterns)}")
        
        # Start watching (blocks until interrupted)
        self.watcher.start()
    
    def run(self):
        """Run the full interactive session."""
        self._show_info(
            f"Interactive Firmware Development Session\n"
            f"Session ID: {self.session_id}\n\n"
            f"Project: {self.config.project_path}\n"
            f"Target: {self.config.target}\n"
            f"Port: {self.config.port}\n\n"
            f"The AI will monitor logs and prompt you when issues are detected."
        )
        
        # Initial build and flash
        if self._ask_yes_no("Build and flash firmware now?"):
            if not self._build_and_flash():
                if not self._ask_yes_no("Build/flash failed. Continue with monitoring only?"):
                    return
        
        # Start monitoring
        self.start_monitoring()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive Firmware Development Session"
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
        choices=["esp-idf", "arduino", "generic"],
        default="esp-idf",
        help="Platform type (default: esp-idf)"
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
