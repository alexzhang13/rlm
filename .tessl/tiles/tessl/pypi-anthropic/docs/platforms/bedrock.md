# AWS Bedrock Integration

Use Claude models via AWS Bedrock with automatic authentication and region configuration.

## Installation

```bash
pip install anthropic[bedrock]
```

## Client Initialization

```python { .api }
class AnthropicBedrock:
    """Synchronous client for Claude on AWS Bedrock."""

    def __init__(
        self,
        *,
        aws_access_key: str | None = None,
        aws_secret_key: str | None = None,
        aws_session_token: str | None = None,
        aws_region: str | None = None,
        aws_profile: str | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ):
        """
        Initialize Bedrock client.

        Parameters:
            aws_access_key: AWS access key ID (or AWS_ACCESS_KEY_ID env var)
            aws_secret_key: AWS secret access key (or AWS_SECRET_ACCESS_KEY env var)
            aws_session_token: AWS session token (or AWS_SESSION_TOKEN env var)
            aws_region: AWS region (or AWS_REGION env var, default: us-east-1)
            aws_profile: AWS profile from ~/.aws/credentials
            timeout: Request timeout
            max_retries: Maximum retry attempts
            default_headers: Custom headers
            http_client: Custom httpx.Client
        """
        ...

class AsyncAnthropicBedrock:
    """Asynchronous client for Claude on AWS Bedrock."""
    # Same parameters as AnthropicBedrock
    ...
```

## Bedrock Model Identifiers

```python { .api }
# Claude 3.5 on Bedrock
"anthropic.claude-3-5-sonnet-20241022-v2:0"
"anthropic.claude-3-5-sonnet-20240620-v1:0"
"anthropic.claude-3-5-haiku-20241022-v1:0"

# Claude 3 on Bedrock
"anthropic.claude-3-opus-20240229-v1:0"
"anthropic.claude-3-sonnet-20240229-v1:0"
"anthropic.claude-3-haiku-20240307-v1:0"
```

## Quick Examples

### Basic Usage

```python
from anthropic import AnthropicBedrock

client = AnthropicBedrock()  # Uses environment variables

message = client.messages.create(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Explicit Credentials

```python
client = AnthropicBedrock(
    aws_access_key="AKIA...",
    aws_secret_key="wJal...",
    aws_region="us-east-1"
)
```

### Using AWS Profile

```python
client = AnthropicBedrock(
    aws_profile="production",
    aws_region="us-west-2"
)
```

### Streaming

```python
with client.messages.stream(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Multi-Region Deployment

```python
regions = ["us-east-1", "us-west-2", "eu-west-1"]

for region in regions:
    client = AnthropicBedrock(aws_region=region)
    message = client.messages.create(...)
    client.close()
```

### Async Client

```python
import asyncio
from anthropic import AsyncAnthropicBedrock

async def main():
    client = AsyncAnthropicBedrock(aws_region="us-east-1")
    message = await client.messages.create(...)
    await client.close()

asyncio.run(main())
```

## Environment Variables

- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_SESSION_TOKEN` - AWS session token
- `AWS_REGION` - AWS region (default: us-east-1)

## See Also

- [Messages API](../api/messages.md) - Core message creation
- [Streaming API](../api/streaming.md) - Streaming responses
