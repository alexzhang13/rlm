# Completions API Reference (Legacy)

The Text Completions API is the legacy interface for text generation with Claude. For new applications, use the [Messages API](./messages.md) instead, which provides better conversation handling and additional features.

## Overview

The Completions API generates text based on a prompt string. It uses special prompt markers (`HUMAN_PROMPT` and `AI_PROMPT`) to structure conversations.

**Deprecation Notice**: This API is maintained for backward compatibility. New applications should use the Messages API for improved functionality and support.

## Create Completion

```python { .api }
def create(
    self,
    *,
    model: str,
    prompt: str,
    max_tokens_to_sample: int,
    stop_sequences: list[str] = NOT_GIVEN,
    temperature: float = NOT_GIVEN,
    top_p: float = NOT_GIVEN,
    top_k: int = NOT_GIVEN,
    metadata: dict[str, Any] = NOT_GIVEN,
    stream: bool = False,
) -> Completion:
    """
    Create a text completion.

    Parameters:
        model: Model identifier. Examples: "claude-2.1", "claude-instant-1.2"
        prompt: Formatted prompt string with HUMAN_PROMPT and AI_PROMPT markers
        max_tokens_to_sample: Maximum tokens to generate (required)
        stop_sequences: List of sequences that stop generation when encountered
        temperature: Sampling temperature 0.0-1.0 (default: 1.0)
        top_p: Nucleus sampling parameter 0.0-1.0
        top_k: Top-k sampling parameter
        metadata: Request metadata for tracking
        stream: Enable streaming responses

    Returns:
        Completion: Response containing generated text and stop reason

    Raises:
        BadRequestError: Invalid request parameters
        AuthenticationError: Invalid or missing API key
        RateLimitError: Rate limit exceeded
    """
    ...

async def create(...) -> Completion:
    """
    Async version of create.

    Same parameters and returns as synchronous create(), but executes asynchronously.
    """
    ...
```

## Stream Completion

```python { .api }
def stream(
    self,
    *,
    model: str,
    prompt: str,
    max_tokens_to_sample: int,
    **kwargs
) -> Iterator[Completion]:
    """
    Stream a completion response.

    Yields partial completion objects as text is generated.

    Parameters:
        Same as create() method

    Yields:
        Completion objects with incremental text

    Example:
        for chunk in client.completions.stream(
            model="claude-2.1",
            prompt=f"{HUMAN_PROMPT} Hello{AI_PROMPT}",
            max_tokens_to_sample=100
        ):
            print(chunk.completion, end="", flush=True)
    """
    ...

async def stream(...) -> AsyncIterator[Completion]:
    """Async version of stream()."""
    ...
```

## Response Type

```python { .api }
class Completion(BaseModel):
    """
    Text completion response.

    Attributes:
        id: Unique completion identifier
        type: Always "completion"
        completion: Generated text content
        stop_reason: Why generation stopped ("stop_sequence", "max_tokens", or "end_turn")
        model: Model used for generation
    """
    id: str
    type: Literal["completion"]
    completion: str
    stop_reason: str | None
    model: str
```

## Usage Examples

### Basic Completion

```python
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

client = Anthropic()

completion = client.completions.create(
    model="claude-2.1",
    prompt=f"{HUMAN_PROMPT} What is the capital of France?{AI_PROMPT}",
    max_tokens_to_sample=100
)

print(completion.completion)
```

### Multi-turn Conversation

```python
# Build conversation with prompt markers
conversation = f"""{HUMAN_PROMPT} Hello, my name is Alice.{AI_PROMPT} Hi Alice! Nice to meet you.{HUMAN_PROMPT} What's my name?{AI_PROMPT}"""

completion = client.completions.create(
    model="claude-2.1",
    prompt=conversation,
    max_tokens_to_sample=50
)

print(completion.completion)
# Output: "Your name is Alice."
```

### Streaming Completion

```python
prompt = f"{HUMAN_PROMPT} Write a short story about a robot.{AI_PROMPT}"

for chunk in client.completions.stream(
    model="claude-2.1",
    prompt=prompt,
    max_tokens_to_sample=500
):
    print(chunk.completion, end="", flush=True)
```

### With Stop Sequences

```python
completion = client.completions.create(
    model="claude-2.1",
    prompt=f"{HUMAN_PROMPT} List three colors:{AI_PROMPT}",
    max_tokens_to_sample=100,
    stop_sequences=["\n\n", "4."]  # Stop after listing 3 items
)
```

### Temperature Control

```python
# More deterministic (lower temperature)
completion = client.completions.create(
    model="claude-2.1",
    prompt=f"{HUMAN_PROMPT} What is 2+2?{AI_PROMPT}",
    max_tokens_to_sample=10,
    temperature=0.0
)

# More creative (higher temperature)
creative = client.completions.create(
    model="claude-2.1",
    prompt=f"{HUMAN_PROMPT} Write a creative story opening.{AI_PROMPT}",
    max_tokens_to_sample=200,
    temperature=1.0
)
```

### Async Completion

```python
import asyncio

async def generate():
    client = AsyncAnthropic()

    completion = await client.completions.create(
        model="claude-2.1",
        prompt=f"{HUMAN_PROMPT} Hello{AI_PROMPT}",
        max_tokens_to_sample=50
    )

    return completion.completion

result = asyncio.run(generate())
```

### Async Streaming

```python
async def stream_completion():
    client = AsyncAnthropic()

    async for chunk in client.completions.stream(
        model="claude-2.1",
        prompt=f"{HUMAN_PROMPT} Tell me a joke{AI_PROMPT}",
        max_tokens_to_sample=200
    ):
        print(chunk.completion, end="", flush=True)

asyncio.run(stream_completion())
```

## Migration to Messages API

The Messages API provides better conversation handling and additional features. Here's how to migrate:

### Completions API (Legacy)

```python
from anthropic import HUMAN_PROMPT, AI_PROMPT

completion = client.completions.create(
    model="claude-2.1",
    prompt=f"{HUMAN_PROMPT} Hello{AI_PROMPT}",
    max_tokens_to_sample=100
)
print(completion.completion)
```

### Messages API (Recommended)

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)
print(message.content[0].text)
```

### Benefits of Messages API

- Better conversation structure (no manual prompt markers)
- Support for system prompts
- Multimodal input (images, documents)
- Tool/function calling
- Better type safety
- Streaming helpers
- Token counting utilities

## Constants

```python { .api }
from anthropic import HUMAN_PROMPT, AI_PROMPT

HUMAN_PROMPT: str = "\n\nHuman:"  # Marker for user messages
AI_PROMPT: str = "\n\nAssistant:"  # Marker for assistant responses
```

These constants are used to structure prompts in the Completions API format.

## See Also

- [Messages API](./messages.md) - Modern conversation API (recommended)
- [Streaming API](./streaming.md) - Streaming patterns and helpers
- [Client Configuration](../reference/client-config.md) - Client setup
- [Package Constants](../index.md#package-constants) - All SDK constants
