# Azure AI Foundry Integration

Access Claude models via Azure AI Foundry with API key or Azure AD authentication.

## Overview

Azure AI Foundry provides access to Claude through Microsoft's Azure AI platform with:
- Azure API key authentication
- Azure Active Directory (AAD) token provider authentication
- Automatic base URL construction from resource names

## Client Initialization

```python { .api }
class AnthropicFoundry:
    def __init__(
        self,
        *,
        resource: str | None = None,
        api_key: str | None = None,
        azure_ad_token_provider: Callable[[], str] | None = None,
        base_url: str | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ):
        """
        Initialize Azure AI Foundry client.

        Parameters:
            resource: Azure resource name (e.g., "my-resource" for
                     https://my-resource.services.ai.azure.com/anthropic/)
            api_key: Azure API key (or ANTHROPIC_FOUNDRY_API_KEY env var)
            azure_ad_token_provider: Function returning Azure AD token
            base_url: Full base URL (mutually exclusive with resource)
            timeout: Request timeout
            max_retries: Maximum retry attempts
            default_headers: Custom headers
            http_client: Custom httpx.Client

        Environment Variables:
            ANTHROPIC_FOUNDRY_API_KEY: Default API key
            ANTHROPIC_FOUNDRY_RESOURCE: Default resource name
            ANTHROPIC_FOUNDRY_BASE_URL: Default base URL

        Note:
            Must provide either api_key or azure_ad_token_provider.
            Must provide either resource or base_url.
        """
        ...

class AsyncAnthropicFoundry:
    # Same parameters, but azure_ad_token_provider can return Awaitable[str]
    ...
```

## Quick Examples

### API Key Authentication

```python
from anthropic import AnthropicFoundry

client = AnthropicFoundry(
    resource="my-resource",
    api_key="your-api-key"
)

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Azure AD Token Provider

```python
def get_azure_ad_token():
    """Fetch Azure AD token using your preferred method."""
    # Implement token retrieval
    return "your-azure-ad-token"

client = AnthropicFoundry(
    resource="my-resource",
    azure_ad_token_provider=get_azure_ad_token
)
```

### Using Base URL Directly

```python
client = AnthropicFoundry(
    base_url="https://my-resource.services.ai.azure.com/anthropic/",
    api_key="your-api-key"
)
```

### Async Client

```python
import asyncio
from anthropic import AsyncAnthropicFoundry

async def main():
    client = AsyncAnthropicFoundry(
        resource="my-resource",
        api_key="your-api-key"
    )
    message = await client.messages.create(...)

asyncio.run(main())
```

### Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Limitations

The Azure AI Foundry integration has the following limitations:
1. **No Models API**: `client.models` resource not available
2. **No Message Batches**: `client.messages.batches` resource not available
3. **No Beta Batches**: `client.beta.messages.batches` resource not available

## Environment Variables

- `ANTHROPIC_FOUNDRY_API_KEY` - Default API key
- `ANTHROPIC_FOUNDRY_RESOURCE` - Default resource name
- `ANTHROPIC_FOUNDRY_BASE_URL` - Default base URL

## See Also

- [Messages API](../api/messages.md) - Core message creation
- [Streaming API](../api/streaming.md) - Streaming responses
