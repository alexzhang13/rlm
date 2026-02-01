# Streaming Guide

Advanced patterns for streaming responses from Claude.

## Basic Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()
```

## Event-Based Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for event in stream:
        if event.type == "message_start":
            print("Stream started")
        elif event.type == "content_block_start":
            print(f"\nContent block {event.index} started")
        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
        elif event.type == "message_stop":
            print("\nStream completed")
```

## Get Final Message

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is 2+2?"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Get complete message after streaming
message = stream.get_final_message()
print(f"\nTokens used: {message.usage.output_tokens}")
```

## Stream with Tool Use

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[{
        "name": "get_weather",
        "description": "Get weather",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    }],
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
            elif event.delta.type == "input_json_delta":
                print(event.delta.partial_json, end="")

message = stream.get_final_message()
```

## Async Streaming

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku"}]
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)
    print()

asyncio.run(main())
```

## Track Token Usage

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write an essay"}]
) as stream:
    tokens_used = 0

    for event in stream:
        if event.type == "message_delta":
            tokens_used = event.usage.output_tokens
            print(f"\nTokens: {tokens_used}", end="\r")
        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

## Stream with Beta Features

```python
with client.beta.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    thinking={"type": "enabled"},
    messages=[{"role": "user", "content": "Explain quantum computing"}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"[Thinking: {event.delta.thinking}]")
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

## Error Handling

```python
from anthropic import APIError

try:
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
except APIError as e:
    print(f"\nStream error: {e.message}")
```

## Buffered Streaming

Buffer output for smoother display:

```python
import time

with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    buffer = ""

    for text in stream.text_stream:
        buffer += text

        # Flush buffer every 10 characters or at punctuation
        if len(buffer) >= 10 or text in ".!?\n":
            print(buffer, end="", flush=True)
            buffer = ""
            time.sleep(0.01)  # Smooth animation

    if buffer:  # Flush remaining
        print(buffer, end="", flush=True)
```

## Best Practices

### 1. Use Context Managers

Always use `with` statement to ensure proper cleanup:

```python
with client.messages.stream(...) as stream:
    ...
# Stream automatically closed
```

### 2. Handle Interruptions

```python
import signal

def signal_handler(sig, frame):
    print("\nStream interrupted")
    stream.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

### 3. Set Appropriate Timeouts

```python
import httpx

client = Anthropic(
    timeout=httpx.Timeout(120.0)  # 2 minutes for streaming
)
```

## See Also

- [Streaming API](../api/streaming.md) - Complete API reference
- [Messages API](../api/messages.md) - Message creation
- [Beta Features](../beta/index.md) - Extended thinking streaming
