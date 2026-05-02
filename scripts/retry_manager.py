#!/usr/bin/env python3
"""
Retry Manager for Interactive Firmware Development

Provides smart retry logic with exponential backoff for transient failures.
Distinguishes between transient errors (retryable) and permanent errors (abort).
"""

import time
import random
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any, List


class ErrorType(Enum):
    """Classification of error types."""
    TRANSIENT = "transient"      # Can be retried
    PERMANENT = "permanent"      # Should abort
    UNKNOWN = "unknown"          # Default, treated as transient


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 10.0
    backoff_strategy: str = "exponential"  # "exponential", "linear", "fixed"
    jitter: bool = True  # Add randomness to prevent thundering herd
    retry_on: List[str] = None
    abort_on: List[str] = None
    
    def __post_init__(self):
        if self.retry_on is None:
            self.retry_on = [
                "timeout",
                "no_response",
                "intermittent_read",
                "communication_timeout",
                "transient_error"
            ]
        if self.abort_on is None:
            self.abort_on = [
                "hardware_not_found",
                "panic",
                "boot_failure",
                "assert_failed",
                "guru_meditation",
                "stack_overflow"
            ]


@dataclass
class RetryResult:
    """Result of a retry operation."""
    success: bool
    attempts: int
    total_time: float
    last_error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    data: Any = None


class RetryManager:
    """
    Manages retry logic with configurable backoff strategies.
    
    Usage:
        retry_mgr = RetryManager(RetryConfig(max_attempts=3))
        
        def test_operation():
            # Your test code here
            if not detected:
                raise TimeoutError("No response")
            return detection_data
        
        result = retry_mgr.execute(test_operation)
        if result.success:
            print(f"Success after {result.attempts} attempts")
        else:
            print(f"Failed: {result.last_error}")
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify an error as transient or permanent based on config.
        
        Args:
            error: The exception that occurred
            
        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check abort patterns first (more specific)
        for pattern in self.config.abort_on:
            if pattern.lower() in error_str or pattern.lower() in error_type:
                return ErrorType.PERMANENT
        
        # Check retry patterns
        for pattern in self.config.retry_on:
            if pattern.lower() in error_str or pattern.lower() in error_type:
                return ErrorType.TRANSIENT
        
        # Default: unknown errors are transient (safer to retry)
        return ErrorType.UNKNOWN
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry based on strategy.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        if self.config.backoff_strategy == "fixed":
            delay = self.config.initial_delay
        elif self.config.backoff_strategy == "linear":
            delay = self.config.initial_delay * (attempt + 1)
        else:  # exponential (default)
            delay = self.config.initial_delay * (2 ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    def execute(
        self, 
        operation: Callable,
        *args,
        **kwargs
    ) -> RetryResult:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            RetryResult with success status and metadata
        """
        start_time = time.time()
        last_error = None
        error_type = None
        
        for attempt in range(self.config.max_attempts):
            try:
                # Attempt the operation
                result = operation(*args, **kwargs)
                
                # Success!
                total_time = time.time() - start_time
                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    total_time=total_time,
                    data=result
                )
                
            except Exception as e:
                last_error = str(e)
                error_type = self.classify_error(e)
                
                # Log the failure
                print(f"  Attempt {attempt + 1}/{self.config.max_attempts} failed: {last_error}")
                print(f"  Error type: {error_type.value}")
                
                # Check if we should abort
                if error_type == ErrorType.PERMANENT:
                    print(f"  Permanent error detected, aborting retries.")
                    break
                
                # Check if we should retry
                if attempt < self.config.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    print(f"  Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        # All attempts failed
        total_time = time.time() - start_time
        return RetryResult(
            success=False,
            attempts=self.config.max_attempts,
            total_time=total_time,
            last_error=last_error,
            error_type=error_type
        )
    
    def execute_with_callback(
        self,
        operation: Callable,
        on_retry: Optional[Callable] = None,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> RetryResult:
        """
        Execute with callbacks for each stage.
        
        Args:
            operation: Callable to execute
            on_retry: Called before each retry attempt
            on_success: Called on successful completion
            on_failure: Called on final failure
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            RetryResult
        """
        result = self.execute(operation, *args, **kwargs)
        
        if result.success and on_success:
            on_success(result)
        elif not result.success and on_failure:
            on_failure(result)
        
        return result


class TestRetryManager(RetryManager):
    """
    Specialized retry manager for hardware testing scenarios.
    
    Provides convenient methods for common test patterns.
    """
    
    def wait_for_log_pattern(
        self,
        log_watcher,
        pattern: str,
        timeout: float = 10.0,
        poll_interval: float = 0.1
    ) -> RetryResult:
        """
        Wait for a specific log pattern with retry logic.
        
        Args:
            log_watcher: LogWatcher instance
            pattern: Pattern to wait for
            timeout: Maximum time to wait
            poll_interval: How often to check
            
        Returns:
            RetryResult
        """
        start_time = time.time()
        
        def check_pattern():
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Pattern '{pattern}' not found in {timeout}s")
            
            # Check if pattern is in recent logs
            # This is a simplified version - real implementation would
            # check the log watcher's buffer
            time.sleep(poll_interval)
            return None  # Would return match data
        
        return self.execute(check_pattern)
    
    def retry_hardware_operation(
        self,
        operation: Callable,
        hardware_name: str,
        *args,
        **kwargs
    ) -> RetryResult:
        """
        Retry a hardware operation with user-friendly messages.
        
        Args:
            operation: Hardware operation to perform
            hardware_name: Name of hardware for messages
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            RetryResult
        """
        print(f"Testing {hardware_name}...")
        
        def wrapped_operation(*args, **kwargs):
            result = operation(*args, **kwargs)
            if not result:
                raise Exception(f"{hardware_name} did not respond")
            return result
        
        result = self.execute(wrapped_operation, *args, **kwargs)
        
        if result.success:
            print(f"✓ {hardware_name} test passed")
        else:
            print(f"✗ {hardware_name} test failed: {result.last_error}")
        
        return result


# Convenience functions for common retry scenarios

def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff: str = "exponential"
):
    """
    Decorator to add retry logic to any function.
    
    Usage:
        @with_retry(max_attempts=3)
        def test_nfc_card():
            # Test code here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                backoff_strategy=backoff
            )
            manager = RetryManager(config)
            return manager.execute(func, *args, **kwargs)
        return wrapper
    return decorator


def quick_retry(operation: Callable, max_attempts: int = 3) -> RetryResult:
    """
    Quick retry with default settings.
    
    Args:
        operation: Function to retry
        max_attempts: Number of attempts
        
    Returns:
        RetryResult
    """
    manager = RetryManager(RetryConfig(max_attempts=max_attempts))
    return manager.execute(operation)


if __name__ == "__main__":
    # Example usage
    print("Testing Retry Manager...")
    
    # Simulate a flaky operation using closure to avoid global state
    def create_flaky_operation():
        attempt_count = [0]  # Use list to create mutable closure
        
        def flaky_operation():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise TimeoutError("No response from device")
            return "Success!"
        
        return flaky_operation
    
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        backoff_strategy="exponential"
    )
    
    manager = RetryManager(config)
    result = manager.execute(create_flaky_operation())
    
    print(f"\nResult: {result}")
    print(f"Success: {result.success}")
    print(f"Attempts: {result.attempts}")
    print(f"Time: {result.total_time:.2f}s")
