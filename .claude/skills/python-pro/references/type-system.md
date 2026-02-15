# Type System Reference

## Basic Annotations

```python
from typing import Any
from collections.abc import Sequence, Mapping

# Use | for unions (Python 3.10+)
def find_user(user_id: int | str) -> dict[str, Any] | None:
    ...

# Prefer collections.abc for abstract types
def process_items(items: Sequence[str]) -> list[str]:
    """Accepts list, tuple, or any sequence."""
    return [item.upper() for item in items]

def merge_configs(base: Mapping[str, int], override: dict[str, int]) -> dict[str, int]:
    """Mapping for read-only, dict for mutable."""
    return {**base, **override}
```

## Generic Types

```python
from typing import TypeVar, Generic
from collections.abc import Sequence

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

def first_element(items: Sequence[T]) -> T | None:
    return items[0] if items else None

class Cache(Generic[K, V]):
    def __init__(self) -> None:
        self._data: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value
```

## Protocol for Structural Typing

```python
from typing import Protocol, runtime_checkable

class Drawable(Protocol):
    def draw(self) -> str: ...

    @property
    def color(self) -> str: ...

# Circle implements Drawable without inheriting
class Circle:
    def draw(self) -> str:
        return f"Drawing circle"

    @property
    def color(self) -> str:
        return "red"

def render(shape: Drawable) -> str:
    return shape.draw()

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...
```

## Advanced Features

```python
from typing import Literal, TypeAlias, TypedDict, NotRequired, Self, overload

# Literal types
Mode = Literal["read", "write", "append"]

# Type aliases
JsonDict: TypeAlias = dict[str, Any]

# TypedDict
class UserDict(TypedDict):
    id: int
    name: str
    email: NotRequired[str]

# Self type for method chaining
class Builder:
    def add(self, n: int) -> Self:
        self._value += n
        return self

# Overload for different signatures
@overload
def process(data: str) -> str: ...
@overload
def process(data: int) -> int: ...
def process(data: str | int) -> str | int:
    if isinstance(data, str):
        return data.upper()
    return data * 2
```

## Callable Types

```python
from collections.abc import Callable
from typing import ParamSpec, Concatenate

P = ParamSpec('P')
R = TypeVar('R')

# Preserve function signatures in decorators
def logging_decorator(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

## Type Narrowing

```python
from typing import assert_never

def handle_mode(mode: Literal["read", "write"]) -> str:
    if mode == "read":
        return "Reading"
    elif mode == "write":
        return "Writing"
    else:
        assert_never(mode)  # Exhaustiveness check
```

## Common Patterns in RLM

```python
# Result type for operations that can fail
@dataclass
class Success(Generic[T]):
    value: T

@dataclass
class Error:
    message: str

Result = Success[T] | Error

# Protocol for LM clients
class LMProtocol(Protocol):
    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str: ...
    async def acompletion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str: ...
    def get_usage_summary(self) -> UsageSummary: ...
```
