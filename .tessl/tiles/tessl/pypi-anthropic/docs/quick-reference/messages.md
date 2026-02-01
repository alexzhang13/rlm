# Messages API - Quick Reference

Compact API signatures for the Messages API. For examples and detailed documentation, see **[Messages API Reference](../api/messages.md)**.

## create()

```python { .api }
def create(
    self,
    *,
    model: str,                                        # Required: Model ID
    messages: list[MessageParam],                     # Required: Conversation messages
    max_tokens: int,                                  # Required: Max generation tokens
    system: str | list[TextBlockParam] = NOT_GIVEN,   # System prompt
    metadata: MetadataParam = NOT_GIVEN,              # Request metadata (user_id)
    stop_sequences: list[str] = NOT_GIVEN,            # Custom stop sequences (max 4)
    stream: bool = False,                             # Enable streaming (use stream() instead)
    temperature: float = NOT_GIVEN,                   # Sampling temperature 0.0-1.0
    top_p: float = NOT_GIVEN,                         # Nucleus sampling 0.0-1.0
    top_k: int = NOT_GIVEN,                           # Top-k sampling
    tools: list[ToolParam] = NOT_GIVEN,               # Available tools
    tool_choice: ToolChoice = NOT_GIVEN,              # Tool selection control
    service_tier: Literal["auto", "standard_only"] = NOT_GIVEN,  # Service tier
    thinking: ThinkingConfigParam = NOT_GIVEN,        # Extended thinking (beta)
) -> Message
```

**Async:** `async def create(...) -> Message`

**Raises:** `BadRequestError`, `AuthenticationError`, `RateLimitError`, `InternalServerError`

## stream()

```python { .api }
def stream(
    self,
    *,
    model: str,                    # Required: Model ID
    messages: list[MessageParam],  # Required: Conversation messages
    max_tokens: int,               # Required: Max generation tokens
    **kwargs                       # All create() parameters supported
) -> MessageStreamManager
```

**Returns:** Context manager with `.text_stream`, `.get_final_message()`, `.get_final_text()`

**Async:** `async def stream(...) -> AsyncMessageStreamManager`

## count_tokens()

```python { .api }
def count_tokens(
    self,
    *,
    model: str,                                        # Required: Model ID
    messages: list[MessageParam],                     # Required: Messages to count
    system: str | list[TextBlockParam] = NOT_GIVEN,   # System prompt
    tools: list[ToolParam] = NOT_GIVEN,               # Tools to include
    tool_choice: ToolChoice = NOT_GIVEN,              # Tool choice config
    thinking: ThinkingConfigParam = NOT_GIVEN,        # Thinking config
) -> MessageTokensCount
```

**Returns:** `MessageTokensCount` with `.input_tokens`

**Async:** `async def count_tokens(...) -> MessageTokensCount`

## Key Types

```python { .api }
class MessageParam(TypedDict):
    role: Literal["user", "assistant"]
    content: str | list[ContentBlockParam]

class Message(BaseModel):
    id: str
    type: Literal["message"]
    role: Literal["assistant"]
    content: list[ContentBlock]  # TextBlock | ToolUseBlock
    model: str
    stop_reason: StopReason | None
    usage: Usage

class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int | None
    cache_read_input_tokens: int | None

StopReason = Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]
```

## See Also

- **[Complete API Documentation](../api/messages.md)** - Full details with examples
- **[Basic Messaging Tasks](../common-tasks/basic-messaging.md)** - Task-oriented guide
- **[Type System Reference](../reference/types.md)** - Complete type definitions
