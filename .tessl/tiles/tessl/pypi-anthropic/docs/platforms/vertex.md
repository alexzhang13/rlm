# Google Vertex AI Integration

Access Claude models on Google Cloud Platform with Vertex AI integration.

## Installation

```bash
pip install anthropic[vertex]
```

## Client Initialization

```python { .api }
class AnthropicVertex:
    """Synchronous client for Claude on Google Vertex AI."""

    def __init__(
        self,
        *,
        project_id: str | None = None,
        region: str | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ):
        """
        Initialize Vertex AI client.

        Parameters:
            project_id: GCP project ID (or CLOUD_ML_PROJECT_ID/GOOGLE_CLOUD_PROJECT env var)
            region: GCP region (or CLOUD_ML_REGION env var, default: us-east5)
            timeout: Request timeout
            max_retries: Maximum retry attempts
            default_headers: Custom headers
            http_client: Custom httpx.Client
        """
        ...

class AsyncAnthropicVertex:
    """Asynchronous client for Claude on Google Vertex AI."""
    # Same parameters as AnthropicVertex
    ...
```

## Vertex Model Identifiers

```python { .api }
# Claude models on Vertex AI
"claude-3-5-sonnet-v2@20241022"
"claude-3-5-sonnet@20240620"
"claude-3-5-haiku@20241022"
"claude-3-opus@20240229"
"claude-3-sonnet@20240229"
"claude-3-haiku@20240307"
```

## Quick Examples

### Basic Usage

```python
from anthropic import AnthropicVertex

client = AnthropicVertex(
    project_id="my-gcp-project",
    region="us-east5"
)

message = client.messages.create(
    model="claude-3-5-sonnet-v2@20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Using Environment Variables

```python
# Set: CLOUD_ML_PROJECT_ID=my-gcp-project
# Set: CLOUD_ML_REGION=us-east5

client = AnthropicVertex()  # Automatically uses env vars
```

### Using Application Default Credentials

```python
# First authenticate: gcloud auth application-default login

client = AnthropicVertex(
    project_id="my-gcp-project",
    region="us-east5"
)
```

### Streaming

```python
with client.messages.stream(
    model="claude-3-5-sonnet-v2@20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Multi-Region Deployment

```python
regions = ["us-east5", "europe-west1", "asia-southeast1"]

for region in regions:
    client = AnthropicVertex(
        project_id="my-gcp-project",
        region=region
    )
    message = client.messages.create(...)
    client.close()
```

### Async Client

```python
import asyncio
from anthropic import AsyncAnthropicVertex

async def main():
    client = AsyncAnthropicVertex(
        project_id="my-gcp-project",
        region="us-east5"
    )
    message = await client.messages.create(...)
    await client.close()

asyncio.run(main())
```

## Environment Variables

- `CLOUD_ML_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `CLOUD_ML_REGION` - GCP region (default: us-east5)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account key JSON

## Available Regions

- `us-east5`
- `us-central1`
- `europe-west1`
- `europe-west4`
- `asia-southeast1`

## See Also

- [Messages API](../api/messages.md) - Core message creation
- [Streaming API](../api/streaming.md) - Streaming responses
