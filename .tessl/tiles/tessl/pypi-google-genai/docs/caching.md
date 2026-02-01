# Context Caching

Create and manage cached content to reduce costs and latency for repeated requests with shared context. Context caching stores frequently used content (like large documents or conversation context) so it doesn't need to be sent with every request, significantly reducing token costs and improving response times.

## Capabilities

### Create Cached Content

Create a new cached content resource containing frequently used context.

```python { .api }
class Caches:
    """Synchronous cached content management API."""

    def create(
        self,
        *,
        model: str,
        config: CreateCachedContentConfig
    ) -> CachedContent:
        """
        Create cached content for reuse across requests.

        Parameters:
            model (str): Model identifier (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro').
            config (CreateCachedContentConfig): Cache configuration including:
                - contents: Content to cache (documents, conversation history, etc.)
                - system_instruction: System instruction to cache
                - tools: Tool definitions to cache
                - ttl: Time-to-live duration (e.g., '3600s' for 1 hour)
                - expire_time: Absolute expiration time
                - display_name: Display name for the cache

        Returns:
            CachedContent: Created cache with name, expiration info, and metadata.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncCaches:
    """Asynchronous cached content management API."""

    async def create(
        self,
        *,
        model: str,
        config: CreateCachedContentConfig
    ) -> CachedContent:
        """Async version of create."""
        ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import (
    CreateCachedContentConfig,
    Content,
    Part
)

client = Client(api_key='YOUR_API_KEY')

# Create large document content
document = """
[Large document text here - e.g., 50,000 tokens of product documentation]
"""

config = CreateCachedContentConfig(
    contents=[Content(parts=[Part(text=document)])],
    system_instruction='You are a product support assistant.',
    ttl='3600s',  # Cache for 1 hour
    display_name='Product Documentation Cache'
)

cache = client.caches.create(
    model='gemini-2.0-flash',
    config=config
)

print(f"Created cache: {cache.name}")
print(f"Expires: {cache.expire_time}")
print(f"Usage: {cache.usage_metadata.total_token_count} tokens")

# Use cache in requests
from google.genai.types import GenerateContentConfig

gen_config = GenerateContentConfig(
    cached_content=cache.name
)

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the return policy?',
    config=gen_config
)
print(response.text)
```

### Get Cached Content

Retrieve information about a cached content resource.

```python { .api }
class Caches:
    """Synchronous cached content management API."""

    def get(self, *, name: str) -> CachedContent:
        """
        Get cached content information.

        Parameters:
            name (str): Cache name in format 'cachedContents/{cache_id}'.

        Returns:
            CachedContent: Cache information including expiration and usage.

        Raises:
            ClientError: For client errors including 404 if cache not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncCaches:
    """Asynchronous cached content management API."""

    async def get(self, *, name: str) -> CachedContent:
        """Async version of get."""
        ...
```

### Update Cached Content

Update cached content expiration time or other mutable fields.

```python { .api }
class Caches:
    """Synchronous cached content management API."""

    def update(
        self,
        *,
        name: str,
        config: UpdateCachedContentConfig
    ) -> CachedContent:
        """
        Update cached content.

        Parameters:
            name (str): Cache name in format 'cachedContents/{cache_id}'.
            config (UpdateCachedContentConfig): Update configuration including:
                - ttl: New time-to-live duration
                - expire_time: New absolute expiration time

        Returns:
            CachedContent: Updated cache information.

        Raises:
            ClientError: For client errors including 404 if cache not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncCaches:
    """Asynchronous cached content management API."""

    async def update(
        self,
        *,
        name: str,
        config: UpdateCachedContentConfig
    ) -> CachedContent:
        """Async version of update."""
        ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import UpdateCachedContentConfig

client = Client(api_key='YOUR_API_KEY')

# Extend cache expiration
config = UpdateCachedContentConfig(
    ttl='7200s'  # Extend to 2 hours
)

updated_cache = client.caches.update(
    name='cachedContents/abc123',
    config=config
)

print(f"New expiration: {updated_cache.expire_time}")
```

### Delete Cached Content

Delete a cached content resource. Caches are automatically deleted after expiration, but you can delete them early to free resources.

```python { .api }
class Caches:
    """Synchronous cached content management API."""

    def delete(self, *, name: str) -> None:
        """
        Delete cached content.

        Parameters:
            name (str): Cache name in format 'cachedContents/{cache_id}'.

        Raises:
            ClientError: For client errors including 404 if cache not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncCaches:
    """Asynchronous cached content management API."""

    async def delete(self, *, name: str) -> None:
        """Async version of delete."""
        ...
```

### List Cached Contents

List all cached content resources with optional pagination.

```python { .api }
class Caches:
    """Synchronous cached content management API."""

    def list(
        self,
        *,
        config: Optional[ListCachedContentsConfig] = None
    ) -> Union[Pager[CachedContent], Iterator[CachedContent]]:
        """
        List cached contents.

        Parameters:
            config (ListCachedContentsConfig, optional): List configuration including:
                - page_size: Number of items per page
                - page_token: Token for pagination

        Returns:
            Union[Pager[CachedContent], Iterator[CachedContent]]: Paginated cache list.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncCaches:
    """Asynchronous cached content management API."""

    async def list(
        self,
        *,
        config: Optional[ListCachedContentsConfig] = None
    ) -> Union[AsyncPager[CachedContent], AsyncIterator[CachedContent]]:
        """Async version of list."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# List all caches
for cache in client.caches.list():
    print(f"{cache.display_name}: {cache.name}")
    print(f"  Expires: {cache.expire_time}")
    print(f"  Tokens: {cache.usage_metadata.total_token_count}")
```

## Types

```python { .api }
from typing import Optional, Union, List, Iterator, AsyncIterator
from datetime import datetime
from enum import Enum

# Configuration types
class CreateCachedContentConfig:
    """
    Configuration for creating cached content.

    Attributes:
        contents (list[Content]): Content to cache (documents, examples, etc.).
        system_instruction (Union[str, Content], optional): System instruction to cache.
        tools (list[Tool], optional): Tool definitions to cache.
        tool_config (ToolConfig, optional): Tool configuration to cache.
        ttl (str, optional): Time-to-live duration (e.g., '3600s', '1h'). Either ttl
            or expire_time must be provided.
        expire_time (datetime, optional): Absolute expiration time. Either ttl or
            expire_time must be provided.
        display_name (str, optional): Display name for the cache.
    """
    contents: list[Content]
    system_instruction: Optional[Union[str, Content]] = None
    tools: Optional[list[Tool]] = None
    tool_config: Optional[ToolConfig] = None
    ttl: Optional[str] = None
    expire_time: Optional[datetime] = None
    display_name: Optional[str] = None

class UpdateCachedContentConfig:
    """
    Configuration for updating cached content.

    Attributes:
        ttl (str, optional): New time-to-live duration. Either ttl or expire_time
            must be provided.
        expire_time (datetime, optional): New absolute expiration time.
    """
    ttl: Optional[str] = None
    expire_time: Optional[datetime] = None

class ListCachedContentsConfig:
    """
    Configuration for listing cached contents.

    Attributes:
        page_size (int, optional): Number of items per page.
        page_token (str, optional): Token for pagination.
    """
    page_size: Optional[int] = None
    page_token: Optional[str] = None

# Response types
class CachedContent:
    """
    Cached content resource.

    Attributes:
        name (str): Resource name in format 'cachedContents/{cache_id}'.
        model (str): Model identifier this cache is for.
        display_name (str, optional): Display name.
        contents (list[Content]): Cached content.
        system_instruction (Content, optional): Cached system instruction.
        tools (list[Tool], optional): Cached tools.
        tool_config (ToolConfig, optional): Cached tool config.
        create_time (datetime): When cache was created.
        update_time (datetime): When cache was last updated.
        expire_time (datetime): When cache will expire.
        usage_metadata (CachedContentUsageMetadata): Token usage information.
    """
    name: str
    model: str
    display_name: Optional[str] = None
    contents: list[Content]
    system_instruction: Optional[Content] = None
    tools: Optional[list[Tool]] = None
    tool_config: Optional[ToolConfig] = None
    create_time: datetime
    update_time: datetime
    expire_time: datetime
    usage_metadata: CachedContentUsageMetadata

class CachedContentUsageMetadata:
    """
    Token usage metadata for cached content.

    Attributes:
        total_token_count (int): Total tokens in cached content.
    """
    total_token_count: int

# Core types (from content-generation)
class Content:
    """Content container with role and parts."""
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """Individual content part."""
    text: Optional[str] = None
    inline_data: Optional[Blob] = None
    file_data: Optional[FileData] = None

class Blob:
    """Binary data with MIME type."""
    mime_type: str
    data: bytes

class FileData:
    """Reference to uploaded file."""
    file_uri: str
    mime_type: str

class Tool:
    """Tool with function declarations."""
    function_declarations: Optional[list[FunctionDeclaration]] = None

class FunctionDeclaration:
    """Function definition."""
    name: str
    description: str
    parameters: Optional[Schema] = None

class ToolConfig:
    """Tool configuration."""
    function_calling_config: Optional[FunctionCallingConfig] = None

class FunctionCallingConfig:
    """Function calling mode configuration."""
    mode: FunctionCallingConfigMode
    allowed_function_names: Optional[list[str]] = None

class FunctionCallingConfigMode(Enum):
    """Function calling modes."""
    MODE_UNSPECIFIED = 'MODE_UNSPECIFIED'
    AUTO = 'AUTO'
    ANY = 'ANY'
    NONE = 'NONE'

class Schema:
    """JSON schema."""
    type: Type
    properties: Optional[dict[str, Schema]] = None

class Type(Enum):
    """JSON schema types."""
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    INTEGER = 'INTEGER'
    BOOLEAN = 'BOOLEAN'
    ARRAY = 'ARRAY'
    OBJECT = 'OBJECT'

# Pager types
class Pager[T]:
    """Synchronous pager."""
    page: list[T]
    def next_page(self) -> None: ...
    def __iter__(self) -> Iterator[T]: ...

class AsyncPager[T]:
    """Asynchronous pager."""
    page: list[T]
    async def next_page(self) -> None: ...
    async def __aiter__(self) -> AsyncIterator[T]: ...
```
