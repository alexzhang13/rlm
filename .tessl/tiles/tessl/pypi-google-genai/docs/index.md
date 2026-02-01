# Google GenAI Python SDK

A comprehensive Python SDK for integrating Google's generative AI models into applications, supporting both the Gemini Developer API and Vertex AI APIs. The SDK provides a unified interface for content generation, multi-turn conversations, embeddings, image and video generation, file management, caching, batch processing, fine-tuning, and real-time bidirectional streaming.

## Package Information

- **Package Name**: google-genai
- **Language**: Python
- **Installation**: `pip install google-genai`
- **Version**: 1.51.0

## Core Imports

```python
from google import genai
```

Common imports:

```python
from google.genai import Client
from google.genai import types
```

## Basic Usage

```python
from google.genai import Client

# Initialize client with API key (Gemini Developer API)
client = Client(api_key='YOUR_API_KEY')

# Generate content
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Explain how AI works in simple terms.'
)
print(response.text)

# Multi-turn chat
chat = client.chats.create(model='gemini-2.0-flash')
response = chat.send_message('What is machine learning?')
print(response.text)

# Close client
client.close()
```

With context manager:

```python
from google.genai import Client

with Client(api_key='YOUR_API_KEY') as client:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello!'
    )
    print(response.text)
```

## Architecture

The SDK follows a modular architecture with these key components:

- **Client**: Main entry point providing access to all API modules, supports both Gemini Developer API (api_key) and Vertex AI (credentials/project)
- **API Modules**: Specialized interfaces for models, chats, files, caches, batches, tunings, file_search_stores, operations, live
- **Types System**: Comprehensive type definitions with both Pydantic models and TypedDict variants for flexible usage
- **Async Support**: Complete async/await implementations via the `aio` property on the Client
- **Streaming**: Built-in streaming support for content generation and live interactions
- **Function Calling**: Automatic and manual function calling with Python functions or JSON schemas

## Capabilities

### Client Initialization

Initialize the main client to access all SDK functionality with support for both Gemini Developer API and Vertex AI.

```python { .api }
class Client:
    def __init__(
        self,
        *,
        vertexai: Optional[bool] = None,
        api_key: Optional[str] = None,
        credentials: Optional[google.auth.credentials.Credentials] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        debug_config: Optional[DebugConfig] = None,
        http_options: Optional[Union[HttpOptions, HttpOptionsDict]] = None
    ): ...

    @property
    def aio(self) -> AsyncClient: ...

    def close(self) -> None: ...
    def __enter__(self) -> 'Client': ...
    def __exit__(self, *args) -> None: ...

class AsyncClient:
    @property
    def models(self) -> AsyncModels: ...
    @property
    def chats(self) -> AsyncChats: ...
    @property
    def files(self) -> AsyncFiles: ...
    @property
    def caches(self) -> AsyncCaches: ...
    @property
    def batches(self) -> AsyncBatches: ...
    @property
    def tunings(self) -> AsyncTunings: ...
    @property
    def file_search_stores(self) -> AsyncFileSearchStores: ...
    @property
    def live(self) -> AsyncLive: ...
    @property
    def operations(self) -> AsyncOperations: ...

    async def aclose(self) -> None: ...
    async def __aenter__(self) -> 'AsyncClient': ...
    async def __aexit__(self, *args) -> None: ...
```

[Client Initialization](./client.md)

### Content Generation

Generate text and multimodal content using Gemini models with support for streaming, function calling, structured output, and extensive configuration options.

```python { .api }
def generate_content(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[GenerateContentConfig] = None
) -> GenerateContentResponse: ...

def generate_content_stream(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[GenerateContentConfig] = None
) -> Iterator[GenerateContentResponse]: ...
```

[Content Generation](./content-generation.md)

### Multi-Turn Conversations

Create and manage chat sessions for multi-turn conversations with automatic history management.

```python { .api }
class Chat:
    def send_message(
        self,
        message: Union[str, Content],
        config: Optional[GenerateContentConfig] = None
    ) -> GenerateContentResponse: ...

    def send_message_stream(
        self,
        message: Union[str, Content],
        config: Optional[GenerateContentConfig] = None
    ) -> Iterator[GenerateContentResponse]: ...

    def get_history(self, curated: bool = False) -> list[Content]: ...
```

[Multi-Turn Conversations](./chats.md)

### Embeddings

Generate text embeddings for semantic search, clustering, and similarity comparisons.

```python { .api }
def embed_content(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[EmbedContentConfig] = None
) -> EmbedContentResponse: ...
```

[Embeddings](./embeddings.md)

### Image Generation

Generate, edit, upscale, and segment images using Imagen models.

```python { .api }
def generate_images(
    *,
    model: str,
    prompt: str,
    config: Optional[GenerateImagesConfig] = None
) -> GenerateImagesResponse: ...

def edit_image(
    *,
    model: str,
    prompt: str,
    reference_images: Sequence[ReferenceImage],
    config: Optional[EditImageConfig] = None
) -> EditImageResponse: ...

def upscale_image(
    *,
    model: str,
    image: Image,
    upscale_factor: str,
    config: Optional[UpscaleImageConfig] = None
) -> UpscaleImageResponse: ...
```

[Image Generation](./image-generation.md)

### Video Generation

Generate videos from prompts, images, or existing videos using Veo models.

```python { .api }
def generate_videos(
    *,
    model: str,
    prompt: Optional[str] = None,
    image: Optional[Image] = None,
    video: Optional[Video] = None,
    config: Optional[GenerateVideosConfig] = None
) -> GenerateVideosOperation: ...
```

[Video Generation](./video-generation.md)

### File Management

Upload, manage, and download files for use with multimodal content generation (Gemini Developer API only).

```python { .api }
class Files:
    def upload(
        self,
        *,
        file: Union[str, Path, IO],
        config: Optional[UploadFileConfig] = None
    ) -> File: ...

    def get(self, *, name: str) -> File: ...
    def delete(self, *, name: str) -> None: ...
    def download(self, *, name: str, path: Optional[str] = None) -> bytes: ...
    def list(self, *, config: Optional[ListFilesConfig] = None) -> Union[Pager[File], Iterator[File]]: ...
```

[File Management](./files.md)

### Context Caching

Create and manage cached content to reduce costs and latency for repeated requests with shared context.

```python { .api }
class Caches:
    def create(
        self,
        *,
        model: str,
        config: CreateCachedContentConfig
    ) -> CachedContent: ...

    def get(self, *, name: str) -> CachedContent: ...
    def update(self, *, name: str, config: UpdateCachedContentConfig) -> CachedContent: ...
    def delete(self, *, name: str) -> None: ...
    def list(self, *, config: Optional[ListCachedContentsConfig] = None) -> Union[Pager[CachedContent], Iterator[CachedContent]]: ...
```

[Context Caching](./caching.md)

### Batch Processing

Submit batch prediction jobs for high-volume inference with cost savings.

```python { .api }
class Batches:
    def create(
        self,
        *,
        model: str,
        src: Union[str, list[dict]],
        dest: Optional[str] = None,
        config: Optional[CreateBatchJobConfig] = None
    ) -> BatchJob: ...

    def create_embeddings(
        self,
        *,
        model: str,
        src: Union[str, list[dict]],
        dest: Optional[str] = None,
        config: Optional[CreateBatchJobConfig] = None
    ) -> BatchJob: ...

    def get(self, *, name: str) -> BatchJob: ...
    def cancel(self, *, name: str) -> None: ...
    def delete(self, *, name: str) -> None: ...
    def list(self, *, config: Optional[ListBatchJobsConfig] = None) -> Union[Pager[BatchJob], Iterator[BatchJob]]: ...
```

[Batch Processing](./batches.md)

### Model Fine-Tuning

Create and manage supervised fine-tuning jobs to customize models (Vertex AI only).

```python { .api }
class Tunings:
    def tune(
        self,
        *,
        base_model: str,
        training_dataset: TuningDataset,
        config: Optional[CreateTuningJobConfig] = None
    ) -> TuningJob: ...

    def get(self, *, name: str, config: Optional[GetTuningJobConfig] = None) -> TuningJob: ...
    def cancel(self, *, name: str) -> None: ...
    def list(self, *, config: Optional[ListTuningJobsConfig] = None) -> Union[Pager[TuningJob], Iterator[TuningJob]]: ...
```

[Model Fine-Tuning](./tuning.md)

### File Search Stores

Create and manage file search stores with document retrieval for retrieval-augmented generation.

```python { .api }
class FileSearchStores:
    def create(self, *, config: CreateFileSearchStoreConfig) -> FileSearchStore: ...
    def get(self, *, name: str) -> FileSearchStore: ...
    def delete(self, *, name: str) -> None: ...
    def import_file(
        self,
        *,
        store: str,
        source: ImportFileSource,
        config: Optional[ImportFileConfig] = None
    ) -> ImportFileOperation: ...
    def upload_to_file_search_store(
        self,
        *,
        store: str,
        file: Union[str, Path, IO],
        config: Optional[UploadToFileSearchStoreConfig] = None
    ) -> UploadToFileSearchStoreOperation: ...
    def list(self, *, config: Optional[ListFileSearchStoresConfig] = None) -> Union[Pager[FileSearchStore], Iterator[FileSearchStore]]: ...
```

[File Search Stores](./file-search-stores.md)

### Live API

Real-time bidirectional streaming for interactive applications with support for audio, video, and function calling (Preview).

```python { .api }
class AsyncLive:
    async def connect(
        self,
        *,
        model: str,
        config: Optional[LiveConnectConfig] = None
    ) -> AsyncIterator[AsyncSession]: ...

class AsyncSession:
    async def send_client_content(
        self,
        *,
        turns: Optional[Union[Content, list[Content]]] = None,
        turn_complete: bool = False
    ) -> None: ...

    async def send_realtime_input(
        self,
        *,
        media_chunks: Optional[Sequence[Blob]] = None
    ) -> None: ...

    async def send_tool_response(
        self,
        *,
        function_responses: Sequence[FunctionResponse]
    ) -> None: ...

    async def receive(self) -> AsyncIterator[LiveServerMessage]: ...
    async def close(self) -> None: ...
```

[Live API](./live.md)

### Token Operations

Count tokens and compute detailed token information for content, with support for local tokenization without API calls.

```python { .api }
def count_tokens(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[CountTokensConfig] = None
) -> CountTokensResponse: ...

def compute_tokens(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[ComputeTokensConfig] = None
) -> ComputeTokensResponse: ...

class LocalTokenizer:
    def __init__(self, model_name: str): ...
    def count_tokens(
        self,
        contents: Union[str, list[Content], Content],
        *,
        config: Optional[CountTokensConfig] = None
    ) -> CountTokensResult: ...
    def compute_tokens(
        self,
        contents: Union[str, list[Content], Content]
    ) -> ComputeTokensResult: ...
```

[Token Operations](./tokens.md)

### Model Information

Retrieve and manage model information and capabilities.

```python { .api }
def get(self, *, model: str, config: Optional[GetModelConfig] = None) -> Model: ...
def update(self, *, model: str, config: UpdateModelConfig) -> Model: ...
def delete(self, *, model: str, config: Optional[DeleteModelConfig] = None) -> DeleteModelResponse: ...
def list(self, *, config: Optional[ListModelsConfig] = None) -> Union[Pager[Model], Iterator[Model]]: ...
```

[Model Information](./models.md)

### Long-Running Operations

Monitor and retrieve status of long-running operations like video generation and file imports.

```python { .api }
class Operations:
    def get(self, operation: Union[Operation, str]) -> Operation: ...
```

[Long-Running Operations](./operations.md)

## Core Types

### Content and Parts

```python { .api }
class Content:
    """Container for conversation content with role and parts."""
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """Individual content part - text, image, video, function call, etc."""
    text: Optional[str] = None
    inline_data: Optional[Blob] = None
    file_data: Optional[FileData] = None
    function_call: Optional[FunctionCall] = None
    function_response: Optional[FunctionResponse] = None
    executable_code: Optional[ExecutableCode] = None
    code_execution_result: Optional[CodeExecutionResult] = None

class Blob:
    """Binary data with MIME type."""
    mime_type: str
    data: bytes

class Image:
    """Image data - can be URL, file path, bytes, PIL Image, or FileData."""
    # Various constructors supported

class Video:
    """Video data - can be URL, file path, bytes, or FileData."""
    # Various constructors supported
```

### Generation Configuration

```python { .api }
class GenerateContentConfig:
    """Configuration for content generation."""
    system_instruction: Optional[Union[str, Content]] = None
    contents: Optional[Union[str, list[Content], Content]] = None
    generation_config: Optional[GenerationConfig] = None
    safety_settings: Optional[list[SafetySetting]] = None
    tools: Optional[list[Tool]] = None
    tool_config: Optional[ToolConfig] = None
    cached_content: Optional[str] = None

class GenerationConfig:
    """Core generation parameters."""
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    candidate_count: Optional[int] = None
    max_output_tokens: Optional[int] = None
    stop_sequences: Optional[list[str]] = None
    response_mime_type: Optional[str] = None
    response_schema: Optional[Schema] = None
```

### Response Types

```python { .api }
class GenerateContentResponse:
    """Response from content generation."""
    text: str  # Convenience property
    candidates: list[Candidate]
    usage_metadata: Optional[GenerateContentResponseUsageMetadata] = None
    prompt_feedback: Optional[GenerateContentResponsePromptFeedback] = None

class Candidate:
    """Generated candidate with content and metadata."""
    content: Content
    finish_reason: Optional[FinishReason] = None
    safety_ratings: Optional[list[SafetyRating]] = None
    citation_metadata: Optional[CitationMetadata] = None
    grounding_metadata: Optional[GroundingMetadata] = None
```

### Function Calling

```python { .api }
class Tool:
    """Tool containing function declarations."""
    function_declarations: Optional[list[FunctionDeclaration]] = None
    google_search: Optional[GoogleSearch] = None
    code_execution: Optional[ToolCodeExecution] = None

class FunctionDeclaration:
    """Function schema definition."""
    name: str
    description: str
    parameters: Optional[Schema] = None

class FunctionCall:
    """Function invocation from model."""
    name: str
    args: dict[str, Any]

class FunctionResponse:
    """Function execution response."""
    name: str
    response: dict[str, Any]
```

### Error Handling

```python { .api }
class APIError(Exception):
    """Base exception for API errors."""
    code: int
    status: Optional[str]
    message: Optional[str]
    details: Any

class ClientError(APIError):
    """Client errors (4xx status codes)."""
    pass

class ServerError(APIError):
    """Server errors (5xx status codes)."""
    pass
```

## Type System

The SDK provides comprehensive type coverage with 695+ type classes organized into categories including:

- **Enumerations** (50+): HarmCategory, HarmBlockThreshold, FinishReason, BlockedReason, etc.
- **Content Types** (20+): Content, Part, Blob, Image, Video, FileData, etc.
- **Function Calling** (15+): Tool, FunctionDeclaration, FunctionCall, FunctionResponse, etc.
- **Retrieval & RAG** (25+): GoogleSearchRetrieval, FileSearch, VertexAISearch, VertexRagStore, etc.
- **Generation Config** (30+): GenerateContentConfig, GenerationConfig, SafetySetting, etc.
- **Response Types** (40+): GenerateContentResponse, Candidate, SafetyRating, GroundingMetadata, etc.
- **Embeddings** (10+): EmbedContentConfig, EmbedContentResponse, ContentEmbedding, etc.
- **Image Generation** (40+): GenerateImagesConfig, EditImageConfig, UpscaleImageConfig, etc.
- **Video Generation** (20+): GenerateVideosConfig, GenerateVideosResponse, GeneratedVideo, etc.
- **Model Management** (20+): Model, TunedModelInfo, Endpoint, etc.
- **Tuning** (30+): TuningJob, TuningDataset, SupervisedTuningSpec, HyperParameters, etc.
- **Batches** (20+): BatchJob, CreateBatchJobConfig, etc.
- **Caching** (15+): CachedContent, CreateCachedContentConfig, etc.
- **Files** (20+): File, FileStatus, UploadFileConfig, etc.
- **Live API** (60+): LiveConnectConfig, LiveClientMessage, LiveServerMessage, etc.

All types are available via `from google.genai import types` and include both Pydantic models and TypedDict variants for flexible usage.
