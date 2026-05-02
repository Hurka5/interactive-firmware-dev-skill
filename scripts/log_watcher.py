#!/usr/bin/env python3
"""
Log Watcher for Interactive Firmware Development
Monitors serial logs and triggers callbacks when patterns are detected.
Runs in a separate thread so Zenity prompts can work concurrently.
"""

import subprocess
import re
import sys
import json
import time
import signal
import argparse
import threading
import queue
from pathlib import Path
from typing import List, Dict, Callable, Optional, Pattern
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class LogMatch:
    """Represents a detected log pattern match."""
    timestamp: str
    level: LogLevel
    pattern: str
    log_line: str
    context: List[str]  # Previous lines for context
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "pattern": self.pattern,
            "log_line": self.log_line,
            "context": self.context
        }


class LogWatcher:
    """Watches firmware logs and detects patterns in a background thread."""

    # Default patterns for ESP-IDF
    ESP_IDF_PATTERNS = {
        'error': (r'E \(\d+\)', LogLevel.ERROR),
        'warning': (r'W \(\d+\)', LogLevel.WARNING),
        'info': (r'I \(\d+\)', LogLevel.INFO),
        'debug': (r'D \(\d+\)', LogLevel.DEBUG),
        'verbose': (r'V \(\d+\)', LogLevel.DEBUG),
        'panic': (r'Guru Meditation|abort\(\)|Stack overflow|Core \d+ panic', LogLevel.FATAL),
        'watchdog': (r'Task watchdog|WDT timeout|Watchdog triggered', LogLevel.ERROR),
        'wifi_fail': (r'wifi:.*failed|WIFI:.*FAIL|connection failed', LogLevel.ERROR),
        'ble_fail': (r'ble:.*error|BT:.*fail', LogLevel.ERROR),
        'i2c_fail': (r'I2C.*NACK|I2C.*timeout|i2c:.*fail', LogLevel.ERROR),
        'spi_fail': (r'SPI.*error|spi:.*fail', LogLevel.ERROR),
        'sensor_fail': (r'sensor.*not found|device.*not detected', LogLevel.ERROR),
        'heap_low': (r'heap.*low|memory.*low|out of memory', LogLevel.WARNING),
        'ota_fail': (r'ota:.*fail|OTA.*error', LogLevel.ERROR),
        'assert_fail': (r'assert.*failed|ASSERT.*FAIL', LogLevel.FATAL),
    }

    # Default patterns for Arduino
    ARDUINO_PATTERNS = {
        'error': (r'error|Error|ERROR', LogLevel.ERROR),
        'warning': (r'warning|Warning|WARNING', LogLevel.WARNING),
        'panic': (r'panic|Exception|Reset', LogLevel.FATAL),
        'wifi_fail': (r'WiFi.*fail|connection.*fail', LogLevel.ERROR),
        'sensor_fail': (r'not found|failed.*init|init.*fail', LogLevel.ERROR),
    }

    # Reset detection patterns - when these are seen, clear the log file
    RESET_PATTERNS = [
        r'rst:.*\(RESET|restart|reboot|boot:|ESP-ROM|loading:|Starting|Initializing',
        r'cpu reset|system reset|watchdog reset|power-on reset',
        r'\[boot\]|Booting|Boot mode|ets Jun|ESP32|ESP8266',
    ]

    # Default pattern limits - how many times each pattern should reasonably occur
    DEFAULT_PATTERN_LIMITS = {
        'panic': 1,  # Should only happen once (then device crashes)
        'watchdog': 2,  # 1-2 times max, more indicates loop
        'assert_fail': 1,  # Should only happen once
        'wifi_fail': 3,  # May retry a few times
        'ble_fail': 3,
        'i2c_fail': 2,  # Should detect and stop
        'spi_fail': 2,
        'sensor_fail': 1,  # Init should only happen once
        'ota_fail': 2,
    }

    def __init__(
        self,
        port: str,
        baud: int = 115200,
        platform: str = "esp-idf",
        custom_patterns: Optional[Dict[str, str]] = None,
        context_lines: int = 5,
        on_match: Optional[Callable[[LogMatch], None]] = None,
        log_file: Optional[str] = None,
        clear_on_reset: bool = True,
        pattern_limits: Optional[Dict[str, int]] = None,
        on_limit_exceeded: Optional[Callable[[str, int], None]] = None,
        stop_on_limit: bool = True
    ):
        self.port = port
        self.baud = baud
        self.platform = platform
        self.context_lines = context_lines
        self.on_match = on_match
        self.running = False
        self.process: Optional[subprocess.Popen] = None
        self.watch_thread: Optional[threading.Thread] = None
        self.match_queue: queue.Queue = queue.Queue()

        # Log file settings
        self.log_file_path: Optional[Path] = Path(log_file) if log_file else None
        self.clear_on_reset = clear_on_reset
        self.log_file_handle: Optional[object] = None
        self.reset_compiled_patterns: List[Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.RESET_PATTERNS
        ]

        # Pattern limits and monitoring control
        self.pattern_limits: Dict[str, int] = pattern_limits or self.DEFAULT_PATTERN_LIMITS.copy()
        self.on_limit_exceeded = on_limit_exceeded
        self.stop_on_limit = stop_on_limit
        self.limits_exceeded: Dict[str, int] = {}  # Track which limits were exceeded
        self._stop_reason: Optional[str] = None

        # Build pattern list
        self.patterns: Dict[str, tuple] = {}
        if platform == "esp-idf":
            self.patterns.update(self.ESP_IDF_PATTERNS)
        elif platform == "arduino":
            self.patterns.update(self.ARDUINO_PATTERNS)

        # Add custom patterns
        if custom_patterns:
            for name, pattern in custom_patterns.items():
                self.patterns[name] = (pattern, LogLevel.WARNING)

        # Compile regexes
        self.compiled_patterns: Dict[str, tuple] = {}
        for name, (pattern, level) in self.patterns.items():
            try:
                self.compiled_patterns[name] = (re.compile(pattern, re.IGNORECASE), level)
            except re.error as e:
                print(f"Warning: Invalid pattern '{name}': {e}", file=sys.stderr)

        # Context buffer
        self.context_buffer: List[str] = []
        self.buffer_lock = threading.Lock()

        # Statistics - protected by lock for thread safety
        self.match_count: Dict[str, int] = {name: 0 for name in self.patterns}
        self.match_count_lock = threading.Lock()
        self.start_time: Optional[datetime] = None
        self.reset_count: int = 0
    
    def _get_monitor_command(self) -> List[str]:
        """Get the appropriate monitor command for the platform."""
        if self.platform == "esp-idf":
            return ["idf.py", "monitor", "--port", self.port]
        elif self.platform == "arduino":
            # Try different serial monitor tools
            if self._command_exists("screen"):
                return ["screen", self.port, str(self.baud)]
            elif self._command_exists("minicom"):
                return ["minicom", "-D", self.port, "-b", str(self.baud)]
            elif self._command_exists("picocom"):
                return ["picocom", self.port, "-b", str(self.baud)]
            else:
                # Fallback to Python serial
                return [sys.executable, "-m", "serial.tools.miniterm", self.port, str(self.baud)]
        else:
            return ["cat", self.port]  # Fallback
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists."""
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _check_patterns(self, line: str) -> Optional[LogMatch]:
        """Check if line matches any pattern."""
        for name, (regex, level) in self.compiled_patterns.items():
            if regex.search(line):
                # Thread-safe increment of match count
                with self.match_count_lock:
                    self.match_count[name] += 1
                    current_count = self.match_count[name]

                # Check if pattern limits exceeded
                if not self._check_pattern_limits(name, line, current_count):
                    # Limit exceeded - signal to stop monitoring
                    self.running = False
                    return None

                with self.buffer_lock:
                    return LogMatch(
                        timestamp=datetime.now().isoformat(),
                        level=level,
                        pattern=name,
                        log_line=line.rstrip(),
                        context=self.context_buffer.copy()
                    )
        return None
    
    def _update_context(self, line: str):
        """Update the context buffer."""
        with self.buffer_lock:
            self.context_buffer.append(line.rstrip())
            if len(self.context_buffer) > self.context_lines:
                self.context_buffer.pop(0)

    def _check_pattern_limits(self, pattern_name: str, line_content: str, current_count: int) -> bool:
        """
        Check if pattern has exceeded its occurrence limit.

        Args:
            pattern_name: Name of the pattern that matched
            line_content: The log line content
            current_count: Current occurrence count (thread-safe)

        Returns:
            True if monitoring should continue, False if limit exceeded
        """
        # Check absolute occurrence limit
        limit = self.pattern_limits.get(pattern_name)
        if limit and current_count > limit:
            if pattern_name not in self.limits_exceeded:
                self.limits_exceeded[pattern_name] = current_count
                message = f"Pattern '{pattern_name}' exceeded limit ({current_count} > {limit})"
                print(f"\n[MONITOR STOP] {message}")

                if self.on_limit_exceeded:
                    self.on_limit_exceeded(pattern_name, current_count)

                if self.stop_on_limit:
                    self._stop_reason = message
                    return False

        return True

    def _is_reset_line(self, line: str) -> bool:
        """Check if a line indicates a device reset."""
        for pattern in self.reset_compiled_patterns:
            if pattern.search(line):
                return True
        return False

    def _open_log_file(self):
        """Open the log file for writing."""
        if self.log_file_path:
            try:
                # Ensure directory exists
                self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
                # Open in append mode initially
                self.log_file_handle = open(self.log_file_path, 'a', buffering=1)
                # Write session start marker
                self.log_file_handle.write(f"\n{'='*60}\n")
                self.log_file_handle.write(f"Session started: {datetime.now().isoformat()}\n")
                self.log_file_handle.write(f"Port: {self.port}, Baud: {self.baud}\n")
                self.log_file_handle.write(f"{'='*60}\n\n")
                self.log_file_handle.flush()
            except Exception as e:
                print(f"Warning: Failed to open log file: {e}", file=sys.stderr)
                self.log_file_handle = None

    def _clear_log_file(self):
        """Clear/truncate the log file on reset."""
        if self.log_file_path and self.log_file_handle:
            try:
                self.log_file_handle.close()
                # Reopen in write mode to truncate
                self.log_file_handle = open(self.log_file_path, 'w', buffering=1)
                self.reset_count += 1
                # Write reset marker
                self.log_file_handle.write(f"{'='*60}\n")
                self.log_file_handle.write(f"RESET #{self.reset_count} detected: {datetime.now().isoformat()}\n")
                self.log_file_handle.write(f"Previous logs cleared.\n")
                self.log_file_handle.write(f"{'='*60}\n\n")
                self.log_file_handle.flush()
                print(f"[Log file cleared - Reset #{self.reset_count} detected]")
            except Exception as e:
                print(f"Warning: Failed to clear log file: {e}", file=sys.stderr)

    def _write_to_log_file(self, line: str):
        """Write a line to the log file."""
        if self.log_file_handle:
            try:
                self.log_file_handle.write(line)
                self.log_file_handle.flush()
            except Exception as e:
                print(f"Warning: Failed to write to log file: {e}", file=sys.stderr)

    def read_log_file(self, lines: Optional[int] = None) -> str:
        """
        Read the contents of the log file.

        Args:
            lines: If specified, read only the last N lines. If None, read all.

        Returns:
            The log file contents as a string.
        """
        if not self.log_file_path or not self.log_file_path.exists():
            return ""

        try:
            if lines:
                # Read last N lines
                with open(self.log_file_path, 'r') as f:
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
            else:
                # Read all
                with open(self.log_file_path, 'r') as f:
                    return f.read()
        except Exception as e:
            print(f"Warning: Failed to read log file: {e}", file=sys.stderr)
            return ""

    def get_log_file_path(self) -> Optional[str]:
        """Get the path to the log file."""
        return str(self.log_file_path) if self.log_file_path else None
    
    def _watch_loop(self):
        """Background thread that watches logs."""
        cmd = self._get_monitor_command()
        print(f"Starting log watcher: {' '.join(cmd)}")
        print(f"Monitoring patterns: {', '.join(self.patterns.keys())}")
        if self.log_file_path:
            print(f"Logging to: {self.log_file_path}")
            print(f"Clear on reset: {self.clear_on_reset}")
        print("-" * 60)

        # Open log file if specified
        self._open_log_file()

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            for line in self.process.stdout:
                if not self.running:
                    break

                # Print the line immediately
                print(line, end='', flush=True)

                # Write to log file
                self._write_to_log_file(line)

                # Check for reset and clear log if needed
                if self.clear_on_reset and self._is_reset_line(line):
                    self._clear_log_file()

                # Update context buffer
                self._update_context(line)

                # Check for pattern matches
                match = self._check_patterns(line)
                if match and self.on_match:
                    # Put match in queue for main thread to handle
                    self.match_queue.put(match)

                # Check if we should stop (limit exceeded)
                if not self.running and self._stop_reason:
                    print(f"\n[Monitoring stopped: {self._stop_reason}]")
                    break

        except Exception as e:
            print(f"\nLog watcher error: {e}", file=sys.stderr)
        finally:
            # Close log file
            if self.log_file_handle:
                try:
                    self.log_file_handle.close()
                except:
                    pass
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
    
    def start(self):
        """Start watching logs in a background thread."""
        self.running = True
        self.start_time = datetime.now()
        
        # Start the watcher thread
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
    
    def process_matches(self):
        """
        Process any pending matches in the queue.
        Call this periodically from the main thread to handle matches
        (including showing Zenity dialogs).
        """
        try:
            while True:
                match = self.match_queue.get_nowait()
                if self.on_match:
                    self.on_match(match)
        except queue.Empty:
            pass
    
    def stop(self):
        """Stop watching logs."""
        self.running = False
        # Close log file
        if self.log_file_handle:
            try:
                self.log_file_handle.close()
                self.log_file_handle = None
            except:
                pass
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=5)

    def get_stop_reason(self) -> Optional[str]:
        """Get the reason why monitoring stopped (if limit was exceeded)."""
        return self._stop_reason

    def get_limits_exceeded(self) -> Dict[str, int]:
        """Get patterns that exceeded their limits and their counts."""
        return self.limits_exceeded.copy()

    def set_pattern_limit(self, pattern_name: str, limit: int):
        """Set or update the occurrence limit for a pattern."""
        self.pattern_limits[pattern_name] = limit

    def get_stats(self) -> Dict:
        """Get watching statistics."""
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()

        return {
            "duration_seconds": duration,
            "total_matches": sum(self.match_count.values()),
            "matches_by_pattern": self.match_count,
            "patterns_monitored": list(self.patterns.keys()),
            "resets_detected": self.reset_count,
            "log_file": str(self.log_file_path) if self.log_file_path else None,
            "limits_exceeded": self.limits_exceeded,
            "stop_reason": self._stop_reason
        }


def default_match_handler(match: LogMatch):
    """Default handler that prints match info."""
    print(f"\n{'='*60}")
    print(f"PATTERN DETECTED: {match.pattern} ({match.level.value.upper()})")
    print(f"Time: {match.timestamp}")
    print(f"Line: {match.log_line}")
    if match.context:
        print(f"Context:")
        for ctx_line in match.context:
            print(f"  {ctx_line}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Watch firmware logs and detect patterns"
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
        "--platform",
        choices=["esp-idf", "arduino", "generic"],
        default="esp-idf",
        help="Platform type (default: esp-idf)"
    )
    parser.add_argument(
        "--patterns",
        help="Comma-separated list of pattern names to watch (default: all)"
    )
    parser.add_argument(
        "--custom-pattern",
        action="append",
        metavar="NAME=REGEX",
        help="Add custom pattern (can be used multiple times)"
    )
    parser.add_argument(
        "--context",
        type=int,
        default=5,
        help="Number of context lines to keep (default: 5)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output matches as JSON"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print statistics on exit"
    )
    parser.add_argument(
        "--log-file", "-l",
        help="Write logs to file (cleared on each reset)"
    )
    parser.add_argument(
        "--no-clear-on-reset",
        action="store_true",
        help="Don't clear log file on reset (append mode)"
    )
    parser.add_argument(
        "--read-log",
        action="store_true",
        help="Read log file contents and exit"
    )
    parser.add_argument(
        "--tail",
        type=int,
        metavar="N",
        help="Read last N lines from log file (use with --read-log)"
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
        help="Don't stop monitoring when limits are exceeded (just warn)"
    )

    args = parser.parse_args()

    # Handle read-log mode
    if args.read_log:
        if not args.log_file:
            print("Error: --read-log requires --log-file", file=sys.stderr)
            sys.exit(1)
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
            print(f"Error reading log file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    
    # Parse custom patterns
    custom_patterns = {}
    if args.custom_pattern:
        for pattern_def in args.custom_pattern:
            if '=' in pattern_def:
                name, regex = pattern_def.split('=', 1)
                custom_patterns[name] = regex

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

    # Create watcher
    watcher = LogWatcher(
        port=args.port,
        baud=args.baud,
        platform=args.platform,
        custom_patterns=custom_patterns if custom_patterns else None,
        context_lines=args.context,
        on_match=default_match_handler,
        log_file=args.log_file,
        clear_on_reset=not args.no_clear_on_reset,
        pattern_limits=pattern_limits if pattern_limits else None,
        stop_on_limit=not args.no_stop_on_limit
    )
    
    # Filter patterns if specified
    if args.patterns:
        enabled = set(args.patterns.split(','))
        watcher.compiled_patterns = {
            k: v for k, v in watcher.compiled_patterns.items()
            if k in enabled
        }
    
    # Handle signals
    def signal_handler(sig, frame):
        print("\nReceived signal, stopping...")
        watcher.stop()
        if args.stats:
            print("\nStatistics:")
            print(json.dumps(watcher.get_stats(), indent=2))
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start watching in background thread
    watcher.start()

    # Main loop - process matches and keep thread alive
    stop_reason = None
    try:
        while watcher.running:
            watcher.process_matches()
            time.sleep(0.1)  # Small delay to prevent CPU spinning

        # Check if stopped due to limit
        stop_reason = watcher.get_stop_reason()

    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()

    # Print stats on normal exit
    if args.stats or stop_reason:
        print("\n" + "="*60)
        if stop_reason:
            print(f"STOPPED: {stop_reason}")
        print("Statistics:")
        print(json.dumps(watcher.get_stats(), indent=2))
        print("="*60)

    # Exit with error code if limits were exceeded
    if watcher.get_limits_exceeded():
        sys.exit(1)


if __name__ == "__main__":
    main()
