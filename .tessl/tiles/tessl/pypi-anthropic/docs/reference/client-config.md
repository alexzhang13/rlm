# Client Configuration Reference

Initialize and configure Anthropic API clients for synchronous and asynchronous operations.

## Synchronous Client

```python { .api }
class Anthropic:
    """Synchronous client for Anthropic API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        auth_token: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, object] | None = None,
        http_client: httpx.Client | None = None,
    ):
        """
        Initialize Anthropic client.

        Parameters:
            api_key: API key (defaults to ANTHROPIC_API_KEY env var)
            auth_token: Bearer token (alternative to api_key)
            base_url: Override base URL (defaults to ANTHROPIC_BASE_URL env var)
            timeout: Request timeout (default: 600s)
            max_retries: Maximum retry attempts (default: 2)
            default_headers: Headers added to all requests
            default_query: Query parameters added to all requests
            http_client: Custom httpx.Client instance
        """
        ...

    def close(self) -> None:
        """Close the underlying HTTP client."""
        ...

    def __enter__(self) -> Anthropic:
        """Context manager entry."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        ...

    @property
    def messages(self) -> Messages:
        """Access Messages resource."""
        ...

    @property
    def beta(self) -> Beta:
        """Access Beta resources."""
        ...

    @property
    def models(self) -> Models:
        """Access Models resource."""
        ...
```

## Asynchronous Client

```python { .api }
class AsyncAnthropic:
    """Asynchronous client for Anthropic API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        auth_token: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        """Initialize async Anthropic client. Same parameters as Anthropic."""
        ...

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        ...

    async def __aenter__(self) -> AsyncAnthropic:
        """Async context manager entry."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        ...
```

## Constants

```python { .api }
DEFAULT_TIMEOUT: float = 600.0  # 10 minutes
DEFAULT_MAX_RETRIES: int = 2
```

## Quick Examples

### Basic Initialization

```python
from anthropic import Anthropic

# Using environment variable ANTHROPIC_API_KEY
client = Anthropic()

# Explicit API key
client = Anthropic(api_key="your-api-key")
```

### Context Manager

```python
with Anthropic() as client:
    message = client.messages.create(...)
# Client automatically closed
```

### Custom Timeout

```python
import httpx

# Single timeout value (applies to all)
client = Anthropic(timeout=120.0)

# Granular timeout control
client = Anthropic(
    timeout=httpx.Timeout(
        connect=10.0,   # Connection timeout
        read=60.0,      # Read timeout
        write=10.0,     # Write timeout
        pool=10.0,      # Pool timeout
    )
)
```

### Retry Configuration

```python
# Increase retries
client = Anthropic(max_retries=5)

# Disable retries
client = Anthropic(max_retries=0)
```

### Custom Headers

```python
client = Anthropic(
    default_headers={
        "X-Custom-Header": "value",
        "User-Agent": "MyApp/1.0",
    }
)
```

### Custom Base URL

```python
# Development environment
client = Anthropic(
    base_url="https://api.dev.anthropic.com"
)

# Using environment variable ANTHROPIC_BASE_URL
import os
os.environ["ANTHROPIC_BASE_URL"] = "https://api.dev.anthropic.com"
client = Anthropic()
```

### Custom HTTP Client

```python
import httpx

# Custom httpx client
http_client = httpx.Client(
    proxy="http://proxy.example.com:8080",
    limits=httpx.Limits(max_connections=100),
)

client = Anthropic(http_client=http_client)
```

### Async Client

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()
    message = await client.messages.create(...)
    await client.close()

asyncio.run(main())
```

### Async Context Manager

```python
async def main():
    async with AsyncAnthropic() as client:
        message = await client.messages.create(...)
    # Client automatically closed
```

### Bearer Token Authentication

```python
client = Anthropic(auth_token="your-bearer-token")
```

### HTTP Client with Proxy

```python
import httpx

client = Anthropic(
    http_client=httpx.Client(
        proxy="http://proxy.example.com:8080"
    )
)
```

### Connection Pool Configuration

```python
import httpx

client = Anthropic(
    http_client=httpx.Client(
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        )
    )
)
```

### Request Per-Call Options

```python
# Override timeout for specific request
message = client.messages.with_options(timeout=120.0).create(...)

# Override headers
message = client.messages.with_options(
    headers={"X-Request-ID": "abc123"}
).create(...)

# Override max retries
message = client.messages.with_options(max_retries=5).create(...)
```

## HTTP Client Factories

```python { .api }
class DefaultHttpxClient:
    """Default synchronous HTTP client using httpx."""
    def __init__(
        self,
        *,
        proxy: str | httpx.Proxy | None = None,
        transport: httpx.HTTPTransport | None = None,
        **kwargs
    ): ...

class DefaultAsyncHttpxClient:
    """Default asynchronous HTTP client using httpx."""
    def __init__(
        self,
        *,
        proxy: str | httpx.Proxy | None = None,
        transport: httpx.AsyncHTTPTransport | None = None,
        **kwargs
    ): ...

class DefaultAioHttpClient:
    """Alternative async client using aiohttp (better concurrency)."""
    def __init__(self, **kwargs): ...
```

## Environment Variables

- `ANTHROPIC_API_KEY` - API key for authentication
- `ANTHROPIC_BASE_URL` - Override base URL
- `ANTHROPIC_AUTH_TOKEN` - Bearer token (alternative to API key)

## See Also

- [Error Handling](./errors.md) - Exception handling and retry logic
- [Utilities](./utilities.md) - HTTP client utilities
