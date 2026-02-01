# Warning Types and Error Handling

Comprehensive warning type hierarchy for pytest-specific warnings including deprecation warnings, configuration warnings, collection warnings, and error handling patterns. These warnings help developers identify potential issues and deprecated functionality.

## Capabilities

### Base Warning Types

Foundation warning classes for the pytest warning hierarchy.

```python { .api }
class PytestWarning(UserWarning):
    """
    Base class for all pytest warnings.
    
    This is the base class that all pytest-specific warnings inherit from.
    It extends Python's UserWarning to provide pytest-specific warning behavior.
    """

class PytestDeprecationWarning(PytestWarning, DeprecationWarning):
    """
    Warning for features that will be removed in future versions.
    
    Used to warn about deprecated pytest functionality that will be removed
    in upcoming major releases. Extends both PytestWarning and DeprecationWarning.
    """
```

### Specific Warning Categories

Detailed warning types for different aspects of pytest functionality.

```python { .api }
class PytestAssertRewriteWarning(PytestWarning):
    """
    Warnings from the assert rewrite module.
    
    Issued when there are problems with assertion rewriting, such as:
    - Files that cannot be rewritten
    - Import-time assertion rewrite issues
    - Conflicting assertion rewrite configurations
    """

class PytestCacheWarning(PytestWarning):
    """
    Cache plugin warnings.
    
    Issued when there are problems with pytest's caching functionality:
    - Cache directory access issues
    - Cache corruption problems
    - Cache configuration warnings
    """

class PytestCollectionWarning(PytestWarning):
    """
    Collection failures for files or symbols.
    
    Issued during test collection when:
    - Files cannot be imported
    - Test functions/classes cannot be collected
    - Collection configuration issues arise
    """

class PytestConfigWarning(PytestWarning):
    """
    Configuration issues and warnings.
    
    Issued when there are problems with pytest configuration:
    - Invalid configuration values
    - Conflicting configuration options
    - Missing required configuration
    """

class PytestUnknownMarkWarning(PytestWarning):
    """
    Unknown marker usage warnings.
    
    Issued when tests use marks that haven't been registered:
    - Unregistered custom marks
    - Typos in mark names
    - Missing mark definitions
    """
```

### Experimental and Future Warnings

Warnings for experimental features and future changes.

```python { .api }
class PytestExperimentalApiWarning(PytestWarning, FutureWarning):
    """
    Experimental API usage warnings.
    
    Issued when using experimental pytest APIs that:
    - May change without notice
    - Are not covered by backward compatibility guarantees
    - Are in development and may be removed
    """

class PytestRemovedIn9Warning(PytestDeprecationWarning):
    """
    Features that will be removed in pytest 9.
    
    Specific deprecation warning for functionality scheduled for removal
    in pytest version 9.0. Provides clear migration path and timeline.
    """
```

### Runtime and Execution Warnings

Warnings related to test execution and runtime behavior.

```python { .api }
class PytestReturnNotNoneWarning(PytestWarning):
    """
    Test functions returning non-None values.
    
    Issued when test functions return values other than None:
    - Test functions that return values
    - Generator functions used as tests incorrectly
    - Functions that should be fixtures but aren't marked
    """

class PytestUnraisableExceptionWarning(PytestWarning):
    """
    Unraisable exceptions (e.g., in __del__ methods).
    
    Issued when exceptions occur that cannot be properly raised:
    - Exceptions in __del__ methods
    - Exceptions in cleanup code
    - Exceptions in background threads
    """

class PytestUnhandledThreadExceptionWarning(PytestWarning):
    """
    Unhandled exceptions in threads.
    
    Issued when exceptions occur in threads that are not properly handled:
    - Background thread exceptions
    - Thread pool exceptions
    - Daemon thread exceptions
    """

class PytestFDWarning(PytestWarning):
    """
    File descriptor leak warnings.
    
    Issued by the lsof plugin when file descriptor leaks are detected:
    - Open files not properly closed
    - Network connections left open
    - Resource leaks between tests
    """
```

## Warning Usage Examples

### Filtering Warnings

```python
import pytest
import warnings

# Filter warnings in test code
def test_with_warning_filter():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", PytestDeprecationWarning)
        # Code that would generate deprecation warnings
        deprecated_function()

# Using pytest.mark.filterwarnings
@pytest.mark.filterwarnings("ignore::pytest.PytestDeprecationWarning")
def test_ignore_deprecation():
    deprecated_function()

@pytest.mark.filterwarnings("error::pytest.PytestUnknownMarkWarning") 
def test_treat_unknown_marks_as_errors():
    pass
```

### Configuration-based Warning Control

```python
# pytest.ini
[tool:pytest]
filterwarnings =
    error
    ignore::pytest.PytestDeprecationWarning
    ignore::DeprecationWarning:django.*
    default::pytest.PytestExperimentalApiWarning

# pyproject.toml
[tool.pytest.ini_options]
filterwarnings = [
    "error",
    "ignore::pytest.PytestDeprecationWarning",
    "default::pytest.PytestExperimentalApiWarning",
]
```

### Custom Warning Handling

```python
import pytest
import warnings

def test_custom_warning_handling(recwarn):
    # Trigger some pytest warnings
    warnings.warn("Test warning", PytestConfigWarning)
    warnings.warn("Another warning", PytestCollectionWarning)
    
    # Check that warnings were issued
    assert len(recwarn) == 2
    assert recwarn[0].category == PytestConfigWarning
    assert recwarn[1].category == PytestCollectionWarning
    
    # Check warning messages
    assert "Test warning" in str(recwarn[0].message)
    assert "Another warning" in str(recwarn[1].message)

def test_specific_warning_check():
    with pytest.warns(PytestDeprecationWarning, match="deprecated"):
        warnings.warn("This feature is deprecated", PytestDeprecationWarning)
```

## Common Warning Scenarios

### Unknown Marks

```python
# This will generate PytestUnknownMarkWarning
@pytest.mark.unknownmark  # Typo or unregistered mark
def test_with_unknown_mark():
    pass

# Fix by registering the mark
# pytest.ini
[tool:pytest]
markers =
    unknownmark: description of the mark
```

### Return Values in Tests

```python
# This will generate PytestReturnNotNoneWarning
def test_returning_value():
    return "Should not return anything"  # Warning issued

# Fix by not returning values
def test_fixed():
    result = calculate_something()
    assert result == expected  # Don't return the result
```

### Deprecated Features

```python
# Using deprecated pytest features
def test_with_deprecated_feature():
    # This might generate PytestDeprecationWarning or PytestRemovedIn9Warning
    pytest.deprecated_function()  # Replace with newer API

# Check for specific deprecation warnings
def test_handle_deprecation():
    with pytest.warns(PytestRemovedIn9Warning):
        use_deprecated_feature()
```

### Configuration Issues

```python
# pytest.ini with conflicting options might generate PytestConfigWarning
[tool:pytest]
addopts = --strict-markers
markers =
    # Missing marker definitions can cause warnings

# Fix by properly defining all markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

## Warning Hierarchy

The complete warning hierarchy:

```
UserWarning
├── PytestWarning (base for all pytest warnings)
    ├── PytestAssertRewriteWarning
    ├── PytestCacheWarning
    ├── PytestCollectionWarning
    ├── PytestConfigWarning
    ├── PytestUnknownMarkWarning
    ├── PytestReturnNotNoneWarning
    ├── PytestUnraisableExceptionWarning
    ├── PytestUnhandledThreadExceptionWarning
    ├── PytestFDWarning
    ├── PytestDeprecationWarning (also extends DeprecationWarning)
    │   └── PytestRemovedIn9Warning
    └── PytestExperimentalApiWarning (also extends FutureWarning)
```

## Best Practices

### Handling Warnings in Tests

```python
# Don't ignore all warnings - be specific
@pytest.mark.filterwarnings("ignore::DeprecationWarning:specific_module.*")

# Test that warnings are properly issued
def test_warning_issued():
    with pytest.warns(PytestDeprecationWarning):
        deprecated_api()

# Handle warnings in fixtures
@pytest.fixture
def ignore_known_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", PytestConfigWarning)
        yield
```

### Warning Documentation

```python
def deprecated_function():
    """
    This function is deprecated.
    
    .. deprecated:: 8.0
        Use new_function() instead. Will be removed in pytest 9.0.
    """
    warnings.warn(
        "deprecated_function is deprecated, use new_function instead",
        PytestRemovedIn9Warning,
        stacklevel=2
    )
```