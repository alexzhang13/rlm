# Messages API Reference

The Messages API is the primary interface for conversational interactions with Claude.

## Create Message

```python { .api }
def create(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    system: str | list[TextBlockParam] = NOT_GIVEN,
    metadata: MetadataParam = NOT_GIVEN,
    stop_sequences: list[str] = NOT_GIVEN,
    stream: bool = False,
    temperature: float = NOT_GIVEN,
    top_p: float = NOT_GIVEN,
    top_k: int = NOT_GIVEN,
    tools: list[ToolParam] = NOT_GIVEN,
    tool_choice: ToolChoice = NOT_GIVEN,
    service_tier: Literal["auto", "standard_only"] = NOT_GIVEN,
    thinking: ThinkingConfigParam = NOT_GIVEN,
) -> Message:
    """
    Create a message with Claude.

    Parameters:
        model: Model identifier (required). Examples: "claude-sonnet-4-5-20250929",
            "claude-opus-4-5-20250929"
        messages: List of conversation messages alternating between "user" and "assistant"
            roles (required). Must start with user message.
        max_tokens: Maximum number of tokens to generate (required). Must be positive integer.
        system: System prompt to guide Claude's behavior. Can be string or list of text blocks
            with cache control. Use for setting persona, instructions, or context.
        metadata: Request metadata containing user_id for tracking and abuse prevention.
        stop_sequences: List of strings that will stop generation when encountered.
            Up to 4 sequences allowed.
        stream: Enable streaming responses. If true, use stream() method instead for
            better streaming helpers.
        temperature: Sampling temperature 0.0-1.0 (default: 1.0). Lower values = more
            deterministic, higher values = more creative.
        top_p: Nucleus sampling parameter 0.0-1.0. Cumulative probability threshold
            for token selection.
        top_k: Top-k sampling parameter. Only sample from top K most likely tokens.
        tools: List of tools Claude can use. Enables function calling capabilities.
        tool_choice: Control how Claude selects tools. Options: "auto" (default), "any"
            (force tool use), "none" (disable tools), or specific tool name.
        service_tier: Service tier selection. "auto" (default) or "standard_only" for
            guaranteed standard capacity.
        thinking: Extended thinking configuration (beta). Enables enhanced reasoning with
            budget control.

    Returns:
        Message: Complete message response from Claude containing:
            - id: Unique message identifier
            - content: List of text and/or tool_use blocks
            - role: Always "assistant"
            - stop_reason: Why generation stopped
            - usage: Token usage statistics
            - model: Model that generated response

    Raises:
        BadRequestError: Invalid request parameters (e.g., empty messages, invalid model)
        AuthenticationError: Invalid or missing API key
        PermissionDeniedError: API key lacks required permissions
        RateLimitError: Rate limit exceeded. Check retry-after header.
        RequestTooLargeError: Request payload exceeds size limits
        InternalServerError: Anthropic server error. Safe to retry.
        OverloadedError: Service temporarily overloaded. Retry with backoff.
    """
    ...

async def create(...) -> Message:
    """
    Async version of create.

    Same parameters and returns as synchronous create(), but executes asynchronously.
    """
    ...
```

## Stream Message

```python { .api }
def stream(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    **kwargs
) -> MessageStreamManager:
    """
    Stream a message response with helper utilities.

    Provides a context manager that handles streaming with convenient helpers
    for text accumulation, final message access, and event handling.

    Parameters:
        model: Model identifier (required)
        messages: List of conversation messages (required)
        max_tokens: Maximum tokens to generate (required)
        **kwargs: All other parameters from create() method supported

    Returns:
        MessageStreamManager: Context manager that yields MessageStreamEvent objects.
            Provides helpers:
            - .text_stream: Iterator of text deltas only
            - .get_final_message(): Get complete Message after stream ends
            - .get_final_text(): Get accumulated text after stream ends
            - .current_message_snapshot: Current state during streaming

    Raises:
        Same exceptions as create() method

    Example:
        with client.messages.stream(...) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
    """
    ...

def stream(...) -> AsyncMessageStreamManager:
    """
    Async version of stream.

    Same parameters and returns as synchronous stream(), but executes asynchronously.
    Use with `async with` syntax.
    """
    ...
```

## Count Tokens

```python { .api }
def count_tokens(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    system: str | list[TextBlockParam] = NOT_GIVEN,
    tools: list[ToolParam] = NOT_GIVEN,
    tool_choice: ToolChoice = NOT_GIVEN,
    thinking: ThinkingConfigParam = NOT_GIVEN,
) -> MessageTokensCount:
    """
    Count input tokens without creating a message.

    Useful for estimating costs before making API calls or checking if
    input fits within model's context window.

    Parameters:
        model: Model identifier (required). Token counts vary by model.
        messages: List of conversation messages to count (required)
        system: System prompt to include in count
        tools: Tools to include in count
        tool_choice: Tool choice configuration to include in count
        thinking: Thinking configuration to include in count

    Returns:
        MessageTokensCount: Object containing:
            - input_tokens: Total number of input tokens

    Raises:
        BadRequestError: Invalid request parameters
        AuthenticationError: Invalid or missing API key
        RateLimitError: Rate limit exceeded

    Note:
        Token count is exact for billing purposes. Includes all overhead
        from system prompt, tools, and message formatting.
    """
    ...

async def count_tokens(...) -> MessageTokensCount:
    """
    Async version of count_tokens.

    Same parameters and returns as synchronous count_tokens(), but executes asynchronously.
    """
    ...
```

## Response Types

### Message

```python { .api }
class Message(BaseModel):
    """
    Complete message response from Claude.

    Attributes:
        id: Unique message identifier (e.g., "msg_01XYZ...")
        type: Always "message"
        role: Always "assistant" for Claude's responses
        content: List of content blocks (text, tool_use) in response
        model: Model identifier used for generation
        stop_reason: Reason generation stopped:
            - "end_turn": Natural completion point
            - "max_tokens": Hit max_tokens limit
            - "stop_sequence": Hit custom stop sequence
            - "tool_use": Model wants to use a tool
        stop_sequence: Specific stop sequence that triggered completion (if applicable)
        usage: Token usage statistics for billing and tracking
    """
    id: str
    type: Literal["message"]
    role: Literal["assistant"]
    content: list[ContentBlock]  # TextBlock | ToolUseBlock
    model: str
    stop_reason: StopReason | None
    stop_sequence: str | None
    usage: Usage
```

### ContentBlock

```python { .api }
ContentBlock = Union[TextBlock, ToolUseBlock]

class TextBlock(BaseModel):
    """
    Text content block in response.

    Attributes:
        type: Always "text"
        text: The text content generated by Claude
    """
    type: Literal["text"]
    text: str

class ToolUseBlock(BaseModel):
    """
    Tool invocation request from Claude.

    Attributes:
        type: Always "tool_use"
        id: Unique identifier for this tool call (use in tool_result)
        name: Name of tool Claude wants to invoke
        input: Tool input parameters as dict matching tool's input_schema
    """
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
```

### Usage

```python { .api }
class Usage(BaseModel):
    """
    Token usage statistics for billing and optimization.

    Attributes:
        input_tokens: Number of tokens in the input (prompt, system, tools)
        output_tokens: Number of tokens generated in response
        cache_creation_input_tokens: Tokens used to create new cache entries
            (charged at cache creation rate)
        cache_read_input_tokens: Tokens read from cache (charged at reduced rate)
    """
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int | None
    cache_read_input_tokens: int | None
```

### Stop Reasons

```python { .api }
StopReason = Literal[
    "end_turn",        # Natural completion - Claude finished responding
    "max_tokens",      # Hit max_tokens limit - response may be incomplete
    "stop_sequence",   # Hit custom stop sequence - check stop_sequence field
    "tool_use",        # Model wants to use a tool - check content for ToolUseBlock
]
```

## Request Types

### MessageParam

```python { .api }
class MessageParam(TypedDict):
    """
    User or assistant message in conversation.

    Fields:
        role: Message sender - "user" for input, "assistant" for Claude's responses
        content: Message content - string for simple text, or list of content blocks
            for multimodal (text, images, documents) or tool-related content
    """
    role: Literal["user", "assistant"]
    content: str | list[ContentBlockParam]
```

### ContentBlockParam

```python { .api }
ContentBlockParam = Union[
    TextBlockParam,
    ImageBlockParam,
    DocumentBlockParam,
    ToolUseBlockParam,
    ToolResultBlockParam,
]

class TextBlockParam(TypedDict):
    """
    Text content in user or assistant message.

    Fields:
        type: Always "text"
        text: The text content
        cache_control: Optional prompt caching configuration. Use {"type": "ephemeral"}
            to cache this content block for subsequent requests
    """
    type: Literal["text"]
    text: str
    cache_control: NotRequired[CacheControlEphemeral]

class ImageBlockParam(TypedDict):
    """
    Image content in user message for vision capabilities.

    Fields:
        type: Always "image"
        source: Image source - base64-encoded data or URL
        cache_control: Optional prompt caching for image
    """
    type: Literal["image"]
    source: Base64ImageSource | URLImageSource
    cache_control: NotRequired[CacheControlEphemeral]

class DocumentBlockParam(TypedDict):
    """
    Document content (PDF or text) in user message.

    Fields:
        type: Always "document"
        source: Document source - base64-encoded PDF/text or URL
        cache_control: Optional prompt caching for document
    """
    type: Literal["document"]
    source: Base64PDFSource | URLPDFSource | PlainTextSource
    cache_control: NotRequired[CacheControlEphemeral]

class ToolUseBlockParam(TypedDict):
    """
    Tool invocation in assistant message (when echoing Claude's tool request).

    Fields:
        type: Always "tool_use"
        id: Tool call identifier from Claude's response
        name: Tool name that was invoked
        input: Tool input parameters as dict
        cache_control: Optional prompt caching
    """
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
    cache_control: NotRequired[CacheControlEphemeral]

class ToolResultBlockParam(TypedDict):
    """
    Tool execution result in user message.

    Fields:
        type: Always "tool_result"
        tool_use_id: ID from Claude's ToolUseBlock that this result corresponds to
        content: Tool result - string for simple output, or list of text/image blocks
            for structured results
        is_error: Set to True if tool execution failed, False otherwise (default: False)
        cache_control: Optional prompt caching
    """
    type: Literal["tool_result"]
    tool_use_id: str
    content: NotRequired[str | list[TextBlockParam | ImageBlockParam]]
    is_error: NotRequired[bool]
    cache_control: NotRequired[CacheControlEphemeral]
```

### Source Types

```python { .api }
class Base64ImageSource(TypedDict):
    """
    Base64-encoded image source for vision input.

    Fields:
        type: Always "base64"
        media_type: Image MIME type - jpeg, png, gif, or webp
        data: Base64-encoded image bytes (without data URL prefix)
    """
    type: Literal["base64"]
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    data: str

class URLImageSource(TypedDict):
    """
    Image from URL for vision input.

    Fields:
        type: Always "url"
        url: Publicly accessible image URL (must be accessible to Anthropic servers)
    """
    type: Literal["url"]
    url: str

class Base64PDFSource(TypedDict):
    """
    Base64-encoded PDF document source.

    Fields:
        type: Always "base64"
        media_type: Always "application/pdf"
        data: Base64-encoded PDF bytes (without data URL prefix)
    """
    type: Literal["base64"]
    media_type: Literal["application/pdf"]
    data: str

class URLPDFSource(TypedDict):
    """
    PDF from URL for document processing.

    Fields:
        type: Always "url"
        media_type: Always "application/pdf"
        url: Publicly accessible PDF URL
    """
    type: Literal["url"]
    media_type: Literal["application/pdf"]
    url: str

class PlainTextSource(TypedDict):
    """
    Plain text document source.

    Fields:
        type: Always "text"
        media_type: Always "text/plain"
        data: Plain text content
    """
    type: Literal["text"]
    media_type: Literal["text/plain"]
    data: str
```

### Configuration Types

```python { .api }
class MetadataParam(TypedDict, total=False):
    """
    Request metadata for tracking and compliance.

    Fields:
        user_id: End-user identifier for tracking, rate limiting, and abuse prevention.
            Should be unique per end-user, not per API key.
    """
    user_id: str

class CacheControlEphemeral(TypedDict):
    """
    Prompt caching configuration for reducing costs on repeated content.

    Fields:
        type: Always "ephemeral" - content cached temporarily (~5 minutes)
    """
    type: Literal["ephemeral"]

class MessageTokensCount(BaseModel):
    """
    Token count response from count_tokens().

    Attributes:
        input_tokens: Exact number of input tokens for billing estimation
    """
    input_tokens: int
```

## Quick Examples

### Basic Text

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)
print(message.content[0].text)
```

### System Prompt

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)
```

### Multi-Turn Conversation

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "My name is Alice."},
        {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
        {"role": "user", "content": "What's my name?"}
    ]
)
```

### Image Analysis

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

### Document Processing

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_base64_data
                }
            },
            {"type": "text", "text": "Summarize this document."}
        ]
    }]
)
```

### Temperature Control

```python
# Deterministic (temperature = 0)
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=0.0,
    messages=[{"role": "user", "content": "What is 2+2?"}]
)

# Creative (temperature = 1)
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=1.0,
    messages=[{"role": "user", "content": "Write a creative story."}]
)
```

### Prompt Caching

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert on Shakespeare.",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[
        {"role": "user", "content": "Tell me about Hamlet."}
    ]
)

# Check cache usage
print(f"Cache creation: {message.usage.cache_creation_input_tokens}")
print(f"Cache read: {message.usage.cache_read_input_tokens}")
```

### Token Counting

```python
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-5-20250929",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)
print(f"Input tokens: {token_count.input_tokens}")
```

### Metadata Tracking

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    metadata={"user_id": "user_12345"},
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Raw Response Access

Access raw HTTP responses for headers, status codes, and debugging.

```python { .api }
# Access raw response wrapper
client.messages.with_raw_response.create(...)  # Returns APIResponse[Message]
client.messages.with_streaming_response.stream(...)  # Returns APIResponse with streaming

# Async versions
async_client.messages.with_raw_response.create(...)
async_client.messages.with_streaming_response.stream(...)
```

### Raw Response Example

```python
# Get raw HTTP response
response = client.messages.with_raw_response.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)

# Access HTTP response details
print(f"Status: {response.http_response.status_code}")
print(f"Headers: {response.http_response.headers}")
print(f"Request ID: {response.http_response.headers.get('request-id')}")

# Access parsed message object
message = response.parse()
print(message.content[0].text)
```

### Streaming Raw Response

```python
# Get raw streaming response
with client.messages.with_streaming_response.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
) as response:
    # Access response object before streaming
    print(f"Status: {response.http_response.status_code}")

    # Stream normally
    for text in response.text_stream:
        print(text, end="", flush=True)
```

### Check Rate Limit Headers

```python
response = client.messages.with_raw_response.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)

headers = response.http_response.headers
print(f"Rate limit: {headers.get('anthropic-ratelimit-requests-limit')}")
print(f"Remaining: {headers.get('anthropic-ratelimit-requests-remaining')}")
print(f"Reset: {headers.get('anthropic-ratelimit-requests-reset')}")
```

## See Also

- [Streaming API](./streaming.md) - Real-time response streaming
- [Tool Use API](./tools.md) - Function calling capabilities
- [Multimodal Guide](../guides/multimodal.md) - Images and documents
- [Type System](../reference/types.md) - Complete type definitions
