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
    
    def __init__(
        self,
        port: str,
        baud: int = 115200,
        platform: str = "esp-idf",
        custom_patterns: Optional[Dict[str, str]] = None,
        context_lines: int = 5,
        on_match: Optional[Callable[[LogMatch], None]] = None
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
        
        # Statistics
        self.match_count: Dict[str, int] = {name: 0 for name in self.patterns}
        self.start_time: Optional[datetime] = None
    
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
                self.match_count[name] += 1
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
    
    def _watch_loop(self):
        """Background thread that watches logs."""
        cmd = self._get_monitor_command()
        print(f"Starting log watcher: {' '.join(cmd)}")
        print(f"Monitoring patterns: {', '.join(self.patterns.keys())}")
        print("-" * 60)
        
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
                
                # Update context buffer
                self._update_context(line)
                
                # Check for pattern matches
                match = self._check_patterns(line)
                if match and self.on_match:
                    # Put match in queue for main thread to handle
                    self.match_queue.put(match)
                    
        except Exception as e:
            print(f"\nLog watcher error: {e}", file=sys.stderr)
        finally:
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
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=5)
    
    def get_stats(self) -> Dict:
        """Get watching statistics."""
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "duration_seconds": duration,
            "total_matches": sum(self.match_count.values()),
            "matches_by_pattern": self.match_count,
            "patterns_monitored": list(self.patterns.keys())
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
    
    args = parser.parse_args()
    
    # Parse custom patterns
    custom_patterns = {}
    if args.custom_pattern:
        for pattern_def in args.custom_pattern:
            if '=' in pattern_def:
                name, regex = pattern_def.split('=', 1)
                custom_patterns[name] = regex
    
    # Create watcher
    watcher = LogWatcher(
        port=args.port,
        baud=args.baud,
        platform=args.platform,
        custom_patterns=custom_patterns if custom_patterns else None,
        context_lines=args.context,
        on_match=default_match_handler
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
    try:
        while watcher.running:
            watcher.process_matches()
            time.sleep(0.1)  # Small delay to prevent CPU spinning
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
    
    # Print stats on normal exit
    if args.stats:
        print("\nStatistics:")
        print(json.dumps(watcher.get_stats(), indent=2))


if __name__ == "__main__":
    main()
