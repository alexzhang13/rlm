# Responses API

Create responses with advanced tool support including computer use, file search, and code patching. The Responses API provides an enhanced interface for complex assistant interactions.

## Capabilities

### Create Response

Generate a response with advanced tools and capabilities.

```python { .api }
def create(
    self,
    *,
    model: str,
    input: dict | list[dict],
    instructions: str | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    reasoning_effort: str | Omit = omit,
    store: bool | Omit = omit,
    stream: bool | Omit = omit,
    temperature: float | Omit = omit,
    tool_choice: str | dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    top_p: float | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Response:
    """
    Create a response with advanced tools.

    Args:
        model: Model ID to use.

        input: Input message(s). Can be:
            - Single message: {"role": "user", "content": "..."}
            - List of messages: [{"role": "user", "content": "..."}, ...]

        instructions: System instructions for the response.

        metadata: Key-value pairs (max 16).

        parallel_tool_calls: Enable parallel tool execution.

        reasoning_effort: Reasoning level for reasoning models.

        store: If true, store response for later retrieval.

        stream: Enable streaming response.

        temperature: Sampling temperature.

        tool_choice: Tool choice configuration.

        tools: Available tools. Options:
            - {"type": "function", "function": {...}}: Custom functions
            - {"type": "file_search"}: File search
            - {"type": "computer_use"}: Computer use (screen/keyboard/mouse)
            - {"type": "apply_patch"}: Code patching

        top_p: Nucleus sampling.

    Returns:
        Response: Generated response with tool results.
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic response
response = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Hello!"}
)

print(response.output[0].content)

# With file search
response = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Find information about Python."},
    tools=[{"type": "file_search"}]
)

# With computer use (beta)
response = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Click the button."},
    tools=[{
        "type": "computer_use",
        "display_width_px": 1920,
        "display_height_px": 1080
    }]
)

# With code patching
response = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Fix the bug in this code."},
    tools=[{"type": "apply_patch"}]
)

# Multi-turn conversation
messages = [
    {"role": "user", "content": "What is 2+2?"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "What about 3+3?"}
]

response = client.responses.create(
    model="gpt-4",
    input=messages
)

# Streaming response
stream = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Tell me a story."},
    stream=True
)

for chunk in stream:
    if chunk.delta:
        print(chunk.delta.content, end="", flush=True)
```

### Retrieve Response

Get a stored response by ID.

```python { .api }
def retrieve(
    self,
    response_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Response:
    """Retrieve a stored response."""
```

### Delete Response

Delete a stored response by ID.

```python { .api }
def delete(
    self,
    response_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> None:
    """
    Delete a response with the given ID.

    Args:
        response_id: The ID of the response to delete.
    """
```

### Cancel Response

Cancel an in-progress response.

```python { .api }
def cancel(
    self,
    response_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Response:
    """
    Cancel an in-progress response.

    Only responses created with the `background` parameter set to `true` can be cancelled.

    Args:
        response_id: The ID of the response to cancel.
    """
```

### Stream Response

Stream a response in real-time, either creating a new response or streaming an existing one.

```python { .api }
def stream(
    self,
    *,
    response_id: str = omit,
    input: str | dict | list[dict] | None = omit,
    model: str | None = omit,
    background: bool | None = omit,
    text_format: type = omit,
    tools: list[dict] | None = omit,
    conversation: dict | None = omit,
    include: list[str] | None = omit,
    instructions: str | None = omit,
    max_output_tokens: int | None = omit,
    max_tool_calls: int | None = omit,
    metadata: dict[str, str] | None = omit,
    parallel_tool_calls: bool | None = omit,
    previous_response_id: str | None = omit,
    prompt: dict | None = omit,
    prompt_cache_key: str | None = omit,
    prompt_cache_retention: Literal["in-memory", "24h"] | None = omit,
    reasoning: dict | None = omit,
    safety_identifier: str | None = omit,
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = omit,
    store: bool | None = omit,
    stream_options: dict | None = omit,
    temperature: float | None = omit,
    text: dict | None = omit,
    tool_choice: str | dict | None = omit,
    top_logprobs: int | None = omit,
    top_p: float | None = omit,
    truncation: Literal["auto", "disabled"] | None = omit,
    user: str | None = omit,
    starting_after: int | None = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ResponseStreamManager:
    """
    Stream a response. Can either create a new response or stream an existing one.

    Args:
        response_id: If provided, stream an existing response. Otherwise, create a new response.
        input: Input message(s) for creating a new response.
        model: Model ID to use for creating a new response.
        text_format: Parse streaming text into a specific format type.
        starting_after: For streaming existing responses, start streaming after this item index.

    Returns:
        ResponseStreamManager: Streaming response manager for iterating over chunks.
    """
```

### Parse Response

Create a response with structured output parsing using a format type.

```python { .api }
def parse(
    self,
    *,
    text_format: type,
    background: bool | None = omit,
    conversation: dict | None = omit,
    include: list[str] | None = omit,
    input: str | dict | list[dict] | None = omit,
    instructions: str | None = omit,
    max_output_tokens: int | None = omit,
    max_tool_calls: int | None = omit,
    metadata: dict[str, str] | None = omit,
    model: str | None = omit,
    parallel_tool_calls: bool | None = omit,
    previous_response_id: str | None = omit,
    prompt: dict | None = omit,
    prompt_cache_key: str | None = omit,
    prompt_cache_retention: Literal["in-memory", "24h"] | None = omit,
    reasoning: dict | None = omit,
    safety_identifier: str | None = omit,
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = omit,
    store: bool | None = omit,
    stream: Literal[False] | Literal[True] | None = omit,
    stream_options: dict | None = omit,
    temperature: float | None = omit,
    text: dict | None = omit,
    tool_choice: str | dict | None = omit,
    tools: list[dict] | None = omit,
    top_logprobs: int | None = omit,
    top_p: float | None = omit,
    truncation: Literal["auto", "disabled"] | None = omit,
    user: str | None = omit,
    verbosity: Literal["low", "medium", "high"] | None = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ParsedResponse:
    """
    Create a response with structured output parsing.

    Args:
        text_format: A type (Pydantic model or similar) to parse the response into.
        input: Input message(s).
        model: Model ID to use.

    Returns:
        ParsedResponse: Response with parsed structured output.
    """
```

### Input Items

List input items for a response.

```python { .api }
def input_items.list(
    self,
    response_id: str,
    *,
    after: str | None = omit,
    include: list[str] | None = omit,
    limit: int | None = omit,
    order: Literal["asc", "desc"] | None = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[ResponseItem]:
    """
    Returns a list of input items for a given response.

    Args:
        response_id: The ID of the response.
        after: An item ID to list items after, used in pagination.
        include: Additional fields to include in the response.
        limit: Limit on number of objects (1-100, default 20).
        order: Order to return items ('asc' or 'desc', default 'desc').

    Returns:
        Paginated list of response input items.
    """
```

### Input Tokens

Count input tokens for a potential response.

```python { .api }
def input_tokens.count(
    self,
    *,
    conversation: dict | None = omit,
    input: str | list[dict] | None = omit,
    instructions: str | None = omit,
    model: str | None = omit,
    parallel_tool_calls: bool | None = omit,
    previous_response_id: str | None = omit,
    reasoning: dict | None = omit,
    text: dict | None = omit,
    tool_choice: dict | None = omit,
    tools: list[dict] | None = omit,
    truncation: Literal["auto", "disabled"] | None = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> InputTokenCountResponse:
    """
    Get input token counts for a potential response without making the request.

    Args:
        conversation: The conversation context.
        input: Text, image, or file inputs.
        instructions: System instructions.
        model: Model ID.
        tools: Available tools.

    Returns:
        InputTokenCountResponse: Token count information.
    """
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Response(BaseModel):
    """Response object."""
    id: str
    created_at: int
    model: str
    object: Literal["response"]
    output: list[ResponseContent]
    status: Literal["in_progress", "completed", "failed", "cancelled"]
    tool_calls: list[ToolCall] | None
    usage: Usage | None

class ResponseContent(BaseModel):
    """Response content."""
    role: Literal["assistant"]
    content: str
    type: Literal["text"]

class ToolCall(BaseModel):
    """Tool invocation."""
    id: str
    type: str
    function: dict | None
    computer_use: dict | None
    apply_patch: dict | None

class Usage(BaseModel):
    """Token usage."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
```

## Tool Types

### Computer Use

```python
{
    "type": "computer_use",
    "display_width_px": 1920,
    "display_height_px": 1080,
    "display_number": 1  # Optional, for multi-monitor
}
```

Enables the model to interact with a computer:
- View screenshots
- Control mouse (move, click)
- Type on keyboard
- Execute commands

### Apply Patch

```python
{
    "type": "apply_patch"
}
```

Enables code modification:
- Generate code patches
- Apply changes to files
- Fix bugs
- Refactor code

### File Search

```python
{
    "type": "file_search"
}
```

Search uploaded files and documents.

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Use for complex multi-step tasks
response = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Analyze this codebase and fix all bugs."},
    tools=[
        {"type": "file_search"},
        {"type": "apply_patch"}
    ]
)

# 2. Handle tool calls
if response.tool_calls:
    for tool_call in response.tool_calls:
        if tool_call.type == "apply_patch":
            # Review and apply patch
            patch = tool_call.apply_patch
            print(f"Patch: {patch}")

# 3. Store important responses
response = client.responses.create(
    model="gpt-4",
    input={"role": "user", "content": "Important analysis"},
    store=True
)

# Retrieve later
stored = client.responses.retrieve(response.id)
```

### Compact Conversation

Compact a conversation to reduce its size while maintaining context and essential information. This optimization utility helps manage token usage and costs for long conversations.

```python { .api }
def compact(
    self,
    *,
    model: str,
    input: str | list[dict] | Omit = omit,
    instructions: str | Omit = omit,
    previous_response_id: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> CompactedResponse:
    """
    Compact conversation to optimize token usage.

    This method compresses conversation history while preserving essential
    context, enabling more efficient multi-turn conversations by reducing
    token consumption.

    Args:
        model: Model ID used to generate the response. OpenAI offers a
            wide range of models with different capabilities and price points.

        input: Text, image, or file inputs to the model. Can be a string
            or list of input item dictionaries.

        instructions: System (developer) message for the model's context.
            When used with previous_response_id, previous instructions
            are not carried over.

        previous_response_id: Unique ID of the previous response to create
            multi-turn conversations. Cannot be used with conversation parameter.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        CompactedResponse: Compacted response with reduced token count.
    """
```

Usage example:

```python
# Compact a long conversation
compacted = client.responses.compact(
    model="gpt-4",
    input="Summarize the key points from our previous discussion",
    previous_response_id="resp-abc123"
)

print(f"Original tokens: {compacted.original_token_count}")
print(f"Compacted tokens: {compacted.token_count}")
print(f"Reduction: {compacted.reduction_percentage}%")
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_response():
    client = AsyncOpenAI()

    response = await client.responses.create(
        model="gpt-4",
        input={"role": "user", "content": "Hello!"}
    )

    return response.output[0].content

content = asyncio.run(create_response())
```
