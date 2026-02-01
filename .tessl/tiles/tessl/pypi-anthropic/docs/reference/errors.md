# Error Handling Reference

Complete exception hierarchy and error handling patterns for the Anthropic Python SDK.

## Exception Hierarchy

```python { .api }
AnthropicError
├── APIError
│   ├── APIStatusError
│   │   ├── BadRequestError (400)
│   │   ├── AuthenticationError (401)
│   │   ├── PermissionDeniedError (403)
│   │   ├── NotFoundError (404)
│   │   ├── ConflictError (409)
│   │   ├── RequestTooLargeError (413)
│   │   ├── UnprocessableEntityError (422)
│   │   ├── RateLimitError (429)
│   │   ├── InternalServerError (≥500)
│   │   ├── ServiceUnavailableError (503)
│   │   ├── DeadlineExceededError (504)
│   │   └── OverloadedError (529)
│   ├── APIConnectionError
│   ├── APITimeoutError
│   └── APIResponseValidationError
```

## Exception Classes

### Base Exceptions

```python { .api }
class AnthropicError(Exception):
    """Base exception for all Anthropic errors."""
    ...

class APIError(AnthropicError):
    """Base for all API-related errors."""
    message: str
    request: httpx.Request | None
    body: object | None
```

### HTTP Status Errors

```python { .api }
class APIStatusError(APIError):
    """HTTP status code error."""
    response: httpx.Response
    status_code: int
    request_id: str | None

class BadRequestError(APIStatusError):
    """400 - Invalid request."""
    ...

class AuthenticationError(APIStatusError):
    """401 - Invalid API key."""
    ...

class PermissionDeniedError(APIStatusError):
    """403 - Insufficient permissions."""
    ...

class NotFoundError(APIStatusError):
    """404 - Resource not found."""
    ...

class ConflictError(APIStatusError):
    """409 - Request conflicts with current state."""
    ...

class RequestTooLargeError(APIStatusError):
    """413 - Request payload too large."""
    ...

class UnprocessableEntityError(APIStatusError):
    """422 - Request semantically invalid."""
    ...

class RateLimitError(APIStatusError):
    """429 - Rate limit exceeded."""
    ...

class InternalServerError(APIStatusError):
    """500+ - Server error."""
    ...

class ServiceUnavailableError(APIStatusError):
    """503 - Service temporarily unavailable."""
    ...

class DeadlineExceededError(APIStatusError):
    """504 - Request exceeded deadline."""
    ...

class OverloadedError(APIStatusError):
    """529 - Service overloaded."""
    ...
```

### Connection Errors

```python { .api }
class APIConnectionError(APIError):
    """Failed to connect to API."""
    ...

class APITimeoutError(APIError):
    """Request timed out."""
    ...

class APIResponseValidationError(APIError):
    """Response validation failed."""
    ...
```

## Error Response Format

```python { .api }
class ErrorObject(BaseModel):
    """Error object in API responses."""
    type: str
    message: str

class ErrorResponse(BaseModel):
    """Error response wrapper."""
    type: Literal["error"]
    error: ErrorObject
```

## Quick Examples

### Basic Error Handling

```python
from anthropic import APIError

try:
    message = client.messages.create(...)
except APIError as e:
    print(f"Error: {e.message}")
```

### Handle Specific Errors

```python
from anthropic import (
    RateLimitError,
    AuthenticationError,
    BadRequestError,
)

try:
    message = client.messages.create(...)
except RateLimitError as e:
    retry_after = e.response.headers.get("retry-after")
    print(f"Rate limited. Retry after {retry_after}s")
except AuthenticationError:
    print("Invalid API key")
except BadRequestError as e:
    print(f"Invalid request: {e.message}")
```

### Retry with Exponential Backoff

```python
import time
from anthropic import RateLimitError, InternalServerError

def create_message_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.messages.create(...)
        except (RateLimitError, InternalServerError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Retry {attempt + 1} after {wait_time}s")
            time.sleep(wait_time)
```

### Extract Request ID

```python
from anthropic import APIStatusError

try:
    message = client.messages.create(...)
except APIStatusError as e:
    print(f"Request ID: {e.request_id}")
    print(f"Status: {e.status_code}")
```

### Validate Response

```python
from anthropic import APIResponseValidationError

try:
    message = client.messages.create(...)
except APIResponseValidationError as e:
    print(f"Response validation failed: {e.message}")
```

### Handle All Errors

```python
from anthropic import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
)

try:
    message = client.messages.create(...)
except APITimeoutError:
    print("Request timed out")
except APIConnectionError:
    print("Connection failed")
except RateLimitError:
    print("Rate limit exceeded")
except APIError as e:
    print(f"API error: {e.message}")
```

## Best Practices

### Always Handle Exceptions

```python
# Bad
message = client.messages.create(...)

# Good
try:
    message = client.messages.create(...)
except APIError as e:
    # Handle error
    ...
```

### Use Specific Exception Types

```python
# Less precise
try:
    message = client.messages.create(...)
except Exception:
    ...

# More precise
try:
    message = client.messages.create(...)
except RateLimitError:
    # Handle rate limit
    ...
except APIError:
    # Handle other API errors
    ...
```

### Log Request Context

```python
import logging

logger = logging.getLogger(__name__)

try:
    message = client.messages.create(...)
except APIStatusError as e:
    logger.error(
        "API request failed",
        extra={
            "request_id": e.request_id,
            "status_code": e.status_code,
            "error_message": e.message,
        }
    )
```

## See Also

- [Client Configuration](./client-config.md) - Configure retry and timeout behavior
- [Error Handling Guide](../guides/error-handling.md) - Advanced error handling patterns
