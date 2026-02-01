# Streaming API Reference

Stream message responses with rich event handling and helper utilities for incremental processing.

## Stream Message

```python { .api }
def stream(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    system: str | list[TextBlockParam] = NOT_GIVEN,
    temperature: float = NOT_GIVEN,
    tools: list[ToolParam] = NOT_GIVEN,
    **kwargs
) -> MessageStreamManager:
    """
    Stream a message response with helper utilities.

    Returns a context manager that provides streaming with convenient helpers
    for text accumulation, event handling, and final message access.

    Parameters:
        model: Model identifier (required)
        messages: List of conversation messages (required)
        max_tokens: Maximum tokens to generate (required)
        system: System prompt (string or list with cache control)
        temperature: Sampling temperature 0.0-1.0
        tools: Available tools for function calling
        **kwargs: All other parameters from messages.create() are supported

    Returns:
        MessageStreamManager: Context manager that provides:
            - MessageStream for iteration
            - Helper methods for text and final message extraction

    Raises:
        Same exceptions as messages.create()

    Example:
        with client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello"}]
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
    """
    ...

async def stream(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    **kwargs
) -> AsyncMessageStreamManager:
    """
    Async version of stream.

    Same parameters and behavior as synchronous stream(), but executes
    asynchronously. Use with `async with` syntax.

    Returns:
        AsyncMessageStreamManager: Async context manager for streaming
    """
    ...
```

## MessageStream

```python { .api }
class MessageStream:
    """
    Synchronous message stream with rich event handling and helper methods.

    Provides convenient access to streaming events, text deltas, and final message
    accumulation. Use via MessageStreamManager context manager.
    """

    def __iter__(self) -> Iterator[MessageStreamEvent]:
        """
        Iterate over all stream events.

        Yields:
            MessageStreamEvent: Events including message_start, content_block_start,
                content_block_delta, content_block_stop, message_delta, message_stop
        """
        ...

    def __enter__(self) -> MessageStream:
        """Context manager entry. Returns self."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit. Closes stream and cleans up resources."""
        ...

    def get_final_message(self) -> Message:
        """
        Get final accumulated message after stream completes.

        Must be called after iterating through the stream. Returns complete Message
        object with all content blocks, usage statistics, and stop reason.

        Returns:
            Message: Complete message with all accumulated content

        Raises:
            RuntimeError: If called before stream completes
        """
        ...

    def get_final_text(self) -> str:
        """
        Get final accumulated text from all text blocks.

        Concatenates text from all TextBlock content blocks in the message.
        Useful for simple text-only responses.

        Returns:
            str: Concatenated text from all text blocks

        Raises:
            RuntimeError: If called before stream completes
        """
        ...

    @property
    def text_stream(self) -> Iterator[str]:
        """
        Iterate over text deltas only, filtering out other events.

        Convenient property for streaming text to console or UI. Automatically
        extracts text from content_block_delta events.

        Yields:
            str: Text delta strings as they arrive

        Example:
            for text in stream.text_stream:
                print(text, end="", flush=True)
        """
        ...

    @property
    def current_message_snapshot(self) -> Message:
        """
        Get current accumulated message snapshot during streaming.

        Provides partial Message object with content accumulated so far. Useful
        for showing partial results or implementing custom UI updates.

        Returns:
            Message: Partial message with current content (usage may be incomplete)
        """
        ...

class AsyncMessageStream:
    """
    Asynchronous message stream with rich event handling and helper methods.

    Async version of MessageStream. All methods are async and use async iteration.
    """

    def __aiter__(self) -> AsyncIterator[MessageStreamEvent]:
        """
        Async iterate over all stream events.

        Yields:
            MessageStreamEvent: Events as they arrive from the API
        """
        ...

    async def __aenter__(self) -> AsyncMessageStream:
        """Async context manager entry. Returns self."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit. Closes stream and cleans up resources."""
        ...

    async def get_final_message(self) -> Message:
        """
        Get final accumulated message after stream completes.

        Returns:
            Message: Complete message with all accumulated content
        """
        ...

    async def get_final_text(self) -> str:
        """
        Get final accumulated text from all text blocks.

        Returns:
            str: Concatenated text from all text blocks
        """
        ...

    @property
    def text_stream(self) -> AsyncIterator[str]:
        """
        Async iterate over text deltas only.

        Yields:
            str: Text delta strings as they arrive
        """
        ...

    @property
    def current_message_snapshot(self) -> Message:
        """
        Get current accumulated message snapshot during streaming.

        Returns:
            Message: Partial message with current content
        """
        ...
```

## MessageStreamManager

Context manager for streaming messages with helper methods.

```python { .api }
class MessageStreamManager:
    """
    Synchronous context manager for message streaming.

    Provides:
        - Context manager protocol
        - Access to MessageStream with helpers
    """
    def __enter__(self) -> MessageStream:
        """Enter context and return stream."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and cleanup."""
        ...

class AsyncMessageStreamManager:
    """
    Asynchronous context manager for message streaming.

    Provides:
        - Async context manager protocol
        - Access to AsyncMessageStream with helpers
    """
    async def __aenter__(self) -> AsyncMessageStream:
        """Enter async context and return stream."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and cleanup."""
        ...
```

## Base Stream Classes

For advanced use cases requiring raw SSE event access.

```python { .api }
class Stream(Generic[T]):
    """
    Base synchronous stream for raw SSE events.

    Provides:
        - Raw event iteration
        - Response access
    """
    def __iter__(self) -> Iterator[T]:
        """Iterate over stream items."""
        ...

    def __enter__(self) -> Stream[T]:
        """Context manager entry."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        ...

    @property
    def response(self) -> httpx.Response:
        """Access raw HTTP response."""
        ...

class AsyncStream(Generic[T]):
    """
    Base asynchronous stream for raw SSE events.

    Provides:
        - Async raw event iteration
        - Response access
    """
    def __aiter__(self) -> AsyncIterator[T]:
        """Async iterate over stream items."""
        ...

    async def __aenter__(self) -> AsyncStream[T]:
        """Async context manager entry."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        ...

    @property
    def response(self) -> httpx.Response:
        """Access raw HTTP response."""
        ...
```

## Stream Events

```python { .api }
MessageStreamEvent = Union[
    MessageStartEvent,         # Stream started
    MessageDeltaEvent,        # Usage or stop_reason updated
    MessageStopEvent,         # Stream completed
    ContentBlockStartEvent,   # New content block begins
    ContentBlockDeltaEvent,   # Content delta received
    ContentBlockStopEvent,    # Content block completed
]
```

### Message Lifecycle Events

```python { .api }
class MessageStartEvent(BaseModel):
    """
    Stream started with initial message metadata.

    First event in every stream. Contains message skeleton with empty content.

    Attributes:
        type: Always "message_start"
        message: Initial Message object with id, role, model, but empty content
    """
    type: Literal["message_start"]
    message: Message

class MessageDeltaEvent(BaseModel):
    """
    Message metadata updated (stop_reason or usage).

    Sent near end of stream when stop_reason is determined or final usage
    statistics are available.

    Attributes:
        type: Always "message_delta"
        delta: Changed message fields (stop_reason, stop_sequence)
        usage: Updated token usage (output_tokens)
    """
    type: Literal["message_delta"]
    delta: MessageDelta
    usage: MessageDeltaUsage

class MessageDelta(BaseModel):
    """
    Changed message fields in MessageDeltaEvent.

    Attributes:
        stop_reason: Why generation stopped - "end_turn", "max_tokens",
            "stop_sequence", or "tool_use"
        stop_sequence: Stop sequence that triggered completion (if applicable)
    """
    stop_reason: StopReason | None
    stop_sequence: str | None

class MessageDeltaUsage(BaseModel):
    """
    Token usage update in MessageDeltaEvent.

    Attributes:
        output_tokens: Total output tokens generated so far
    """
    output_tokens: int

class MessageStopEvent(BaseModel):
    """
    Stream completed successfully.

    Final event in every successful stream. After this event, stream is closed
    and final message is available via get_final_message().

    Attributes:
        type: Always "message_stop"
    """
    type: Literal["message_stop"]
```

### Content Block Events

```python { .api }
class ContentBlockStartEvent(BaseModel):
    """
    New content block started in response.

    Sent when Claude begins generating a new content block (text or tool_use).
    Contains initial empty block structure.

    Attributes:
        type: Always "content_block_start"
        index: Zero-based index of this content block in message.content list
        content_block: Initial ContentBlock (TextBlock or ToolUseBlock) with
            empty/default values
    """
    type: Literal["content_block_start"]
    index: int
    content_block: ContentBlock

class ContentBlockDeltaEvent(BaseModel):
    """
    Content block received incremental update.

    Most frequent event type. Contains incremental content (text deltas or
    JSON deltas for tool inputs).

    Attributes:
        type: Always "content_block_delta"
        index: Zero-based index of content block being updated
        delta: Delta content - TextDelta for text blocks, InputJSONDelta for
            tool_use blocks
    """
    type: Literal["content_block_delta"]
    index: int
    delta: ContentBlockDelta

ContentBlockDelta = Union[TextDelta, InputJSONDelta]

class TextDelta(BaseModel):
    """
    Text content delta for TextBlock.

    Attributes:
        type: Always "text_delta"
        text: Incremental text to append to current text block
    """
    type: Literal["text_delta"]
    text: str

class InputJSONDelta(BaseModel):
    """
    Tool input JSON delta for ToolUseBlock.

    Attributes:
        type: Always "input_json_delta"
        partial_json: Incremental JSON string to append. May be incomplete JSON
            until block completes.
    """
    type: Literal["input_json_delta"]
    partial_json: str

class ContentBlockStopEvent(BaseModel):
    """
    Content block completed.

    Sent when a content block finishes. After this event, the content block
    at the given index is complete.

    Attributes:
        type: Always "content_block_stop"
        index: Zero-based index of completed content block
    """
    type: Literal["content_block_stop"]
    index: int
```

### Raw Stream Events

For advanced use cases requiring access to raw SSE events before parsing.

```python { .api }
RawMessageStreamEvent = Union[
    RawMessageStartEvent,
    RawMessageDeltaEvent,
    RawMessageStopEvent,
    RawContentBlockStartEvent,
    RawContentBlockDeltaEvent,
    RawContentBlockStopEvent,
]

class RawMessageStartEvent(BaseModel):
    """Raw message start event from SSE."""
    type: Literal["message_start"]
    message: Message

class RawMessageDeltaEvent(BaseModel):
    """Raw message delta event from SSE."""
    type: Literal["message_delta"]
    delta: dict[str, Any]
    usage: MessageDeltaUsage

class RawMessageStopEvent(BaseModel):
    """Raw message stop event from SSE."""
    type: Literal["message_stop"]

class RawContentBlockStartEvent(BaseModel):
    """Raw content block start from SSE."""
    type: Literal["content_block_start"]
    index: int
    content_block: dict[str, Any]

class RawContentBlockDeltaEvent(BaseModel):
    """Raw content block delta from SSE."""
    type: Literal["content_block_delta"]
    index: int
    delta: dict[str, Any]

class RawContentBlockStopEvent(BaseModel):
    """Raw content block stop from SSE."""
    type: Literal["content_block_stop"]
    index: int
```

## Quick Examples

### Basic Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a short story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()
```

### Stream All Events

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for event in stream:
        if event.type == "message_start":
            print(f"Message started: {event.message.id}")
        elif event.type == "content_block_start":
            print(f"Content block {event.index} started")
        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
        elif event.type == "content_block_stop":
            print(f"\nContent block {event.index} stopped")
        elif event.type == "message_delta":
            print(f"Stop reason: {event.delta.stop_reason}")
        elif event.type == "message_stop":
            print("Message stopped")
```

### Get Final Message

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is 2+2?"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

message = stream.get_final_message()
print(f"\nTotal tokens: {message.usage.output_tokens}")
```

### Stream with Tool Use

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[
        {
            "name": "get_weather",
            "description": "Get weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"],
            },
        }
    ],
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ],
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"Tool call: {event.content_block.name}")
        elif event.type == "content_block_delta":
            if event.delta.type == "input_json_delta":
                print(event.delta.partial_json, end="")

message = stream.get_final_message()

# Process tool calls
for block in message.content:
    if block.type == "tool_use":
        print(f"Tool: {block.name}")
        print(f"Input: {block.input}")
```

### Async Streaming

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

### Get Final Text Only

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    # Consume stream
    for _ in stream:
        pass

# Get accumulated text
text = stream.get_final_text()
print(text)
```

### Stream with Current Snapshot

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Count to 10"}]
) as stream:
    for event in stream:
        # Get current accumulated message
        current = stream.current_message_snapshot
        if current.content:
            print(f"Current text length: {len(current.content[0].text)}")
```

### Async Event Processing

```python
import asyncio
from anthropic import AsyncAnthropic

async def stream_with_events():
    client = AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    ) as stream:
        async for event in stream:
            print(f"Event: {event.type}")

asyncio.run(stream_with_events())
```

### Error Handling in Streams

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
    print(f"Stream error: {e}")
```

### Manual Stream Iteration

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
finally:
    stream_manager.__exit__(None, None, None)
```

### Streaming with Temperature

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=0.8,
    messages=[{"role": "user", "content": "Write a creative story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Stream Multi-Turn Conversation

```python
conversation = [
    {"role": "user", "content": "Hi, I'm Alice"},
]

with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=conversation,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

    message = stream.get_final_message()

# Add to conversation
conversation.append({
    "role": "assistant",
    "content": message.content,
})
conversation.append({
    "role": "user",
    "content": "What's my name?",
})

# Continue streaming
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=conversation,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Access Raw HTTP Response

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    # Access underlying HTTP response
    print(f"Request ID: {stream.response.headers.get('request-id')}")

    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Concurrent Async Streams

```python
async def stream_multiple():
    client = AsyncAnthropic()

    async def stream_one(prompt: str):
        async with client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            text = await stream.get_final_text()
            return text

    results = await asyncio.gather(
        stream_one("What is 2+2?"),
        stream_one("What is the capital of France?"),
        stream_one("What is Python?"),
    )

    for result in results:
        print(result)
        print("---")

asyncio.run(stream_multiple())
```

### Track Token Usage During Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a long essay"}]
) as stream:
    for event in stream:
        if event.type == "message_delta":
            print(f"\nTokens so far: {event.usage.output_tokens}")
        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

## See Also

- [Messages API](./messages.md) - Core message creation
- [Streaming Guide](../guides/streaming-guide.md) - Advanced streaming patterns
- [Type System](../reference/types.md) - Complete type definitions
