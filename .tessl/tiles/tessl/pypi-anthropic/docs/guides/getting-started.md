# Getting Started Guide

Step-by-step guide to using the Anthropic Python SDK.

## Installation

```bash
pip install anthropic
```

Optional extras:
```bash
pip install anthropic[bedrock]  # AWS Bedrock
pip install anthropic[vertex]   # Google Vertex AI
pip install anthropic[aiohttp]  # Alternative async HTTP
```

## Authentication

Set your API key as an environment variable:

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

Or pass it explicitly:

```python
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")
```

## Basic Message

```python
from anthropic import Anthropic

client = Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(message.content[0].text)
```

## System Prompts

Configure Claude's behavior with system prompts:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful AI assistant specializing in Python programming.",
    messages=[
        {"role": "user", "content": "How do I read a file?"}
    ]
)
```

## Multi-Turn Conversations

Maintain conversation history:

```python
messages = [
    {"role": "user", "content": "My name is Alice."},
    {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
    {"role": "user", "content": "What's my name?"}
]

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=messages
)

print(message.content[0].text)  # "Your name is Alice."
```

## Streaming Responses

Stream responses for real-time feedback:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write a short story"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()
```

## Working with Images

Send images to Claude:

```python
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode()

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            },
            {"type": "text", "text": "What's in this image?"}
        ]
    }]
)
```

## Error Handling

Always handle potential errors:

```python
from anthropic import APIError, RateLimitError

try:
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.response.headers.get('retry-after')}s")
except APIError as e:
    print(f"API error: {e.message}")
```

## Async Usage

For async applications:

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )

    print(message.content[0].text)

asyncio.run(main())
```

## Best Practices

### 1. Use Context Managers

```python
with Anthropic() as client:
    message = client.messages.create(...)
# Client automatically closed
```

### 2. Handle Errors Gracefully

```python
try:
    message = client.messages.create(...)
except APIError as e:
    # Handle error
    ...
```

### 3. Use Appropriate Models

- `claude-sonnet-4-5-20250929` - Balanced intelligence and speed
- `claude-opus-4-5-20250929` - Maximum capability
- `claude-3-5-haiku-20241022` - Fast and cost-effective

### 4. Set Reasonable Timeouts

```python
import httpx

client = Anthropic(
    timeout=httpx.Timeout(60.0)
)
```

### 5. Track Token Usage

```python
message = client.messages.create(...)
print(f"Input tokens: {message.usage.input_tokens}")
print(f"Output tokens: {message.usage.output_tokens}")
```

## Next Steps

- [Multimodal Content](./multimodal.md) - Images, documents, PDFs
- [Tool Usage](./tool-usage.md) - Function calling
- [Streaming Guide](./streaming-guide.md) - Advanced streaming
- [Error Handling](./error-handling.md) - Robust error management

## See Also

- [Messages API](../api/messages.md) - Complete API reference
- [Client Configuration](../reference/client-config.md) - Advanced configuration
