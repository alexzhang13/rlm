# Error Handling Guide

Robust error handling patterns for production applications using the Anthropic Python SDK.

## Basic Error Handling

```python
from anthropic import APIError

try:
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except APIError as e:
    print(f"Error: {e.message}")
```

## Specific Error Types

```python
from anthropic import (
    RateLimitError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    InternalServerError,
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
except NotFoundError:
    print("Resource not found")
except InternalServerError:
    print("Server error, please retry")
```

## Retry with Exponential Backoff

```python
import time
from anthropic import RateLimitError, InternalServerError

def create_message_with_retry(max_retries=3, base_delay=1.0):
    """Create message with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello"}]
            )
        except (RateLimitError, InternalServerError) as e:
            if attempt == max_retries - 1:
                raise

            wait_time = base_delay * (2 ** attempt)
            print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)

message = create_message_with_retry()
```

## Advanced Retry Pattern

```python
import random
import time
from anthropic import APIError, RateLimitError

def exponential_backoff_retry(
    func,
    max_retries=5,
    base_delay=1.0,
    max_delay=60.0,
    jitter=True
):
    """
    Execute function with exponential backoff retry.

    Args:
        func: Function to execute
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to avoid thundering herd
    """
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            # Use retry-after header if available
            retry_after = e.response.headers.get("retry-after")
            if retry_after:
                wait_time = float(retry_after)
            else:
                wait_time = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    wait_time *= (0.5 + random.random())

            print(f"Rate limited. Waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except APIError as e:
            if attempt == max_retries - 1:
                raise
            print(f"API error: {e.message}. Retrying...")
            time.sleep(base_delay)

# Usage
message = exponential_backoff_retry(
    lambda: client.messages.create(...)
)
```

## Async Error Handling

```python
import asyncio
from anthropic import AsyncAnthropic, APIError

async def create_message_safe():
    client = AsyncAnthropic()

    try:
        message = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello"}]
        )
        return message
    except APIError as e:
        print(f"Error: {e.message}")
        return None

result = asyncio.run(create_message_safe())
```

## Circuit Breaker Pattern

```python
import time
from anthropic import APIError

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.is_open:
            # Check if timeout has passed
            if time.time() - self.last_failure_time < self.timeout:
                raise Exception("Circuit breaker is open")
            else:
                # Try to close circuit
                self.is_open = False
                self.failure_count = 0

        try:
            result = func(*args, **kwargs)
            self.failure_count = 0  # Reset on success
            return result
        except APIError as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                print(f"Circuit breaker opened after {self.failure_count} failures")

            raise

# Usage
circuit_breaker = CircuitBreaker()

try:
    message = circuit_breaker.call(
        client.messages.create,
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except Exception as e:
    print(f"Circuit breaker error: {e}")
```

## Logging Errors

```python
import logging
from anthropic import APIError, APIStatusError

logging.basicConfig(level=logging.INFO)
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
            "error_type": e.body.get("error", {}).get("type") if e.body else None,
        }
    )
except APIError as e:
    logger.error(f"API error: {e.message}")
```

## Graceful Degradation

```python
from anthropic import APIError

def get_response_with_fallback(user_message):
    """Try primary model, fall back to simpler model on error."""
    models = [
        "claude-sonnet-4-5-20250929",
        "claude-3-5-haiku-20241022",
    ]

    for model in models:
        try:
            message = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": user_message}]
            )
            return message.content[0].text
        except APIError as e:
            print(f"Failed with {model}: {e.message}")
            continue

    return "Service temporarily unavailable"

response = get_response_with_fallback("What is AI?")
```

## Validate Inputs Before API Call

```python
from anthropic import BadRequestError

def validate_and_create_message(messages):
    """Validate inputs before making API call."""
    # Validate message structure
    if not messages:
        raise ValueError("Messages list cannot be empty")

    for msg in messages:
        if "role" not in msg or "content" not in msg:
            raise ValueError("Each message must have 'role' and 'content'")

        if msg["role"] not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {msg['role']}")

    # Make API call
    try:
        return client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=messages
        )
    except BadRequestError as e:
        print(f"API validation failed: {e.message}")
        raise
```

## Best Practices

### 1. Always Handle Exceptions

Never let exceptions go unhandled in production.

### 2. Use Specific Exception Types

Catch specific exceptions for targeted handling.

### 3. Implement Retry Logic

Always retry transient errors (rate limits, server errors).

### 4. Log with Context

Include request IDs and relevant context in logs.

### 5. Set Reasonable Timeouts

```python
import httpx

client = Anthropic(
    timeout=httpx.Timeout(60.0),
    max_retries=3
)
```

### 6. Monitor Error Rates

Track error rates to detect issues early.

## See Also

- [Error Reference](../reference/errors.md) - Complete exception hierarchy
- [Client Configuration](../reference/client-config.md) - Timeout and retry configuration
