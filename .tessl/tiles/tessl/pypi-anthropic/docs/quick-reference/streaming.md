# Streaming API - Quick Reference

Compact API signatures for streaming. For examples and patterns, see **[Streaming API Reference](../api/streaming.md)**.

## stream()

```python { .api }
def stream(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    **kwargs  # All messages.create() parameters supported
) -> MessageStreamManager
```

**Async:** `async def stream(...) -> AsyncMessageStreamManager`

## MessageStreamManager

```python { .api }
class MessageStreamManager:
    def __enter__(self) -> MessageStream
    def __exit__(self, exc_type, exc_val, exc_tb) -> None
```

## MessageStream

```python { .api }
class MessageStream:
    def __iter__(self) -> Iterator[MessageStreamEvent]

    @property
    def text_stream(self) -> Iterator[str]:
        """Iterate over text deltas only"""
        ...

    @property
    def current_message_snapshot(self) -> Message:
        """Current accumulated message during streaming"""
        ...

    def get_final_message(self) -> Message:
        """Complete message after stream ends"""
        ...

    def get_final_text(self) -> str:
        """Accumulated text after stream ends"""
        ...
```

**Async:** `AsyncMessageStream` with `async` versions of all methods

## Stream Events

```python { .api }
MessageStreamEvent = Union[
    MessageStartEvent,       # Stream started
    MessageDeltaEvent,       # Usage/stop_reason updated
    MessageStopEvent,        # Stream completed
    ContentBlockStartEvent,  # New content block
    ContentBlockDeltaEvent,  # Content delta
    ContentBlockStopEvent,   # Block completed
]

class MessageStartEvent(BaseModel):
    type: Literal["message_start"]
    message: Message  # Initial skeleton

class ContentBlockDeltaEvent(BaseModel):
    type: Literal["content_block_delta"]
    index: int
    delta: ContentBlockDelta  # TextDelta | InputJSONDelta

class TextDelta(BaseModel):
    type: Literal["text_delta"]
    text: str  # Incremental text to append

class MessageDeltaEvent(BaseModel):
    type: Literal["message_delta"]
    delta: MessageDelta  # stop_reason, stop_sequence
    usage: MessageDeltaUsage  # output_tokens

class MessageStopEvent(BaseModel):
    type: Literal["message_stop"]
```

## Common Patterns

```python
# Text streaming
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Event processing
with client.messages.stream(...) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="")

# Get final message
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="")
message = stream.get_final_message()
```

## See Also

- **[Complete Streaming Documentation](../api/streaming.md)** - All event types and patterns
- **[Streaming Tasks Guide](../common-tasks/streaming-responses.md)** - Task-oriented examples
- **[Streaming Guide](../guides/streaming-guide.md)** - Advanced patterns
