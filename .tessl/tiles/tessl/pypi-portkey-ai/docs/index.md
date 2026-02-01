# Portkey AI

Python client library for the Portkey API - Control Panel for AI Apps. Built on top of the OpenAI SDK, allowing seamless integration of Portkey's advanced features including AI Gateway capabilities (unified API signature, automated fallbacks & retries, load balancing, semantic caching, virtual keys), and comprehensive observability features (logging, request tracing, custom metadata, feedback collection, analytics).

## Package Information

- **Package Name**: portkey-ai
- **Language**: Python
- **Installation**: `pip install portkey-ai`

## Core Imports

```python
from portkey_ai import Portkey, AsyncPortkey
```

For OpenAI compatibility:

```python
from portkey_ai import openai
```

For specific components:

```python
from portkey_ai import (
    Config, 
    LLMOptions, 
    Modes,
    ProviderTypes,
    createHeaders
)
```

## Basic Usage

```python
from portkey_ai import Portkey

# Initialize client with API key and virtual key
portkey = Portkey(
    api_key="PORTKEY_API_KEY", 
    virtual_key="VIRTUAL_KEY"
)

# Make a chat completion request
chat_completion = portkey.chat.completions.create(
    messages=[{"role": "user", "content": "Say this is a test"}],
    model="gpt-4"
)

print(chat_completion)
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def main():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    chat_completion = await portkey.chat.completions.create(
        messages=[{"role": "user", "content": "Say this is a test"}],
        model="gpt-4"
    )
    
    print(chat_completion)

asyncio.run(main())
```

## Architecture

Portkey's architecture centers around two main client classes that provide comprehensive AI API management:

- **Portkey/AsyncPortkey**: Main client classes providing unified interface to 40+ AI providers
- **API Resources**: Organized into functional areas (chat, completions, images, audio, etc.)
- **Configuration System**: Flexible config management for providers, fallbacks, retries, and routing
- **Observability Layer**: Built-in logging, tracing, analytics, and feedback collection
- **Security Layer**: Virtual key management and secure credential handling

The dual client pattern ensures both synchronous and asynchronous support across all operations, while maintaining full OpenAI SDK compatibility.

## Capabilities

### Core Client & Configuration

Primary client classes and configuration utilities for initializing and managing Portkey connections with comprehensive provider support and advanced routing capabilities.

```python { .api }
class Portkey:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        virtual_key: Optional[str] = None,
        config: Optional[Union[Mapping, str]] = None,
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Union[Optional[dict[str, str]], str] = None,
        **kwargs
    ) -> None: ...

class AsyncPortkey:
    def __init__(self, **kwargs) -> None: ...

def createHeaders(**kwargs) -> dict: ...
```

[Core Client & Configuration](./core-client.md)

### Chat Completions

OpenAI-compatible chat completion API with support for all major providers, streaming, function calling, and advanced Portkey features like fallbacks and load balancing.

```python { .api }
class ChatCompletion:
    completions: Completions

class Completions:
    def create(
        self,
        *,
        messages: Iterable[dict],
        model: Optional[str] = "portkey-default",
        **kwargs
    ) -> Union[ChatCompletions, Iterator[ChatCompletionChunk]]: ...
    
    messages: ChatCompletionsMessages

class AsyncChatCompletion:
    completions: AsyncCompletions
```

[Chat Completions](./chat-completions.md)

### Text Completions

Legacy text completion API for non-chat models, supporting streaming and all OpenAI-compatible parameters with Portkey enhancements.

```python { .api }
class Completion:
    def create(
        self,
        *,
        prompt: Union[str, List[str]],
        model: str,
        **kwargs
    ) -> Union[TextCompletion, Iterator[TextCompletionChunk]]: ...

class AsyncCompletion:
    async def create(
        self,
        *,
        prompt: Union[str, List[str]],
        model: str,
        **kwargs
    ) -> Union[TextCompletion, AsyncIterator[TextCompletionChunk]]: ...
```

[Text Completions](./text-completions.md)

### Prompt Management

Advanced prompt management system with templating, rendering, versioning, and prompt execution capabilities.

```python { .api }
class Prompts:
    def render(self, **kwargs): ...
    def completions(self, **kwargs): ...

class AsyncPrompts:
    async def render(self, **kwargs): ...
    async def completions(self, **kwargs): ...

class Generations:
    def create(self, **kwargs): ...

class AsyncGenerations:
    async def create(self, **kwargs): ...
```

[Prompt Management](./prompt-management.md)

### Embeddings

Text embedding generation for semantic similarity, search, and machine learning applications with support for multiple providers.

```python { .api }
class Embeddings:
    def create(
        self,
        *,
        input: str,
        model: Optional[str] = "portkey-default",
        dimensions: Union[int, NotGiven] = NOT_GIVEN,
        encoding_format: Union[str, NotGiven] = NOT_GIVEN,
        user: Union[str, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> CreateEmbeddingResponse: ...

class AsyncEmbeddings:
    async def create(self, **kwargs) -> CreateEmbeddingResponse: ...
```

[Embeddings](./embeddings.md)

### Models

Model management and information retrieval for accessing available AI models across different providers.

```python { .api }
class Models:
    def list(self, **kwargs) -> ModelList: ...
    def retrieve(
        self,
        model: str,
        *,
        timeout: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> Model: ...
    def delete(
        self,
        model: str,
        *,
        timeout: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> ModelDeleted: ...

class AsyncModels:
    async def list(self, **kwargs) -> ModelList: ...
    async def retrieve(self, model: str, **kwargs) -> Model: ...
    async def delete(self, model: str, **kwargs) -> ModelDeleted: ...
```

[Models](./models.md)

### Multimodal APIs

Image generation, audio processing (speech-to-text, text-to-speech, translation), and content moderation capabilities with OpenAI compatibility.

```python { .api }
class Images:
    def generate(self, **kwargs): ...
    def create_variation(self, **kwargs): ...
    def edit(self, **kwargs): ...

class Audio:
    transcriptions: Transcriptions
    translations: Translations
    speech: Speech

class Moderations:
    def create(self, **kwargs): ...
```

[Multimodal APIs](./multimodal-apis.md)

### File Management

File upload, management, and processing capabilities including support for assistants, fine-tuning, and batch operations.

```python { .api }
class MainFiles:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def delete(self, **kwargs): ...

class Uploads:
    def create(self, **kwargs): ...
    parts: Parts
```

[File Management](./file-management.md)

### Assistants & Threads

OpenAI Assistants API implementation with thread management, message handling, and tool execution support.

```python { .api }
class Assistants:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...

class Threads:
    def create(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
    messages: Messages
    runs: Runs
```

[Assistants & Threads](./assistants-threads.md)

### Vector Stores

Vector database operations for retrieval-augmented generation (RAG) applications with file management and batch processing.

```python { .api }
class VectorStores:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
    files: VectorFiles
    file_batches: VectorFileBatches
```

[Vector Stores](./vector-stores.md)

### Fine-Tuning

Model fine-tuning capabilities with job management, checkpoint handling, and training monitoring.

```python { .api }
class FineTuning:
    jobs: Jobs
    checkpoints: Checkpoints

class Jobs:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def cancel(self, **kwargs): ...
```

[Fine-Tuning](./fine-tuning.md)

### Batch Processing

Batch API for processing large volumes of requests efficiently with cost optimization and result management.

```python { .api }
class Batches:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def cancel(self, **kwargs): ...
```

[Batch Processing](./batch-processing.md)

### Administration & User Management

Administrative functions for managing users, workspaces, invitations, and organizational settings.

```python { .api }
class Admin:
    users: Users
    invites: Invites
    workspaces: Workspaces

class Users:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
```

[Administration & User Management](./administration.md)

### Configuration Management

Advanced configuration system for managing provider settings, routing rules, fallback strategies, and load balancing configurations.

```python { .api }
class Configs:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
```

[Configuration Management](./configuration-management.md)

### API Key & Virtual Key Management

Secure API key and virtual key management for credential protection and access control.

```python { .api }
class ApiKeys:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...

class VirtualKeys:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
```

[API Key & Virtual Key Management](./key-management.md)

### Observability & Analytics

Comprehensive logging, request tracing, analytics, and monitoring capabilities with custom metadata and performance metrics.

```python { .api }
class Logs:
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class Responses:
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    input_items: InputItems
    output_items: OutputItems

class Labels:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
```

[Observability & Analytics](./observability-analytics.md)

### Feedback & Collections

User feedback collection and data organization capabilities for improving AI applications and gathering insights.

```python { .api }
class Feedback:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class Collections:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
```

[Feedback & Collections](./feedback-collections.md)

### Evaluation & Testing

AI evaluation framework with automated grading, test execution, and performance measurement capabilities.

```python { .api }
class Evals:
    runs: EvalsRuns

class EvalsRuns:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class Alpha:
    graders: Graders

class Graders:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
```

[Evaluation & Testing](./evaluation-testing.md)

### Container & Content Management

Container-based deployment and content management capabilities for scalable AI applications.

```python { .api }
class Containers:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
    files: ContainersFiles

class Content:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
```

[Container & Content Management](./container-content.md)

### Large File Uploads

Multi-part upload system for large files with chunked upload support and integrity verification.

```python { .api }
class Uploads:
    def create(
        self,
        *,
        bytes: int,
        filename: str,
        mime_type: str,
        purpose: Any,
        **kwargs
    ) -> Upload: ...
    
    def upload_file_chunked(
        self,
        *,
        file: Union[os.PathLike[str], bytes],
        mime_type: str,
        purpose: Any,
        **kwargs
    ) -> Any: ...
    
    def complete(
        self,
        upload_id: str,
        *,
        part_ids: List[str],
        **kwargs
    ) -> Upload: ...
    
    parts: Parts

class AsyncUploads:
    async def create(self, **kwargs) -> Upload: ...
    async def upload_file_chunked(self, **kwargs) -> Any: ...
    async def complete(self, upload_id: str, **kwargs) -> Upload: ...
    parts: AsyncParts
```

[Large File Uploads](./uploads.md)

### Beta Realtime API

Real-time audio and WebSocket-based AI interactions for building conversational applications with low-latency voice communication.

```python { .api }
class BetaRealtime:
    def connect(
        self,
        *,
        model: str,
        websocket_connection_options: WebsocketConnectionOptions = {},
        **kwargs
    ) -> RealtimeConnectionManager: ...
    
    sessions: BetaSessions

class BetaSessions:
    def create(
        self,
        *,
        model: Any = "portkey-default",
        modalities: Union[List[Any], NotGiven] = NOT_GIVEN,
        voice: Union[Any, NotGiven] = NOT_GIVEN,
        instructions: Union[str, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> SessionCreateResponse: ...

class AsyncBetaRealtime:
    def connect(self, **kwargs) -> AsyncRealtimeConnectionManager: ...
    sessions: AsyncBetaSessions
```

[Beta Realtime API](./beta-realtime.md)

### Provider & Integration Management

Management of AI providers and third-party integrations with workspace-level and model-level configuration.

```python { .api }
class Providers:
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class Integrations:
    workspaces: IntegrationsWorkspaces
    models: IntegrationsModels

class IntegrationsWorkspaces:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
```

[Provider & Integration Management](./provider-integration.md)

### Framework Integrations

Pre-built integrations with popular AI frameworks including LangChain and LlamaIndex callback handlers.

```python { .api }
from portkey_ai.langchain import PortkeyLangchainCallbackHandler
from portkey_ai.llamaindex import PortkeyLlamaCallbackHandler
```

[Framework Integrations](./framework-integrations.md)

## Types

### Core Configuration Types

```python { .api }
class Config(TypedDict):
    """Configuration object for Portkey requests"""
    ...

class LLMOptions(TypedDict):
    """LLM-specific options and parameters"""
    ...

class Modes(Enum):
    """Available Portkey modes"""
    SINGLE = "single"
    FALLBACK = "fallback"
    LOADBALANCE = "loadbalance"
    AB_TEST = "ab_test"

class ProviderTypes(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure-openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    # ... and 35+ more providers

class RetrySettings(TypedDict):
    """Retry configuration settings"""
    attempts: int
    on_status_codes: List[int]
```

### Response Types

```python { .api }
class PortkeyResponse:
    """Base response class for all Portkey operations"""
    ...

class ChatCompletions:
    """Chat completion response"""
    id: str
    object: str
    created: int
    model: str
    choices: List[dict]
    usage: dict

class ChatCompletionChunk:
    """Streaming chat completion chunk"""
    id: str
    object: str
    created: int
    model: str
    choices: List[dict]

class TextCompletion:
    """Text completion response"""
    id: str
    object: str
    created: int
    model: str
    choices: List[dict]
    usage: dict

class Message:
    """Message object for chat completions"""
    role: str
    content: str
```

### Exception Types

```python { .api }
class APIStatusError(Exception):
    """Base exception for API status errors"""
    ...

class BadRequestError(APIStatusError):
    """400 Bad Request error"""
    ...

class AuthenticationError(APIStatusError):
    """401 Authentication error"""
    ...

class PermissionDeniedError(APIStatusError):
    """403 Permission denied error"""
    ...

class NotFoundError(APIStatusError):
    """404 Not found error"""
    ...

class RateLimitError(APIStatusError):
    """429 Rate limit error"""
    ...

class InternalServerError(APIStatusError):
    """500 Internal server error"""
    ...
```