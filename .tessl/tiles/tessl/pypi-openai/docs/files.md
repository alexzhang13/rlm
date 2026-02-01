# Files

Upload and manage files for use with OpenAI features like Assistants, Fine-tuning, Batch processing, and Vision. Provides file storage with purpose-specific handling.

## Capabilities

### Upload File

Upload a file for use with OpenAI services.

```python { .api }
def create(
    self,
    *,
    file: FileTypes,
    purpose: FilePurpose,
    expires_after: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FileObject:
    """
    Upload a file for use with OpenAI services.

    Args:
        file: File to upload. Can be file path string, file object, or tuple.
            Maximum file size varies by purpose.

        purpose: Intended purpose of the file. Options:
            - "assistants": For Assistants API and file_search tool
            - "batch": For Batch API operations
            - "fine-tune": For fine-tuning jobs
            - "vision": For vision model inputs
            - "user_data": Flexible file type for any purpose
            - "evals": For evaluation data sets

        expires_after: Expiration policy for the file (ExpiresAfter type). By default,
            files with purpose="batch" expire after 30 days and all other files persist
            until manually deleted. Structure:
            - anchor: "created_at" (file creation time)
            - seconds: int (3600-2592000, time in seconds until expiration)

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FileObject: Uploaded file metadata including ID.

    Raises:
        BadRequestError: Invalid file format, size, or purpose
        AuthenticationError: Invalid API key
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Upload file for assistants
with open("document.pdf", "rb") as file:
    response = client.files.create(
        file=file,
        purpose="assistants"
    )

file_id = response.id
print(f"File ID: {file_id}")

# Upload for fine-tuning
with open("training_data.jsonl", "rb") as file:
    response = client.files.create(
        file=file,
        purpose="fine-tune"
    )

# Upload for batch processing
with open("batch_requests.jsonl", "rb") as file:
    response = client.files.create(
        file=file,
        purpose="batch"
    )

# Using file_from_path helper
from openai import file_from_path

response = client.files.create(
    file=file_from_path("data.csv"),
    purpose="assistants"
)

# Check upload details
print(f"Filename: {response.filename}")
print(f"Size: {response.bytes} bytes")
print(f"Purpose: {response.purpose}")
print(f"Status: {response.status}")
```

### Retrieve File Metadata

Get information about a specific file.

```python { .api }
def retrieve(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FileObject:
    """
    Retrieve file metadata.

    Args:
        file_id: The ID of the file to retrieve.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FileObject: File metadata.

    Raises:
        NotFoundError: File not found
    """
```

Usage example:

```python
file = client.files.retrieve("file-abc123")

print(f"Filename: {file.filename}")
print(f"Purpose: {file.purpose}")
print(f"Size: {file.bytes} bytes")
print(f"Created: {file.created_at}")
```

### List Files

List all uploaded files with optional filtering.

```python { .api }
def list(
    self,
    *,
    purpose: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    after: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[FileObject]:
    """
    List uploaded files with optional filtering and pagination.

    Args:
        purpose: Filter by file purpose (e.g., "assistants", "fine-tune").
        limit: Number of files to retrieve (max 10000). Default 10000.
        order: Sort order. "asc" for ascending, "desc" for descending. Default "desc".
        after: Cursor for pagination. Return files after this file ID.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[FileObject]: Cursor-paginated list of files.
    """
```

Usage examples:

```python
# List all files
files = client.files.list()

for file in files.data:
    print(f"{file.filename} ({file.id})")

# Filter by purpose
assistant_files = client.files.list(purpose="assistants")

# Pagination
page1 = client.files.list(limit=10)
page2 = client.files.list(limit=10, after=page1.data[-1].id)

# Iterate through all files
for file in client.files.list():
    print(file.filename)
```

### Delete File

Delete a file from OpenAI storage.

```python { .api }
def delete(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FileDeleted:
    """
    Delete a file.

    Args:
        file_id: The ID of the file to delete.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FileDeleted: Deletion confirmation.

    Raises:
        NotFoundError: File not found
    """
```

Usage example:

```python
# Delete file
result = client.files.delete("file-abc123")

print(f"Deleted: {result.id}")
print(f"Success: {result.deleted}")
```

### Download File Content

Retrieve the binary content of a file.

```python { .api }
def content(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> HttpxBinaryResponseContent:
    """
    Retrieve file content.

    Args:
        file_id: The ID of the file to download.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        HttpxBinaryResponseContent: File content as binary data.

    Raises:
        NotFoundError: File not found
    """
```

Usage example:

```python
from pathlib import Path

# Download file content
content = client.files.content("file-abc123")

# Save to file
Path("downloaded_file.txt").write_bytes(content.content)

# Or use read()
file_bytes = content.read()

# Stream to file
content.stream_to_file("output.txt")
```

### Retrieve File Content (Alias)

Retrieve the textual content of a file. This is an alias method that retrieves content and returns it as a string.

```python { .api }
def retrieve_content(
    self,
    file_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> str:
    """
    Retrieve file content as a string.

    This method retrieves the contents of the specified file and returns
    it as a string. For binary content, use the content() method instead.

    Args:
        file_id: The ID of the file to retrieve content from.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        str: The file content as a string.

    Raises:
        NotFoundError: File not found
    """
```

Usage example:

```python
# Retrieve file content as string
text_content = client.files.retrieve_content("file-abc123")
print(text_content)
```

### Wait for Processing

Poll until file processing is complete (helper method).

```python { .api }
def wait_for_processing(
    self,
    file_id: str,
    *,
    poll_interval: float = 5.0,
    max_wait_seconds: float = 1800,
) -> FileObject:
    """
    Wait for file processing to complete.

    Args:
        file_id: The ID of the file to wait for.
        poll_interval: Seconds between status checks. Default 5.0.
        max_wait_seconds: Maximum seconds to wait. Default 1800 (30 minutes).

    Returns:
        FileObject: File with completed status.

    Raises:
        TimeoutError: Processing not completed within max_wait_seconds
        APIError: Processing failed
    """
```

Usage example:

```python
# Upload and wait
with open("large_file.pdf", "rb") as file:
    uploaded = client.files.create(file=file, purpose="assistants")

# Wait for processing
ready_file = client.files.wait_for_processing(uploaded.id)

print(f"File ready: {ready_file.status}")
```

## Types

```python { .api }
from typing import Literal, TypedDict, Required, Union, Iterator
from pydantic import BaseModel

class FileObject(BaseModel):
    """File metadata."""
    id: str
    bytes: int
    created_at: int
    filename: str
    object: Literal["file"]
    purpose: FilePurpose
    status: FileStatus
    status_details: str | None

class FileDeleted(BaseModel):
    """File deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["file"]

FilePurpose = Literal[
    "assistants",
    "assistants_output",
    "batch",
    "batch_output",
    "fine-tune",
    "fine-tune-results",
    "vision",
    "user_data",
    "evals"
]

FileStatus = Literal["uploaded", "processed", "error"]

class ExpiresAfter(TypedDict):
    """File expiration policy configuration."""
    anchor: Required[Literal["created_at"]]
    """Anchor timestamp after which the expiration policy applies. Currently only 'created_at' is supported."""

    seconds: Required[int]
    """Number of seconds after the anchor time that the file will expire. Must be between 3600 (1 hour) and 2592000 (30 days)."""

# File types
FileTypes = Union[
    FileContent,  # File-like object
    tuple[str | None, FileContent],  # (filename, content)
    tuple[str | None, FileContent, str | None]  # (filename, content, content_type)
]

# Pagination
class SyncPage[T](BaseModel):
    data: list[T]
    object: str
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...
```

## File Size Limits

| Purpose | Format | Max Size |
|---------|--------|----------|
| assistants | Various | 512 MB |
| batch | JSONL | 100 MB |
| fine-tune | JSONL | 1 GB |
| vision | Images | 20 MB |

## Best Practices

```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

# 1. Check file exists before upload
file_path = Path("data.txt")
if file_path.exists():
    with open(file_path, "rb") as f:
        file = client.files.create(file=f, purpose="assistants")

# 2. Clean up unused files
files = client.files.list(purpose="assistants")
for file in files:
    if should_delete(file):
        client.files.delete(file.id)

# 3. Handle upload errors
from openai import APIError

try:
    with open("large_file.pdf", "rb") as f:
        file = client.files.create(file=f, purpose="assistants")
except APIError as e:
    print(f"Upload failed: {e}")

# 4. Track file IDs for later use
uploaded_files = []

for file_path in ["file1.txt", "file2.txt"]:
    with open(file_path, "rb") as f:
        file = client.files.create(file=f, purpose="assistants")
        uploaded_files.append(file.id)

# Use files with assistant
assistant = client.beta.assistants.create(
    model="gpt-4",
    tools=[{"type": "file_search"}],
    tool_resources={"file_search": {"file_ids": uploaded_files}}
)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def upload_file():
    client = AsyncOpenAI()

    with open("document.pdf", "rb") as file:
        response = await client.files.create(
            file=file,
            purpose="assistants"
        )

    return response.id

file_id = asyncio.run(upload_file())
```
