# Testing Functions

Core functions for controlling test execution flow and outcomes. These functions provide the fundamental building blocks for managing test behavior, conditional execution, and early termination scenarios.

## Capabilities

### Test Skipping

Skip test execution with optional reason and support for module-level skipping.

```python { .api }
def skip(reason: str = "", *, allow_module_level: bool = False):
    """
    Imperatively skip a test with optional reason.
    
    Parameters:
    - reason: Explanation for why the test is skipped
    - allow_module_level: Whether to allow skipping at module level (outside test functions)
    
    Raises:
    pytest.skip.Exception (Skipped)
    """
```

**Usage Example:**

```python
import pytest

def test_conditional_skip():
    if not has_network():
        pytest.skip("Network not available")
    # test code here

# Module-level skip
if not sys.platform.startswith("linux"):
    pytest.skip("Linux-only tests", allow_module_level=True)
```

### Expected Failures

Mark tests as expected to fail with optional reason.

```python { .api }
def xfail(reason: str = ""):
    """
    Mark test as expected to fail.
    
    Parameters:
    - reason: Explanation for why the test is expected to fail
    
    Raises:
    pytest.xfail.Exception (XFailed)
    """
```

**Usage Example:**

```python
import pytest

def test_known_bug():
    if bug_exists():
        pytest.xfail("Bug #123 not fixed yet")
    assert complex_calculation() == expected_result
```

### Test Failures

Explicitly fail tests with custom messages and traceback control.

```python { .api }
def fail(reason: str = "", pytrace: bool = True):
    """
    Explicitly fail a test with message and traceback control.
    
    Parameters:
    - reason: Failure message to display
    - pytrace: Whether to show pytest traceback (True) or just the message (False)
    
    Raises:
    pytest.fail.Exception (Failed)
    """
```

**Usage Example:**

```python
import pytest

def test_validation():
    result = validate_data(data)
    if not result.is_valid:
        pytest.fail(f"Validation failed: {result.errors}")
```

### Test Suite Exit

Exit the entire test suite immediately with reason and exit code.

```python { .api }
def exit(reason: str = "", returncode: int | None = None):
    """
    Exit testing process immediately.
    
    Parameters:
    - reason: Explanation for early exit
    - returncode: Exit code to use (defaults to appropriate pytest exit code)
    
    Raises:
    pytest.exit.Exception (Exit)
    """
```

**Usage Example:**

```python
import pytest

def test_critical_setup():
    if not critical_system_available():
        pytest.exit("Critical system unavailable, cannot continue testing")
```

### Conditional Imports

Import modules or skip tests if import fails, with version checking support.

```python { .api }
def importorskip(
    modname: str, 
    minversion: str | None = None, 
    reason: str | None = None, 
    *, 
    exc_type: type[ImportError] | None = None
):
    """
    Import module or skip test if import fails.
    
    Parameters:
    - modname: Name of module to import
    - minversion: Minimum required version (if module has __version__)
    - reason: Custom skip reason if import/version check fails
    - exc_type: Specific exception type to catch (defaults to ImportError)
    
    Returns:
    The imported module
    
    Raises:
    pytest.skip.Exception if import fails or version insufficient
    """
```

**Usage Example:**

```python
import pytest

# Skip test if numpy not available
numpy = pytest.importorskip("numpy")

# Skip if version too old
requests = pytest.importorskip("requests", minversion="2.20.0")

def test_with_numpy():
    array = numpy.array([1, 2, 3])
    assert len(array) == 3

def test_with_requests():
    response = requests.get("https://httpbin.org/get")
    assert response.status_code == 200
```

## Exception Types

```python { .api }
# These are the exceptions raised by the testing functions
class skip.Exception(Exception):
    """Raised by pytest.skip()"""

class xfail.Exception(Exception):
    """Raised by pytest.xfail()"""
    
class fail.Exception(Exception):
    """Raised by pytest.fail()"""
    
class exit.Exception(Exception):
    """Raised by pytest.exit()"""
```