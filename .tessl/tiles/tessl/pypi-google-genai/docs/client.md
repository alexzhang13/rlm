# Client Initialization and Configuration

Client initialization and configuration for accessing the Google GenAI Python SDK. The SDK supports both the Gemini Developer API (using API keys) and Vertex AI API (using Google Cloud credentials and project configuration). The Client class provides access to all SDK functionality through specialized API modules.

## Capabilities

### Client Initialization

Initialize the main synchronous client to access all SDK functionality. The client automatically determines which API to use based on the provided configuration.

```python { .api }
class Client:
    """
    Primary synchronous client for making requests to Gemini Developer API or Vertex AI API.

    Parameters:
        vertexai (bool, optional): Use Vertex AI API endpoints. Defaults to False (Gemini Developer API).
            Can be set via GOOGLE_GENAI_USE_VERTEXAI environment variable.
        api_key (str, optional): API key for Gemini Developer API authentication.
            Can be set via GOOGLE_API_KEY environment variable.
        credentials (google.auth.credentials.Credentials, optional): Google Cloud credentials for Vertex AI API.
            Uses Application Default Credentials if not provided.
        project (str, optional): Google Cloud project ID for Vertex AI API quota.
            Can be set via GOOGLE_CLOUD_PROJECT environment variable.
        location (str, optional): Google Cloud location for Vertex AI API (e.g., 'us-central1').
            Can be set via GOOGLE_CLOUD_LOCATION environment variable.
        debug_config (DebugConfig, optional): Configuration for testing and debugging network behavior.
        http_options (Union[HttpOptions, HttpOptionsDict], optional): HTTP client configuration options.

    Returns:
        Client instance providing access to all SDK API modules.
    """
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
    def aio(self) -> AsyncClient:
        """Access the async client interface for non-blocking operations."""
        ...

    @property
    def models(self) -> Models:
        """Access models API for content generation, embeddings, and image/video generation."""
        ...

    @property
    def chats(self) -> Chats:
        """Create multi-turn chat sessions with automatic history management."""
        ...

    @property
    def files(self) -> Files:
        """Access file management API (Gemini Developer API only)."""
        ...

    @property
    def caches(self) -> Caches:
        """Access cached content API for context caching."""
        ...

    @property
    def batches(self) -> Batches:
        """Access batch prediction jobs API."""
        ...

    @property
    def tunings(self) -> Tunings:
        """Access tuning jobs API (Vertex AI only)."""
        ...

    @property
    def file_search_stores(self) -> FileSearchStores:
        """Access file search stores API for retrieval-augmented generation."""
        ...

    @property
    def auth_tokens(self) -> Tokens:
        """Access authentication tokens API."""
        ...

    @property
    def operations(self) -> Operations:
        """Access long-running operations API."""
        ...

    @property
    def vertexai(self) -> bool:
        """Returns True if the client is using Vertex AI API, False otherwise."""
        ...

    def close(self) -> None:
        """
        Close the synchronous client explicitly to release resources.

        Note: This does not close the async client. Use Client.aio.aclose() for async client.
        """
        ...

    def __enter__(self) -> 'Client':
        """Context manager entry for automatic resource cleanup."""
        ...

    def __exit__(self, *args) -> None:
        """Context manager exit for automatic resource cleanup."""
        ...
```

**Usage Example - Gemini Developer API:**

```python
from google.genai import Client

# Initialize with API key
client = Client(api_key='YOUR_API_KEY')

# Generate content
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Explain quantum computing'
)
print(response.text)

# Close when done
client.close()
```

**Usage Example - Context Manager:**

```python
from google.genai import Client

with Client(api_key='YOUR_API_KEY') as client:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello!'
    )
    print(response.text)
# Client automatically closes
```

**Usage Example - Vertex AI:**

```python
from google.genai import Client

# Initialize for Vertex AI
client = Client(
    vertexai=True,
    project='my-project-id',
    location='us-central1'
)

# Generate content
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Explain machine learning'
)
print(response.text)

client.close()
```

### Async Client

Access asynchronous (non-blocking) client for concurrent operations. The async client provides the same API modules as the sync client but with async/await support.

```python { .api }
class AsyncClient:
    """
    Asynchronous client for making non-blocking requests.

    Access via Client.aio property. All methods are async and require await.
    """

    @property
    def models(self) -> AsyncModels:
        """Access async models API."""
        ...

    @property
    def chats(self) -> AsyncChats:
        """Create async multi-turn chat sessions."""
        ...

    @property
    def files(self) -> AsyncFiles:
        """Access async file management API."""
        ...

    @property
    def caches(self) -> AsyncCaches:
        """Access async cached content API."""
        ...

    @property
    def batches(self) -> AsyncBatches:
        """Access async batch prediction jobs API."""
        ...

    @property
    def tunings(self) -> AsyncTunings:
        """Access async tuning jobs API."""
        ...

    @property
    def file_search_stores(self) -> AsyncFileSearchStores:
        """Access async file search stores API."""
        ...

    @property
    def live(self) -> AsyncLive:
        """Access async live API for real-time bidirectional streaming."""
        ...

    @property
    def auth_tokens(self) -> AsyncTokens:
        """Access async authentication tokens API."""
        ...

    @property
    def operations(self) -> AsyncOperations:
        """Access async long-running operations API."""
        ...

    async def aclose(self) -> None:
        """
        Close the async client explicitly to release resources.

        Note: This does not close the sync client. Use Client.close() for sync client.
        """
        ...

    async def __aenter__(self) -> 'AsyncClient':
        """Async context manager entry."""
        ...

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        ...
```

**Usage Example - Async Client:**

```python
import asyncio
from google.genai import Client

async def main():
    client = Client(api_key='YOUR_API_KEY')
    async_client = client.aio

    # Make async request
    response = await async_client.models.generate_content(
        model='gemini-2.0-flash',
        contents='What is AI?'
    )
    print(response.text)

    # Close async client
    await async_client.aclose()
    client.close()

asyncio.run(main())
```

**Usage Example - Async Context Manager:**

```python
import asyncio
from google.genai import Client

async def main():
    client = Client(api_key='YOUR_API_KEY')

    async with client.aio as async_client:
        response = await async_client.models.generate_content(
            model='gemini-2.0-flash',
            contents='Hello!'
        )
        print(response.text)

    client.close()

asyncio.run(main())
```

### HTTP Configuration

Configure HTTP client behavior including API version, timeouts, retries, and custom headers.

```python { .api }
class HttpOptions:
    """
    HTTP client configuration options.

    Parameters:
        api_version (str, optional): API version to use (e.g., 'v1', 'v1beta'). Defaults to 'v1beta'.
        base_url (str, optional): Override base URL for API requests.
        timeout (float, optional): Request timeout in seconds.
        headers (Dict[str, str], optional): Additional HTTP headers for all requests.
        retry_options (HttpRetryOptions, optional): Retry configuration for failed requests.
    """
    api_version: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[float] = None
    headers: Optional[Dict[str, str]] = None
    retry_options: Optional[HttpRetryOptions] = None

class HttpRetryOptions:
    """
    HTTP retry configuration for handling transient failures.

    Parameters:
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
        initial_backoff (float, optional): Initial backoff delay in seconds. Defaults to 1.0.
        max_backoff (float, optional): Maximum backoff delay in seconds. Defaults to 60.0.
        backoff_multiplier (float, optional): Backoff multiplier for exponential backoff. Defaults to 2.0.
        retry_statuses (List[int], optional): HTTP status codes that trigger retries.
            Defaults to [408, 429, 500, 502, 503, 504].
    """
    max_retries: Optional[int] = None
    initial_backoff: Optional[float] = None
    max_backoff: Optional[float] = None
    backoff_multiplier: Optional[float] = None
    retry_statuses: Optional[List[int]] = None

# TypedDict variants for flexible usage
class HttpOptionsDict(TypedDict, total=False):
    api_version: str
    base_url: str
    timeout: float
    headers: Dict[str, str]
    retry_options: Union[HttpRetryOptions, 'HttpRetryOptionsDict']

class HttpRetryOptionsDict(TypedDict, total=False):
    max_retries: int
    initial_backoff: float
    max_backoff: float
    backoff_multiplier: float
    retry_statuses: List[int]
```

**Usage Example - HTTP Configuration:**

```python
from google.genai import Client
from google.genai.types import HttpOptions, HttpRetryOptions

# Configure HTTP options
http_options = HttpOptions(
    api_version='v1',
    timeout=30.0,
    headers={'User-Agent': 'MyApp/1.0'},
    retry_options=HttpRetryOptions(
        max_retries=5,
        initial_backoff=2.0,
        max_backoff=120.0
    )
)

client = Client(
    api_key='YOUR_API_KEY',
    http_options=http_options
)

# All requests use these HTTP options
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Hello'
)
```

### Debug Configuration

Configure client behavior for testing and debugging, including record/replay functionality for deterministic testing.

```python { .api }
class DebugConfig:
    """
    Configuration options for testing and debugging client network behavior.

    Parameters:
        client_mode (str, optional): Client operation mode. Options:
            - 'record': Record API requests and responses to replay files
            - 'replay': Replay API responses from recorded files
            - 'auto': Automatically record if replay file doesn't exist, otherwise replay
            Can be set via GOOGLE_GENAI_CLIENT_MODE environment variable.
        replays_directory (str, optional): Directory for storing replay files.
            Can be set via GOOGLE_GENAI_REPLAYS_DIRECTORY environment variable.
        replay_id (str, optional): Identifier for replay file.
            Can be set via GOOGLE_GENAI_REPLAY_ID environment variable.
    """
    client_mode: Optional[str] = None
    replays_directory: Optional[str] = None
    replay_id: Optional[str] = None
```

**Usage Example - Debug Configuration:**

```python
from google.genai import Client
from google.genai.client import DebugConfig

# Configure for recording API interactions
debug_config = DebugConfig(
    client_mode='record',
    replays_directory='./test_replays',
    replay_id='test_001'
)

client = Client(
    api_key='YOUR_API_KEY',
    debug_config=debug_config
)

# Requests are recorded to ./test_replays/test_001.json
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Test prompt'
)

# Later, replay the recorded interactions
debug_config = DebugConfig(
    client_mode='replay',
    replays_directory='./test_replays',
    replay_id='test_001'
)

# Responses are replayed from recorded file
```

## Types

```python { .api }
from typing import Optional, Union, Dict, List, TypedDict
import google.auth.credentials

# Credentials type from google.auth
Credentials = google.auth.credentials.Credentials

# HTTP response metadata
class HttpResponse:
    """
    HTTP response metadata from API requests.

    Attributes:
        status_code (int): HTTP status code
        headers (Dict[str, str]): Response headers
        request_url (str): URL of the request
    """
    status_code: int
    headers: Dict[str, str]
    request_url: str
```
