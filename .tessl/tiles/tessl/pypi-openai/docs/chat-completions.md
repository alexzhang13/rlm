# Chat Completions

Create conversational responses using OpenAI's language models with support for text, vision inputs, audio, function calling, structured outputs, and streaming. Chat completions are the primary interface for interacting with models like GPT-4 and GPT-3.5.

## Access Patterns

Chat completions are accessible via:
- `client.chat.completions` - Primary access pattern
- `client.beta.chat.completions` - Beta namespace alias (identical to `client.chat`)

## Capabilities

### Create Chat Completion

Generate a response for a chat conversation with extensive configuration options.

```python { .api }
def create(
    self,
    *,
    messages: Iterable[ChatCompletionMessageParam],
    model: str | ChatModel,
    audio: ChatCompletionAudioParam | None | Omit = omit,
    frequency_penalty: float | None | Omit = omit,
    function_call: dict | str | Omit = omit,
    functions: Iterable[dict] | Omit = omit,
    logit_bias: dict[str, int] | None | Omit = omit,
    logprobs: bool | None | Omit = omit,
    max_completion_tokens: int | None | Omit = omit,
    max_tokens: int | None | Omit = omit,
    metadata: dict[str, str] | None | Omit = omit,
    modalities: list[Literal["text", "audio"]] | None | Omit = omit,
    n: int | None | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    prediction: dict | None | Omit = omit,
    presence_penalty: float | None | Omit = omit,
    prompt_cache_key: str | Omit = omit,
    prompt_cache_retention: Literal["in-memory", "24h"] | None | Omit = omit,
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high"] | None | Omit = omit,
    response_format: completion_create_params.ResponseFormat | Omit = omit,
    safety_identifier: str | Omit = omit,
    seed: int | None | Omit = omit,
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None | Omit = omit,
    stop: str | list[str] | None | Omit = omit,
    store: bool | None | Omit = omit,
    stream: bool | Omit = omit,
    stream_options: dict | None | Omit = omit,
    temperature: float | None | Omit = omit,
    tool_choice: ChatCompletionToolChoiceOptionParam | Omit = omit,
    tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit,
    top_logprobs: int | None | Omit = omit,
    top_p: float | None | Omit = omit,
    user: str | Omit = omit,
    verbosity: Literal["low", "medium", "high"] | None | Omit = omit,
    web_search_options: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatCompletion | Stream[ChatCompletionChunk]:
    """
    Create a model response for the given chat conversation.

    Args:
        messages: List of messages comprising the conversation. Each message can be:
            - System message: {"role": "system", "content": "..."}
            - User message: {"role": "user", "content": "..."}
            - Assistant message: {"role": "assistant", "content": "..."}
            - Tool message: {"role": "tool", "content": "...", "tool_call_id": "..."}
            Supports text, images, and audio content.

        model: Model ID like "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", or "o1".
            See https://platform.openai.com/docs/models for available models.

        audio: Parameters for audio output when modalities includes "audio".
            {"voice": "alloy|echo|fable|onyx|nova|shimmer", "format": "wav|mp3|flac|opus|pcm16"}

        frequency_penalty: Number between -2.0 and 2.0. Penalizes tokens based on frequency
            in the text, reducing repetition. Default 0.

        function_call: (Deprecated, use tool_choice) Controls function calling.
            - "none": No function calls
            - "auto": Model decides
            - {"name": "function_name"}: Force specific function

        functions: (Deprecated, use tools) List of function definitions.

        logit_bias: Modify token probabilities. Maps token IDs to bias values from
            -100 to 100. Values near ±1 slightly adjust probability, ±100 ban/force tokens.

        logprobs: If true, returns log probabilities of output tokens.

        max_completion_tokens: Maximum tokens for completion including reasoning tokens.
            Preferred over max_tokens for o-series models.

        max_tokens: (Deprecated for o-series) Maximum tokens in completion.
            Use max_completion_tokens instead.

        metadata: Up to 16 key-value pairs for storing additional object information.
            Keys max 64 chars, values max 512 chars.

        modalities: Output types to generate. Options: ["text"], ["audio"], ["text", "audio"].
            Default ["text"]. Audio requires gpt-4o-audio-preview model.

        n: Number of completion choices to generate. Default 1.
            Costs scale with number of choices.

        parallel_tool_calls: Enable parallel function calling during tool use.
            Default true when tools are present.

        prediction: Static predicted output for regeneration tasks (e.g., file content).

        presence_penalty: Number between -2.0 and 2.0. Penalizes tokens based on
            presence in text, encouraging new topics. Default 0.

        prompt_cache_key: Cache identifier for optimizing similar requests.
            Replaces the user field for caching.

        prompt_cache_retention: Cache retention policy. "24h" enables extended caching
            up to 24 hours. Default "in-memory".

        reasoning_effort: Effort level for reasoning models (o-series).
            Options: "none", "minimal", "low", "medium", "high".
            - gpt-5.1: defaults to "none"
            - Other models: default "medium"
            - gpt-5-pro: only supports "high"

        response_format: Output format specification.
            - {"type": "text"}: Plain text (default)
            - {"type": "json_object"}: Valid JSON
            - {"type": "json_schema", "json_schema": {...}}: Structured Outputs

        safety_identifier: Stable user identifier (hashed) for policy violation detection.

        seed: For deterministic sampling (Beta). Same seed + parameters should return
            same result, but not guaranteed. Check system_fingerprint for changes.

        service_tier: Processing type for serving. Options: "auto", "default", "flex",
            "scale", "priority". Affects latency and pricing.

        stop: Up to 4 sequences where generation stops. Can be string or list of strings.

        store: If true, stores the completion for model distillation/evals.

        stream: If true, returns SSE stream of ChatCompletionChunk objects.
            Returns Stream[ChatCompletionChunk] instead of ChatCompletion.

        stream_options: Streaming configuration. Accepts dict with:
            - "include_usage": bool - If true, includes token usage in final chunk
            - "include_obfuscation": bool - If true (default), adds random characters
              to obfuscation field on streaming delta events to normalize payload sizes
              as mitigation for side-channel attacks. Set to false to optimize bandwidth.

        temperature: Sampling temperature between 0 and 2. Higher values (e.g., 0.8)
            make output more random, lower values (e.g., 0.2) more deterministic.
            Default 1. Alter this or top_p, not both.

        tool_choice: Controls tool/function calling.
            - "none": No tools called
            - "auto": Model decides (default when tools present)
            - "required": Model must call at least one tool
            - {"type": "function", "function": {"name": "..."}}: Force specific tool

        tools: List of tools/functions available to the model. Each tool:
            {
                "type": "function",
                "function": {
                    "name": "function_name",
                    "description": "What it does",
                    "parameters": {...}  # JSON Schema
                }
            }

        top_logprobs: Number of most likely tokens to return with logprobs (0-20).
            Requires logprobs=true.

        top_p: Nucleus sampling parameter between 0 and 1. Model considers tokens
            with top_p probability mass. E.g., 0.1 means only tokens in top 10%.
            Default 1. Alter this or temperature, not both.

        user: (Deprecated for caching, use prompt_cache_key) Unique user identifier
            for abuse monitoring.

        verbosity: Output detail level for reasoning models. Options: "low", "medium", "high".

        web_search_options: Web search configuration (if available for model).

        extra_headers: Additional HTTP headers for the request.

        extra_query: Additional query parameters for the request.

        extra_body: Additional JSON fields for the request body.

        timeout: Request timeout in seconds.

    Returns:
        ChatCompletion: If stream=False (default), returns complete response.
        Stream[ChatCompletionChunk]: If stream=True, returns streaming response.

    Raises:
        BadRequestError: Invalid parameters
        AuthenticationError: Invalid API key
        RateLimitError: Rate limit exceeded
        APIError: Other API errors
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic chat completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)
print(response.choices[0].message.content)

# With multiple messages and temperature
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a creative writer."},
        {"role": "user", "content": "Write a haiku about coding."},
    ],
    temperature=0.8,
    max_tokens=100
)

# With vision (image input)
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"}
                }
            ]
        }
    ]
)

# With function calling / tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g., San Francisco"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in Boston?"}],
    tools=tools,
    tool_choice="auto"
)

# Check if model wants to call a function
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")

# Streaming response
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story."}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# With reasoning effort (o-series models)
response = client.chat.completions.create(
    model="o1",
    messages=[
        {"role": "user", "content": "Solve this complex math problem: ..."}
    ],
    reasoning_effort="high"
)

# With structured output (JSON Schema)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "List 3 colors"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "colors_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["colors"],
                "additionalProperties": False
            }
        }
    }
)
```

### Parse with Structured Output

Create chat completion with automatic Pydantic model parsing for structured outputs.

```python { .api }
def parse(
    self,
    *,
    messages: Iterable[ChatCompletionMessageParam],
    model: str | ChatModel,
    response_format: type[ResponseFormatT] | Omit = omit,
    audio: ChatCompletionAudioParam | None | Omit = omit,
    frequency_penalty: float | None | Omit = omit,
    function_call: dict | str | Omit = omit,
    functions: Iterable[dict] | Omit = omit,
    logit_bias: dict[str, int] | None | Omit = omit,
    logprobs: bool | None | Omit = omit,
    max_completion_tokens: int | None | Omit = omit,
    max_tokens: int | None | Omit = omit,
    metadata: dict[str, str] | None | Omit = omit,
    modalities: list[Literal["text", "audio"]] | None | Omit = omit,
    n: int | None | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    prediction: dict | None | Omit = omit,
    presence_penalty: float | None | Omit = omit,
    prompt_cache_key: str | Omit = omit,
    prompt_cache_retention: Literal["in-memory", "24h"] | None | Omit = omit,
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high"] | None | Omit = omit,
    safety_identifier: str | Omit = omit,
    seed: int | None | Omit = omit,
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None | Omit = omit,
    stop: str | list[str] | None | Omit = omit,
    store: bool | None | Omit = omit,
    stream_options: dict | None | Omit = omit,
    temperature: float | None | Omit = omit,
    tool_choice: ChatCompletionToolChoiceOptionParam | Omit = omit,
    tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit,
    top_logprobs: int | None | Omit = omit,
    top_p: float | None | Omit = omit,
    user: str | Omit = omit,
    verbosity: Literal["low", "medium", "high"] | None | Omit = omit,
    web_search_options: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ParsedChatCompletion[ResponseFormatT]:
    """
    Create chat completion with automatic Pydantic model parsing.

    Converts Pydantic model to JSON schema, sends to API, and parses response
    back into the model. Also automatically parses function tool calls when
    using pydantic_function_tool() or strict mode.

    Args:
        messages: List of conversation messages.
        model: Model ID to use.
        response_format: Pydantic model class for structured output.
        (other parameters same as create method)

    Returns:
        ParsedChatCompletion[ResponseFormatT]: Completion with parsed content.
            Access via completion.choices[0].message.parsed

    Raises:
        Same as create method, plus validation errors for malformed responses.
    """
```

Usage example:

```python
from pydantic import BaseModel
from openai import OpenAI

# Define response structure
class Step(BaseModel):
    explanation: str
    output: str

class MathResponse(BaseModel):
    steps: list[Step]
    final_answer: str

client = OpenAI()

# Parse returns strongly-typed response
completion = client.chat.completions.parse(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "Solve: 8x + 31 = 2"}
    ],
    response_format=MathResponse
)

# Access parsed content with full type safety
message = completion.choices[0].message
if message.parsed:
    for step in message.parsed.steps:
        print(f"{step.explanation}: {step.output}")
    print(f"Answer: {message.parsed.final_answer}")

# With function tools using pydantic
from openai import pydantic_function_tool

class WeatherParams(BaseModel):
    location: str
    unit: Literal["celsius", "fahrenheit"] = "celsius"

tool = pydantic_function_tool(
    WeatherParams,
    name="get_weather",
    description="Get current weather"
)

completion = client.chat.completions.parse(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=[tool],
    response_format=MathResponse  # For assistant's final response
)

# Tool calls are automatically parsed
if completion.choices[0].message.tool_calls:
    for call in completion.choices[0].message.tool_calls:
        if call.type == "function":
            # call.function.parsed_arguments is a WeatherParams instance
            params = call.function.parsed_arguments
            print(f"Location: {params.location}, Unit: {params.unit}")
```

### Stored Chat Completions

Store, retrieve, update, and delete chat completions for persistent conversation management.

```python { .api }
def retrieve(
    self,
    completion_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatCompletion:
    """
    Retrieve a previously stored chat completion by its ID.

    Args:
        completion_id: The ID of the stored chat completion to retrieve.

    Returns:
        ChatCompletion: The stored completion object.
    """

def update(
    self,
    completion_id: str,
    *,
    metadata: dict[str, str] | None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatCompletion:
    """
    Update metadata for a stored chat completion.

    Args:
        completion_id: The ID of the stored completion to update.
        metadata: Updated metadata key-value pairs (max 16 pairs). Required parameter.

    Returns:
        ChatCompletion: The updated completion object.
    """

def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    metadata: dict[str, str] | None | Omit = omit,
    model: str | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[ChatCompletion]:
    """
    List stored chat completions with cursor-based pagination.

    Args:
        after: Cursor for pagination (ID of object to start after).
        limit: Maximum number of completions to return (default 20, max 100).
        metadata: Filter by metadata key-value pairs. Only returns completions with matching metadata.
        model: Filter by model. Only returns completions generated with the specified model.
        order: Sort order: "asc" (oldest first) or "desc" (newest first).

    Returns:
        SyncCursorPage[ChatCompletion]: Paginated list of completions.
    """

def delete(
    self,
    completion_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatCompletionDeleted:
    """
    Delete a stored chat completion.

    Args:
        completion_id: The ID of the stored completion to delete.

    Returns:
        ChatCompletionDeleted: Confirmation of deletion with deleted=True.
    """
```

Access stored completion messages:

```python { .api }
# Via client.chat.completions.messages.list()
def list(
    self,
    completion_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[ChatCompletionStoreMessage]:
    """
    List messages from a stored chat completion.

    Args:
        completion_id: The ID of the stored completion.
        after: Cursor for pagination.
        limit: Maximum number of messages to return.
        order: Sort order: "asc" or "desc".

    Returns:
        SyncCursorPage[ChatCompletionStoreMessage]: Paginated list of messages.
    """
```

#### Usage Example

```python
from openai import OpenAI

client = OpenAI()

# Create a chat completion with store=True
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me about Python"}],
    store=True,
    metadata={"user_id": "user123", "session": "abc"}
)

completion_id = response.id
print(f"Stored completion: {completion_id}")

# Retrieve the stored completion later
stored = client.chat.completions.retrieve(completion_id)
print(stored.choices[0].message.content)

# Update metadata
updated = client.chat.completions.update(
    completion_id,
    metadata={"user_id": "user123", "session": "abc", "reviewed": "true"}
)

# List all stored completions
page = client.chat.completions.list(limit=10, order="desc")
for completion in page.data:
    print(f"{completion.id}: {completion.created}")

# List messages from a specific completion
messages_page = client.chat.completions.messages.list(completion_id)
for message in messages_page.data:
    print(f"{message.role}: {message.content}")

# Delete when no longer needed
deleted = client.chat.completions.delete(completion_id)
print(f"Deleted: {deleted.deleted}")
```

### Stream Chat Completions

Wrapper over `create(stream=True)` that provides a more granular event API and automatic accumulation of deltas. Requires use within a context manager.

```python { .api }
def stream(
    self,
    *,
    messages: Iterable[ChatCompletionMessageParam],
    model: str | ChatModel,
    audio: ChatCompletionAudioParam | None | Omit = omit,
    frequency_penalty: float | None | Omit = omit,
    function_call: dict | str | Omit = omit,
    functions: Iterable[dict] | Omit = omit,
    logit_bias: dict[str, int] | None | Omit = omit,
    logprobs: bool | None | Omit = omit,
    max_completion_tokens: int | None | Omit = omit,
    max_tokens: int | None | Omit = omit,
    metadata: dict[str, str] | None | Omit = omit,
    modalities: list[Literal["text", "audio"]] | None | Omit = omit,
    n: int | None | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    prediction: dict | None | Omit = omit,
    presence_penalty: float | None | Omit = omit,
    prompt_cache_key: str | Omit = omit,
    prompt_cache_retention: Literal["in-memory", "24h"] | None | Omit = omit,
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high"] | None | Omit = omit,
    response_format: completion_create_params.ResponseFormat | Omit = omit,
    safety_identifier: str | Omit = omit,
    seed: int | None | Omit = omit,
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None | Omit = omit,
    stop: str | list[str] | None | Omit = omit,
    store: bool | None | Omit = omit,
    stream_options: dict | None | Omit = omit,
    temperature: float | None | Omit = omit,
    tool_choice: ChatCompletionToolChoiceOptionParam | Omit = omit,
    tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit,
    top_logprobs: int | None | Omit = omit,
    top_p: float | None | Omit = omit,
    user: str | Omit = omit,
    verbosity: Literal["low", "medium", "high"] | None | Omit = omit,
    web_search_options: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatCompletionStreamManager:
    """
    Streaming wrapper with granular event API and automatic delta accumulation.

    Unlike create(stream=True), this method requires a context manager to prevent
    resource leaks. Yields detailed events including content.delta, content.done,
    and provides accumulated snapshots.

    Args:
        Same parameters as create() method.

    Returns:
        ChatCompletionStreamManager: Context manager yielding stream events.
    """
```

**Usage Example:**

```python
from openai import OpenAI

client = OpenAI()

# Must use within context manager
with client.chat.completions.stream(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
) as stream:
    for event in stream:
        if event.type == "content.delta":
            print(event.delta, flush=True, end="")
        elif event.type == "content.done":
            print(f"\nFinal content: {event.content}")

# Access accumulated result after streaming
print(f"Model: {stream.response.model}")
print(f"Total tokens: {stream.response.usage.total_tokens}")
```

### Streaming with Helpers

Advanced streaming with context managers for easier handling.

```python
from openai import OpenAI

client = OpenAI()

# Using stream() method with context manager
with client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Count to 5"}],
    stream=True
) as stream:
    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

# Using stream context manager explicitly
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a joke"}],
    stream=True
)

# Access streaming response
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

# Stream with usage information
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
    stream_options={"include_usage": True}
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
    # Usage included in final chunk
    if hasattr(chunk, 'usage') and chunk.usage:
        print(f"\nTokens used: {chunk.usage.total_tokens}")
```

## Types

```python { .api }
from typing import Literal, TypeVar, Generic
from pydantic import BaseModel
from openai.types.chat import (
    ChatCompletionToolUnionParam,
    ChatCompletionToolChoiceOptionParam,
    completion_create_params,
)

# Message types
ChatCompletionMessageParam = dict[str, Any]  # Union of message types

class ChatCompletionSystemMessageParam(TypedDict):
    role: Literal["system"]
    content: str
    name: NotRequired[str]

class ChatCompletionUserMessageParam(TypedDict):
    role: Literal["user"]
    content: str | list[dict]  # Text or multimodal content
    name: NotRequired[str]

class ChatCompletionAssistantMessageParam(TypedDict):
    role: Literal["assistant"]
    content: str | None
    name: NotRequired[str]
    tool_calls: NotRequired[list[dict]]

class ChatCompletionToolMessageParam(TypedDict):
    role: Literal["tool"]
    content: str
    tool_call_id: str

# Response types
class ChatCompletion(BaseModel):
    id: str
    choices: list[Choice]
    created: int
    model: str
    object: Literal["chat.completion"]
    system_fingerprint: str | None
    usage: CompletionUsage | None

class Choice(BaseModel):
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"]
    index: int
    logprobs: Logprobs | None
    message: ChatCompletionMessage

class ChatCompletionMessage(BaseModel):
    content: str | None
    role: Literal["assistant"]
    tool_calls: list[ChatCompletionMessageToolCall] | None
    function_call: FunctionCall | None  # Deprecated
    audio: Audio | None  # When modalities includes audio

class ChatCompletionStoreMessage(BaseModel):
    """Message from a stored chat completion."""
    content: str | None
    role: Literal["system", "user", "assistant", "tool"]
    tool_calls: list[ChatCompletionMessageToolCall] | None
    tool_call_id: str | None  # For tool messages

class ChatCompletionMessageToolCall(BaseModel):
    id: str
    function: Function
    type: Literal["function"]

class Function(BaseModel):
    arguments: str  # JSON string
    name: str

class CompletionUsage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    completion_tokens_details: CompletionTokensDetails | None

# Streaming types
class ChatCompletionChunk(BaseModel):
    id: str
    choices: list[ChunkChoice]
    created: int
    model: str
    object: Literal["chat.completion.chunk"]
    system_fingerprint: str | None
    usage: CompletionUsage | None  # Only in final chunk with include_usage

class ChunkChoice(BaseModel):
    delta: ChoiceDelta
    finish_reason: str | None
    index: int
    logprobs: Logprobs | None

class ChoiceDelta(BaseModel):
    content: str | None
    role: Literal["assistant"] | None
    tool_calls: list[ChoiceDeltaToolCall] | None

# Parsed completion types
ResponseFormatT = TypeVar("ResponseFormatT", bound=BaseModel)

class ParsedChatCompletion(Generic[ResponseFormatT], ChatCompletion):
    """ChatCompletion with parsed content."""
    choices: list[ParsedChoice[ResponseFormatT]]

class ParsedChoice(Generic[ResponseFormatT], Choice):
    message: ParsedChatCompletionMessage[ResponseFormatT]

class ParsedChatCompletionMessage(Generic[ResponseFormatT], ChatCompletionMessage):
    parsed: ResponseFormatT | None
    tool_calls: list[ParsedFunctionToolCall] | None

class ParsedFunctionToolCall(ChatCompletionMessageToolCall):
    function: ParsedFunction
    type: Literal["function"]

class ParsedFunction(Function):
    parsed_arguments: BaseModel | None

# Deletion type
class ChatCompletionDeleted(BaseModel):
    id: str
    deleted: bool
    object: Literal["chat.completion"]

# Tool/function definitions
class ChatCompletionToolParam(TypedDict):
    type: Literal["function"]
    function: FunctionDefinition

class FunctionDefinition(TypedDict):
    name: str
    description: NotRequired[str]
    parameters: dict  # JSON Schema
    strict: NotRequired[bool]  # Enable strict schema adherence

# Response format types
class ResponseFormatText(TypedDict):
    type: Literal["text"]

class ResponseFormatJSONObject(TypedDict):
    type: Literal["json_object"]

class ResponseFormatJSONSchema(TypedDict):
    type: Literal["json_schema"]
    json_schema: JSONSchema

class JSONSchema(TypedDict):
    name: str
    description: NotRequired[str]
    schema: dict  # JSON Schema object
    strict: NotRequired[bool]

# Audio types
class ChatCompletionAudioParam(TypedDict):
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    format: Literal["wav", "mp3", "flac", "opus", "pcm16"]

# Streaming options
class ChatCompletionStreamOptionsParam(TypedDict):
    include_usage: NotRequired[bool]

# Tool choice types
ChatCompletionToolChoiceOptionParam = (
    Literal["none", "auto", "required"] | dict
)

class ToolChoiceFunction(TypedDict):
    type: Literal["function"]
    function: FunctionChoice

class FunctionChoice(TypedDict):
    name: str

# Stream wrapper type
class Stream(Generic[T]):
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T: ...
    def __enter__(self) -> Stream[T]: ...
    def __exit__(self, *args) -> None: ...
    def close(self) -> None: ...
```

## Async Usage

All chat completion methods are available in async variants through `AsyncOpenAI`:

```python
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI()

    # Async create - returns ChatCompletion or AsyncStream[ChatCompletionChunk]
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

    # Async streaming
    async for chunk in await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Tell me a story"}],
        stream=True
    ):
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")

    # Async parse - returns ParsedChatCompletion with structured output
    from pydantic import BaseModel

    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]

    response = await client.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": "Alice and Bob are meeting on Friday"}],
        response_format=CalendarEvent
    )
    event = response.choices[0].message.parsed

    # Other async methods: retrieve, update, list, delete, stream
    # All have the same signatures as sync versions

asyncio.run(main())
```

**Note**: AsyncOpenAI uses `AsyncStream[ChatCompletionChunk]` for streaming responses instead of `Stream[ChatCompletionChunk]`.

## Error Handling

```python
from openai import OpenAI, APIError, RateLimitError

client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError as e:
    print(f"Rate limit hit: {e}")
    # Handle rate limiting (e.g., retry with backoff)
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
    # Handle other API errors
```
