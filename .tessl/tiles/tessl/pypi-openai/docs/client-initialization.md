# Client Initialization

Initialize OpenAI and Azure OpenAI clients with API credentials, configuration options, and custom HTTP settings. The library provides both synchronous and asynchronous implementations for all clients.

## Capabilities

### OpenAI Client

Creates a synchronous client for making API calls to OpenAI's services.

```python { .api }
class OpenAI:
    """
    Synchronous client for OpenAI API.

    Automatically infers credentials from environment variables:
    - api_key from OPENAI_API_KEY
    - organization from OPENAI_ORG_ID
    - project from OPENAI_PROJECT_ID
    - webhook_secret from OPENAI_WEBHOOK_SECRET
    - base_url from OPENAI_BASE_URL
    """

    def __init__(
        self,
        *,
        api_key: str | Callable[[], str] | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | httpx.URL | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Construct a new synchronous OpenAI client instance.

        Args:
            api_key: OpenAI API key. Can be a string or callable that returns a string.
                If None, reads from OPENAI_API_KEY environment variable.
            organization: OpenAI organization ID for multi-org accounts.
                If None, reads from OPENAI_ORG_ID environment variable.
            project: OpenAI project ID for project-scoped usage tracking.
                If None, reads from OPENAI_PROJECT_ID environment variable.
            webhook_secret: Secret for verifying webhook signatures.
                If None, reads from OPENAI_WEBHOOK_SECRET environment variable.
            base_url: Override the default API base URL (https://api.openai.com/v1).
                If None, reads from OPENAI_BASE_URL environment variable.
            websocket_base_url: Base URL for WebSocket connections (realtime API).
                If None, defaults to base_url with wss:// scheme.
            timeout: Request timeout in seconds. Can be a float or Timeout object.
                Default is NOT_GIVEN which uses library defaults.
            max_retries: Maximum number of retry attempts for failed requests.
                Default is 2.
            default_headers: Additional HTTP headers to include in all requests.
            default_query: Additional query parameters to include in all requests.
            http_client: Custom httpx.Client instance for advanced HTTP configuration.
            _strict_response_validation: Enable strict API response validation.
                Raises APIResponseValidationError if API returns invalid data.

        Raises:
            OpenAIError: If api_key is not provided and OPENAI_API_KEY is not set.
        """
```

Usage example:

```python
from openai import OpenAI

# Basic initialization with API key
client = OpenAI(api_key="sk-...")

# Using environment variable (OPENAI_API_KEY)
client = OpenAI()

# Advanced configuration
client = OpenAI(
    api_key="sk-...",
    organization="org-...",
    project="proj_...",
    timeout=30.0,
    max_retries=3,
    default_headers={"X-Custom-Header": "value"}
)

# Dynamic API key with callable
def get_api_key() -> str:
    return retrieve_key_from_secure_storage()

client = OpenAI(api_key=get_api_key)

# Custom HTTP client with specific configuration
import httpx

http_client = httpx.Client(
    limits=httpx.Limits(max_keepalive_connections=10),
    proxies="http://proxy.example.com:8080"
)
client = OpenAI(
    api_key="sk-...",
    http_client=http_client
)
```

### Async OpenAI Client

Creates an asynchronous client for making non-blocking API calls to OpenAI's services.

```python { .api }
class AsyncOpenAI:
    """
    Asynchronous client for OpenAI API.

    Automatically infers credentials from environment variables:
    - api_key from OPENAI_API_KEY
    - organization from OPENAI_ORG_ID
    - project from OPENAI_PROJECT_ID
    - webhook_secret from OPENAI_WEBHOOK_SECRET
    - base_url from OPENAI_BASE_URL
    """

    def __init__(
        self,
        *,
        api_key: str | Callable[[], Awaitable[str]] | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | httpx.URL | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Construct a new asynchronous OpenAI client instance.

        Args:
            api_key: OpenAI API key. Can be a string, sync callable, or async callable.
                If None, reads from OPENAI_API_KEY environment variable.
            organization: OpenAI organization ID for multi-org accounts.
                If None, reads from OPENAI_ORG_ID environment variable.
            project: OpenAI project ID for project-scoped usage tracking.
                If None, reads from OPENAI_PROJECT_ID environment variable.
            webhook_secret: Secret for verifying webhook signatures.
                If None, reads from OPENAI_WEBHOOK_SECRET environment variable.
            base_url: Override the default API base URL (https://api.openai.com/v1).
                If None, reads from OPENAI_BASE_URL environment variable.
            websocket_base_url: Base URL for WebSocket connections (realtime API).
                If None, defaults to base_url with wss:// scheme.
            timeout: Request timeout in seconds. Can be a float or Timeout object.
                Default is NOT_GIVEN which uses library defaults.
            max_retries: Maximum number of retry attempts for failed requests.
                Default is 2.
            default_headers: Additional HTTP headers to include in all requests.
            default_query: Additional query parameters to include in all requests.
            http_client: Custom httpx.AsyncClient instance for advanced HTTP configuration.
            _strict_response_validation: Enable strict API response validation.
                Raises APIResponseValidationError if API returns invalid data.

        Raises:
            OpenAIError: If api_key is not provided and OPENAI_API_KEY is not set.
        """
```

Usage example:

```python
import asyncio
from openai import AsyncOpenAI

async def main():
    # Basic initialization
    client = AsyncOpenAI(api_key="sk-...")

    # Using environment variable
    client = AsyncOpenAI()

    # Make async API calls
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

    # Custom async HTTP client
    import httpx

    async with httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=10)
    ) as http_client:
        client = AsyncOpenAI(
            api_key="sk-...",
            http_client=http_client
        )
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )

asyncio.run(main())
```

### Azure OpenAI Client

Creates a synchronous client for Azure OpenAI Service with Azure-specific authentication and configuration.

```python { .api }
class AzureOpenAI:
    """
    Synchronous client for Azure OpenAI Service.

    Automatically infers credentials from environment variables:
    - api_key from AZURE_OPENAI_API_KEY
    - azure_ad_token from AZURE_OPENAI_AD_TOKEN
    - azure_endpoint from AZURE_OPENAI_ENDPOINT
    - api_version from OPENAI_API_VERSION
    - organization from OPENAI_ORG_ID
    - project from OPENAI_PROJECT_ID
    """

    def __init__(
        self,
        *,
        api_version: str | None = None,
        azure_endpoint: str | None = None,
        azure_deployment: str | None = None,
        api_key: str | Callable[[], str] | None = None,
        azure_ad_token: str | None = None,
        azure_ad_token_provider: Callable[[], str] | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Construct a new synchronous Azure OpenAI client instance.

        Authentication is mutually exclusive - provide only ONE of:
        - api_key
        - azure_ad_token
        - azure_ad_token_provider

        Args:
            api_version: Azure OpenAI API version (e.g., "2024-02-15-preview").
                If None, reads from OPENAI_API_VERSION environment variable.
            azure_endpoint: Azure resource endpoint (e.g., "https://example.azure.openai.com/").
                If None, reads from AZURE_OPENAI_ENDPOINT environment variable.
            azure_deployment: Model deployment name. When provided with azure_endpoint,
                sets base URL to include /deployments/{azure_deployment}.
                Not supported with Assistants APIs.
            api_key: Azure OpenAI API key.
                If None, reads from AZURE_OPENAI_API_KEY environment variable.
            azure_ad_token: Azure Active Directory (Entra ID) access token.
                If None, reads from AZURE_OPENAI_AD_TOKEN environment variable.
            azure_ad_token_provider: Function returning Azure AD token, invoked per request.
                Useful for automatic token refresh.
            organization: OpenAI organization ID (optional for Azure).
                If None, reads from OPENAI_ORG_ID environment variable.
            project: OpenAI project ID (optional for Azure).
                If None, reads from OPENAI_PROJECT_ID environment variable.
            webhook_secret: Secret for verifying webhook signatures.
            websocket_base_url: Base URL for WebSocket connections.
            base_url: Override the base URL (alternative to azure_endpoint).
            timeout: Request timeout in seconds.
                Default is NOT_GIVEN which uses library defaults.
            max_retries: Maximum number of retry attempts for failed requests.
                Default is 2.
            default_headers: Additional HTTP headers to include in all requests.
            default_query: Additional query parameters to include in all requests.
            http_client: Custom httpx.Client instance for advanced HTTP configuration.
            _strict_response_validation: Enable strict API response validation.

        Raises:
            OpenAIError: If no authentication credentials are provided.
            MutuallyExclusiveAuthError: If multiple authentication methods are provided.
        """
```

Usage example:

```python
from openai import AzureOpenAI

# Using API key authentication
client = AzureOpenAI(
    api_key="your-azure-api-key",
    azure_endpoint="https://your-resource.azure.openai.com/",
    api_version="2024-02-15-preview"
)

# Using environment variables
# Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, OPENAI_API_VERSION
client = AzureOpenAI()

# With deployment name (for model-specific endpoints)
client = AzureOpenAI(
    api_key="your-azure-api-key",
    azure_endpoint="https://your-resource.azure.openai.com/",
    azure_deployment="gpt-4-deployment",
    api_version="2024-02-15-preview"
)

# Using Azure AD (Entra ID) authentication
client = AzureOpenAI(
    azure_ad_token="your-azure-ad-token",
    azure_endpoint="https://your-resource.azure.openai.com/",
    api_version="2024-02-15-preview"
)

# Using Azure AD with automatic token refresh
def get_azure_ad_token() -> str:
    # Implement token retrieval/refresh logic
    from azure.identity import DefaultAzureCredential
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    return token.token

client = AzureOpenAI(
    azure_ad_token_provider=get_azure_ad_token,
    azure_endpoint="https://your-resource.azure.openai.com/",
    api_version="2024-02-15-preview"
)

# Make API calls (same interface as OpenAI)
response = client.chat.completions.create(
    model="gpt-4",  # Uses deployment if azure_deployment was set
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Async Azure OpenAI Client

Creates an asynchronous client for Azure OpenAI Service.

```python { .api }
class AsyncAzureOpenAI:
    """
    Asynchronous client for Azure OpenAI Service.

    Automatically infers credentials from environment variables:
    - api_key from AZURE_OPENAI_API_KEY
    - azure_ad_token from AZURE_OPENAI_AD_TOKEN
    - azure_endpoint from AZURE_OPENAI_ENDPOINT
    - api_version from OPENAI_API_VERSION
    - organization from OPENAI_ORG_ID
    - project from OPENAI_PROJECT_ID
    """

    def __init__(
        self,
        *,
        azure_endpoint: str | None = None,
        azure_deployment: str | None = None,
        api_version: str | None = None,
        api_key: str | Callable[[], Awaitable[str]] | None = None,
        azure_ad_token: str | None = None,
        azure_ad_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | None = None,
        websocket_base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Construct a new asynchronous Azure OpenAI client instance.

        Authentication is mutually exclusive - provide only ONE of:
        - api_key
        - azure_ad_token
        - azure_ad_token_provider

        Args:
            api_version: Azure OpenAI API version (e.g., "2024-02-15-preview").
                If None, reads from OPENAI_API_VERSION environment variable.
            azure_endpoint: Azure resource endpoint (e.g., "https://example.azure.openai.com/").
                If None, reads from AZURE_OPENAI_ENDPOINT environment variable.
            azure_deployment: Model deployment name. When provided with azure_endpoint,
                sets base URL to include /deployments/{azure_deployment}.
                Not supported with Assistants APIs.
            api_key: Azure OpenAI API key. Can be a string, sync callable, or async callable.
                If None, reads from AZURE_OPENAI_API_KEY environment variable.
            azure_ad_token: Azure Active Directory (Entra ID) access token.
                If None, reads from AZURE_OPENAI_AD_TOKEN environment variable.
            azure_ad_token_provider: Function returning Azure AD token (sync or async),
                invoked per request. Useful for automatic token refresh.
            organization: OpenAI organization ID (optional for Azure).
                If None, reads from OPENAI_ORG_ID environment variable.
            project: OpenAI project ID (optional for Azure).
                If None, reads from OPENAI_PROJECT_ID environment variable.
            webhook_secret: Secret for verifying webhook signatures.
            websocket_base_url: Base URL for WebSocket connections.
            base_url: Override the base URL (alternative to azure_endpoint).
            timeout: Request timeout in seconds.
                Default is NOT_GIVEN which uses library defaults.
            max_retries: Maximum number of retry attempts for failed requests.
                Default is 2.
            default_headers: Additional HTTP headers to include in all requests.
            default_query: Additional query parameters to include in all requests.
            http_client: Custom httpx.AsyncClient instance for advanced HTTP configuration.
            _strict_response_validation: Enable strict API response validation.

        Raises:
            OpenAIError: If no authentication credentials are provided.
            MutuallyExclusiveAuthError: If multiple authentication methods are provided.
        """
```

Usage example:

```python
import asyncio
from openai import AsyncAzureOpenAI

async def main():
    # Basic async Azure client
    client = AsyncAzureOpenAI(
        api_key="your-azure-api-key",
        azure_endpoint="https://your-resource.azure.openai.com/",
        api_version="2024-02-15-preview"
    )

    # Async Azure AD token provider
    async def get_azure_ad_token() -> str:
        # Implement async token retrieval
        from azure.identity.aio import DefaultAzureCredential
        credential = DefaultAzureCredential()
        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        return token.token

    client = AsyncAzureOpenAI(
        azure_ad_token_provider=get_azure_ad_token,
        azure_endpoint="https://your-resource.azure.openai.com/",
        api_version="2024-02-15-preview"
    )

    # Make async API calls
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Types

```python { .api }
from typing import Callable, Mapping, Awaitable
import httpx

# Timeout configuration
Timeout = float | httpx.Timeout

# Sentinel for omitted parameters
class NotGiven:
    """Sentinel value indicating a parameter was not provided."""

NOT_GIVEN: NotGiven

# Azure AD token providers
AzureADTokenProvider = Callable[[], str]
AsyncAzureADTokenProvider = Callable[[], str | Awaitable[str]]
```

## Client Utility Methods

All clients provide utility methods for creating client copies with modified configuration and accessing raw HTTP responses.

### Copy Client with Modified Options

Create a new client instance reusing the same options with optional overrides.

```python { .api }
def copy(
    self,
    *,
    api_key: str | Callable[[], str] | None = None,
    organization: str | None = None,
    project: str | None = None,
    webhook_secret: str | None = None,
    websocket_base_url: str | httpx.URL | None = None,
    base_url: str | httpx.URL | None = None,
    timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
    http_client: httpx.Client | None = None,
    max_retries: int | Omit = omit,
    default_headers: Mapping[str, str] | None = None,
    set_default_headers: Mapping[str, str] | None = None,
    default_query: Mapping[str, object] | None = None,
    set_default_query: Mapping[str, object] | None = None,
) -> OpenAI:
    """
    Create a new client instance re-using the same options with optional overriding.

    Args:
        api_key: Override API key
        organization: Override organization
        project: Override project
        webhook_secret: Override webhook secret
        websocket_base_url: Override WebSocket base URL
        base_url: Override base URL
        timeout: Override timeout
        http_client: Override HTTP client
        max_retries: Override max retries
        default_headers: Merge these headers with existing default headers
        set_default_headers: Replace all default headers with these
        default_query: Merge these query params with existing defaults
        set_default_query: Replace all default query params with these

    Returns:
        New client instance with merged configuration.

    Note:
        - default_headers and set_default_headers are mutually exclusive
        - default_query and set_default_query are mutually exclusive
    """

# Alias for nicer inline usage
with_options = copy
```

Usage example:

```python
from openai import OpenAI

# Create base client
client = OpenAI(api_key="sk-...", timeout=30)

# Create a copy with longer timeout for specific operations
slow_client = client.copy(timeout=120)

# Or use the with_options alias for inline usage
response = client.with_options(timeout=60).chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Complex query..."}]
)

# Create a copy with additional headers
custom_client = client.copy(
    default_headers={"X-Request-ID": "abc123"}
)

# Replace all headers
new_client = client.copy(
    set_default_headers={"X-Custom": "value"}
)
```

### Access Raw HTTP Responses

Access the underlying `httpx.Response` object for any API call.

```python { .api }
@property
def with_raw_response(self) -> OpenAIWithRawResponse:
    """
    Property that returns a client wrapper providing access to raw HTTP responses.

    All API methods on this wrapper return a response object with:
    - parsed: The normally returned parsed response object
    - http_response: The raw httpx.Response object
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Access raw HTTP response
response = client.with_raw_response.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Access parsed response
completion = response.parsed
print(completion.choices[0].message.content)

# Access raw HTTP response details
http_response = response.http_response
print(f"Status: {http_response.status_code}")
print(f"Headers: {dict(http_response.headers)}")
print(f"Request ID: {http_response.headers.get('x-request-id')}")
```

### Stream HTTP Responses

Stream responses without loading them into memory, useful for large responses like file downloads.

```python { .api }
@property
def with_streaming_response(self) -> OpenAIWithStreamedResponse:
    """
    Property that returns a client wrapper for streaming HTTP responses.

    Instead of loading the entire response into memory, returns a response
    object that can be iterated over in chunks.
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Stream file content without loading into memory
response = client.with_streaming_response.files.content("file-abc123")

# Stream chunks
for chunk in response.iter_bytes(chunk_size=8192):
    process_chunk(chunk)

# Or write directly to file
with open("output.txt", "wb") as f:
    for chunk in response.iter_bytes():
        f.write(chunk)

# Also works with other endpoints
response = client.with_streaming_response.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello world"
)

with open("speech.mp3", "wb") as f:
    for chunk in response.iter_bytes():
        f.write(chunk)
```

Async clients have the same methods:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

# Raw response (async)
response = await client.with_raw_response.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Streaming response (async)
response = await client.with_streaming_response.files.content("file-abc123")
async for chunk in response.iter_bytes():
    process_chunk(chunk)

# Copy/with_options (async)
slow_client = client.copy(timeout=120)
```

## Client Properties

All clients (OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI) expose the following resource properties for accessing API endpoints:

```python { .api }
# Core resources
client.chat                 # Chat completions
client.completions          # Legacy text completions
client.embeddings           # Vector embeddings
client.audio                # Audio transcription, translation, TTS
client.images               # Image generation
client.videos               # Video generation
client.files                # File management
client.models               # Model information
client.moderations          # Content moderation
client.fine_tuning          # Fine-tuning jobs
client.batches              # Batch processing
client.vector_stores        # Vector stores
client.uploads              # Multipart uploads
client.responses            # Responses API
client.realtime             # Realtime API
client.webhooks             # Webhook verification
client.beta                 # Beta features (Assistants, Threads, etc.)
client.conversations        # Conversations API
client.evals                # Evaluations
client.containers           # Containers
```

## Error Handling

All client initialization errors inherit from OpenAIError:

```python { .api }
class OpenAIError(Exception):
    """Base exception for all OpenAI errors."""

class MutuallyExclusiveAuthError(OpenAIError):
    """Raised when multiple authentication methods are provided to Azure clients."""
```

Common initialization errors:

```python
from openai import OpenAI, OpenAIError, AzureOpenAI, MutuallyExclusiveAuthError

# Handle missing API key
try:
    client = OpenAI()  # No api_key and OPENAI_API_KEY not set
except OpenAIError as e:
    print(f"Missing API key: {e}")

# Handle Azure authentication conflicts
try:
    client = AzureOpenAI(
        api_key="key",
        azure_ad_token="token"  # Can't provide both
    )
except MutuallyExclusiveAuthError as e:
    print(f"Auth conflict: {e}")
```
