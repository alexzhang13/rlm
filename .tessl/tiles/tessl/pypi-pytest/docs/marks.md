# Marks and Parametrization

Mark system for test categorization, parametrization, and metadata attachment enabling flexible test selection and data-driven testing. The mark system provides a powerful way to organize and control test execution.

## Capabilities

### Mark Generation

Dynamic mark creation system providing access to built-in and custom marks.

```python { .api }
class MarkGenerator:
    """Generates mark decorators dynamically."""
    
    def __getattr__(self, name: str) -> MarkDecorator:
        """Create MarkDecorator for any mark name."""
    
    # Built-in marks
    def parametrize(
        self,
        argnames: str | list[str] | tuple[str, ...],
        argvalues,
        *,
        indirect: bool | list[str] = False,
        ids=None,
        scope: str | None = None
    ) -> MarkDecorator:
        """Parametrize test function."""
    
    def skip(self, reason: str = "") -> MarkDecorator:
        """Skip test unconditionally."""
    
    def skipif(
        self, 
        condition, 
        *, 
        reason: str = ""
    ) -> MarkDecorator:
        """Skip test conditionally."""
    
    def xfail(
        self,
        condition=True,
        *,
        reason: str = "",
        raises=None,
        run: bool = True,
        strict: bool = False
    ) -> MarkDecorator:
        """Mark test as expected to fail."""
    
    def usefixtures(self, *names: str) -> MarkDecorator:
        """Use fixtures without declaring them as arguments."""
    
    def filterwarnings(self, *filters: str) -> MarkDecorator:
        """Filter warnings for specific test."""

# Global mark instance
mark: MarkGenerator
```

**Usage Example:**

```python
import pytest

# Basic marks
@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
def test_new_feature():
    pass

@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    assert False

# Custom marks
@pytest.mark.integration
@pytest.mark.database
def test_database_integration():
    pass

# Using fixtures without parameters
@pytest.mark.usefixtures("setup_test_data", "cleanup_temp_files")
def test_with_automatic_fixtures():
    pass

# Filter warnings
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_legacy_code():
    pass
```

### Mark Decorators

Decorators that apply marks to test functions and classes.

```python { .api }
class MarkDecorator:
    """Decorator that applies marks to test functions and classes."""
    
    # Attributes
    mark: Mark  # The underlying mark
    markname: str  # Mark name
    args: tuple  # Mark arguments
    kwargs: dict  # Mark keyword arguments
    
    def __call__(self, func_or_class):
        """Apply mark to function or class."""
    
    def with_args(self, *args, **kwargs) -> MarkDecorator:
        """Create new decorator with additional arguments."""
    
    def combine(self, other: MarkDecorator) -> MarkDecorator:
        """Combine with another mark decorator."""
```

### Mark Objects

Represents a mark applied to a test with its arguments and metadata.

```python { .api }
class Mark:
    """Represents a mark applied to a test."""
    
    # Attributes
    name: str  # Mark name
    args: tuple  # Mark arguments
    kwargs: dict  # Mark keyword arguments
    
    def combined_with(self, other: Mark) -> Mark:
        """Combine with another mark."""
    
    def _for_parametrize(self) -> Mark:
        """Create mark suitable for parametrization."""
```

### Test Parametrization

Create parameter sets for data-driven testing.

```python { .api }
def param(*values, marks=(), id=None):
    """
    Create parameter sets for pytest.mark.parametrize.
    
    Parameters:
    - values: Parameter values for the test
    - marks: Marks to apply to this parameter set
    - id: Identifier for this parameter set
    
    Returns:
    ParameterSet object
    """

class ParameterSet:
    """Represents a set of parameters for parametrized tests."""
    
    # Attributes
    values: tuple  # Parameter values
    marks: tuple[Mark, ...]  # Applied marks
    id: str | None  # Parameter set identifier
    
    @classmethod
    def param(cls, *values, marks=(), id=None) -> ParameterSet:
        """Create parameter set."""
    
    @classmethod
    def extract_from(
        cls, 
        parameterset, 
        legacy_force_tuple: bool = False
    ) -> ParameterSet:
        """Extract parameter set from various input formats."""
```

**Usage Example:**

```python
import pytest

# Basic parametrization
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert input ** 2 == expected

# Named parameters with IDs
@pytest.mark.parametrize(
    "operation,a,b,expected",
    [
        ("add", 2, 3, 5),
        ("multiply", 4, 5, 20),
        ("subtract", 10, 3, 7),
    ],
    ids=["addition", "multiplication", "subtraction"]
)
def test_math_operations(operation, a, b, expected):
    if operation == "add":
        assert a + b == expected
    elif operation == "multiply":
        assert a * b == expected
    elif operation == "subtract":
        assert a - b == expected

# Using pytest.param with marks
@pytest.mark.parametrize("value", [
    1,
    2,
    pytest.param(3, marks=pytest.mark.xfail(reason="Known issue with 3")),
    pytest.param(4, marks=pytest.mark.skip(reason="Skip 4 for now")),
    pytest.param(5, id="special_five"),
])
def test_values(value):
    assert value < 10

# Multiple parametrizations
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
@pytest.mark.parametrize("os", ["windows", "linux", "mac"])
def test_cross_platform(browser, os):
    # Runs 6 times (2 browsers × 3 operating systems)
    pass

# Indirect parametrization (parameters passed to fixtures)
@pytest.fixture
def database(request):
    db_type = request.param
    return setup_database(db_type)

@pytest.mark.parametrize("database", ["sqlite", "postgresql"], indirect=True)
def test_with_database(database):
    # database fixture receives "sqlite" or "postgresql" as request.param
    pass
```

### Mark Constants

Special constants for controlling mark behavior.

```python { .api }
HIDDEN_PARAM = object()  # Special value to hide parameters from test names
```

**Usage Example:**

```python
@pytest.mark.parametrize("value,description", [
    (1, "first"),
    (2, "second"),
    (pytest.HIDDEN_PARAM, "hidden"),  # This parameter won't appear in test name
])
def test_with_hidden_param(value, description):
    pass
```

## Built-in Marks

### Skip Marks

```python
# Unconditional skip
@pytest.mark.skip(reason="Not implemented")

# Conditional skip  
@pytest.mark.skipif(condition, reason="Explanation")
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
@pytest.mark.skipif(not has_feature(), reason="Feature not available")
```

### Expected Failure Marks

```python
# Basic expected failure
@pytest.mark.xfail(reason="Known bug")

# Conditional expected failure
@pytest.mark.xfail(sys.version_info < (3, 9), reason="Requires Python 3.9+")

# Strict xfail (failure if test unexpectedly passes)
@pytest.mark.xfail(strict=True, reason="Should definitely fail")

# Expected specific exception
@pytest.mark.xfail(raises=ValueError, reason="Should raise ValueError")

# Don't run, just mark as xfail
@pytest.mark.xfail(run=False, reason="Don't run this test")
```

### Parametrization Marks

```python
# Simple parametrization
@pytest.mark.parametrize("value", [1, 2, 3])

# Multiple parameters
@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (2, 3, 5)])

# Custom IDs
@pytest.mark.parametrize("value", [1, 2, 3], ids=["one", "two", "three"])

# Indirect parametrization
@pytest.mark.parametrize("fixture_name", ["value1", "value2"], indirect=True)
```

### Fixture Marks

```python
# Use fixtures without declaring as parameters
@pytest.mark.usefixtures("setup_database", "cleanup_temp_files")

# Filter warnings
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.filterwarnings("error::UserWarning")
```

## Running Tests with Marks

Command-line options for running specific marked tests:

```bash
# Run only tests with specific mark
pytest -m "slow"

# Run tests with multiple marks  
pytest -m "slow and integration"

# Run tests without specific mark
pytest -m "not slow"

# Complex mark expressions
pytest -m "(slow or integration) and not windows"
```

## Custom Marks

Register custom marks in pytest configuration:

```python
# pytest.ini
[tool:pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    smoke: marks tests as smoke tests
    regression: marks tests as regression tests
    
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]
```