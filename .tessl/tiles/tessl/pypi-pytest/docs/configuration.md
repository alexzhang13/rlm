# Configuration and Plugin System

Central configuration management and plugin architecture enabling extensive customization through hooks, configuration files, command-line options, and the pluggy-based plugin system.

## Capabilities

### Configuration Management

Central configuration object providing access to all pytest settings and options.

```python { .api }
class Config:
    """Central configuration object with access to pluginmanager and hooks."""
    
    # Core attributes
    pluginmanager: PytestPluginManager  # Plugin manager instance
    invocation_params: InvocationParams  # Command-line invocation parameters
    option: argparse.Namespace  # Parsed command-line options
    rootpath: Path  # Root directory path
    inipath: Path | None  # Path to configuration file
    
    def getini(self, name: str) -> Any:
        """
        Get configuration value from ini file.
        
        Parameters:
        - name: Configuration option name
        
        Returns:
        Configuration value
        """
    
    def getoption(self, name: str, default=None, skip: bool = False) -> Any:
        """
        Get command-line option value.
        
        Parameters:
        - name: Option name
        - default: Default value if option not set
        - skip: Whether to skip if option not found
        
        Returns:
        Option value
        """
    
    def addinivalue_line(self, name: str, line: str) -> None:
        """
        Add line to multi-line ini configuration value.
        
        Parameters:
        - name: Configuration option name
        - line: Line to add
        """
    
    def issue_config_time_warning(self, warning: Warning, stacklevel: int) -> None:
        """Issue warning during configuration time."""
```

### Plugin Management

Plugin manager extending pluggy with pytest-specific functionality for loading and managing plugins.

```python { .api }
class PytestPluginManager:
    """Extends pluggy.PluginManager with pytest-specific functionality."""
    
    def register(self, plugin, name: str | None = None) -> None:
        """
        Register a plugin instance.
        
        Parameters:
        - plugin: Plugin instance
        - name: Optional plugin name
        """
    
    def unregister(self, plugin=None, name: str | None = None) -> Any:
        """
        Unregister a plugin instance.
        
        Parameters:
        - plugin: Plugin instance to unregister
        - name: Plugin name to unregister
        
        Returns:
        Unregistered plugin
        """
    
    def get_plugin(self, name: str):
        """Get plugin by name."""
    
    def is_registered(self, plugin) -> bool:
        """Check if plugin is registered."""
    
    def list_plugin_distinfo(self) -> list[tuple[Any, DistInfo]]:
        """List all plugin distribution info."""
    
    def list_name_plugin(self) -> list[tuple[str, Any]]:
        """List all plugins with their names."""
    
    def get_canonical_name(self, plugin) -> str:
        """Get canonical name for plugin."""
    
    def load_setuptools_entrypoints(self, group: str, names: str | None = None) -> int:
        """Load plugins from setuptools entry points."""
    
    def consider_env(self, name: str, value: str | None = None) -> None:
        """Consider environment variable for plugin loading."""
    
    def consider_preparse(self, args: list[str], exclude_only: bool = False) -> None:
        """Consider command-line arguments for plugin loading."""
    
    def consider_conftest(self, conftestmodule) -> None:
        """Register hooks from conftest module."""
```

### Hook System

Decorators for marking functions as hook implementations and specifications.

```python { .api }
def hookimpl(**kwargs):
    """
    Mark function as hook implementation.
    
    Parameters:
    - tryfirst: Execute this hook first
    - trylast: Execute this hook last  
    - hookwrapper: Hook wrapper (can yield)
    - optionalhook: Hook is optional
    - specname: Name of hook specification
    
    Returns:
    HookimplMarker decorator
    """

def hookspec(**kwargs):
    """
    Mark function as hook specification.
    
    Parameters:
    - firstresult: Return first non-None result
    - historic: Historic hook (replay for late registrations)
    - warn_on_impl: Issue warnings for implementations
    
    Returns:
    HookspecMarker decorator
    """
```

**Usage Example:**

```python
import pytest

# Plugin implementation
class MyPlugin:
    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config):
        print("Configuring my plugin")
    
    @pytest.hookimpl
    def pytest_collection_modifyitems(self, config, items):
        # Modify collected test items
        pass
    
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        print(f"Setting up {item.name}")
        outcome = yield
        print(f"Setup complete for {item.name}")

# Register plugin
def pytest_configure(config):
    config.pluginmanager.register(MyPlugin(), "myplugin")
```

### Argument Parsing

Command-line argument parser for pytest with support for options and ini values.

```python { .api }
class Parser:
    """Command-line argument parser for pytest."""
    
    def addoption(
        self,
        *names,
        action=None,
        nargs=None,
        const=None,
        default=None,
        type=None,
        choices=None,
        required=None,
        help=None,
        metavar=None,
        dest=None,
        **kwargs
    ) -> None:
        """Add command-line option."""
    
    def getgroup(self, name: str, description: str = "") -> OptionGroup:
        """Get or create option group."""
    
    def addini(
        self,
        name: str,
        help: str,
        type: str | None = None,
        default=None,
        **kwargs
    ) -> None:
        """Add ini file configuration option."""

class OptionGroup:
    """Groups related command-line options."""
    
    def addoption(self, *names, **kwargs) -> None:
        """Add option to this group."""
    
    def _addoption(self, *names, **kwargs) -> None:
        """Internal method to add option."""
```

**Usage Example:**

```python
# In conftest.py or plugin
def pytest_addoption(parser):
    parser.addoption(
        "--myopt", 
        action="store", 
        default="default",
        help="My custom option"
    )
    
    group = parser.getgroup("mygroup", "My custom options")
    group.addoption(
        "--verbose-mode",
        action="store_true",
        help="Enable verbose mode"
    )
    
    parser.addini(
        "my_setting",
        help="My configuration setting",
        type="string",
        default="default_value"
    )

def pytest_configure(config):
    my_opt = config.getoption("myopt")
    my_setting = config.getini("my_setting")
```

### Exit Codes

Enumeration of pytest exit codes for different execution outcomes.

```python { .api }
from enum import IntEnum

class ExitCode(IntEnum):
    """Integer enum for pytest exit codes."""
    
    OK = 0                # All tests passed
    TESTS_FAILED = 1      # One or more tests failed
    INTERRUPTED = 2       # Test run interrupted
    INTERNAL_ERROR = 3    # Internal pytest error
    USAGE_ERROR = 4       # Command-line usage error
    NO_TESTS_RAN = 5      # No tests found/collected
```

### Configuration Exceptions

```python { .api }
class UsageError(Exception):
    """
    Raised for command-line usage errors.
    
    This exception is raised when:
    - Invalid command-line arguments are provided
    - Required options are missing
    - Option values are invalid
    """
```

## Entry Points

Main entry points for running pytest programmatically.

```python { .api }
def main(args=None, plugins=None) -> int:
    """
    Main entry point for running pytest programmatically.
    
    Parameters:
    - args: Command-line arguments (defaults to sys.argv)
    - plugins: List of plugin objects to register
    
    Returns:
    Exit code (ExitCode enum value)
    """

def console_main() -> int:
    """
    Console script entry point.
    Called by pytest command-line script.
    
    Returns:
    Exit code
    """

# Module-level entry point
import pytest.config.cmdline

def cmdline.main() -> int:
    """Command line interface entry point."""
```

## Configuration Files

pytest supports multiple configuration file formats:

```python
# pytest.ini
[tool:pytest]
addopts = -v --tb=short
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests

# pyproject.toml
[tool.pytest.ini_options]
addopts = "-v --tb=short"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]

# setup.cfg  
[tool:pytest]
addopts = -v --tb=short
testpaths = tests
```

## Hook Specifications

Comprehensive hook system for extending pytest functionality at every stage:

```python { .api }
# Configuration and startup hooks
def pytest_configure(config: Config) -> None:
    """Called after command line options are parsed and plugins loaded."""

def pytest_unconfigure(config: Config) -> None:
    """Called before test process is exited."""

def pytest_sessionstart(session: Session) -> None:
    """Called after Session object has been created."""

def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    """Called after whole test run finished."""

# Collection hooks
def pytest_collect_file(parent: Collector, path: Path) -> Collector | None:
    """Create a collector for the given path."""

def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Called after collection is completed to modify or re-order items."""

def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Generate (parametrize) tests for the given function."""

# Test execution hooks
def pytest_runtest_setup(item: Item) -> None:
    """Called to perform the setup phase for a test item."""

def pytest_runtest_call(item: Item) -> None:
    """Called to run the test for test item."""

def pytest_runtest_teardown(item: Item, nextitem: Item | None) -> None:
    """Called to perform the teardown phase for a test item."""

def pytest_runtest_makereport(item: Item, call: CallInfo) -> TestReport | None:
    """Called to create a TestReport for each phase."""

# Fixture hooks
def pytest_fixture_setup(fixturedef: FixtureDef, request: FixtureRequest) -> object:
    """Perform fixture setup execution."""

def pytest_fixture_post_finalizer(fixturedef: FixtureDef, request: FixtureRequest) -> None:
    """Called after fixture teardown."""

# Reporting hooks
def pytest_report_teststatus(report: TestReport, config: Config) -> tuple[str, str, str] | None:
    """Return result-category, shortletter and verbose word for reporting."""

def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus: int, config: Config) -> None:
    """Add sections to the terminal summary reporting."""

# Warning and error hooks
def pytest_warning_recorded(warning_message, when: str, nodeid: str, location: tuple[str, int, str]) -> None:
    """Process a warning captured by the internal pytest warnings plugin."""

def pytest_internalerror(excrepr: ExceptionRepr, excinfo: ExceptionInfo) -> bool:
    """Called for internal errors."""
```

## Plugin Development

```python
# conftest.py - Automatic plugin loading
def pytest_configure(config):
    """Called after command line options are parsed."""
    
def pytest_collection_modifyitems(config, items):
    """Called after collection is completed."""
    
def pytest_runtest_setup(item):
    """Called before each test runs."""

# External plugin package
from setuptools import setup

setup(
    name="pytest-myplugin",
    entry_points={
        "pytest11": [
            "myplugin = myplugin.plugin",
        ],
    },
)
```

## Types

```python { .api }
from typing import Any
from pathlib import Path

class ExceptionRepr:
    """Representation of an exception for reporting purposes."""
    
    def toterminal(self, tw: TerminalWriter) -> None:
        """Write exception representation to terminal."""
    
    def __str__(self) -> str:
        """String representation of exception."""

class InvocationParams:
    """Parameters used during pytest invocation."""
    
    # Attributes
    args: tuple[str, ...]  # Command line arguments
    plugins: tuple[str, ...] | None  # Plugin names
    dir: Path  # Working directory
```