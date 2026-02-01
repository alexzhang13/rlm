# Assertions and Exception Handling

Context managers and utilities for asserting exceptions, warnings, and performing approximate numerical comparisons. These tools provide comprehensive testing capabilities for exception handling, warning validation, and floating-point comparisons.

## Capabilities

### Exception Assertion

Context manager for asserting that specific exceptions are raised during code execution.

```python { .api }
def raises(expected_exception, *, match=None, check=None):
    """
    Context manager for asserting exceptions are raised.
    
    Parameters:
    - expected_exception: Exception class or tuple of exception classes
    - match: Regex pattern that exception message should match
    - check: Callable to perform additional validation on exception
    
    Returns:
    RaisesExc context manager or ExceptionInfo if used as function decorator
    """

class RaisesExc:
    """Context manager for exception assertion with type checking."""
    
    def matches(self, expected_exception) -> bool:
        """Check if captured exception matches expected type."""
    
    def __enter__(self) -> ExceptionInfo:
        """Enter context manager."""
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager and validate exception."""
```

**Usage Example:**

```python
import pytest
import re

# Basic exception assertion
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

# With message matching
def test_invalid_input():
    with pytest.raises(ValueError, match=r"invalid.*input"):
        process_input("invalid data")

# Multiple exception types
def test_file_operations():
    with pytest.raises((FileNotFoundError, PermissionError)):
        open("/nonexistent/file", "r")

# Custom validation
def test_custom_exception():
    with pytest.raises(CustomError) as exc_info:
        raise_custom_error()
    
    assert exc_info.value.error_code == 123
    assert "custom message" in str(exc_info.value)
```

### Exception Group Assertion

Context manager for asserting ExceptionGroup exceptions (Python 3.11+).

```python { .api }
class RaisesGroup:
    """Context manager for ExceptionGroup assertion."""
    
    def matches(self, expected_exceptions) -> bool:
        """Check if exception group contains expected exceptions."""
    
    def expected_type(self) -> type:
        """Get the expected exception group type."""
```

### Exception Information

Provides detailed information about caught exceptions with advanced introspection capabilities.

```python { .api }
class ExceptionInfo:
    """Information about caught exceptions."""
    
    type: type  # Exception type
    value: Exception  # Exception instance
    tb: types.TracebackType  # Traceback object
    typename: str  # Exception type name as string
    traceback: Traceback  # pytest's enhanced traceback
    
    def exconly(self, tryshort: bool = False) -> str:
        """Return exception as string without traceback."""
    
    def errisinstance(self, exc: type | tuple[type, ...]) -> bool:
        """Check if exception is instance of given type(s)."""
    
    def match(self, regexp: str | re.Pattern) -> bool:
        """Check if exception message matches regex pattern."""
    
    def group_contains(self, expected_exception, *, match=None, depth: int = 1) -> bool:
        """Check if exception group contains specific exception type."""
```

### Warning Assertion

Context manager for asserting that specific warnings are issued during code execution.

```python { .api }
def warns(expected_warning, *, match=None):
    """
    Context manager for asserting warnings are issued.
    
    Parameters:
    - expected_warning: Warning class or tuple of warning classes
    - match: Regex pattern that warning message should match
    
    Returns:
    WarningsRecorder context manager
    """

class WarningsRecorder:
    """Records warnings during test execution."""
    
    def pop(self, cls=Warning):
        """Remove and return last warning of given class."""
    
    def clear(self):
        """Clear all recorded warnings."""
    
    @property
    def list(self) -> list:
        """List of all recorded warnings."""
```

**Usage Example:**

```python
import pytest
import warnings

def test_deprecation_warning():
    with pytest.warns(DeprecationWarning):
        warnings.warn("This is deprecated", DeprecationWarning)

def test_warning_message():
    with pytest.warns(UserWarning, match=r"custom.*warning"):
        warnings.warn("This is a custom warning", UserWarning)

def test_multiple_warnings():
    with pytest.warns() as record:
        warnings.warn("Warning 1", UserWarning)
        warnings.warn("Warning 2", FutureWarning)
    
    assert len(record) == 2
    assert record[0].category == UserWarning
    assert record[1].category == FutureWarning
```

### Deprecation Call Assertion

Context manager for asserting that deprecation warnings are issued during function calls.

```python { .api }
def deprecated_call(func=None, *args, **kwargs):
    """
    Context manager for asserting deprecation warnings.
    
    Parameters:
    - func: Function to call (optional, can be used as context manager)
    - args: Arguments to pass to function
    - kwargs: Keyword arguments to pass to function
    
    Returns:
    WarningsRecorder if used as context manager, function result if used as function call
    """
```

**Usage Example:**

```python
import pytest

# As context manager
def test_deprecated_usage():
    with pytest.deprecated_call():
        deprecated_function()

# As function call
def test_deprecated_function():
    result = pytest.deprecated_call(deprecated_function, arg1, arg2)
    assert result == expected_value
```

### Approximate Comparisons

Create approximate comparison objects for floating-point numbers, sequences, and mappings.

```python { .api }
def approx(expected, rel=None, abs=None, nan_ok: bool = False):
    """
    Create approximate comparison objects for floating-point numbers.
    
    Parameters:
    - expected: Expected value (number, sequence, or mapping)
    - rel: Relative tolerance (default: 1e-6)
    - abs: Absolute tolerance (default: 1e-12)
    - nan_ok: Whether NaN values should be considered equal
    
    Returns:
    ApproxBase object (ApproxScalar, ApproxSequence, ApproxMapping, or ApproxNumpy)
    """
```

**Usage Example:**

```python
import pytest
import math

def test_float_comparison():
    assert 0.1 + 0.2 == pytest.approx(0.3)
    assert math.pi == pytest.approx(3.14159, rel=1e-4)

def test_sequence_comparison():
    assert [0.1 + 0.2, 0.2 + 0.3] == pytest.approx([0.3, 0.5])

def test_dict_comparison():
    result = {"a": 0.1 + 0.2, "b": 0.2 + 0.3}
    expected = {"a": 0.3, "b": 0.5}
    assert result == pytest.approx(expected)

def test_custom_tolerance():
    assert 1.0001 == pytest.approx(1.0, abs=1e-3)
    assert 1.01 == pytest.approx(1.0, rel=0.02)

def test_nan_handling():
    assert float('nan') == pytest.approx(float('nan'), nan_ok=True)
```

## Types

```python { .api }
from typing import Any, Callable, Pattern, Union
import re
import types

# Type definitions for exception handling
ExceptionClass = type[Exception]
ExceptionTuple = tuple[ExceptionClass, ...]
ExceptionSpec = Union[ExceptionClass, ExceptionTuple]

MatchPattern = Union[str, Pattern[str]]
CheckFunction = Callable[[Exception], bool]

class ApproxBase:
    """Base class for approximate comparison objects."""
    pass

class ApproxScalar(ApproxBase):
    """Approximate comparison for scalar values."""
    pass

class ApproxSequence(ApproxBase):
    """Approximate comparison for sequences."""
    pass

class ApproxMapping(ApproxBase):
    """Approximate comparison for mappings."""
    pass

class ApproxNumpy(ApproxBase):
    """Approximate comparison for numpy arrays."""
    pass
```