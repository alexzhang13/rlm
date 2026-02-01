# pytest

A comprehensive Python testing framework that makes it easy to write simple tests while scaling to support complex functional testing for applications and libraries. pytest features detailed assertion introspection using plain assert statements, automatic test discovery, modular fixtures for managing test resources, and a rich plugin architecture with over 1300 external plugins.

## Package Information

- **Package Name**: pytest
- **Language**: Python
- **Installation**: `pip install pytest`
- **Version**: 8.4.2
- **License**: MIT
- **Python Compatibility**: Python 3.9+ (3.9, 3.10, 3.11, 3.12, 3.13, 3.14)

## Core Imports

```python
import pytest
```

For accessing specific functionality:

```python
from pytest import (
    fixture, raises, skip, xfail, fail,
    mark, param, approx, Config, Session
)
```

## Basic Usage

```python
import pytest

# Simple test function
def test_basic_math():
    assert 2 + 2 == 4
    assert 5 * 3 == 15

# Test with fixture
@pytest.fixture
def sample_data():
    return [1, 2, 3, 4, 5]

def test_with_fixture(sample_data):
    assert len(sample_data) == 5
    assert sum(sample_data) == 15

# Parametrized test
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16)
])
def test_square(input, expected):
    assert input ** 2 == expected

# Exception testing
def test_exception():
    with pytest.raises(ValueError):
        int("invalid")

# Skipping tests
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# Expected failure
@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    assert False
```

## Architecture

pytest's architecture is built around several key components:

- **Collection System**: Automatic discovery and collection of test files, classes, and functions using a tree-based collector hierarchy
- **Fixture System**: Dependency injection framework providing reusable test components with automatic cleanup and parametrization
- **Plugin Architecture**: Hook-based system enabling extensibility through 1300+ community plugins and custom implementations
- **Configuration Management**: Comprehensive configuration through command-line options, ini files, and programmatic access
- **Assertion Introspection**: Advanced assertion rewriting providing detailed failure information without custom assertion methods
- **Mark System**: Flexible test categorization and parametrization supporting conditional execution and metadata attachment

This design enables pytest to scale from simple unit tests to complex functional testing scenarios while maintaining ease of use and extensive customization capabilities.

## Capabilities

### Core Testing Functions

Essential functions for controlling test execution flow including skip, xfail, fail, exit, and conditional imports. These functions provide the fundamental building blocks for test control and outcome management.

```python { .api }
def skip(reason: str = "", *, allow_module_level: bool = False): ...
def xfail(reason: str = ""): ...
def fail(reason: str = "", pytrace: bool = True): ...
def exit(reason: str = "", returncode: int | None = None): ...
def importorskip(modname: str, minversion: str | None = None, reason: str | None = None, *, exc_type: type[ImportError] | None = None): ...
```

[Testing Functions](./testing-functions.md)

### Exception Handling and Assertions

Context managers and utilities for asserting exceptions, warnings, and approximate numerical comparisons. Includes comprehensive exception information and group exception handling.

```python { .api }
def raises(expected_exception, *, match=None, check=None) -> RaisesExc: ...
def warns(expected_warning, *, match=None) -> WarningsRecorder: ...
def deprecated_call(func=None, *args, **kwargs): ...
def approx(expected, rel=None, abs=None, nan_ok: bool = False): ...
```

[Assertions](./assertions.md)

### Fixture System and Dependency Injection

Comprehensive fixture system for managing test dependencies, setup, and teardown with support for multiple scopes, parametrization, and automatic resolution.

```python { .api }
def fixture(fixture_function=None, *, scope="function", params=None, autouse=False, ids=None, name=None): ...

class FixtureRequest:
    def getfixturevalue(self, argname: str): ...
    def applymarker(self, marker): ...
```

[Fixtures](./fixtures.md)

### Configuration and Plugin System

Central configuration management and plugin architecture enabling extensive customization through hooks, configuration files, and command-line options.

```python { .api }
class Config:
    def getini(self, name: str): ...
    def getoption(self, name: str): ...
    def addinivalue_line(self, name: str, line: str): ...

class PytestPluginManager:
    def register(self, plugin, name=None): ...
    def unregister(self, plugin=None, name=None): ...

def hookimpl(**kwargs): ...
def hookspec(**kwargs): ...
```

[Configuration](./configuration.md)

### Test Collection and Execution

Collection tree components for test discovery, organization, and execution including nodes, collectors, items, and session management.

```python { .api }
class Session:
    def collect(self): ...
    def pytest_runtest_protocol(self, item): ...

class Function:
    def runtest(self): ...
    def setup(self): ...
    def teardown(self): ...

class Metafunc:
    def parametrize(self, argnames, argvalues, **kwargs): ...
```

[Test Collection](./test-collection.md)

### Test Utilities and Environment Control

Utilities for controlling test environments including monkeypatching, output capture, temporary paths, caching, and testing framework testing tools.

```python { .api }
class MonkeyPatch:
    def setattr(self, target, name, value=<notset>, raising: bool = True): ...
    def setenv(self, name: str, value: str, prepend: str | None = None): ...
    def chdir(self, path): ...

class CaptureFixture:
    def readouterr(self): ...
    def disabled(self): ...

class Cache:
    def get(self, key: str, default): ...
    def set(self, key: str, value: object) -> None: ...
    def mkdir(self, name: str) -> Path: ...

class Stash:
    def __setitem__(self, key: StashKey[T], value: T) -> None: ...
    def __getitem__(self, key: StashKey[T]) -> T: ...
    def get(self, key: StashKey[T], default: D) -> T | D: ...

class StashKey(Generic[T]):
    """Type-safe key for Stash storage."""

class Pytester:
    def makepyfile(self, **kwargs): ...
    def runpytest(self, *args, **kwargs): ...
```

[Test Utilities](./test-utilities.md)

### Marks and Parametrization

Mark system for test categorization, parametrization, and metadata attachment enabling flexible test selection and data-driven testing.

```python { .api }
class MarkGenerator:
    def parametrize(self, argnames, argvalues, **kwargs): ...
    def skip(self, reason: str = ""): ...
    def skipif(self, condition, *, reason: str = ""): ...
    def xfail(self, condition=True, *, reason: str = "", raises=None, run: bool = True, strict: bool = False): ...

def param(*values, marks=(), id=None): ...

# Access via pytest.mark
mark: MarkGenerator
```

[Marks and Parametrization](./marks.md)

### Test Reporting and Results

Comprehensive reporting system for test execution results, collection reports, and terminal output formatting with detailed information about test outcomes.

```python { .api }
class TestReport:
    def from_item_and_call(cls, item: Item, call: CallInfo[None]) -> TestReport: ...

class CollectReport:
    def _to_json(self) -> dict[str, Any]: ...

class CallInfo(Generic[TResult]):
    def from_call(cls, func: Callable[[], TResult], when: str, reraise=None) -> CallInfo[TResult]: ...

class TerminalReporter:
    def write(self, content: str, *, flush: bool = False, **markup: bool) -> None: ...
    def pytest_runtest_logreport(self, report: TestReport) -> None: ...
```

[Test Reporting](./reporting.md)

### Warning Types and Error Handling

Comprehensive warning type hierarchy for pytest-specific warnings including deprecation warnings, configuration warnings, and collection warnings.

```python { .api }
class PytestWarning(UserWarning): ...
class PytestDeprecationWarning(PytestWarning, DeprecationWarning): ...
class PytestConfigWarning(PytestWarning): ...
class PytestCollectionWarning(PytestWarning): ...
class PytestUnknownMarkWarning(PytestWarning): ...
```

[Warning Types](./warnings.md)

## Entry Points

```python { .api }
def main(
    args: list[str] | os.PathLike[str] | None = None,
    plugins: Sequence[str | _PluggyPlugin] | None = None,
) -> int | ExitCode:
    """
    Main entry point for running pytest programmatically.
    
    Performs an in-process test run with comprehensive configuration
    and plugin management.
    
    Parameters:
    - args: Command line arguments. If None, uses sys.argv. Can be list
            of strings or single PathLike object
    - plugins: Plugin objects or names to auto-register during initialization
    
    Returns:
        Exit code (0 for success, non-zero for failure/errors)
        
    Examples:
        >>> pytest.main()  # Run with default args
        >>> pytest.main(['-v', 'tests/'])  # With specific arguments
        >>> pytest.main(['tests/'], plugins=['my_plugin'])  # With plugins
    """

def console_main() -> int:
    """
    Console script entry point for pytest command.
    
    This is the function called when running 'pytest' from command line.
    Not intended for programmatic use - use main() instead.
    
    Returns:
        Integer exit code for console applications
        
    Note:
        Handles BrokenPipeError gracefully and flushes stdout before returning.
    """

class cmdline:
    """Compatibility namespace for legacy pytest usage."""
    
    main = staticmethod(main)  # Provides pytest.cmdline.main() compatibility
```

**Usage Examples:**

```python
import pytest
from pathlib import Path

# Basic programmatic usage
def run_tests():
    exit_code = pytest.main(['-v', '--tb=short'])
    if exit_code == 0:
        print("All tests passed!")
    return exit_code

# With custom configuration
def run_specific_tests():
    args = [
        'tests/unit/',           # Test directory
        '-v',                    # Verbose output
        '--maxfail=3',          # Stop after 3 failures
        '--tb=short',           # Short traceback format
        '-x'                    # Stop on first failure
    ]
    return pytest.main(args)

# With plugins
def run_with_plugins():
    return pytest.main(
        ['tests/'],
        plugins=['pytest-html', 'pytest-cov']
    )

# Legacy compatibility usage
def legacy_style():
    return pytest.cmdline.main(['-v', 'tests/'])

# Handling results
def test_runner_with_handling():
    result = pytest.main(['tests/integration/'])
    
    if result == pytest.ExitCode.OK:
        print("Tests passed successfully")
    elif result == pytest.ExitCode.TESTS_FAILED:
        print("Some tests failed")
    elif result == pytest.ExitCode.NO_TESTS_RAN:
        print("No tests were collected")
    elif result == pytest.ExitCode.INTERRUPTED:
        print("Test run was interrupted")
    else:
        print(f"Test run failed with exit code: {result}")
    
    return result
```

## Types

```python { .api }
from enum import Enum

class ExitCode(Enum):
    OK = 0
    TESTS_FAILED = 1
    INTERRUPTED = 2
    INTERNAL_ERROR = 3
    USAGE_ERROR = 4
    NO_TESTS_RAN = 5

class UsageError(Exception):
    """Raised for command-line usage errors."""

class FixtureLookupError(Exception):
    """Raised when fixture cannot be found or resolved."""
```

## Built-in Fixtures

pytest provides many built-in fixtures automatically available in all tests:

```python { .api }
# Core configuration and request
def test_core_fixtures(
    request,          # FixtureRequest: Access to test context and other fixtures
    config,           # Config: pytest configuration object
    pytestconfig,     # Config: Alias for config fixture
):
    pass

# Output capture
def test_capture_fixtures(
    capsys,           # CaptureFixture: Capture sys.stdout/stderr (text)
    capsysbinary,     # CaptureFixture: Capture sys.stdout/stderr (binary)
    capfd,            # CaptureFixture: Capture file descriptors 1/2 (text)
    capfdbinary,      # CaptureFixture: Capture file descriptors 1/2 (binary)
    caplog,           # LogCaptureFixture: Capture log messages
):
    pass

# Environment modification
def test_environment_fixtures(
    monkeypatch,      # MonkeyPatch: Modify objects, environment, sys.path
):
    pass

# Temporary paths
def test_temp_fixtures(
    tmp_path,         # pathlib.Path: Temporary directory (function scope)
    tmp_path_factory, # TempPathFactory: Create additional temp directories
    tmpdir,           # py.path.local: Legacy temp directory (deprecated)
    tmpdir_factory,   # TempdirFactory: Legacy temp factory (deprecated)
):
    pass

# Warning handling
def test_warning_fixtures(
    recwarn,          # WarningsRecorder: Record warnings during test
):
    pass

# Plugin testing (requires pytest plugin)
def test_plugin_fixtures(
    pytester,         # Pytester: Test pytest plugins and functionality
    testdir,          # Testdir: Legacy plugin testing (deprecated)
):
    pass

# Doctest integration (requires doctest plugin)
def test_doctest_fixtures(
    doctest_namespace, # dict: Namespace for doctest execution
):
    pass
```

## Version Information

```python { .api }
__version__: str  # Current pytest version string (e.g., "8.4.2")
version_tuple: tuple[int, ...]  # Version as tuple of integers (e.g., (8, 4, 2))
```

**Usage Examples:**

```python
import pytest

# Check pytest version
print(f"pytest version: {pytest.__version__}")
# Output: pytest version: 8.4.2

# Version tuple for programmatic comparison
version = pytest.version_tuple
if version >= (8, 0, 0):
    print("Using modern pytest features")

# Version checking utility
def require_pytest_version(min_version_tuple):
    if pytest.version_tuple < min_version_tuple:
        raise RuntimeError(
            f"pytest {'.'.join(map(str, min_version_tuple))} or higher required, "
            f"found {pytest.__version__}"
        )

# Example usage
require_pytest_version((7, 0, 0))  # Ensure pytest 7.0.0+
```