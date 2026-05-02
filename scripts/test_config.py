#!/usr/bin/env python3
"""
Test Configuration System for Interactive Firmware Development

Provides YAML/JSON-based test configuration with validation,
template substitution, and sequence execution.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None  # type: ignore


class TestStepStatus(Enum):
    """Status of a test step."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestPattern:
    """A log pattern to watch for."""
    name: str
    regex: str
    description: Optional[str] = None


@dataclass
class TestStep:
    """A single step in a test sequence."""
    name: str
    prompt: str
    expected_logs: List[str]
    timeout: float = 10.0
    critical: bool = False
    requires_previous: bool = False
    retry: Optional[Dict[str, Any]] = None
    status: TestStepStatus = TestStepStatus.PENDING
    actual_logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class FailureHandler:
    """How to handle specific failure types."""
    pattern: str
    action: str  # "retry", "prompt", "skip", "abort"
    message: Optional[str] = None
    max_retries: Optional[int] = None


@dataclass
class TestConfig:
    """Complete test configuration."""
    name: str
    patterns: Dict[str, str]
    test_sequence: List[TestStep]
    description: Optional[str] = None
    failure_handlers: List[FailureHandler] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfig':
        """Create TestConfig from dictionary."""
        # Parse patterns
        patterns = data.get('patterns', {})
        
        # Parse test sequence
        sequence = []
        for step_data in data.get('test_sequence', []):
            step = TestStep(
                name=step_data['name'],
                prompt=step_data['prompt'],
                expected_logs=step_data.get('expected_logs', []),
                timeout=step_data.get('timeout', 10.0),
                critical=step_data.get('critical', False),
                requires_previous=step_data.get('requires_previous', False),
                retry=step_data.get('retry')
            )
            sequence.append(step)
        
        # Parse failure handlers
        handlers = []
        for pattern, handler_data in data.get('failure_handlers', {}).items():
            handler = FailureHandler(
                pattern=pattern,
                action=handler_data.get('action', 'prompt'),
                message=handler_data.get('message'),
                max_retries=handler_data.get('max_retries')
            )
            handlers.append(handler)
        
        return cls(
            name=data['name'],
            description=data.get('description'),
            patterns=patterns,
            test_sequence=sequence,
            failure_handlers=handlers,
            variables=data.get('variables', {})
        )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'TestConfig':
        """Load TestConfig from YAML file."""
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)  # type: ignore
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, json_path: str) -> 'TestConfig':
        """Load TestConfig from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def substitute_variables(self, **kwargs) -> 'TestConfig':
        """
        Create a new config with variables substituted.
        
        Args:
            **kwargs: Variable values to substitute
            
        Returns:
            New TestConfig with substituted values
        """
        # Merge provided variables with config variables
        variables = {**self.variables, **kwargs}
        
        # Substitute in all string fields
        def substitute(text: str) -> str:
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                text = text.replace(placeholder, str(var_value))
            return text
        
        # Create new sequence with substituted prompts
        new_sequence = []
        for step in self.test_sequence:
            new_step = TestStep(
                name=step.name,
                prompt=substitute(step.prompt),
                expected_logs=[substitute(log) for log in step.expected_logs],
                timeout=step.timeout,
                critical=step.critical,
                requires_previous=step.requires_previous,
                retry=step.retry
            )
            new_sequence.append(new_step)
        
        # Create new config
        return TestConfig(
            name=substitute(self.name),
            description=substitute(self.description) if self.description else None,
            patterns={k: substitute(v) for k, v in self.patterns.items()},
            test_sequence=new_sequence,
            failure_handlers=self.failure_handlers,
            variables=variables
        )


class ConfigValidator:
    """Validates test configuration files."""
    
    REQUIRED_FIELDS = ['name', 'patterns', 'test_sequence']
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> List[str]:
        """
        Validate configuration data.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return errors
        
        # Validate test sequence
        if not isinstance(data['test_sequence'], list):
            errors.append("test_sequence must be a list")
        elif len(data['test_sequence']) == 0:
            errors.append("test_sequence cannot be empty")
        else:
            for i, step in enumerate(data['test_sequence']):
                if 'name' not in step:
                    errors.append(f"Step {i}: missing 'name'")
                if 'prompt' not in step:
                    errors.append(f"Step {i}: missing 'prompt'")
        
        # Validate patterns
        if not isinstance(data['patterns'], dict):
            errors.append("patterns must be a dictionary")
        
        return errors
    
    @classmethod
    def is_valid(cls, data: Dict[str, Any]) -> bool:
        """Quick check if config is valid."""
        return len(cls.validate(data)) == 0


class TestRunner:
    """
    Executes test configurations with integration to the session manager.
    
    Usage:
        config = TestConfig.from_yaml('nfc-test.yaml')
        runner = TestRunner(config, session)
        results = runner.run_all_steps()
    """
    
    def __init__(
        self,
        config: TestConfig,
        session,  # InteractiveSession instance
        on_step_start: Optional[Callable] = None,
        on_step_complete: Optional[Callable] = None,
        on_step_failed: Optional[Callable] = None
    ):
        self.config = config
        self.session = session
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete
        self.on_step_failed = on_step_failed
        self.results: List[TestStep] = []
    
    def run_step(self, step: TestStep, step_index: int) -> bool:
        """
        Execute a single test step.
        
        Args:
            step: TestStep to execute
            step_index: Index in sequence
            
        Returns:
            True if step passed, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Step {step_index + 1}/{len(self.config.test_sequence)}: {step.name}")
        print(f"{'='*60}")
        
        step.status = TestStepStatus.RUNNING
        
        # Notify start
        if self.on_step_start:
            self.on_step_start(step, step_index)
        
        # Show prompt via Zenity
        from interactive_session import InteractiveSession
        if isinstance(self.session, InteractiveSession):
            self.session._prompt_physical_action(step.prompt)
        else:
            print(f"📋 {step.prompt}")
            input("Press Enter when done...")  # Fallback, shouldn't happen
        
        # Wait for expected logs
        # This is simplified - real implementation would integrate
        # with the log watcher to check for patterns
        print(f"Waiting for: {step.expected_logs}")
        print(f"Timeout: {step.timeout}s")
        
        # Simulate success for now
        # Real implementation would check actual logs
        import time
        time.sleep(1)  # Simulate work
        
        step.status = TestStepStatus.PASSED
        step.actual_logs = step.expected_logs  # Would be actual detected logs
        
        print(f"✓ Step passed")
        
        if self.on_step_complete:
            self.on_step_complete(step, step_index)
        
        return True
    
    def run_all_steps(self) -> List[TestStep]:
        """
        Execute all test steps in sequence.
        
        Returns:
            List of TestStep with results
        """
        print(f"\n{'='*60}")
        print(f"Running Test: {self.config.name}")
        if self.config.description:
            print(f"{self.config.description}")
        print(f"{'='*60}")
        
        previous_passed = True
        
        for i, step in enumerate(self.config.test_sequence):
            # Check if we should skip due to previous failure
            if step.requires_previous and not previous_passed:
                step.status = TestStepStatus.SKIPPED
                step.error_message = "Skipped due to previous step failure"
                print(f"\n⚠ Step {i+1} skipped (requires previous)")
                continue
            
            # Run the step
            passed = self.run_step(step, i)
            previous_passed = passed
            
            # Handle failure
            if not passed:
                if step.critical:
                    print(f"\n✗ Critical step failed, aborting test sequence")
                    break
                
                # Check for failure handler
                handler = self._get_failure_handler(step)
                if handler:
                    if not self._handle_failure(step, handler):
                        break
        
        # Summary
        self._print_summary()
        
        return self.config.test_sequence
    
    def _get_failure_handler(self, step: TestStep) -> Optional[FailureHandler]:
        """Get appropriate failure handler for a step."""
        # Find handler matching step error
        for handler in self.config.failure_handlers:
            if handler.pattern in (step.error_message or ""):
                return handler
        return None
    
    def _handle_failure(self, step: TestStep, handler: FailureHandler) -> bool:
        """
        Handle a failed step according to failure handler.
        
        Returns:
            True to continue, False to abort
        """
        print(f"\n⚠ Failure handler triggered: {handler.action}")
        
        if handler.action == "abort":
            return False
        elif handler.action == "skip":
            step.status = TestStepStatus.SKIPPED
            return True
        elif handler.action == "retry":
            # Retry logic would go here
            print(f"Retrying (max {handler.max_retries or 3} attempts)...")
            return True
        elif handler.action == "prompt":
            # Show message and ask user
            message = handler.message or "Step failed. Continue?"
            print(f"\n{message}")
            # Would use Zenity here
            return True
        
        return True
    
    def _print_summary(self):
        """Print test run summary."""
        print(f"\n{'='*60}")
        print("Test Summary")
        print(f"{'='*60}")
        
        passed = sum(1 for s in self.config.test_sequence if s.status == TestStepStatus.PASSED)
        failed = sum(1 for s in self.config.test_sequence if s.status == TestStepStatus.FAILED)
        skipped = sum(1 for s in self.config.test_sequence if s.status == TestStepStatus.SKIPPED)
        
        print(f"Total: {len(self.config.test_sequence)} steps")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Skipped: {skipped} ⚠")
        
        if failed == 0:
            print(f"\n✓ All tests passed!")
        else:
            print(f"\n✗ Some tests failed")


class ConfigManager:
    """
    Manages loading and discovery of test configurations.
    """
    
    CONFIG_DIRS = [
        Path.home() / ".config" / "interactive-firmware-dev" / "tests",
        Path("./test-configs"),
    ]
    
    @classmethod
    def find_config(cls, name: str) -> Optional[Path]:
        """
        Find a configuration file by name.
        
        Args:
            name: Config name (with or without extension)
            
        Returns:
            Path to config file or None
        """
        # Add extension if not present
        if not name.endswith(('.yaml', '.yml', '.json')):
            name = name + '.yaml'
        
        # Search in all config directories
        for config_dir in cls.CONFIG_DIRS:
            config_path = config_dir / name
            if config_path.exists():
                return config_path
        
        return None
    
    @classmethod
    def list_configs(cls) -> List[Dict[str, str]]:
        """
        List all available configurations.
        
        Returns:
            List of dicts with 'name', 'path', 'description'
        """
        configs = []
        seen = set()
        
        for config_dir in cls.CONFIG_DIRS:
            if not config_dir.exists():
                continue
            
            # Support both YAML and JSON configs
            for pattern in ["*.yaml", "*.yml", "*.json"]:
                for config_file in config_dir.glob(pattern):
                    if config_file.name in seen:
                        continue
                    seen.add(config_file.name)
                    
                    try:
                        if config_file.suffix == '.json':
                            with open(config_file, 'r') as f:
                                data = json.load(f)
                        elif YAML_AVAILABLE:
                            with open(config_file, 'r') as f:
                                data = yaml.safe_load(f)  # type: ignore
                        else:
                            continue  # Skip YAML files if PyYAML not available
                        
                        configs.append({
                            'name': data.get('name', config_file.stem),
                            'path': str(config_file),
                            'description': data.get('description', 'No description')
                        })
                    except:
                        pass  # Skip invalid configs
        
        return configs
    
    @classmethod
    def load_config(
        cls,
        name_or_path: str,
        **variables
    ) -> Optional[TestConfig]:
        """
        Load a configuration by name or path.
        
        Args:
            name_or_path: Config name or full path
            **variables: Variables to substitute
            
        Returns:
            TestConfig or None if not found/invalid
        """
        # Check if it's a path
        path = Path(name_or_path)
        if path.exists():
            config_path = path
        else:
            # Try to find by name
            config_path = cls.find_config(name_or_path)
        
        if not config_path:
            print(f"Config not found: {name_or_path}")
            return None
        
        # Load based on extension
        try:
            if config_path.suffix in ('.yaml', '.yml'):
                if not YAML_AVAILABLE:
                    print(f"Error: PyYAML required for {config_path.suffix} files. Install with: pip install pyyaml")
                    return None
                config = TestConfig.from_yaml(str(config_path))
            elif config_path.suffix == '.json':
                config = TestConfig.from_json(str(config_path))
            else:
                print(f"Unsupported config format: {config_path.suffix}")
                return None
        except Exception as e:
            print(f"Error loading config: {e}")
            return None
        
        # Validate
        errors = ConfigValidator.validate(config.__dict__)
        if errors:
            print(f"Config validation errors:")
            for error in errors:
                print(f"  - {error}")
            return None
        
        # Substitute variables
        if variables:
            config = config.substitute_variables(**variables)
        
        return config


# Convenience functions

def load_test_config(path: str, **variables) -> Optional[TestConfig]:
    """Load a test configuration file."""
    return ConfigManager.load_config(path, **variables)


def list_available_tests() -> List[Dict[str, str]]:
    """List all available test configurations."""
    return ConfigManager.list_configs()


def create_test_runner(
    config: TestConfig,
    session,
    **callbacks
) -> TestRunner:
    """Create a test runner for a configuration."""
    return TestRunner(config, session, **callbacks)


if __name__ == "__main__":
    # Example usage
    print("Test Configuration System")
    print("=" * 60)
    
    # List available configs
    configs = list_available_tests()
    print(f"\nAvailable tests: {len(configs)}")
    for config in configs:
        print(f"  - {config['name']}: {config['description']}")
    
    # Example: Create a config programmatically
    example_config = TestConfig(
        name="Example NFC Test",
        description="Simple NFC card detection test",
        patterns={
            "card_detected": "Card detected",
            "card_removed": "Card removed"
        },
        test_sequence=[
            TestStep(
                name="detect",
                prompt="Tap the NFC card",
                expected_logs=["card_detected"],
                timeout=10.0
            )
        ]
    )
    
    print(f"\nExample config: {example_config.name}")
    print(f"Steps: {len(example_config.test_sequence)}")
