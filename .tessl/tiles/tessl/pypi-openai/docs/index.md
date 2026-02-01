# OpenAI Python Library

The official Python client library for the OpenAI API, providing comprehensive access to OpenAI's suite of AI models including GPT-4, DALL-E, Whisper, and Embeddings. The library features both synchronous and asynchronous implementations, complete type definitions, streaming support, structured output parsing, and integration with OpenAI's latest features including the Assistants API, Realtime API, and advanced capabilities like function calling and vision inputs.

## Package Information

- **Package Name**: openai
- **Language**: Python
- **Installation**: `pip install openai`
- **Python Version**: 3.9+
- **Official Documentation**: https://platform.openai.com/docs/api-reference

## Quick Start for Agents

```python
# Minimal working example - most common agent use case
from openai import OpenAI

client = OpenAI()  # Reads OPENAI_API_KEY from environment

# Simple completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# With error handling (production pattern)
from openai import OpenAIError, RateLimitError, APIError

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    content = response.choices[0].message.content
except RateLimitError as e:
    # Handle rate limiting with exponential backoff
    print(f"Rate limited: {e}")
except APIError as e:
    # Handle API errors
    print(f"API error: {e}")
except OpenAIError as e:
    # Handle all other OpenAI errors
    print(f"Error: {e}")
```

## Core Imports

```python
# Essential imports for most use cases
from openai import OpenAI, AsyncOpenAI
from openai import AzureOpenAI, AsyncAzureOpenAI  # For Azure

# Common types and utilities
from typing import Callable, Iterable, Awaitable, Mapping, Literal, AsyncGenerator
import httpx
from openai import (
    Stream, AsyncStream, Client, AsyncClient,
    NOT_GIVEN, NotGiven, not_given, Omit, omit,
    AssistantEventHandler, AsyncAssistantEventHandler,
    HttpxBinaryResponseContent, RequestOptions, Timeout,
    APIResponse, AsyncAPIResponse
)
from openai._types import FileTypes
from openai.types.websocket_connection_options import WebsocketConnectionOptions

# Chat completion types (most commonly used)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
    ChatCompletionToolChoiceOptionParam,
    completion_create_params,
)

# Pagination types
from openai.pagination import (
    SyncPage, AsyncPage,
    SyncCursorPage, AsyncCursorPage,
    SyncConversationCursorPage, AsyncConversationCursorPage
)

# Helpers for audio recording and playback
from openai.helpers import Microphone, LocalAudioPlayer

# Access all type definitions
from openai import types
# Examples: types.ChatCompletion, types.Embedding, types.FileObject
# Use types.chat.ChatCompletionMessageParam for nested types

# Error handling imports
from openai import (
    OpenAIError, APIError, APIStatusError,
    APITimeoutError, APIConnectionError, APIResponseValidationError,
    BadRequestError, AuthenticationError, PermissionDeniedError,
    NotFoundError, ConflictError, UnprocessableEntityError,
    RateLimitError, InternalServerError,
    LengthFinishReasonError, ContentFilterFinishReasonError
)
```

## Basic Usage

```python
from openai import OpenAI

# Initialize the client (reads OPENAI_API_KEY from environment by default)
client = OpenAI(api_key="your-api-key")  # Or omit api_key to use env var

# Create a chat completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)

# Async usage
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(api_key="your-api-key")
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Module-Level Configuration (Legacy)

The library supports a legacy module-level configuration pattern for backward compatibility. You can configure the default client by setting module-level variables:

```python
import openai

# API Configuration
openai.api_key = "your-api-key"
openai.organization = "org-xxx"
openai.project = "proj-xxx"
openai.webhook_secret = "whsec_xxx"

# Network Configuration
openai.base_url = "https://api.openai.com/v1"
openai.timeout = 60.0  # seconds
openai.max_retries = 3
openai.default_headers = {"Custom-Header": "value"}
openai.default_query = {"custom_param": "value"}
openai.http_client = custom_httpx_client

# Azure OpenAI Configuration
openai.api_type = "azure"  # "openai" or "azure"
openai.api_version = "2024-02-01"
openai.azure_endpoint = "https://your-resource.openai.azure.com"
openai.azure_ad_token = "your-ad-token"
openai.azure_ad_token_provider = lambda: get_token()

# After setting these, you can use module-level methods:
# (This pattern is deprecated; prefer explicit client instantiation)
```

**Note**: The module-level configuration pattern is legacy. For new code, prefer explicit client instantiation:

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    organization="org-xxx",
    timeout=60.0
)
```

## Architecture

The OpenAI Python library is structured around client-resource architecture:

- **Clients**: `OpenAI`, `AsyncOpenAI`, `AzureOpenAI`, `AsyncAzureOpenAI` - Entry points for API access with configuration
- **Resources**: Organized API endpoints (chat, audio, images, files, etc.) accessible as client attributes
- **Types**: Comprehensive Pydantic models for all requests and responses with full type safety
- **Streaming**: First-class streaming support via `Stream` and `AsyncStream` classes
- **Error Handling**: Structured exception hierarchy for different error types

The library provides both synchronous and asynchronous implementations for all operations, enabling integration into any Python application architecture.

## Capabilities

### Client Initialization

Initialize OpenAI clients with API credentials and configuration options for both OpenAI and Azure OpenAI services.

```python { .api }
class OpenAI:
    """Synchronous client for OpenAI API."""
    def __init__(
        self,
        *,
        api_key: str | None | Callable[[], str] = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | httpx.URL | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
    ): ...

class AsyncOpenAI:
    """Asynchronous client for OpenAI API."""
    def __init__(
        self,
        *,
        api_key: str | None | Callable[[], Awaitable[str]] = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | httpx.URL | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ): ...

class AzureOpenAI:
    """Synchronous client for Azure OpenAI Service."""
    def __init__(
        self,
        *,
        api_version: str | None = None,
        azure_endpoint: str | None = None,
        azure_deployment: str | None = None,
        api_key: str | None | Callable[[], str] = None,
        azure_ad_token: str | None = None,
        azure_ad_token_provider: Callable[[], str] | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | httpx.URL | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
    ): ...

class AsyncAzureOpenAI:
    """Asynchronous client for Azure OpenAI Service."""
    def __init__(
        self,
        *,
        api_version: str | None = None,
        azure_endpoint: str | None = None,
        azure_deployment: str | None = None,
        api_key: str | None | Callable[[], Awaitable[str]] = None,
        azure_ad_token: str | None = None,
        azure_ad_token_provider: Callable[[], Awaitable[str] | str] | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | httpx.URL | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ): ...

# Aliases for convenience
Client = OpenAI
AsyncClient = AsyncOpenAI
```

[Client Initialization](./client-initialization.md)

### Chat Completions

Create conversational responses using OpenAI's language models with support for text, function calling, vision inputs, audio, and structured output parsing.

```python { .api }
def create(
    self,
    *,
    messages: Iterable[ChatCompletionMessageParam],
    model: str | ChatModel,
    audio: dict | Omit = omit,
    frequency_penalty: float | Omit = omit,
    function_call: str | dict | Omit = omit,
    functions: Iterable[dict] | Omit = omit,
    logit_bias: dict[str, int] | Omit = omit,
    logprobs: bool | Omit = omit,
    top_logprobs: int | Omit = omit,
    max_completion_tokens: int | Omit = omit,
    max_tokens: int | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    modalities: list[Literal["text", "audio"]] | Omit = omit,
    n: int | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    prediction: dict | Omit = omit,
    presence_penalty: float | Omit = omit,
    prompt_cache_key: str | Omit = omit,
    prompt_cache_retention: Literal["in-memory", "24h"] | Omit = omit,
    reasoning_effort: str | Omit = omit,
    response_format: completion_create_params.ResponseFormat | Omit = omit,
    safety_identifier: str | Omit = omit,
    seed: int | Omit = omit,
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | Omit = omit,
    stop: str | list[str] | Omit = omit,
    store: bool | Omit = omit,
    stream: bool | Omit = omit,
    stream_options: dict | Omit = omit,
    temperature: float | Omit = omit,
    tool_choice: ChatCompletionToolChoiceOptionParam | Omit = omit,
    tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit,
    top_p: float | Omit = omit,
    user: str | Omit = omit,
    verbosity: Literal["low", "medium", "high"] | Omit = omit,
    web_search_options: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given,
) -> ChatCompletion | Stream[ChatCompletionChunk]: ...

def parse(
    self,
    *,
    messages: Iterable[ChatCompletionMessageParam],
    model: str | ChatModel,
    response_format: Type[BaseModel],
    **kwargs
) -> ParsedChatCompletion: ...
```

[Chat Completions](./chat-completions.md)

### Text Completions

Generate text completions using legacy completion models.

```python { .api }
def create(
    self,
    *,
    model: str,
    prompt: str | list[str] | list[int] | list[list[int]] | None,
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
    stream_options: Optional[dict] | Omit = omit,
    stream: bool | Omit = omit,
    suffix: str | Omit = omit,
    temperature: float | Omit = omit,
    top_p: float | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given,
) -> Completion | Stream[Completion]: ...
```

[Text Completions](./completions.md)

### Embeddings

Create vector embeddings for text inputs to use in semantic search, clustering, and other ML applications.

```python { .api }
def create(
    self,
    *,
    input: str | list[str] | list[int] | list[list[int]],
    model: str | EmbeddingModel,
    dimensions: int | Omit = omit,
    encoding_format: Literal["float", "base64"] | Omit = omit,
    user: str | Omit = omit,
    extra_headers: Mapping[str, str] | None = None,
    extra_query: Mapping[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given,
) -> CreateEmbeddingResponse: ...
```

[Embeddings](./embeddings.md)

### Audio

Convert audio to text (transcription and translation) and text to speech using Whisper and TTS models.

```python { .api }
# Transcription
def create(
    self,
    *,
    file: FileTypes,
    model: str | AudioModel,
    chunking_strategy: Optional[dict] | Omit = omit,
    include: list[str] | Omit = omit,
    known_speaker_names: list[str] | Omit = omit,
    known_speaker_references: list[str] | Omit = omit,
    language: str | Omit = omit,
    prompt: str | Omit = omit,
    response_format: str | Omit = omit,
    stream: bool | Omit = omit,
    temperature: float | Omit = omit,
    timestamp_granularities: list[str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given,
) -> Transcription | TranscriptionVerbose | TranscriptionDiarized | Stream[TranscriptionStreamEvent]: ...

# Translation
def create(
    self,
    *,
    file: FileTypes,
    model: str | AudioModel,
    prompt: str | Omit = omit,
    response_format: str | Omit = omit,
    temperature: float | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given,
) -> Translation | TranslationVerbose: ...

# Text-to-Speech
def create(
    self,
    *,
    input: str,
    model: str | SpeechModel,
    voice: str,
    instructions: str | Omit = omit,
    response_format: str | Omit = omit,
    speed: float | Omit = omit,
    stream_format: Literal["sse", "audio"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given,
) -> HttpxBinaryResponseContent: ...
```

[Audio](./audio.md)

### Images

Generate, edit, and create variations of images using DALL-E models.

```python { .api }
def generate(
    self,
    *,
    prompt: str,
    background: Literal["transparent", "opaque", "auto"] | None | Omit = omit,
    model: str | ImageModel | None = None,
    moderation: Literal["low", "auto"] | None | Omit = omit,
    n: int | None = None,
    output_compression: int | None | Omit = omit,
    output_format: Literal["png", "jpeg", "webp"] | None | Omit = omit,
    partial_images: int | None | Omit = omit,
    quality: str | None = None,
    response_format: str | None = None,
    size: str | None = None,
    stream: bool | None | Omit = omit,
    style: str | None = None,
    user: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ImagesResponse: ...

def edit(
    self,
    *,
    image: FileTypes | list[FileTypes],
    prompt: str,
    background: Literal["transparent", "opaque", "auto"] | None | Omit = omit,
    input_fidelity: Literal["high", "low"] | None | Omit = omit,
    mask: FileTypes | None = None,
    model: str | ImageModel | None = None,
    n: int | None = None,
    output_compression: int | None | Omit = omit,
    output_format: Literal["png", "jpeg", "webp"] | None | Omit = omit,
    partial_images: int | None | Omit = omit,
    quality: Literal["standard", "low", "medium", "high", "auto"] | None | Omit = omit,
    response_format: str | None = None,
    size: str | None = None,
    stream: bool | None | Omit = omit,
    user: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ImagesResponse: ...

def create_variation(
    self,
    *,
    image: FileTypes,
    model: str | ImageModel | None = None,
    n: int | None = None,
    response_format: str | None = None,
    size: str | None = None,
    user: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ImagesResponse: ...
```

[Images](./images.md)

### Videos

Generate and manipulate videos using video generation models.

```python { .api }
def create(
    self,
    *,
    prompt: str,
    input_reference: FileTypes | Omit = omit,
    model: VideoModel | Omit = omit,
    seconds: VideoSeconds | Omit = omit,
    size: VideoSize | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video: ...

def create_and_poll(
    self,
    *,
    prompt: str,
    input_reference: FileTypes | Omit = omit,
    model: VideoModel | Omit = omit,
    seconds: VideoSeconds | Omit = omit,
    size: VideoSize | Omit = omit,
    poll_interval_ms: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video: ...

def poll(
    self,
    video_id: str,
    *,
    poll_interval_ms: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video: ...

def retrieve(
    self,
    video_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Video: ...

def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Video]: ...

def delete(
    self,
    video_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VideoDeleteResponse: ...

def download_content(
    self,
    video_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> HttpxBinaryResponseContent: ...

def remix(
    self,
    video_id: str,
    *,
    prompt: str,
    seconds: VideoSeconds | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video: ...
```

[Videos](./videos.md)

### Files

Upload and manage files for use with various OpenAI features like Assistants, Fine-tuning, and Batch processing.

```python { .api }
def create(
    self,
    *,
    file: FileTypes,
    purpose: str | FilePurpose,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FileObject: ...

def retrieve(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FileObject: ...

def list(
    self,
    *,
    purpose: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    after: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncPage[FileObject]: ...

def delete(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FileDeleted: ...

def content(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> HttpxBinaryResponseContent: ...

def retrieve_content(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> HttpxBinaryResponseContent: ...

def wait_for_processing(
    self,
    file_id: str,
    *,
    poll_interval: float = 5.0,
    max_wait: float = 3600.0,
) -> FileObject: ...
```

[Files](./files.md)

### Uploads

Upload large files in chunks for use with Assistants and other features. Upload parts are managed through the `.parts` subresource.

```python { .api }
def create(
    self,
    *,
    bytes: int,
    filename: str,
    mime_type: str,
    purpose: FilePurpose,
    expires_after: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Upload: ...

def complete(
    self,
    upload_id: str,
    *,
    part_ids: list[str],
    md5: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Upload: ...

def cancel(
    self,
    upload_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Upload: ...

def upload_file_chunked(
    self,
    *,
    file: str | os.PathLike | bytes,
    mime_type: str,
    purpose: FilePurpose,
    filename: str | None = None,
    bytes: int | None = None,
    part_size: int | None = None,
    md5: str | Omit = omit,
) -> Upload: ...

# Access via client.uploads.parts
def create(
    self,
    upload_id: str,
    *,
    data: FileTypes,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> UploadPart: ...
```

[Uploads](./uploads.md)

### Models

Retrieve information about available models and manage fine-tuned models.

```python { .api }
def retrieve(
    self,
    model: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Model: ...

def list(
    self,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncPage[Model]: ...

def delete(
    self,
    model: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ModelDeleted: ...
```

[Models](./models.md)

### Fine-tuning

Create and manage fine-tuning jobs to customize models on your own data. Fine-tuning operations are accessed through the `.jobs` and `.checkpoints` subresources.

```python { .api }
# Access via client.fine_tuning.jobs
def create(
    self,
    *,
    model: str,
    training_file: str,
    hyperparameters: dict | None = None,
    method: dict | None = None,
    integrations: list[dict] | None = None,
    seed: int | None = None,
    suffix: str | None = None,
    validation_file: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FineTuningJob: ...

def retrieve(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FineTuningJob: ...

def list(
    self,
    *,
    after: str | None = None,
    limit: int | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[FineTuningJob]: ...

def cancel(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FineTuningJob: ...

def pause(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FineTuningJob: ...

def resume(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> FineTuningJob: ...

def list_events(
    self,
    fine_tuning_job_id: str,
    *,
    after: str | None = None,
    limit: int | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[FineTuningJobEvent]: ...

# Access via client.fine_tuning.checkpoints
def list(
    self,
    fine_tuning_job_id: str,
    *,
    after: str | None = None,
    limit: int | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[FineTuningJobCheckpoint]: ...
```

[Fine-tuning](./fine-tuning.md)

### Moderations

Check content against OpenAI's usage policies to detect potentially harmful content.

```python { .api }
def create(
    self,
    *,
    input: str | list[str],
    model: str | ModerationModel | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ModerationCreateResponse: ...
```

[Moderations](./moderations.md)

### Batch Processing

Submit batch requests for asynchronous processing of multiple API calls.

```python { .api }
def create(
    self,
    *,
    completion_window: str,
    endpoint: str,
    input_file_id: str,
    metadata: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Batch: ...

def retrieve(
    self,
    batch_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Batch: ...

def list(
    self,
    *,
    after: str | None = None,
    limit: int | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[Batch]: ...

def cancel(
    self,
    batch_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Batch: ...
```

[Batch Processing](./batches.md)

### Vector Stores

Create and manage vector stores for semantic search and retrieval with the Assistants API. Vector store files are managed through the `.files` subresource, and file batches through the `.file_batches` subresource.

```python { .api }
def create(
    self,
    *,
    file_ids: list[str] | None = None,
    name: str | None = None,
    expires_after: dict | None = None,
    chunking_strategy: dict | None = None,
    metadata: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStore: ...

def retrieve(
    self,
    vector_store_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStore: ...

def update(
    self,
    vector_store_id: str,
    *,
    name: str | None = None,
    expires_after: dict | None = None,
    metadata: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStore: ...

def list(
    self,
    *,
    after: str | None = None,
    before: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[VectorStore]: ...

def delete(
    self,
    vector_store_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreDeleted: ...

def search(
    self,
    vector_store_id: str,
    *,
    query: str,
    limit: int | None = None,
    filter: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreSearchResponse: ...

# Access via client.vector_stores.files
def create(
    self,
    vector_store_id: str,
    *,
    file_id: str,
    chunking_strategy: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreFile: ...

def retrieve(
    self,
    vector_store_id: str,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreFile: ...

def list(
    self,
    vector_store_id: str,
    *,
    after: str | None = None,
    before: str | None = None,
    filter: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[VectorStoreFile]: ...

def delete(
    self,
    vector_store_id: str,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreFileDeleted: ...

# Access via client.vector_stores.file_batches
def create(
    self,
    vector_store_id: str,
    *,
    file_ids: list[str],
    chunking_strategy: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreFileBatch: ...

def retrieve(
    self,
    vector_store_id: str,
    batch_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreFileBatch: ...

def cancel(
    self,
    vector_store_id: str,
    batch_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> VectorStoreFileBatch: ...

def list_files(
    self,
    vector_store_id: str,
    batch_id: str,
    *,
    after: str | None = None,
    before: str | None = None,
    filter: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[VectorStoreFile]: ...
```

[Vector Stores](./vector-stores.md)

### Assistants API (Beta)

Build AI assistants with advanced capabilities including code interpreter, file search, and function calling.

```python { .api }
def create(
    self,
    *,
    model: str,
    description: str | None = None,
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    name: str | None = None,
    response_format: dict | None = None,
    temperature: float | None = None,
    tool_resources: dict | None = None,
    tools: list[dict] | None = None,
    top_p: float | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Assistant: ...

def retrieve(
    self,
    assistant_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Assistant: ...

def update(
    self,
    assistant_id: str,
    *,
    description: str | None = None,
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    model: str | None = None,
    name: str | None = None,
    response_format: dict | None = None,
    temperature: float | None = None,
    tool_resources: dict | None = None,
    tools: list[dict] | None = None,
    top_p: float | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Assistant: ...

def list(
    self,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Assistant]: ...

def delete(
    self,
    assistant_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> AssistantDeleted: ...
```

[Assistants API](./assistants.md)

### Threads and Messages (Beta)

Create conversational threads and manage messages within the Assistants API.

```python { .api }
# Threads
def create(
    self,
    *,
    messages: list[dict] | None = None,
    metadata: dict[str, str] | None = None,
    tool_resources: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Thread: ...

def retrieve(
    self,
    thread_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Thread: ...

def update(
    self,
    thread_id: str,
    *,
    metadata: dict[str, str] | None = None,
    tool_resources: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Thread: ...

def delete(
    self,
    thread_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ThreadDeleted: ...

def create_and_run(
    self,
    *,
    assistant_id: str,
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    model: str | None = None,
    thread: dict | None = None,
    tools: list[dict] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def create_and_run_poll(
    self,
    *,
    assistant_id: str,
    poll_interval_ms: int | None = None,
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    model: str | None = None,
    thread: dict | None = None,
    tools: list[dict] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def create_and_run_stream(
    self,
    *,
    assistant_id: str,
    event_handler: AssistantEventHandler | None = None,
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    model: str | None = None,
    thread: dict | None = None,
    tools: list[dict] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> AssistantStreamManager: ...

# Messages
def create(
    self,
    thread_id: str,
    *,
    role: str,
    content: str | list[dict],
    attachments: list[dict] | None = None,
    metadata: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Message: ...

def retrieve(
    self,
    thread_id: str,
    message_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Message: ...

def update(
    self,
    thread_id: str,
    message_id: str,
    *,
    metadata: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Message: ...

def list(
    self,
    thread_id: str,
    *,
    after: str | None = None,
    before: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    run_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[Message]: ...

def delete(
    self,
    thread_id: str,
    message_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> MessageDeleted: ...
```

[Threads and Messages](./threads-messages.md)

### Runs (Beta)

Execute assistants on threads and handle tool calls. Run steps are managed through the `.steps` subresource.

```python { .api }
def create(
    self,
    thread_id: str,
    *,
    assistant_id: str,
    additional_instructions: str | None = None,
    additional_messages: list[dict] | None = None,
    instructions: str | None = None,
    max_completion_tokens: int | None = None,
    max_prompt_tokens: int | None = None,
    metadata: dict[str, str] | None = None,
    model: str | None = None,
    parallel_tool_calls: bool | None = None,
    response_format: dict | None = None,
    stream: bool | None = None,
    temperature: float | None = None,
    tool_choice: str | dict | None = None,
    tools: list[dict] | None = None,
    top_p: float | None = None,
    truncation_strategy: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def retrieve(
    self,
    thread_id: str,
    run_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def update(
    self,
    thread_id: str,
    run_id: str,
    *,
    metadata: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def list(
    self,
    thread_id: str,
    *,
    after: str | None = None,
    before: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[Run]: ...

def cancel(
    self,
    thread_id: str,
    run_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def submit_tool_outputs(
    self,
    thread_id: str,
    run_id: str,
    *,
    tool_outputs: list[dict],
    stream: bool | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Run: ...

def stream(
    self,
    thread_id: str,
    *,
    assistant_id: str,
    event_handler: AssistantEventHandler | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> AssistantStreamManager: ...

# Access via client.beta.threads.runs.steps
def retrieve(
    self,
    thread_id: str,
    run_id: str,
    step_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> RunStep: ...

def list(
    self,
    thread_id: str,
    run_id: str,
    *,
    after: str | None = None,
    before: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> SyncCursorPage[RunStep]: ...
```

[Runs](./runs.md)

### ChatKit (Beta)

Simplified, high-level interface for building chat applications with session and thread management.

```python { .api }
def create(
    self,
    *,
    user: str,
    workflow: ChatSessionWorkflowParam,
    chatkit_configuration: ChatSessionChatKitConfigurationParam | Omit = omit,
    expires_after: ChatSessionExpiresAfterParam | Omit = omit,
    rate_limits: ChatSessionRateLimitsParam | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatSession: ...
```

[ChatKit](./chatkit.md)

### Realtime API (Beta)

WebSocket-based realtime communication for low-latency conversational AI experiences. Realtime client secrets and calls are managed through the `.client_secrets` and `.calls` subresources.

```python { .api }
def connect(
    self,
    *,
    call_id: str | Omit = omit,
    model: str | Omit = omit,
    extra_query: dict[str, object] = {},
    extra_headers: dict[str, str] = {},
    websocket_connection_options: WebsocketConnectionOptions = {},
) -> RealtimeConnectionManager: ...

# Access via client.realtime.client_secrets
def create(
    self,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ClientSecret: ...

# Access via client.realtime.calls
def create(
    self,
    *,
    model: str,
    call_config: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Call: ...

def retrieve(
    self,
    call_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Call: ...

def update(
    self,
    call_id: str,
    *,
    call_config: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Call: ...

def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Call]: ...
```

[Realtime API](./realtime.md)

### Responses API

Create responses with advanced tool support including computer use, file search, and code patching. Response input items and tokens are managed through the `.input_items` and `.input_tokens` subresources.

```python { .api }
def create(
    self,
    *,
    model: str,
    input: dict | list[dict],
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    parallel_tool_calls: bool | None = None,
    reasoning_effort: str | None = None,
    store: bool | None = None,
    stream: bool | None = None,
    temperature: float | None = None,
    tool_choice: str | dict | None = None,
    tools: list[dict] | None = None,
    top_p: float | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Response: ...

def stream(
    self,
    *,
    model: str,
    input: dict | list[dict],
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    parallel_tool_calls: bool | None = None,
    reasoning_effort: str | None = None,
    store: bool | None = None,
    temperature: float | None = None,
    tool_choice: str | dict | None = None,
    tools: list[dict] | None = None,
    top_p: float | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Stream[ResponseStreamEvent]: ...

def parse(
    self,
    *,
    model: str,
    input: dict | list[dict],
    response_format: Type[BaseModel],
    instructions: str | None = None,
    metadata: dict[str, str] | None = None,
    parallel_tool_calls: bool | None = None,
    reasoning_effort: str | None = None,
    store: bool | None = None,
    temperature: float | None = None,
    tool_choice: str | dict | None = None,
    tools: list[dict] | None = None,
    top_p: float | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ParsedResponse: ...

def retrieve(
    self,
    response_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Response: ...

def delete(
    self,
    response_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ResponseDeleted: ...

def cancel(
    self,
    response_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> Response: ...

# Access via client.responses.input_items
def create(
    self,
    response_id: str,
    *,
    type: str,
    content: str | list[dict] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ResponseInputItem: ...

def delete(
    self,
    response_id: str,
    item_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ResponseInputItemDeleted: ...

# Access via client.responses.input_tokens
def create(
    self,
    response_id: str,
    *,
    token: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ResponseInputToken: ...

def delete(
    self,
    response_id: str,
    token_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | None = None,
) -> ResponseInputTokenDeleted: ...
```

[Responses](./responses.md)

### Evaluations

Create and manage evaluations to test model performance with custom testing criteria. Evaluation runs are managed through the `.runs` subresource.

```python { .api }
def create(
    self,
    *,
    data_source_config: dict,
    testing_criteria: Iterable[dict],
    metadata: dict[str, str] | None | Omit = omit,
    name: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Eval: ...

def retrieve(
    self,
    eval_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Eval: ...

def update(
    self,
    eval_id: str,
    *,
    metadata: dict[str, str] | None | Omit = omit,
    name: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Eval: ...

def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    order_by: Literal["created_at", "updated_at"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Eval]: ...

def delete(
    self,
    eval_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> EvalDeleteResponse: ...

# Access via client.evals.runs
def create(
    self,
    eval_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> EvalRun: ...

def retrieve(
    self,
    eval_id: str,
    run_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> EvalRun: ...

def list(
    self,
    eval_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[EvalRun]: ...
```

[Evaluations](./evals.md)

### Conversations

Create and manage conversations for structured multi-turn interactions. Conversation items are managed through the `.items` subresource.

```python { .api }
def create(
    self,
    *,
    items: Iterable[dict] | None | Omit = omit,
    metadata: dict[str, str] | None | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation: ...

def retrieve(
    self,
    conversation_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation: ...

def update(
    self,
    conversation_id: str,
    *,
    metadata: dict[str, str] | None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation: ...

def delete(
    self,
    conversation_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationDeleted: ...

# Access via client.conversations.items
def create(
    self,
    conversation_id: str,
    *,
    type: str,
    content: str | list[dict] | None = None,
    metadata: dict[str, str] | None | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationItem: ...

def retrieve(
    self,
    conversation_id: str,
    item_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationItem: ...

def update(
    self,
    conversation_id: str,
    item_id: str,
    *,
    content: str | list[dict] | None = None,
    metadata: dict[str, str] | None | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationItem: ...

def list(
    self,
    conversation_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[ConversationItem]: ...

def delete(
    self,
    conversation_id: str,
    item_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationItemDeleted: ...
```

[Conversations](./conversations.md)

### Containers

Create and manage isolated file storage containers for organizing files. Container files are managed through the `.files` subresource.

```python { .api }
def create(
    self,
    *,
    name: str,
    expires_after: dict | Omit = omit,
    file_ids: list[str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Container: ...

def retrieve(
    self,
    container_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Container: ...

def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Container]: ...

def delete(
    self,
    container_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> None: ...

# Access via client.containers.files
def create(
    self,
    container_id: str,
    *,
    file: FileTypes,
    purpose: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ContainerFile: ...

def retrieve(
    self,
    container_id: str,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ContainerFile: ...

def list(
    self,
    container_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[ContainerFile]: ...

def delete(
    self,
    container_id: str,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ContainerFileDeleted: ...
```

[Containers](./containers.md)

### Webhooks

Verify and handle webhook events from OpenAI for asynchronous notifications.

```python { .api }
def verify_signature(
    payload: str | bytes,
    headers: dict[str, str] | list[tuple[str, str]],
    *,
    secret: str | None = None,
    tolerance: int = 300
) -> None: ...

def unwrap(
    payload: str | bytes,
    headers: dict[str, str] | list[tuple[str, str]],
    *,
    secret: str | None = None
) -> UnwrapWebhookEvent: ...
```

[Webhooks](./webhooks.md)

## Response Wrappers

All resources support response wrapper patterns for accessing raw HTTP responses or streaming responses without loading them into memory.

### Raw Response Access

Access the underlying `httpx.Response` object for any API call:

```python
from openai import OpenAI

client = OpenAI()

# Use .with_raw_response prefix
response = client.with_raw_response.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Access parsed response
completion = response.parsed

# Access raw HTTP response
http_response = response.http_response
print(f"Status: {http_response.status_code}")
print(f"Headers: {http_response.headers}")
print(f"Raw content: {http_response.content}")
```

Available on all resources:

```python
client.with_raw_response.chat.completions.create(...)
client.with_raw_response.audio.transcriptions.create(...)
client.with_raw_response.images.generate(...)
# ... and all other resources
```

### Streaming Response Access

Stream responses without loading them into memory, useful for large responses:

```python
response = client.with_streaming_response.files.content("file-abc123")

# Stream chunks
for chunk in response.iter_bytes():
    process_chunk(chunk)

# Or write directly to file
with open("output.txt", "wb") as f:
    for chunk in response.iter_bytes():
        f.write(chunk)
```

Available on all resources:

```python
client.with_streaming_response.chat.completions.create(...)
client.with_streaming_response.files.content(...)
# ... and all other resources
```

Both patterns work with async clients:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

# Raw response (async)
response = await client.with_raw_response.chat.completions.create(...)

# Streaming response (async)
response = await client.with_streaming_response.files.content("file-abc123")
async for chunk in response.iter_bytes():
    process_chunk(chunk)
```

## Error Handling

The library provides a comprehensive exception hierarchy for handling different error scenarios:

```python { .api }
class OpenAIError(Exception):
    """Base exception for all OpenAI errors."""

class APIError(OpenAIError):
    """Base for API-related errors."""

class APIStatusError(APIError):
    """HTTP status code errors (4xx, 5xx)."""
    status_code: int
    response: httpx.Response
    body: object

class APITimeoutError(APIError):
    """Request timeout errors."""

class APIConnectionError(APIError):
    """Connection errors."""

class APIResponseValidationError(APIError):
    """Response validation errors."""

class BadRequestError(APIStatusError):
    """400 Bad Request."""

class AuthenticationError(APIStatusError):
    """401 Authentication error."""

class PermissionDeniedError(APIStatusError):
    """403 Permission denied."""

class NotFoundError(APIStatusError):
    """404 Not found."""

class ConflictError(APIStatusError):
    """409 Conflict."""

class UnprocessableEntityError(APIStatusError):
    """422 Unprocessable Entity."""

class RateLimitError(APIStatusError):
    """429 Rate limit exceeded."""

class InternalServerError(APIStatusError):
    """500+ Server errors."""

class LengthFinishReasonError(OpenAIError):
    """Raised when completion stops due to reaching max tokens."""

class ContentFilterFinishReasonError(OpenAIError):
    """Raised when completion stops due to content filtering."""

class InvalidWebhookSignatureError(OpenAIError):
    """Raised when webhook signature verification fails."""
```

### Production Error Handling Patterns

```python
from openai import OpenAI, OpenAIError, RateLimitError, APIError, APIConnectionError
import time

client = OpenAI()

# Pattern 1: Retry with exponential backoff for rate limits
def create_completion_with_retry(messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + 1  # Exponential backoff
            print(f"Rate limited. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except APIConnectionError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Connection error. Retrying in {wait_time}s...")
            time.sleep(wait_time)

# Pattern 2: Handle all error types
def safe_completion(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        return response.choices[0].message.content
    except RateLimitError as e:
        # Handle rate limiting - implement backoff
        return f"Rate limited: {e}"
    except APIConnectionError as e:
        # Handle connection issues - check network
        return f"Connection error: {e}"
    except APIError as e:
        # Handle general API errors
        return f"API error: {e}"
    except OpenAIError as e:
        # Catch all other OpenAI errors
        return f"OpenAI error: {e}"
    except Exception as e:
        # Catch unexpected errors
        return f"Unexpected error: {e}"

# Pattern 3: Check finish reason
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Write a long story"}],
    max_tokens=100
)

finish_reason = response.choices[0].finish_reason
if finish_reason == "length":
    print("Response truncated - increase max_tokens")
elif finish_reason == "content_filter":
    print("Content filtered - adjust prompt")
elif finish_reason == "stop":
    print("Completed normally")
```

## Common Types

```python { .api }
# Sentinel values for omitted parameters
NOT_GIVEN: Omit  # Sentinel indicating parameter was not provided
not_given: Omit  # Alias for NOT_GIVEN (lowercase convention)

# Omit type for optional API parameters
# Use Omit type with omit default value instead of None for optional parameters
# This distinguishes between "parameter not provided" vs "parameter set to null"
Omit: TypeAlias  # Type for omittable parameters
omit: Omit  # Sentinel value for omitted parameters

# Type utilities
NoneType: Type[None]  # Used for response casting when no response expected

# Common type aliases
# File upload types - can be specified in multiple formats:
#   - Raw file content (bytes, file object, etc.)
#   - (filename, content) tuple
#   - (filename, content, mime_type) tuple
FileTypes = Union[
    FileContent,  # Just the file bytes/buffer
    Tuple[Optional[str], FileContent],  # (filename, content)
    Tuple[Optional[str], FileContent, Optional[str]]  # (filename, content, mime_type)
]

# Timeout can be a float (seconds) or an httpx.Timeout object for fine-grained control
Timeout = Union[float, httpx.Timeout]

# Azure AD Token Provider
# Callable that returns Azure AD tokens for authentication with Azure OpenAI
# Can be sync or async function
AzureADTokenProvider = Callable[[], str] | Callable[[], Awaitable[str]]

# Default configuration constants
DEFAULT_TIMEOUT: httpx.Timeout  # Default timeout: 600s total, 5s connect
DEFAULT_MAX_RETRIES: int  # Default maximum retries: 2
DEFAULT_CONNECTION_LIMITS: httpx.Limits  # Default connection limits: 1000 max connections, 100 keepalive

# Type aliases for specific domains
VideoModel = Literal["sora-2", "sora-2-pro"]
VideoSeconds = int  # Duration in seconds
VideoSize = str  # e.g., "720x1280"

# Request configuration
class RequestOptions(TypedDict, total=False):
    """Options for individual API requests."""
    extra_headers: dict[str, str]
    extra_query: dict[str, object]
    extra_body: dict[str, object]
    timeout: float | httpx.Timeout

# WebSocket configuration for Realtime API
class WebsocketConnectionOptions(TypedDict, total=False):
    """WebSocket connection options for realtime API connections."""
    extensions: Sequence[ClientExtensionFactory] | None  # List of supported extensions
    subprotocols: Sequence[Subprotocol] | None  # List of supported subprotocols
    compression: str | None  # Compression setting ("permessage-deflate" enabled by default, None to disable)
    max_size: int | None  # Maximum size of incoming messages in bytes
    max_queue: int | None | tuple[int | None, int | None]  # High-water mark of receive buffer
    write_limit: int | tuple[int, int | None]  # High-water mark of write buffer in bytes

# Response wrappers
class HttpxBinaryResponseContent:
    """Binary response content for audio, images, etc."""
    content: bytes
    response: httpx.Response
    def read(self) -> bytes: ...
    def write_to_file(self, file: str | os.PathLike) -> None: ...

# Pagination types
class SyncPage[T]:
    """Standard pagination."""
    data: list[T]
    object: str
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T: ...

class AsyncPage[T]:
    """Async pagination."""
    data: list[T]
    object: str
    def __aiter__(self) -> AsyncIterator[T]: ...
    def __anext__(self) -> T: ...

class SyncCursorPage[T]:
    """Cursor-based pagination."""
    data: list[T]
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T: ...

class AsyncCursorPage[T]:
    """Async cursor-based pagination."""
    data: list[T]
    has_more: bool
    def __aiter__(self) -> AsyncIterator[T]: ...
    def __anext__(self) -> T: ...

class SyncConversationCursorPage[T]:
    """Conversation cursor-based pagination."""
    data: list[T]
    has_more: bool
    last_id: str | None
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T: ...

class AsyncConversationCursorPage[T]:
    """Async conversation cursor-based pagination."""
    data: list[T]
    has_more: bool
    last_id: str | None
    def __aiter__(self) -> AsyncIterator[T]: ...
    def __anext__(self) -> T: ...

# Streaming types
class Stream[T]:
    """Synchronous streaming."""
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T: ...
    def __enter__(self) -> Stream[T]: ...
    def __exit__(self, *args) -> None: ...
    def close(self) -> None: ...

class AsyncStream[T]:
    """Asynchronous streaming."""
    def __aiter__(self) -> AsyncIterator[T]: ...
    def __anext__(self) -> T: ...
    async def __aenter__(self) -> AsyncStream[T]: ...
    async def __aexit__(self, *args) -> None: ...
    async def close(self) -> None: ...
```

## Helper Utilities

```python { .api }
# Package Information
__title__: str  # Package name ("openai")
VERSION: str  # Library version string
__version__: str  # Library version (same as VERSION)

# Pydantic Base Model
BaseModel  # Base class for creating custom Pydantic models (from pydantic import BaseModel)

# HTTP Client Classes
class DefaultHttpxClient:
    """Default synchronous httpx client with connection pooling."""

class DefaultAsyncHttpxClient:
    """Default asynchronous httpx client with connection pooling."""

class DefaultAioHttpClient:
    """Alternative async HTTP client using aiohttp."""

# Additional Type Exports
Transport: type  # HTTP transport type (httpx.BaseTransport)
ProxiesTypes: type  # Proxy configuration type

# File and Function Utilities
def file_from_path(path: str) -> FileTypes:
    """
    Load a file from filesystem path for upload to OpenAI API.

    Args:
        path: Filesystem path to the file

    Returns:
        FileTypes: A (filename, content, mime_type) tuple suitable for API upload
    """

def pydantic_function_tool(
    model: Type[BaseModel],
    *,
    name: str | None = None,
    description: str | None = None
) -> ChatCompletionToolParam:
    """
    Create a function tool definition from a Pydantic model for use with chat completions.

    Args:
        model: Pydantic model class defining the function parameters schema
        name: Optional function name (defaults to model class name in snake_case)
        description: Optional function description (defaults to model docstring)

    Returns:
        ChatCompletionToolParam: A tool definition dict with 'type' and 'function' keys.
                                 Type from openai.types.chat module.
                                 Can be passed to chat.completions.create(tools=[...])
    """

class AssistantEventHandler:
    """Base class for handling assistant streaming events."""
    def on_event(self, event) -> None: ...
    def on_run_step_created(self, run_step) -> None: ...
    def on_run_step_done(self, run_step) -> None: ...
    def on_tool_call_created(self, tool_call) -> None: ...
    def on_tool_call_done(self, tool_call) -> None: ...
    def on_message_created(self, message) -> None: ...
    def on_message_done(self, message) -> None: ...
    def on_text_created(self, text) -> None: ...
    def on_text_delta(self, delta, snapshot) -> None: ...
    def on_text_done(self, text) -> None: ...

class AsyncAssistantEventHandler:
    """Base class for handling assistant streaming events asynchronously."""
    async def on_event(self, event) -> None: ...
    async def on_run_step_created(self, run_step) -> None: ...
    async def on_run_step_done(self, run_step) -> None: ...
    async def on_tool_call_created(self, tool_call) -> None: ...
    async def on_tool_call_done(self, tool_call) -> None: ...
    async def on_message_created(self, message) -> None: ...
    async def on_message_done(self, message) -> None: ...
    async def on_text_created(self, text) -> None: ...
    async def on_text_delta(self, delta, snapshot) -> None: ...
    async def on_text_done(self, text) -> None: ...

# Audio Recording Helper
class Microphone(Generic[DType]):
    """
    Microphone helper for recording audio input from default audio device.

    Requires optional dependencies: numpy, sounddevice
    Install with: pip install openai[voice_helpers]

    Type Parameters:
        DType: numpy dtype for audio data (default: np.int16)
    """
    def __init__(
        self,
        channels: int = 1,
        dtype: Type[DType] = np.int16,
        should_record: Callable[[], bool] | None = None,
        timeout: float | None = None,
    ):
        """
        Initialize microphone for recording.

        Args:
            channels: Number of audio channels (1 for mono, 2 for stereo)
            dtype: Numpy data type for audio samples
            should_record: Optional callback function that returns True while recording should continue
            timeout: Maximum recording duration in seconds (None for unlimited)
        """

    async def record(
        self,
        return_ndarray: bool | None = False
    ) -> npt.NDArray[DType] | FileTypes:
        """
        Record audio from microphone.

        Args:
            return_ndarray: If True, return numpy array; if False, return WAV file tuple

        Returns:
            Either a numpy array of audio samples or FileTypes tuple (filename, buffer, mime_type)
            suitable for passing to OpenAI API methods.
        """

# Audio Playback Helper
class LocalAudioPlayer:
    """
    Local audio player for playing audio content through default audio device.

    Requires optional dependencies: numpy, sounddevice
    Install with: pip install openai[voice_helpers]

    The player uses a fixed sample rate of 24000 Hz, 1 channel (mono), and float32 dtype.
    """
    def __init__(
        self,
        should_stop: Callable[[], bool] | None = None,
    ):
        """
        Initialize audio player.

        Args:
            should_stop: Optional callback function that returns True to stop playback
        """

    async def play(
        self,
        input: npt.NDArray[np.int16] | npt.NDArray[np.float32] | HttpxBinaryResponseContent | AsyncStreamedBinaryAPIResponse | StreamedBinaryAPIResponse
    ) -> None:
        """
        Play audio data through local audio device.

        Args:
            input: Audio data as numpy array (int16 or float32) or response content from TTS API
        """

    async def play_stream(
        self,
        buffer_stream: AsyncGenerator[npt.NDArray[np.float32] | npt.NDArray[np.int16] | None, None]
    ) -> None:
        """
        Stream and play audio data as it arrives.

        Useful for playing streaming audio responses from realtime API.

        Args:
            buffer_stream: Async generator yielding audio buffers (numpy arrays) or None to signal completion
        """
```

## Agent Integration Patterns

### Pattern 1: Simple Question-Answer Agent

```python
from openai import OpenAI, OpenAIError

class SimpleAgent:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"

    def ask(self, question: str) -> str:
        """Ask a single question and get an answer."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": question}]
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            return f"Error: {e}"

# Usage
agent = SimpleAgent()
answer = agent.ask("What is the capital of France?")
print(answer)
```

### Pattern 2: Conversational Agent with Memory

```python
from openai import OpenAI
from typing import List, Dict

class ConversationalAgent:
    def __init__(self, system_prompt: str, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def chat(self, user_message: str) -> str:
        """Send a message and maintain conversation history."""
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )

        assistant_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def reset(self):
        """Clear conversation history (keep system prompt)."""
        self.messages = [self.messages[0]]

# Usage
agent = ConversationalAgent("You are a helpful Python expert.")
print(agent.chat("How do I read a file?"))
print(agent.chat("And how do I write to it?"))  # Maintains context
```

### Pattern 3: Function-Calling Agent

```python
from openai import OpenAI
import json

class FunctionAgent:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"

        # Define available functions
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

    def execute_function(self, name: str, arguments: str) -> str:
        """Execute the actual function call."""
        args = json.loads(arguments)

        if name == "get_weather":
            # Implement actual weather lookup
            location = args["location"]
            unit = args.get("unit", "celsius")
            return f"The weather in {location} is 22°{unit[0].upper()}"

        return f"Unknown function: {name}"

    def run(self, user_query: str) -> str:
        """Run agent with function calling capability."""
        messages = [{"role": "user", "content": user_query}]

        # Initial request
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        # Handle function calls
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments

                # Execute function
                function_response = self.execute_function(function_name, function_args)

                # Add function response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response
                })

            # Get final response
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return final_response.choices[0].message.content

        return response_message.content

# Usage
agent = FunctionAgent()
result = agent.run("What's the weather in London?")
print(result)
```

### Pattern 4: Structured Output Agent

```python
from openai import OpenAI
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    """A single task."""
    title: str
    description: str
    priority: int  # 1-5

class TaskList(BaseModel):
    """A list of tasks."""
    tasks: List[Task]

class StructuredAgent:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"

    def extract_tasks(self, text: str) -> TaskList:
        """Extract structured task list from text."""
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "Extract tasks from the user's text."},
                {"role": "user", "content": text}
            ],
            response_format=TaskList
        )

        return completion.choices[0].message.parsed

# Usage
agent = StructuredAgent()
text = "I need to finish the report by Friday, call the client tomorrow, and review the code this afternoon."
tasks = agent.extract_tasks(text)

for task in tasks.tasks:
    print(f"[P{task.priority}] {task.title}: {task.description}")
```

### Pattern 5: Streaming Agent

```python
from openai import OpenAI
from typing import Generator

class StreamingAgent:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"

    def stream_response(self, prompt: str) -> Generator[str, None, None]:
        """Stream response token by token."""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat_stream(self, prompt: str) -> str:
        """Chat with streaming, return complete response."""
        full_response = []
        for chunk in self.stream_response(prompt):
            print(chunk, end="", flush=True)
            full_response.append(chunk)
        print()  # Newline after stream
        return "".join(full_response)

# Usage
agent = StreamingAgent()
response = agent.chat_stream("Tell me a short story about AI.")
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "APIError: The api_key client option must be set"
**Solution**: Set the OPENAI_API_KEY environment variable or pass api_key explicitly:
```python
# Option 1: Environment variable
import os
os.environ["OPENAI_API_KEY"] = "your-key"
client = OpenAI()

# Option 2: Explicit parameter
client = OpenAI(api_key="your-key")
```

#### Issue: Rate limiting (429 errors)
**Solution**: Implement exponential backoff retry logic (see error handling patterns above).

#### Issue: "InvalidRequestError: This model's maximum context length is X tokens"
**Solution**: Reduce message history or use a model with larger context:
```python
# Truncate old messages
max_messages = 10
messages = messages[-max_messages:]

# Or use a larger context model
model = "gpt-4-turbo"  # 128K context
```

#### Issue: Streaming responses cut off
**Solution**: Check finish_reason and handle properly:
```python
stream = client.chat.completions.create(model="gpt-4", messages=messages, stream=True)
for chunk in stream:
    if chunk.choices[0].finish_reason == "length":
        print("[Response truncated - increase max_tokens]")
    elif chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Issue: Async code not working
**Solution**: Ensure you're using AsyncOpenAI and await properly:
```python
from openai import AsyncOpenAI
import asyncio

async def main():
    client = AsyncOpenAI()
    response = await client.chat.completions.create(...)
    print(response.choices[0].message.content)

asyncio.run(main())
```

#### Issue: File uploads failing
**Solution**: Use proper file handling with context managers:
```python
from openai import OpenAI

client = OpenAI()

# Correct approach
with open("file.txt", "rb") as f:
    file_obj = client.files.create(file=f, purpose="assistants")

# Or use file_from_path helper
from openai import file_from_path
file_obj = client.files.create(file=file_from_path("file.txt"), purpose="assistants")
```

#### Issue: Azure OpenAI authentication errors
**Solution**: Verify you're using the correct authentication method:
```python
from openai import AzureOpenAI

# Correct for Azure API key
client = AzureOpenAI(
    api_key="your-azure-key",  # NOT OpenAI key
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_version="2024-02-15-preview"
)
```
