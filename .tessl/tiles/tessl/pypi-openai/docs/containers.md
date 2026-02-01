# Containers

Create and manage isolated file storage containers for organizing and sharing files. Containers provide a way to group related files together with configurable expiration policies.

## Capabilities

### Create Container

Create a new container for file storage.

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
) -> Container:
    """
    Create a container.

    Args:
        name: Name of the container to create. Used for identification.

        expires_after: Container expiration time in seconds relative to anchor time.
            Example: {"anchor": "created_at", "days": 7} expires 7 days after creation.
            Default: containers persist until manually deleted.

        file_ids: IDs of files to copy into the container at creation.
            Files are copied, not moved - originals remain accessible.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Container: Created container object with unique ID.

    Notes:
        - Containers provide isolated file storage
        - Files are copied into containers, not moved
        - Expired containers are automatically cleaned up
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Create empty container
container = client.containers.create(
    name="project-resources"
)
print(f"Created container: {container.id}")

# Create with files
container = client.containers.create(
    name="training-data",
    file_ids=["file-abc123", "file-def456"]
)

# Create with expiration
container = client.containers.create(
    name="temp-files",
    expires_after={
        "anchor": "created_at",
        "days": 1
    }
)

# Create for specific project
container = client.containers.create(
    name="customer-support-logs",
    file_ids=["file-log1", "file-log2", "file-log3"],
    expires_after={
        "anchor": "created_at",
        "days": 30
    }
)
```

### Retrieve Container

Get a container by its ID.

```python { .api }
def retrieve(
    self,
    container_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Container:
    """
    Retrieve a container.

    Args:
        container_id: ID of the container to retrieve.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Container: Container object with metadata and file information.
    """
```

### List Containers

List all containers with pagination support.

```python { .api }
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
) -> SyncCursorPage[Container]:
    """
    List containers.

    Args:
        after: Cursor for pagination. Object ID defining your place in the list.
            For instance, if you receive 100 objects ending with obj_foo,
            use after=obj_foo to fetch the next page.

        limit: Maximum number of objects to return. Range: 1-100. Default: 20.

        order: Sort order by created_at timestamp.
            - "asc": Ascending (oldest first)
            - "desc": Descending (newest first, default)

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[Container]: Paginated list of containers.
            Supports iteration: for container in client.containers.list(): ...
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# List all containers
for container in client.containers.list():
    print(f"{container.name}: {container.id}")

# List with pagination
page = client.containers.list(limit=10)
for container in page:
    print(f"{container.name} - Created: {container.created_at}")

# Get next page
if page.has_more:
    next_page = client.containers.list(
        limit=10,
        after=page.data[-1].id
    )

# List in ascending order (oldest first)
for container in client.containers.list(order="asc"):
    print(container.name)
```

### Delete Container

Delete a container.

```python { .api }
def delete(
    self,
    container_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> None:
    """
    Delete a container.

    Args:
        container_id: ID of the container to delete.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        None: No content returned on successful deletion.

    Notes:
        - Deletion is permanent and cannot be undone
        - Files within the container are not deleted
        - Original files remain accessible outside the container
    """
```

### Container Files

Manage files within a container.

```python { .api }
# Access via client.containers.files

def create(
    self,
    container_id: str,
    *,
    file: FileTypes | Omit = omit,
    file_id: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FileCreateResponse:
    """
    Add a file to a container.

    Args:
        container_id: ID of the container.

        file: File content to upload directly. Provide either this OR file_id.

        file_id: ID of an existing file to add. File is copied into container.
            Provide either this OR file.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FileCreateResponse: File reference within the container.

    Notes:
        - Provide either `file` (for direct upload) OR `file_id` (for reference)
        - When using file_id, file is copied, not moved
        - Original file remains accessible
        - Same file can be in multiple containers
    """

def retrieve(
    self,
    container_id: str,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ContainerFile:
    """
    Retrieve a file from a container.

    Args:
        container_id: ID of the container.
        file_id: ID of the file to retrieve.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ContainerFile: File information and metadata.
    """

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
) -> SyncCursorPage[ContainerFile]:
    """
    List files in a container.

    Args:
        container_id: ID of the container.

        after: Cursor for pagination.

        limit: Maximum number of files to return. Range: 1-100. Default: 20.

        order: Sort order by created_at timestamp ("asc" or "desc").

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[ContainerFile]: Paginated list of files.
    """

def delete(
    self,
    container_id: str,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> None:
    """
    Remove a file from a container.

    Args:
        container_id: ID of the container.
        file_id: ID of the file to remove.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        None: No content returned on successful removal.

    Notes:
        - Removes file from container only
        - Original file is not deleted
        - File remains accessible outside container
    """
```

### Container File Content

Retrieve the binary content of a file stored in a container.

```python { .api }
# Access via client.containers.files.content

def retrieve(
    self,
    file_id: str,
    *,
    container_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> HttpxBinaryResponseContent:
    """
    Retrieve the binary content of a container file.

    Args:
        file_id: ID of the file to retrieve content from.

        container_id: ID of the container containing the file.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        HttpxBinaryResponseContent: Binary content of the file.
            Can be written to disk or processed in memory.

    Notes:
        - Returns raw binary data
        - Suitable for downloading file contents
        - Use .read() or .iter_bytes() to access content
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Retrieve file content from container
content = client.containers.files.content.retrieve(
    container_id="container-abc123",
    file_id="file-def456"
)

# Save to disk
with open("downloaded_file.pdf", "wb") as f:
    f.write(content.read())

# Or process in chunks
for chunk in content.iter_bytes(chunk_size=8192):
    # Process chunk
    pass
```

Complete workflow example:

```python
from openai import OpenAI

client = OpenAI()

# 1. Upload some files first
file1 = client.files.create(
    file=open("document1.pdf", "rb"),
    purpose="assistants"
)

file2 = client.files.create(
    file=open("document2.pdf", "rb"),
    purpose="assistants"
)

# 2. Create container with one file
container = client.containers.create(
    name="project-docs",
    file_ids=[file1.id],
    expires_after={
        "anchor": "created_at",
        "days": 7
    }
)

print(f"Created container: {container.id}")

# 3. Add another file to container
client.containers.files.create(
    container_id=container.id,
    file_id=file2.id
)

# 4. List all files in container
print("Files in container:")
for file in client.containers.files.list(container_id=container.id):
    print(f"  - {file.id}")

# 5. Retrieve specific file from container
file_info = client.containers.files.retrieve(
    container_id=container.id,
    file_id=file1.id
)
print(f"File info: {file_info}")

# 6. Remove a file from container
client.containers.files.delete(
    container_id=container.id,
    file_id=file1.id
)

# 7. Verify removal
remaining_files = client.containers.files.list(container_id=container.id)
print(f"Remaining files: {len(remaining_files.data)}")

# 8. List all containers
print("\nAll containers:")
for c in client.containers.list():
    print(f"  {c.name} ({c.id})")

# 9. Clean up - delete container
client.containers.delete(container_id=container.id)

# Note: Original files still exist
retrieved_file = client.files.retrieve(file_id=file1.id)
print(f"Original file still exists: {retrieved_file.id}")
```

Organizing files by project:

```python
from openai import OpenAI

client = OpenAI()

# Create containers for different projects
ml_container = client.containers.create(
    name="machine-learning-project"
)

web_container = client.containers.create(
    name="web-development-project"
)

# Upload and organize files
ml_file = client.files.create(
    file=open("model_training.py", "rb"),
    purpose="assistants"
)

web_file = client.files.create(
    file=open("api_docs.md", "rb"),
    purpose="assistants"
)

# Add files to appropriate containers
client.containers.files.create(
    container_id=ml_container.id,
    file_id=ml_file.id
)

client.containers.files.create(
    container_id=web_container.id,
    file_id=web_file.id
)

# Later: access files by project
print("ML Project Files:")
for file in client.containers.files.list(container_id=ml_container.id):
    print(f"  - {file.id}")

print("Web Project Files:")
for file in client.containers.files.list(container_id=web_container.id):
    print(f"  - {file.id}")
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def manage_containers():
    client = AsyncOpenAI()

    # Create container
    container = await client.containers.create(
        name="async-project",
        expires_after={"anchor": "created_at", "days": 1}
    )

    # Add file
    await client.containers.files.create(
        container_id=container.id,
        file_id="file-abc123"
    )

    # List files
    async for file in await client.containers.files.list(
        container_id=container.id
    ):
        print(f"File: {file.id}")

    # Delete container
    await client.containers.delete(container_id=container.id)

asyncio.run(manage_containers())
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Container(BaseModel):
    """Container object for file organization."""
    id: str
    created_at: int
    name: str
    object: Literal["container"]
    expires_at: int | None  # Present if expiration configured
    file_count: int | None  # Number of files in container

class ContainerFile(BaseModel):
    """File reference within a container."""
    id: str
    container_id: str
    file_id: str
    created_at: int
    object: Literal["container.file"]

class SyncCursorPage[T]:
    """Cursor-based pagination."""
    data: list[T]
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...

class Omit:
    """Sentinel value for omitted parameters."""

class HttpxBinaryResponseContent:
    """Binary response content from HTTP requests."""
    def read(self) -> bytes: ...
    def iter_bytes(self, chunk_size: int = ...) -> Iterator[bytes]: ...
```

## Access Pattern

```python
# Synchronous
from openai import OpenAI
client = OpenAI()
client.containers.create(...)
client.containers.retrieve(...)
client.containers.list(...)
client.containers.delete(...)
client.containers.files.create(...)
client.containers.files.retrieve(...)
client.containers.files.list(...)
client.containers.files.delete(...)
client.containers.files.content.retrieve(...)

# Asynchronous
from openai import AsyncOpenAI
client = AsyncOpenAI()
await client.containers.create(...)
await client.containers.retrieve(...)
await client.containers.list(...)
await client.containers.delete(...)
await client.containers.files.create(...)
await client.containers.files.retrieve(...)
await client.containers.files.list(...)
await client.containers.files.delete(...)
await client.containers.files.content.retrieve(...)
```
