# Text Completions

Generate text completions using legacy completion models. This API is superseded by Chat Completions for most use cases, but remains available for compatibility with specific completion-optimized models.

## Capabilities

### Create Completion

Generate text completion for a given prompt.

```python { .api }
def create(
    self,
    *,
    model: str,
    prompt: str | list[str] | list[int] | list[list[int]],
    best_of: int | Omit = omit,
    echo: bool | Omit = omit,
    frequency_penalty: float | Omit = omit,
    logit_bias: dict[str, int] | Omit = omit,
    logprobs: int | Omit = omit,
    max_tokens: int | Omit = omit,
    n: int | Omit = omit,
    presence_penalty: float | Omit = omit,
    seed: int | Omit = omit,
    stop: str | list[str] | Omit = omit,
    stream: bool | Omit = omit,
    stream_options: dict | None | Omit = omit,
    suffix: str | Omit = omit,
    temperature: float | Omit = omit,
    top_p: float | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Completion | Stream[Completion]:
    """
    Generate text completion for a prompt.

    NOTE: Most use cases are better served by Chat Completions API.
    This endpoint is primarily for completion-specific models like gpt-3.5-turbo-instruct.

    Args:
        model: Model ID. Supported models:
            - "gpt-3.5-turbo-instruct": Instruction-tuned model optimized for completions
            - "davinci-002": Legacy Davinci model
            - "babbage-002": Legacy Babbage model

        prompt: Text prompt(s) to complete. Can be:
            - Single string: "Once upon a time"
            - List of strings: ["Story 1", "Story 2"]
            - Token array: [123, 456, 789]
            - List of token arrays: [[123, 456], [789, 012]]

        best_of: Generates best_of completions server-side, returns best one.
            Must be greater than n. Used with temperature for better quality.
            Cannot be used with stream.

        echo: If true, echoes the prompt in addition to completion.

        frequency_penalty: Number between -2.0 and 2.0. Penalizes tokens based on
            their frequency in the text so far. Default 0.

        logit_bias: Modify token probabilities. Maps token IDs to bias values
            from -100 to 100.

        logprobs: Include log probabilities of the most likely tokens.
            Returns logprobs number of most likely tokens per position.
            Maximum value is 5.

        max_tokens: Maximum tokens to generate. Default 16.

        n: Number of completions to generate. Default 1.

        presence_penalty: Number between -2.0 and 2.0. Penalizes tokens based on
            whether they appear in the text so far. Default 0.

        seed: For deterministic sampling (Beta). Same seed + parameters should
            return same result. Not guaranteed.

        stop: Up to 4 sequences where generation stops. Can be string or list.

        stream: If true, returns SSE stream of partial completions.

        stream_options: Streaming configuration. Accepts dict with:
            - "include_usage": bool - If true, includes token usage in final chunk
            - "include_obfuscation": bool - If true (default), adds random characters
              to obfuscation field on streaming delta events to normalize payload sizes
              as mitigation for side-channel attacks. Set to false to optimize bandwidth.

        suffix: Text that comes after the completion. Useful for inserting text.

        temperature: Sampling temperature between 0 and 2. Higher values make
            output more random. Default 1. Alter this or top_p, not both.

        top_p: Nucleus sampling parameter between 0 and 1. Default 1.
            Alter this or temperature, not both.

        user: Unique end-user identifier for abuse monitoring.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Completion: If stream=False (default), returns complete response.
        Stream[Completion]: If stream=True, returns streaming response.

    Raises:
        BadRequestError: Invalid parameters
        AuthenticationError: Invalid API key
        RateLimitError: Rate limit exceeded
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic completion
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="Once upon a time",
    max_tokens=50
)

print(response.choices[0].text)

# Multiple prompts
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt=[
        "The capital of France is",
        "The largest ocean on Earth is"
    ],
    max_tokens=10
)

for i, choice in enumerate(response.choices):
    print(f"Completion {i + 1}: {choice.text}")

# With suffix for text insertion
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="def calculate_sum(a, b):\n    \"\"\"",
    suffix="\n    return a + b",
    max_tokens=50
)

print(response.choices[0].text)

# With logprobs
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="The weather today is",
    max_tokens=5,
    logprobs=2,
    echo=True
)

# Access log probabilities
for token, logprob in zip(response.choices[0].logprobs.tokens,
                          response.choices[0].logprobs.token_logprobs):
    print(f"Token: {token}, Log Prob: {logprob}")

# Streaming completion
stream = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="Write a short poem about coding:",
    max_tokens=100,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].text:
        print(chunk.choices[0].text, end="", flush=True)

# With best_of for higher quality
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="Explain quantum computing in simple terms:",
    max_tokens=100,
    best_of=3,
    n=1,
    temperature=0.8
)

# With stop sequences
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="List three colors:\n1.",
    max_tokens=50,
    stop=["\n4.", "\n\n"]
)

# Deterministic completion with seed
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="Generate a random number:",
    seed=42,
    max_tokens=10
)
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Completion(BaseModel):
    """Completion response."""
    id: str
    choices: list[CompletionChoice]
    created: int
    model: str
    object: Literal["text_completion"]
    system_fingerprint: str | None
    usage: CompletionUsage | None

class CompletionChoice(BaseModel):
    """Single completion choice."""
    finish_reason: Literal["stop", "length", "content_filter"]
    index: int
    logprobs: Logprobs | None
    text: str

class Logprobs(BaseModel):
    """Log probability information."""
    text_offset: list[int]
    token_logprobs: list[float | None]
    tokens: list[str]
    top_logprobs: list[dict[str, float]] | None

class CompletionUsage(BaseModel):
    """Token usage statistics."""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

# Stream wrapper
class Stream(Generic[T]):
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T: ...
    def __enter__(self) -> Stream[T]: ...
    def __exit__(self, *args) -> None: ...
```

## Migration to Chat Completions

For most use cases, Chat Completions API is recommended:

```python
# Legacy Completions
response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="Translate to French: Hello"
)

# Equivalent Chat Completion
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Translate to French: Hello"}
    ]
)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def complete_text():
    client = AsyncOpenAI()

    response = await client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Once upon a time",
        max_tokens=50
    )

    return response.choices[0].text

text = asyncio.run(complete_text())
```
