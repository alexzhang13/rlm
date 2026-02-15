# Testing Reference

## Basic Pytest

```python
import pytest

def test_user_creation() -> None:
    user = User(id=1, name="Alice")
    assert user.name == "Alice"

def test_validation_error() -> None:
    with pytest.raises(ValueError, match="Invalid"):
        validate_input("")

class TestUserService:
    def test_find(self) -> None:
        service = UserService()
        assert service.find(1) is not None
```

## Fixtures

```python
from collections.abc import Iterator

@pytest.fixture
def db() -> Iterator[Database]:
    database = Database("test.db")
    database.create_tables()
    yield database
    database.drop_tables()

@pytest.fixture
def sample_user() -> User:
    return User(id=1, name="Test User")

# Parametrized fixture
@pytest.fixture(params=["local", "modal", "docker"])
def environment_name(request: pytest.FixtureRequest) -> str:
    return request.param
```

## Parametrize

```python
@pytest.mark.parametrize(
    "input,expected",
    [
        ("hello", "HELLO"),
        ("", ""),
        ("123", "123"),
    ],
    ids=["basic", "empty", "numbers"]
)
def test_transform(input: str, expected: str) -> None:
    assert transform(input) == expected

# Multiple parameters
@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.parametrize("backend", ["openai", "anthropic"])
def test_routing(depth: int, backend: str) -> None:
    assert route(depth, backend) is not None
```

## Mocking

```python
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Basic mock
def test_with_mock() -> None:
    mock_client = Mock()
    mock_client.get.return_value = {"status": "ok"}
    service = Service(mock_client)
    result = service.fetch()
    mock_client.get.assert_called_once()

# Patch decorator
@patch("mymodule.external_call")
def test_patched(mock_call: Mock) -> None:
    mock_call.return_value = "mocked"
    assert mymodule.do_thing() == "mocked"

# Side effects for retry testing
def test_retry() -> None:
    mock_api = Mock()
    mock_api.call.side_effect = [
        ConnectionError("Failed"),
        {"status": "ok"}
    ]
    result = retry_call(mock_api)
    assert mock_api.call.call_count == 2

# Async mock
@pytest.mark.asyncio
async def test_async() -> None:
    mock_db = AsyncMock()
    mock_db.fetch.return_value = {"id": 1}
    result = await service.get(mock_db, 1)
    mock_db.fetch.assert_awaited_once_with(1)
```

## Async Testing

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch() -> None:
    result = await fetch_data("test")
    assert result is not None

# Async fixture
@pytest.fixture
async def async_client() -> AsyncIterator[Client]:
    client = Client()
    await client.connect()
    yield client
    await client.disconnect()

# Concurrent test
@pytest.mark.asyncio
async def test_concurrent() -> None:
    results = await asyncio.gather(
        fetch("a"), fetch("b"), fetch("c")
    )
    assert len(results) == 3
```

## Markers

```python
@pytest.mark.skip(reason="Not implemented")
def test_future() -> None: ...

@pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires 3.11+")
def test_new_feature() -> None: ...

@pytest.mark.xfail(reason="Known bug #123")
def test_known_bug() -> None: ...

# Custom markers
@pytest.mark.slow
def test_slow() -> None: ...

@pytest.mark.integration
def test_integration() -> None: ...

# Run: pytest -m "not slow"
```

## Factory Pattern

```python
@pytest.fixture
def make_user():
    created: list[User] = []

    def _make(name: str = "Test", **kwargs) -> User:
        user = User(name=name, **kwargs)
        created.append(user)
        return user

    yield _make

    for user in created:
        user.cleanup()
```
