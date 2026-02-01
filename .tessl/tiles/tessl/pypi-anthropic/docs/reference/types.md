# Type System Reference

Comprehensive type definitions for all request parameters and response objects using Pydantic models and TypedDict. All types are fully typed for static analysis and IDE support.

## Core Message Types

### Message

```python { .api }
class Message(BaseModel):
    """
    Complete message response from Claude.

    Attributes:
        id: Unique message identifier (starts with "msg_")
        type: Always "message"
        role: Always "assistant"
        content: List of content blocks (text, tool_use, etc.)
        model: Model identifier used for generation
        stop_reason: Why generation stopped
        stop_sequence: Stop sequence that triggered completion (if any)
        usage: Token usage statistics
    """
    id: str
    type: Literal["message"]
    role: Literal["assistant"]
    content: list[ContentBlock]
    model: str
    stop_reason: StopReason | None
    stop_sequence: str | None
    usage: Usage
```

### MessageParam

```python { .api }
class MessageParam(TypedDict):
    """
    User or assistant message in conversation.

    Fields:
        role: "user" or "assistant"
        content: String or list of content blocks
    """
    role: Literal["user", "assistant"]
    content: str | list[ContentBlockParam]
```

### ContentBlock (Response)

```python { .api }
ContentBlock = Union[TextBlock, ToolUseBlock]

class TextBlock(BaseModel):
    """
    Text content in assistant response.

    Attributes:
        type: Always "text"
        text: The text content
    """
    type: Literal["text"]
    text: str

class ToolUseBlock(BaseModel):
    """
    Tool invocation in assistant response.

    Attributes:
        type: Always "tool_use"
        id: Unique tool call identifier
        name: Tool name
        input: Tool input parameters as dict
    """
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
```

### ContentBlockParam (Request)

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
    Text content in message.

    Fields:
        type: Always "text"
        text: The text content
        cache_control: Optional cache control
    """
    type: Literal["text"]
    text: str
    cache_control: NotRequired[CacheControlEphemeral]

class ImageBlockParam(TypedDict):
    """
    Image content in message.

    Fields:
        type: Always "image"
        source: Image source (base64 or URL)
        cache_control: Optional cache control
    """
    type: Literal["image"]
    source: Base64ImageSource | URLImageSource
    cache_control: NotRequired[CacheControlEphemeral]

class DocumentBlockParam(TypedDict):
    """
    Document content (PDF, text) in message.

    Fields:
        type: Always "document"
        source: Document source (base64 or URL)
        cache_control: Optional cache control
    """
    type: Literal["document"]
    source: Base64PDFSource | URLPDFSource | PlainTextSource
    cache_control: NotRequired[CacheControlEphemeral]

class ToolUseBlockParam(TypedDict):
    """
    Tool invocation in assistant message (for conversation history).

    Fields:
        type: Always "tool_use"
        id: Tool call identifier
        name: Tool name
        input: Tool input parameters
        cache_control: Optional cache control
    """
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
    cache_control: NotRequired[CacheControlEphemeral]

class ToolResultBlockParam(TypedDict):
    """
    Tool result in user message.

    Fields:
        type: Always "tool_result"
        tool_use_id: ID of tool invocation this is result for
        content: String or list of content blocks
        is_error: Whether result represents an error
        cache_control: Optional cache control
    """
    type: Literal["tool_result"]
    tool_use_id: str
    content: NotRequired[str | list[TextBlockParam | ImageBlockParam]]
    is_error: NotRequired[bool]
    cache_control: NotRequired[CacheControlEphemeral]
```

## Content Source Types

### Image Sources

```python { .api }
class Base64ImageSource(TypedDict):
    """
    Base64-encoded image.

    Fields:
        type: Always "base64"
        media_type: MIME type (jpeg, png, gif, webp)
        data: Base64-encoded image data (without data URL prefix)
    """
    type: Literal["base64"]
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    data: str

class URLImageSource(TypedDict):
    """
    Image from URL.

    Fields:
        type: Always "url"
        url: Image URL (must be publicly accessible)
    """
    type: Literal["url"]
    url: str
```

### Document Sources

```python { .api }
class Base64PDFSource(TypedDict):
    """
    Base64-encoded PDF document.

    Fields:
        type: Always "base64"
        media_type: Always "application/pdf"
        data: Base64-encoded PDF data
    """
    type: Literal["base64"]
    media_type: Literal["application/pdf"]
    data: str

class URLPDFSource(TypedDict):
    """
    PDF document from URL.

    Fields:
        type: Always "url"
        media_type: Always "application/pdf"
        url: PDF URL
    """
    type: Literal["url"]
    media_type: Literal["application/pdf"]
    url: str

class PlainTextSource(TypedDict):
    """
    Plain text document.

    Fields:
        type: Always "text"
        media_type: Always "text/plain"
        data: Plain text content
    """
    type: Literal["text"]
    media_type: Literal["text/plain"]
    data: str
```

## Tool Types

### Tool Definition

```python { .api }
class Tool(BaseModel):
    """
    Tool definition in response.

    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON Schema for parameters
    """
    name: str
    description: str
    input_schema: dict[str, Any]

class ToolParam(TypedDict):
    """
    Tool definition in request.

    Fields:
        name: Tool name (alphanumeric + underscores)
        description: What the tool does
        input_schema: JSON Schema for tool parameters
        cache_control: Optional cache control
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    cache_control: NotRequired[CacheControlEphemeral]
```

### Tool Choice

```python { .api }
ToolChoice = Union[
    ToolChoiceAuto,
    ToolChoiceAny,
    ToolChoiceNone,
    ToolChoiceTool,
]

class ToolChoiceAuto(TypedDict):
    """
    Let Claude decide whether to use tools (default).

    Fields:
        type: Always "auto"
        disable_parallel_tool_use: Disable parallel tool calls
    """
    type: Literal["auto"]
    disable_parallel_tool_use: NotRequired[bool]

class ToolChoiceAny(TypedDict):
    """
    Force Claude to use at least one tool.

    Fields:
        type: Always "any"
        disable_parallel_tool_use: Disable parallel tool calls
    """
    type: Literal["any"]
    disable_parallel_tool_use: NotRequired[bool]

class ToolChoiceNone(TypedDict):
    """
    Disable all tool use.

    Fields:
        type: Always "none"
    """
    type: Literal["none"]

class ToolChoiceTool(TypedDict):
    """
    Force Claude to use specific tool.

    Fields:
        type: Always "tool"
        name: Tool name to use
        disable_parallel_tool_use: Disable parallel tool calls
    """
    type: Literal["tool"]
    name: str
    disable_parallel_tool_use: NotRequired[bool]
```

## Configuration Types

### Usage

```python { .api }
class Usage(BaseModel):
    """
    Token usage statistics.

    Attributes:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cache_creation_input_tokens: Tokens used to create cache (if using prompt caching)
        cache_read_input_tokens: Tokens read from cache (if using prompt caching)
    """
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
```

### Metadata

```python { .api }
class Metadata(BaseModel):
    """
    Response metadata.

    Attributes:
        user_id: End-user identifier (if provided)
    """
    user_id: str | None = None

class MetadataParam(TypedDict, total=False):
    """
    Request metadata for tracking and compliance.

    Fields:
        user_id: End-user identifier for tracking and abuse prevention
    """
    user_id: str
```

### Cache Control

```python { .api }
class CacheControlEphemeral(TypedDict):
    """
    Ephemeral cache control for prompt caching.

    Fields:
        type: Always "ephemeral"
    """
    type: Literal["ephemeral"]
```

### Thinking Configuration

```python { .api }
ThinkingConfigParam = Union[ThinkingConfigEnabled, ThinkingConfigDisabled]

class ThinkingConfigEnabled(TypedDict):
    """
    Enable extended thinking for enhanced reasoning.

    Fields:
        type: Always "enabled"
    """
    type: Literal["enabled"]

class ThinkingConfigDisabled(TypedDict):
    """
    Disable extended thinking.

    Fields:
        type: Always "disabled"
    """
    type: Literal["disabled"]
```

### Stop Reason

```python { .api }
StopReason = Literal[
    "end_turn",        # Natural completion
    "max_tokens",      # Hit max_tokens limit
    "stop_sequence",   # Hit custom stop sequence
    "tool_use",        # Model wants to use a tool
]
```

## Token Counting Types

```python { .api }
class MessageTokensCount(BaseModel):
    """
    Token count response.

    Attributes:
        input_tokens: Number of input tokens
    """
    input_tokens: int
```

## Batch Types

### Batch

```python { .api }
class MessageBatch(BaseModel):
    """
    Batch metadata and status.

    Attributes:
        id: Unique batch identifier (starts with "msgbatch_")
        type: Always "message_batch"
        processing_status: Current processing status
        request_counts: Counts by result type
        ended_at: When batch completed (ISO 8601)
        created_at: When batch was created (ISO 8601)
        expires_at: When batch results will expire (ISO 8601)
        cancel_initiated_at: When cancellation was initiated (ISO 8601)
        results_url: URL to download results JSONL
    """
    id: str
    type: Literal["message_batch"]
    processing_status: Literal["in_progress", "canceling", "ended"]
    request_counts: MessageBatchRequestCounts
    ended_at: str | None
    created_at: str
    expires_at: str
    cancel_initiated_at: str | None
    results_url: str | None

class MessageBatchRequestCounts(BaseModel):
    """
    Request count statistics in batch.

    Attributes:
        processing: Requests currently processing
        succeeded: Successful requests
        errored: Failed requests
        canceled: Canceled requests
        expired: Expired requests
    """
    processing: int
    succeeded: int
    errored: int
    canceled: int
    expired: int

class DeletedMessageBatch(BaseModel):
    """
    Deleted batch confirmation.

    Attributes:
        id: Batch identifier that was deleted
        type: Always "message_batch_deleted"
    """
    id: str
    type: Literal["message_batch_deleted"]
```

### Batch Request/Response

```python { .api }
class MessageBatchIndividualRequest(TypedDict):
    """
    Individual request in batch.

    Fields:
        custom_id: Client-provided unique identifier
        params: Message creation parameters
    """
    custom_id: str
    params: MessageCreateParams

class MessageBatchIndividualResponse(BaseModel):
    """
    Individual response in batch results.

    Attributes:
        custom_id: Client-provided identifier from request
        result: Result object (success/error/canceled/expired)
    """
    custom_id: str
    result: MessageBatchResult

MessageBatchResult = Union[
    MessageBatchSucceededResult,
    MessageBatchErroredResult,
    MessageBatchCanceledResult,
    MessageBatchExpiredResult,
]

class MessageBatchSucceededResult(BaseModel):
    """
    Successful batch result.

    Attributes:
        type: Always "succeeded"
        message: The message response
    """
    type: Literal["succeeded"]
    message: Message

class MessageBatchErroredResult(BaseModel):
    """
    Failed batch result.

    Attributes:
        type: Always "errored"
        error: Error details
    """
    type: Literal["errored"]
    error: ErrorObject

class MessageBatchCanceledResult(BaseModel):
    """
    Canceled batch result.

    Attributes:
        type: Always "canceled"
    """
    type: Literal["canceled"]

class MessageBatchExpiredResult(BaseModel):
    """
    Expired batch result.

    Attributes:
        type: Always "expired"
    """
    type: Literal["expired"]
```

## Model Types

```python { .api }
class ModelInfo(BaseModel):
    """
    Model information and capabilities.

    Attributes:
        id: Model identifier
        type: Always "model"
        display_name: Human-readable model name
        created_at: When model was created (ISO 8601)
    """
    id: str
    type: Literal["model"]
    display_name: str
    created_at: str

Model = Literal[
    "claude-opus-4-5-20250929",
    "claude-sonnet-4-5-20250929",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    # Additional models...
]
```

## Error Types

```python { .api }
class ErrorObject(BaseModel):
    """
    Error object in API responses.

    Attributes:
        type: Error type identifier
        message: Human-readable error message
    """
    type: str
    message: str

class ErrorResponse(BaseModel):
    """
    Error response wrapper.

    Attributes:
        type: Always "error"
        error: Error details
    """
    type: Literal["error"]
    error: APIErrorObject

class APIErrorObject(BaseModel):
    """
    API error object.

    Attributes:
        type: Error type
        message: Error message
    """
    type: str
    message: str
```

## Stream Event Types

### Message Stream Events

```python { .api }
MessageStreamEvent = Union[
    MessageStartEvent,
    MessageDeltaEvent,
    MessageStopEvent,
    ContentBlockStartEvent,
    ContentBlockDeltaEvent,
    ContentBlockStopEvent,
]

class MessageStartEvent(BaseModel):
    """
    Stream started with initial message.

    Attributes:
        type: Always "message_start"
        message: Initial message with empty content
    """
    type: Literal["message_start"]
    message: Message

class MessageDeltaEvent(BaseModel):
    """
    Message metadata changed.

    Attributes:
        type: Always "message_delta"
        delta: Changed fields
        usage: Token usage update
    """
    type: Literal["message_delta"]
    delta: MessageDelta
    usage: MessageDeltaUsage

class MessageDelta(BaseModel):
    """
    Message field changes.

    Attributes:
        stop_reason: Updated stop reason
        stop_sequence: Stop sequence that triggered
    """
    stop_reason: StopReason | None
    stop_sequence: str | None

class MessageDeltaUsage(BaseModel):
    """
    Token usage in stream delta.

    Attributes:
        output_tokens: Output tokens generated so far
    """
    output_tokens: int

class MessageStopEvent(BaseModel):
    """
    Stream completed.

    Attributes:
        type: Always "message_stop"
    """
    type: Literal["message_stop"]
```

### Content Block Stream Events

```python { .api }
class ContentBlockStartEvent(BaseModel):
    """
    New content block started.

    Attributes:
        type: Always "content_block_start"
        index: Content block index
        content_block: Initial content block
    """
    type: Literal["content_block_start"]
    index: int
    content_block: ContentBlock

class ContentBlockDeltaEvent(BaseModel):
    """
    Content block received delta.

    Attributes:
        type: Always "content_block_delta"
        index: Content block index
        delta: Delta content
    """
    type: Literal["content_block_delta"]
    index: int
    delta: ContentBlockDelta

ContentBlockDelta = Union[TextDelta, InputJSONDelta]

class TextDelta(BaseModel):
    """
    Text content delta.

    Attributes:
        type: Always "text_delta"
        text: Incremental text
    """
    type: Literal["text_delta"]
    text: str

class InputJSONDelta(BaseModel):
    """
    Tool input JSON delta.

    Attributes:
        type: Always "input_json_delta"
        partial_json: Incremental JSON string
    """
    type: Literal["input_json_delta"]
    partial_json: str

class ContentBlockStopEvent(BaseModel):
    """
    Content block completed.

    Attributes:
        type: Always "content_block_stop"
        index: Content block index
    """
    type: Literal["content_block_stop"]
    index: int
```

### Raw Stream Events

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
    """
    Raw message start event from SSE.

    Attributes:
        type: Always "message_start"
        message: Initial message
    """
    type: Literal["message_start"]
    message: Message

class RawMessageDeltaEvent(BaseModel):
    """
    Raw message delta event from SSE.

    Attributes:
        type: Always "message_delta"
        delta: Changed fields as dict
        usage: Token usage update
    """
    type: Literal["message_delta"]
    delta: dict[str, Any]
    usage: MessageDeltaUsage

class RawMessageStopEvent(BaseModel):
    """
    Raw message stop event from SSE.

    Attributes:
        type: Always "message_stop"
    """
    type: Literal["message_stop"]

class RawContentBlockStartEvent(BaseModel):
    """
    Raw content block start from SSE.

    Attributes:
        type: Always "content_block_start"
        index: Content block index
        content_block: Initial content block as dict
    """
    type: Literal["content_block_start"]
    index: int
    content_block: dict[str, Any]

class RawContentBlockDeltaEvent(BaseModel):
    """
    Raw content block delta from SSE.

    Attributes:
        type: Always "content_block_delta"
        index: Content block index
        delta: Delta content as dict
    """
    type: Literal["content_block_delta"]
    index: int
    delta: dict[str, Any]

class RawContentBlockStopEvent(BaseModel):
    """
    Raw content block stop from SSE.

    Attributes:
        type: Always "content_block_stop"
        index: Content block index
    """
    type: Literal["content_block_stop"]
    index: int
```

## Pagination Types

### Synchronous Pagination

```python { .api }
class SyncPage(Generic[T]):
    """
    Synchronous ID-based pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items across pages automatically."""
        ...

    def __getitem__(self, index: int) -> T:
        """Get item by index in current page."""
        ...

    def has_next_page(self) -> bool:
        """Check if another page exists."""
        ...

    def next_page_info(self) -> dict[str, Any]:
        """Get pagination parameters for next page."""
        ...

    def get_next_page(self) -> SyncPage[T]:
        """Fetch next page."""
        ...

class SyncTokenPage(Generic[T]):
    """
    Synchronous token-based pagination.

    Uses continuation tokens instead of IDs.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __iter__(self) -> Iterator[T]: ...
    def has_next_page(self) -> bool: ...
    def next_page_info(self) -> dict[str, Any]: ...
    def get_next_page(self) -> SyncTokenPage[T]: ...

class SyncPageCursor(Generic[T]):
    """
    Synchronous cursor-based pagination.

    Uses cursors for pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __iter__(self) -> Iterator[T]: ...
    def has_next_page(self) -> bool: ...
    def next_page_info(self) -> dict[str, Any]: ...
    def get_next_page(self) -> SyncPageCursor[T]: ...
```

### Asynchronous Pagination

```python { .api }
class AsyncPage(Generic[T]):
    """
    Asynchronous ID-based pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __aiter__(self) -> AsyncIterator[T]:
        """Async iterate over all items across pages."""
        ...

    def __getitem__(self, index: int) -> T:
        """Get item by index in current page."""
        ...

    async def has_next_page(self) -> bool:
        """Check if another page exists."""
        ...

    async def next_page_info(self) -> dict[str, Any]:
        """Get pagination parameters for next page."""
        ...

    async def get_next_page(self) -> AsyncPage[T]:
        """Fetch next page."""
        ...

class AsyncTokenPage(Generic[T]):
    """
    Asynchronous token-based pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __aiter__(self) -> AsyncIterator[T]: ...
    async def has_next_page(self) -> bool: ...
    async def next_page_info(self) -> dict[str, Any]: ...
    async def get_next_page(self) -> AsyncTokenPage[T]: ...

class AsyncPageCursor(Generic[T]):
    """
    Asynchronous cursor-based pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __aiter__(self) -> AsyncIterator[T]: ...
    async def has_next_page(self) -> bool: ...
    async def next_page_info(self) -> dict[str, Any]: ...
    async def get_next_page(self) -> AsyncPageCursor[T]: ...
```

## Type Helpers

```python { .api }
class NOT_GIVEN:
    """
    Sentinel value for omitted optional parameters.

    Used to distinguish between explicitly passing None vs not passing a parameter.
    This allows the SDK to differentiate between:
    - Parameter not provided (NOT_GIVEN)
    - Parameter explicitly set to None (None)
    """
    ...

NotGiven = type[NOT_GIVEN]

def not_given() -> NOT_GIVEN:
    """Return NOT_GIVEN sentinel."""
    ...

class Omit:
    """
    Type for omitted fields.

    Used internally for partial updates where some fields should be omitted.
    """
    ...

def omit() -> Omit:
    """Return Omit sentinel."""
    ...

NoneType = type[None]
```

## Request Parameter Types

```python { .api }
class MessageCreateParams(TypedDict):
    """
    Complete parameters for message creation.

    Fields:
        model: Model identifier (required)
        messages: Conversation messages (required)
        max_tokens: Maximum tokens to generate (required)
        system: System prompt (optional)
        metadata: Request metadata (optional)
        stop_sequences: Stop sequences (optional)
        stream: Enable streaming (optional)
        temperature: Sampling temperature 0.0-1.0 (optional)
        top_p: Nucleus sampling (optional)
        top_k: Top-k sampling (optional)
        tools: Available tools (optional)
        tool_choice: Tool selection control (optional)
        service_tier: Service tier selection (optional)
        thinking: Extended thinking configuration (optional)
    """
    model: str
    messages: list[MessageParam]
    max_tokens: int
    system: NotRequired[str | list[TextBlockParam]]
    metadata: NotRequired[MetadataParam]
    stop_sequences: NotRequired[list[str]]
    stream: NotRequired[bool]
    temperature: NotRequired[float]
    top_p: NotRequired[float]
    top_k: NotRequired[int]
    tools: NotRequired[list[ToolParam]]
    tool_choice: NotRequired[ToolChoice]
    service_tier: NotRequired[Literal["auto", "standard_only"]]
    thinking: NotRequired[ThinkingConfigParam]

class RequestOptions(TypedDict, total=False):
    """
    Per-request options.

    Fields:
        headers: Custom headers
        max_retries: Maximum retry attempts
        timeout: Request timeout
        query: Custom query parameters
    """
    headers: dict[str, str]
    max_retries: int
    timeout: float | httpx.Timeout
    query: dict[str, object]
```

## Response Wrapper Types

```python { .api }
class APIResponse(Generic[T]):
    """
    HTTP response wrapper with parsed data.

    Attributes:
        data: Parsed response data
        headers: Response headers
        status_code: HTTP status code
        request: Original request
    """
    data: T
    headers: dict[str, str]
    status_code: int
    request: httpx.Request

    def parse(self) -> T:
        """
        Get parsed response data.

        Returns:
            Parsed response object of type T
        """
        ...

class AsyncAPIResponse(Generic[T]):
    """
    Async HTTP response wrapper.

    Attributes:
        data: Parsed response data
        headers: Response headers
        status_code: HTTP status code
        request: Original request
    """
    data: T
    headers: dict[str, str]
    status_code: int
    request: httpx.Request

    async def parse(self) -> T:
        """
        Get parsed response data asynchronously.

        Returns:
            Parsed response object of type T
        """
        ...
```

## Base Model

```python { .api }
class BaseModel(pydantic.BaseModel):
    """
    Base Pydantic model for all response types.

    Provides:
        - JSON serialization/deserialization
        - Type validation
        - Field access
        - Model copying
        - Schema generation
    """
    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        """
        Convert model to dictionary.

        Parameters:
            mode: Serialization mode ("json" or "python")
            include: Fields to include
            exclude: Fields to exclude
            by_alias: Use field aliases
            exclude_unset: Exclude fields that weren't set
            exclude_defaults: Exclude fields with default values
            exclude_none: Exclude fields with None values

        Returns:
            Dictionary representation of model
        """
        ...

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> str:
        """
        Convert model to JSON string.

        Parameters:
            indent: JSON indentation
            include: Fields to include
            exclude: Fields to exclude
            by_alias: Use field aliases
            exclude_unset: Exclude fields that weren't set
            exclude_defaults: Exclude fields with default values
            exclude_none: Exclude fields with None values

        Returns:
            JSON string representation
        """
        ...

    @classmethod
    def model_validate(cls, obj: Any) -> Self:
        """
        Validate and parse object into model.

        Parameters:
            obj: Object to validate (dict, model instance, etc.)

        Returns:
            Validated model instance

        Raises:
            ValidationError: If validation fails
        """
        ...

    @classmethod
    def model_validate_json(cls, json_data: str | bytes) -> Self:
        """
        Validate and parse JSON into model.

        Parameters:
            json_data: JSON string or bytes

        Returns:
            Validated model instance

        Raises:
            ValidationError: If validation fails
        """
        ...

    def model_copy(
        self,
        *,
        update: dict[str, Any] | None = None,
        deep: bool = False,
    ) -> Self:
        """
        Create copy of model with optional updates.

        Parameters:
            update: Dictionary of fields to update
            deep: Whether to make deep copy

        Returns:
            New model instance
        """
        ...

    @classmethod
    def model_json_schema(
        cls,
        *,
        by_alias: bool = True,
        ref_template: str = "#/$defs/{model}",
    ) -> dict[str, Any]:
        """
        Generate JSON Schema for model.

        Parameters:
            by_alias: Use field aliases in schema
            ref_template: Template for $ref values

        Returns:
            JSON Schema dictionary
        """
        ...
```

## SDK Infrastructure Types

### HTTP and Client Types

```python { .api }
from typing import Union
import httpx

Timeout = Union[float, httpx.Timeout, None]
"""
Timeout specification for HTTP requests.

Can be:
- float: Total timeout in seconds
- httpx.Timeout: Granular timeout with connect/read/write/pool settings
- None: No timeout (not recommended)
"""

Transport = Union[httpx.HTTPTransport, httpx.AsyncHTTPTransport]
"""HTTP transport for custom connection pooling and proxying."""

ProxiesTypes = Union[str, httpx.Proxy, dict[str, Union[str, httpx.Proxy]]]
"""
Proxy configuration types.

Can be:
- str: Proxy URL
- httpx.Proxy: Configured proxy object
- dict: Mapping of protocols to proxy URLs
"""

FileTypes = tuple[str, bytes, str]
"""
File tuple for upload operations.

Format: (filename, content, mime_type)

Example:
    ("document.pdf", pdf_bytes, "application/pdf")
"""
```

### Sentinel Types

```python { .api }
class NotGivenType:
    """Singleton type for NOT_GIVEN sentinel value."""
    ...

NotGiven = NotGivenType
"""
Sentinel value indicating a parameter was not provided.

Used to distinguish between None (explicitly passed) and
parameter not passed at all.

Example:
    def create(*, param: str | None | NotGiven = NOT_GIVEN):
        if param is NOT_GIVEN:
            # Parameter not provided
        elif param is None:
            # Parameter explicitly set to None
"""

NOT_GIVEN: NotGiven
"""Singleton instance of NotGiven sentinel."""
```

### Response Wrapper Types

```python { .api }
from typing import Generic, TypeVar

T = TypeVar('T')

class APIResponse(Generic[T]):
    """
    Wrapper providing access to raw HTTP response and parsed data.

    Attributes:
        http_response: Raw httpx.Response object
        data: Cached parsed response data
    """
    http_response: httpx.Response

    def parse(self) -> T:
        """
        Parse and return typed response data.

        Returns:
            Parsed response object of type T
        """
        ...

class AsyncAPIResponse(Generic[T]):
    """
    Async version of APIResponse.

    Attributes:
        http_response: Raw httpx.Response object
        data: Cached parsed response data
    """
    http_response: httpx.Response

    async def parse(self) -> T:
        """
        Async parse and return typed response data.

        Returns:
            Parsed response object of type T
        """
        ...
```

### Base Model

```python { .api }
from pydantic import BaseModel as PydanticBaseModel

class BaseModel(PydanticBaseModel):
    """
    Base Pydantic model with SDK-specific configuration.

    All response types inherit from this class, providing:
    - JSON serialization via .model_dump() and .model_dump_json()
    - Type validation
    - Field aliases and exclusions
    """

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Serialize model to dictionary."""
        ...

    def model_dump_json(self, **kwargs) -> str:
        """Serialize model to JSON string."""
        ...

    @classmethod
    def model_validate(cls, obj: Any) -> Self:
        """Validate and construct model from dict."""
        ...

    @classmethod
    def model_json_schema(cls, **kwargs) -> dict[str, Any]:
        """Generate JSON Schema for model."""
        ...
```

## See Also

- [Messages API](../api/messages.md) - Core message types in use
- [Streaming API](../api/streaming.md) - Stream event types in use
- [Tool Use API](../api/tools.md) - Tool types in use
- [Batches API](../api/batches.md) - Batch types in use
- [Error Handling](./errors.md) - Error types and exception hierarchy
- [Client Configuration](./client-config.md) - Usage of Timeout and Transport types
- [Utilities](./utilities.md) - Usage of FileTypes
