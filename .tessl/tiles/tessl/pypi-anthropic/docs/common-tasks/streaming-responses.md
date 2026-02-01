# Streaming Responses Tasks

Practical patterns for real-time streaming. For complete reference, see **[Streaming API](../api/streaming.md)** and **[Streaming Guide](../guides/streaming-guide.md)**.

## Basic Text Streaming

```python
from anthropic import Anthropic

client = Anthropic()

with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a short story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()  # New line after stream ends
```

**That's it!** The `.text_stream` property automatically filters out non-text events and gives you text deltas ready to print.

## Get Final Message After Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is 2+2?"}]
) as stream:
    # Stream the text
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Get complete message with metadata
message = stream.get_final_message()
print(f"\n\nToken usage: {message.usage.output_tokens}")
print(f"Stop reason: {message.stop_reason}")
```

## Process All Events

For more control, iterate over all stream events:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for event in stream:
        if event.type == "message_start":
            print(f"[Stream started: {event.message.id}]")

        elif event.type == "content_block_start":
            print(f"\n[Content block {event.index} started]")

        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)

        elif event.type == "content_block_stop":
            print(f"\n[Content block {event.index} stopped]")

        elif event.type == "message_delta":
            print(f"\n[Stop reason: {event.delta.stop_reason}]")
            print(f"[Tokens used: {event.usage.output_tokens}]")

        elif event.type == "message_stop":
            print("\n[Stream completed]")
```

## Stream with Tool Use

Detect when Claude wants to use tools:

```python
tools = [{
    "name": "get_weather",
    "description": "Get weather",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        },
        "required": ["location"]
    }
}]

with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"\n[Tool call: {event.content_block.name}]")

        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
            elif event.delta.type == "input_json_delta":
                print(event.delta.partial_json, end="")

message = stream.get_final_message()

# Process tool calls
for block in message.content:
    if block.type == "tool_use":
        print(f"\nTool: {block.name}")
        print(f"Input: {block.input}")
```

## Track Token Usage During Streaming

Monitor token usage in real-time:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a long essay"}]
) as stream:
    current_tokens = 0

    for event in stream:
        if event.type == "message_delta":
            current_tokens = event.usage.output_tokens
            print(f"\r[Tokens: {current_tokens}]", end="")

        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

## Async Streaming

For async applications:

```python
import asyncio
from anthropic import AsyncAnthropic

async def stream_response():
    client = AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku"}]
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)
    print()

asyncio.run(stream_response())
```

## Concurrent Async Streams

Run multiple streams in parallel:

```python
import asyncio
from anthropic import AsyncAnthropic

async def stream_question(client: AsyncAnthropic, question: str) -> str:
    """Stream a question and return final text"""
    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": question}]
    ) as stream:
        # Consume stream
        async for _ in stream:
            pass
    return stream.get_final_text()

async def main():
    client = AsyncAnthropic()

    questions = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?"
    ]

    # Run all streams concurrently
    results = await asyncio.gather(*[
        stream_question(client, q) for q in questions
    ])

    for question, answer in zip(questions, results):
        print(f"\nQ: {question}")
        print(f"A: {answer}")

asyncio.run(main())
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

        # Flush every 10 characters or at punctuation
        if len(buffer) >= 10 or text in ".!?\n":
            print(buffer, end="", flush=True)
            buffer = ""
            time.sleep(0.02)  # Smooth animation

    # Flush remaining
    if buffer:
        print(buffer, end="", flush=True)
```

## Current Message Snapshot

Get partial message during streaming:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Count to 10"}]
) as stream:
    for event in stream:
        # Access current accumulated message
        snapshot = stream.current_message_snapshot

        if snapshot.content:
            current_text = snapshot.content[0].text if snapshot.content[0].type == "text" else ""
            print(f"\rCurrent length: {len(current_text)}", end="")
```

## Error Handling in Streams

```python
from anthropic import APIError, APITimeoutError

try:
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
except APITimeoutError:
    print("\n[Stream timed out]")
except APIError as e:
    print(f"\n[Stream error: {e.message}]")
```

## Multi-Turn Conversation with Streaming

```python
conversation = []

def stream_turn(user_message: str):
    """Stream a conversation turn"""
    conversation.append({"role": "user", "content": user_message})

    print(f"\nUser: {user_message}")
    print("Claude: ", end="")

    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=conversation
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    message = stream.get_final_message()
    conversation.append({
        "role": "assistant",
        "content": message.content
    })
    print()  # New line

# Conversation
stream_turn("Hi, I'm Alice")
stream_turn("What's my name?")  # Claude remembers "Alice"
```

## Stream with System Prompt

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful Python expert. Be concise.",
    messages=[{"role": "user", "content": "Explain list comprehensions"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Stream with Temperature

```python
# Creative streaming
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=0.8,
    messages=[{"role": "user", "content": "Write a creative story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Stream Beta Features

Stream with extended thinking (beta):

```python
with client.beta.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    thinking={"type": "enabled", "budget_tokens": 1000},
    messages=[{"role": "user", "content": "Solve this complex problem: ..."}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"[Thinking: {event.delta.thinking}]", end="")
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

## Access Raw HTTP Response

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    # Access underlying HTTP response
    request_id = stream.response.headers.get("request-id")
    print(f"[Request ID: {request_id}]")

    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Interrupt Streaming

Handle keyboard interrupts gracefully:

```python
import signal
import sys

def signal_handler(sig, frame):
    print("\n[Streaming interrupted]")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a very long story"}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
except KeyboardInterrupt:
    print("\n[Streaming stopped]")
```

## Manual Stream Iteration

For advanced use cases without context manager:

```python
stream_manager = client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

stream = stream_manager.__enter__()

try:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)

    message = stream.get_final_message()
finally:
    stream_manager.__exit__(None, None, None)
```

## Streaming Best Practices

### 1. Always Use Context Managers

```python
# Good - automatic cleanup
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="")

# Bad - manual cleanup required
stream = client.messages.stream(...)
# ... easy to forget cleanup
```

### 2. Set Appropriate Timeouts

```python
import httpx

client = Anthropic(
    timeout=httpx.Timeout(120.0)  # 2 minutes for long streams
)
```

### 3. Handle Interruptions

Always handle potential interruptions gracefully for better UX.

### 4. Use Async for High Concurrency

When handling many concurrent streams, use `AsyncAnthropic` for better performance.

## See Also

- **[Streaming API Reference](../api/streaming.md)** - Complete event types and architecture
- **[Streaming Guide](../guides/streaming-guide.md)** - Advanced patterns
- **[Messages API](../api/messages.md)** - Core message creation
