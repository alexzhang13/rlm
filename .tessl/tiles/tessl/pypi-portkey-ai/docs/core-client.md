# Core Client & Configuration

Primary client classes and configuration utilities for initializing and managing Portkey connections with comprehensive provider support and advanced routing capabilities.

## Capabilities

### Main Client Classes

Core synchronous and asynchronous client classes that provide the primary interface to Portkey's AI gateway and observability features.

```python { .api }
class Portkey:
    """
    Primary synchronous client for Portkey AI API.
    
    Provides unified interface to 40+ AI providers with built-in fallbacks,
    load balancing, caching, and comprehensive observability.
    """
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        virtual_key: Optional[str] = None,
        websocket_base_url: Optional[Union[str, httpx.URL]] = None,
        config: Optional[Union[Mapping, str]] = None,
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Union[Optional[dict[str, str]], str] = None,
        cache_namespace: Optional[str] = None,
        debug: Optional[bool] = None,
        cache_force_refresh: Optional[bool] = None,
        custom_host: Optional[str] = None,
        forward_headers: Optional[List[str]] = None,
        instrumentation: Optional[bool] = None,
        openai_project: Optional[str] = None,
        openai_organization: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        aws_region: Optional[str] = None,
        vertex_project_id: Optional[str] = None,
        vertex_region: Optional[str] = None,
        workers_ai_account_id: Optional[str] = None,
        azure_resource_name: Optional[str] = None,
        azure_deployment_id: Optional[str] = None,
        azure_api_version: Optional[str] = None,
        azure_endpoint_name: Optional[str] = None,
        huggingface_base_url: Optional[str] = None,
        http_client: Optional[httpx.Client] = None,
        request_timeout: Optional[int] = None,
        strict_open_ai_compliance: Optional[bool] = False,
        anthropic_beta: Optional[str] = None,
        anthropic_version: Optional[str] = None,
        mistral_fim_completion: Optional[str] = None,
        vertex_storage_bucket_name: Optional[str] = None,
        provider_file_name: Optional[str] = None,
        provider_model: Optional[str] = None,
        aws_s3_bucket: Optional[str] = None,
        aws_s3_object_key: Optional[str] = None,
        aws_bedrock_model: Optional[str] = None,
        fireworks_account_id: Optional[str] = None,
        calculate_audio_duration: Optional[bool] = True,
        **kwargs
    ) -> None: ...

class AsyncPortkey:
    """
    Asynchronous client for Portkey AI API.
    
    Async version of Portkey client with identical API surface
    supporting concurrent operations and async/await patterns.
    """
    def __init__(self, **kwargs) -> None: ...
```

### Usage Examples

```python
# Basic initialization
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Advanced configuration with provider-specific settings
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    config={
        "strategy": {
            "mode": "fallback"
        },
        "targets": [
            {
                "provider": "openai",
                "api_key": "OPENAI_API_KEY"
            },
            {
                "provider": "anthropic", 
                "api_key": "ANTHROPIC_API_KEY"
            }
        ]
    },
    metadata={
        "environment": "production",
        "user_id": "user123"
    },
    trace_id="trace-abc-123",
    debug=True
)

# Async client usage
import asyncio
from portkey_ai import AsyncPortkey

async def main():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    response = await portkey.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="gpt-4"
    )
    
    print(response)

asyncio.run(main())
```

### Header Creation Utilities

Utility functions for creating and managing Portkey-specific request headers.

```python { .api }
def createHeaders(
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    trace_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    config: Optional[Union[str, dict]] = None,
    cache_namespace: Optional[str] = None,
    cache_force_refresh: Optional[bool] = None,
    virtual_key: Optional[str] = None,
    custom_host: Optional[str] = None,
    forward_headers: Optional[List[str]] = None,
    openai_project: Optional[str] = None,
    openai_organization: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    aws_region: Optional[str] = None,
    vertex_project_id: Optional[str] = None,
    vertex_region: Optional[str] = None,
    workers_ai_account_id: Optional[str] = None,
    azure_resource_name: Optional[str] = None,
    azure_deployment_id: Optional[str] = None,
    azure_api_version: Optional[str] = None,
    azure_endpoint_name: Optional[str] = None,
    anthropic_beta: Optional[str] = None,
    anthropic_version: Optional[str] = None,
    **kwargs
) -> dict:
    """
    Create Portkey-specific headers for API requests.
    
    Returns:
    Dictionary of headers for HTTP requests
    """
```

### Global Configuration Variables

Module-level configuration variables for default settings.

```python { .api }
api_key: Optional[str]
"""Global API key from environment variable PORTKEY_API_KEY"""

base_url: Optional[str] 
"""Global base URL from environment variable PORTKEY_PROXY_ENV or default"""

config: Optional[Union[Mapping, str]]
"""Global configuration object"""

mode: Optional[Union[Modes, ModesLiteral]]
"""Global mode setting"""
```

### Constants

```python { .api }
PORTKEY_BASE_URL: str
"""Default Portkey API base URL"""

PORTKEY_API_KEY_ENV: str
"""Environment variable name for API key"""

PORTKEY_PROXY_ENV: str
"""Environment variable name for proxy URL"""

PORTKEY_GATEWAY_URL: str
"""Gateway URL constant"""
```

## Configuration Parameters

### Core Parameters

- **api_key**: Portkey API key for authentication
- **base_url**: Base URL for API requests (defaults to Portkey gateway)
- **virtual_key**: Virtual key for secure credential management
- **config**: Configuration object for routing, fallbacks, and provider settings
- **provider**: Specific AI provider to use
- **trace_id**: Request tracing identifier for observability
- **metadata**: Custom metadata for request categorization and analytics

### Caching Parameters

- **cache_namespace**: Namespace for cache isolation
- **cache_force_refresh**: Force cache refresh for requests

### Observability Parameters

- **debug**: Enable debug mode for detailed logging
- **instrumentation**: Enable request instrumentation
- **forward_headers**: List of headers to forward to providers

### Provider-Specific Parameters

#### OpenAI
- **openai_project**: OpenAI project ID
- **openai_organization**: OpenAI organization ID

#### AWS/Bedrock
- **aws_secret_access_key**: AWS secret access key
- **aws_access_key_id**: AWS access key ID
- **aws_session_token**: AWS session token
- **aws_region**: AWS region
- **aws_s3_bucket**: S3 bucket for file operations
- **aws_s3_object_key**: S3 object key
- **aws_bedrock_model**: Bedrock model identifier

#### Google Vertex AI
- **vertex_project_id**: Vertex AI project ID
- **vertex_region**: Vertex AI region
- **vertex_storage_bucket_name**: Storage bucket name

#### Azure OpenAI
- **azure_resource_name**: Azure resource name
- **azure_deployment_id**: Azure deployment ID
- **azure_api_version**: Azure API version
- **azure_endpoint_name**: Azure endpoint name

#### Anthropic
- **anthropic_beta**: Anthropic beta features
- **anthropic_version**: Anthropic API version

#### Other Providers
- **workers_ai_account_id**: Cloudflare Workers AI account ID
- **huggingface_base_url**: HuggingFace API base URL
- **fireworks_account_id**: Fireworks AI account ID
- **mistral_fim_completion**: Mistral fill-in-middle completion setting

### HTTP Configuration

- **http_client**: Custom HTTP client instance
- **request_timeout**: Request timeout in seconds
- **websocket_base_url**: WebSocket base URL for real-time features
- **custom_host**: Custom host override
- **strict_open_ai_compliance**: Enforce strict OpenAI API compliance