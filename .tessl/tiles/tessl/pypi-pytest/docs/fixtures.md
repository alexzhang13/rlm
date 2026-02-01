# Fixtures and Dependency Injection

Comprehensive fixture system for managing test dependencies, setup, and teardown with support for multiple scopes, parametrization, and automatic resolution. The fixture system provides a powerful dependency injection framework that eliminates the need for traditional setUp/tearDown methods.

## Capabilities

### Fixture Declaration

Decorator for marking functions as fixture factories that provide reusable test components.

```python { .api }
def fixture(
    fixture_function=None, 
    *, 
    scope: str = "function",
    params=None, 
    autouse: bool = False, 
    ids=None, 
    name: str | None = None
):
    """
    Mark function as fixture factory.
    
    Parameters:
    - fixture_function: Function to mark as fixture (when used as decorator)
    - scope: Fixture scope ("function", "class", "module", "package", "session")
    - params: List of parameters for parametrized fixtures
    - autouse: Whether fixture runs automatically for all tests
    - ids: List of test IDs for parametrized fixtures
    - name: Alternative name for the fixture
    
    Returns:
    FixtureFunctionMarker or FixtureFunctionDefinition
    """
```

**Usage Example:**

```python
import pytest
import tempfile
import os

# Basic fixture
@pytest.fixture
def sample_data():
    return [1, 2, 3, 4, 5]

# Fixture with teardown
@pytest.fixture
def temp_file():
    fd, path = tempfile.mkstemp()
    yield path  # This is where the test runs
    os.close(fd)
    os.unlink(path)

# Scoped fixture
@pytest.fixture(scope="module")
def database_connection():
    connection = create_db_connection()
    yield connection
    connection.close()

# Parametrized fixture
@pytest.fixture(params=[1, 2, 3])
def number(request):
    return request.param

# Autouse fixture
@pytest.fixture(autouse=True)
def setup_test_environment():
    setup_environment()
    yield
    cleanup_environment()

# Named fixture
@pytest.fixture(name="data")
def sample_data_fixture():
    return {"key": "value"}

def test_with_fixtures(sample_data, temp_file, number, data):
    assert len(sample_data) == 5
    assert os.path.exists(temp_file)
    assert number in [1, 2, 3]
    assert data["key"] == "value"
```

### Legacy Fixture Support

```python { .api }
def yield_fixture(*args, **kwargs):
    """
    Legacy alias for fixture decorator (deprecated).
    Use pytest.fixture instead.
    """
```

### Fixture Request

Object passed to fixture functions providing access to the requesting test context and fixture management capabilities.

```python { .api }
class FixtureRequest:
    """Request object passed to fixture functions."""
    
    # Core attributes
    node: Node  # Test node that requested the fixture
    scope: str  # Fixture scope
    fixturename: str  # Name of the fixture
    config: Config  # pytest configuration object
    function: Callable | None  # Test function (if applicable)
    cls: type | None  # Test class (if applicable)
    instance: Any | None  # Test class instance (if applicable)
    module: Any | None  # Test module
    param: Any  # Current parameter (for parametrized fixtures)
    keywords: dict  # Test keywords/markers
    
    def getfixturevalue(self, argname: str) -> Any:
        """
        Get value of another fixture by name.
        
        Parameters:
        - argname: Name of fixture to retrieve
        
        Returns:
        Fixture value
        """
    
    def applymarker(self, marker) -> None:
        """
        Apply marker to the test node.
        
        Parameters:
        - marker: Marker to apply
        """
    
    def raiseerror(self, msg: str | None) -> None:
        """
        Raise FixtureLookupError with given message.
        
        Parameters:
        - msg: Error message
        """
    
    @property
    def fspath(self):
        """Legacy property for file path (use node.path instead)."""
```

**Usage Example:**

```python
import pytest

@pytest.fixture
def user_data(request):
    # Access test function name
    test_name = request.node.name
    
    # Get configuration
    config_value = request.config.getini("test_setting")
    
    # Access other fixtures
    database = request.getfixturevalue("database_connection")
    
    # Create user based on test context
    if "admin" in test_name:
        return create_admin_user(database)
    else:
        return create_regular_user(database)

@pytest.fixture(params=["sqlite", "postgresql"])
def database_type(request):
    return request.param

@pytest.fixture
def configured_database(request, database_type):
    # Access parameter from parametrized dependency
    db_type = database_type
    config = request.config
    
    return setup_database(db_type, config)
```

### Fixture Definition

Container for fixture definitions with metadata and execution logic.

```python { .api }
class FixtureDef:
    """Container for fixture definitions."""
    
    # Core attributes
    argname: str  # Fixture argument name
    func: Callable  # Fixture function
    scope: str  # Fixture scope
    params: list | None  # Parameters for parametrized fixtures
    autouse: bool  # Whether fixture is automatically used
    ids: list | None  # Parameter IDs
    
    # Execution methods (internal use)
    def execute(self, request: FixtureRequest): ...
    def finish(self, request: FixtureRequest): ...
```

### Fixture Exceptions

Exception raised when fixture cannot be found or resolved.

```python { .api }
class FixtureLookupError(Exception):
    """
    Raised when fixture cannot be found or resolved.
    
    This exception is raised when:
    - A fixture name is not found
    - Circular fixture dependencies are detected
    - Fixture scope conflicts occur
    """
```

## Fixture Scopes

```python { .api }
# Fixture scope hierarchy (from narrowest to broadest)
FIXTURE_SCOPES = [
    "function",  # Default: new instance per test function
    "class",     # One instance per test class
    "module",    # One instance per test module
    "package",   # One instance per test package
    "session"    # One instance per test session
]
```

## Built-in Fixtures

pytest provides many built-in fixtures automatically available in all tests:

```python { .api }
# Core built-in fixtures (examples)
def test_with_builtins(
    request,        # FixtureRequest object
    config,         # Config object
    monkeypatch,    # MonkeyPatch object
    capfd,          # CaptureFixture for file descriptors
    capsys,         # CaptureFixture for sys.stdout/stderr
    caplog,         # LogCaptureFixture
    tmp_path,       # pathlib.Path to temporary directory
    tmp_path_factory,  # TempPathFactory
    pytester,       # Pytester for testing pytest plugins
    recwarn         # WarningsRecorder
):
    pass
```

## Advanced Fixture Patterns

### Fixture Dependencies

```python
@pytest.fixture
def database():
    return setup_database()

@pytest.fixture
def user(database):
    return create_user(database)

@pytest.fixture
def admin_user(database):
    return create_admin_user(database)

def test_user_permissions(user, admin_user):
    assert not user.is_admin
    assert admin_user.is_admin
```

### Conditional Fixtures

```python
@pytest.fixture
def storage_backend(request):
    if request.config.getoption("--use-redis"):
        return RedisStorage()
    else:
        return MemoryStorage()
```

### Factory Fixtures

```python
@pytest.fixture
def user_factory():
    created_users = []
    
    def create_user(**kwargs):
        user = User(**kwargs)
        created_users.append(user)
        return user
    
    yield create_user
    
    # Cleanup
    for user in created_users:
        user.delete()

def test_multiple_users(user_factory):
    user1 = user_factory(name="Alice")
    user2 = user_factory(name="Bob")
    assert user1.name != user2.name
```