# Vector Stores

Create and manage vector stores for semantic search and retrieval with the Assistants API. Vector stores enable file search capabilities by storing and indexing documents for efficient retrieval.

## Capabilities

### Create Vector Store

Create a new vector store for storing and searching documents.

```python { .api }
def create(
    self,
    *,
    chunking_strategy: dict | Omit = omit,
    description: str | Omit = omit,
    expires_after: dict | Omit = omit,
    file_ids: list[str] | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    name: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStore:
    """
    Create a vector store for file search.

    Args:
        chunking_strategy: How to chunk files. Options:
            - {"type": "auto"}: Automatic chunking (default)
            - {"type": "static", "static": {"max_chunk_size_tokens": 800, "chunk_overlap_tokens": 400}}

        description: Description of the vector store (optional).

        expires_after: Expiration policy. Options:
            - {"anchor": "last_active_at", "days": 7}: Expires 7 days after last use
            - {"anchor": "last_active_at", "days": 1}: Expires 1 day after last use

        file_ids: List of file IDs to add to the vector store (max 10000).
            Files must have purpose="assistants".

        metadata: Key-value pairs for storing additional info (max 16).
            Keys max 64 chars, values max 512 chars.

        name: Name of the vector store (optional).

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStore: Created vector store.

    Raises:
        BadRequestError: Invalid parameters or too many files
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Create empty vector store
vector_store = client.beta.vector_stores.create(
    name="Product Documentation"
)

print(f"Vector Store ID: {vector_store.id}")

# Create with files
file_ids = ["file-abc123", "file-def456"]

vector_store = client.beta.vector_stores.create(
    name="Knowledge Base",
    file_ids=file_ids
)

# With expiration policy
vector_store = client.beta.vector_stores.create(
    name="Temporary Store",
    expires_after={"anchor": "last_active_at", "days": 7}
)

# With custom chunking
vector_store = client.beta.vector_stores.create(
    name="Custom Chunking",
    file_ids=file_ids,
    chunking_strategy={
        "type": "static",
        "static": {
            "max_chunk_size_tokens": 800,
            "chunk_overlap_tokens": 400
        }
    }
)

# With metadata
vector_store = client.beta.vector_stores.create(
    name="Project Docs",
    metadata={
        "project": "alpha",
        "version": "1.0"
    }
)
```

### Retrieve Vector Store

Get vector store details.

```python { .api }
def retrieve(
    self,
    vector_store_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStore:
    """
    Retrieve vector store details.

    Args:
        vector_store_id: The ID of the vector store.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStore: Vector store details.

    Raises:
        NotFoundError: Vector store not found
    """
```

Usage example:

```python
# Get vector store
store = client.beta.vector_stores.retrieve("vs_abc123")

print(f"Name: {store.name}")
print(f"File counts: {store.file_counts}")
print(f"Status: {store.status}")
```

### Update Vector Store

Modify vector store settings.

```python { .api }
def update(
    self,
    vector_store_id: str,
    *,
    name: str | Omit = omit,
    expires_after: dict | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStore:
    """
    Update vector store properties.

    Args:
        vector_store_id: The ID of the vector store.
        name: New name for the vector store.
        expires_after: New expiration policy.
        metadata: New metadata (replaces existing).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStore: Updated vector store.
    """
```

Usage example:

```python
# Update name
store = client.beta.vector_stores.update(
    "vs_abc123",
    name="Updated Documentation"
)

# Update metadata
store = client.beta.vector_stores.update(
    "vs_abc123",
    metadata={"version": "2.0"}
)
```

### List Vector Stores

List all vector stores with pagination.

```python { .api }
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
) -> SyncCursorPage[VectorStore]:
    """
    List vector stores with pagination.

    Args:
        after: Cursor for next page.
        before: Cursor for previous page.
        limit: Number to retrieve (max 100). Default 20.
        order: Sort order. "asc" or "desc". Default "desc".
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[VectorStore]: Paginated list of vector stores.
    """
```

Usage example:

```python
# List all stores
stores = client.beta.vector_stores.list()

for store in stores:
    print(f"{store.name} ({store.id})")

# Pagination
page1 = client.beta.vector_stores.list(limit=10)
page2 = client.beta.vector_stores.list(limit=10, after=page1.data[-1].id)
```

### Delete Vector Store

Delete a vector store and all its files.

```python { .api }
def delete(
    self,
    vector_store_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreDeleted:
    """
    Delete a vector store.

    Args:
        vector_store_id: The ID of the vector store to delete.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreDeleted: Deletion confirmation.

    Raises:
        NotFoundError: Vector store not found
    """
```

Usage example:

```python
# Delete vector store
result = client.beta.vector_stores.delete("vs_abc123")

print(f"Deleted: {result.deleted}")
```

### Add Files to Vector Store

Add files to an existing vector store.

```python { .api }
def create(
    self,
    vector_store_id: str,
    *,
    file_id: str,
    attributes: dict[str, str | float | bool] | None | Omit = omit,
    chunking_strategy: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFile:
    """
    Add a file to a vector store.

    Args:
        vector_store_id: The vector store ID.
        file_id: The file ID to add.
        attributes: Key-value pairs that can be attached to the file (max 16 pairs).
            Keys: max 64 chars. Values: max 512 chars (strings) or numbers/booleans.
            Useful for storing metadata like version numbers, categories, etc.
        chunking_strategy: Chunking configuration (same as vector store create).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFile: Added file details.
    """
```

Usage example:

```python
# Add file to vector store
file = client.beta.vector_stores.files.create(
    vector_store_id="vs_abc123",
    file_id="file-xyz789"
)

print(f"File status: {file.status}")
```

### Retrieve Vector Store File

Get details about a file in a vector store.

```python { .api }
def retrieve(
    self,
    file_id: str,
    *,
    vector_store_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFile:
    """
    Retrieve details about a vector store file.

    Args:
        file_id: The ID of the file.
        vector_store_id: The vector store ID.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFile: File details including status and metadata.

    Raises:
        NotFoundError: File not found in vector store
    """
```

Usage example:

```python
# Get file details
file = client.beta.vector_stores.files.retrieve(
    file_id="file-xyz789",
    vector_store_id="vs_abc123"
)

print(f"Status: {file.status}")
print(f"Usage bytes: {file.usage_bytes}")
```

### Update Vector Store File

Update attributes on a vector store file.

```python { .api }
def update(
    self,
    file_id: str,
    *,
    vector_store_id: str,
    attributes: dict[str, str | float | bool] | None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFile:
    """
    Update attributes on a vector store file.

    Args:
        file_id: The ID of the file.
        vector_store_id: The vector store ID.
        attributes: Key-value pairs to attach (max 16 pairs).
            Keys: max 64 chars, Values: max 512 chars (or numbers/booleans).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFile: Updated file object.
    """
```

Usage example:

```python
# Update file attributes
file = client.beta.vector_stores.files.update(
    file_id="file-xyz789",
    vector_store_id="vs_abc123",
    attributes={
        "category": "documentation",
        "version": "1.2.0",
        "priority": 5
    }
)
```

### List Vector Store Files

List all files in a vector store with pagination and filtering.

```python { .api }
def list(
    self,
    vector_store_id: str,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    filter: Literal["in_progress", "completed", "failed", "cancelled"] | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[VectorStoreFile]:
    """
    List files in a vector store with optional filtering.

    Args:
        vector_store_id: The vector store ID.
        after: Cursor for pagination (object ID to start after).
        before: Cursor for pagination (object ID to start before).
        filter: Filter by file status: "in_progress", "completed", "failed", "cancelled".
        limit: Number of files to return (1-100, default 20).
        order: Sort order by created_at: "asc" or "desc".
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[VectorStoreFile]: Paginated list of files.
    """
```

Usage examples:

```python
# List all files
files = client.beta.vector_stores.files.list(
    vector_store_id="vs_abc123"
)

for file in files:
    print(f"{file.id}: {file.status}")

# Filter by status
completed_files = client.beta.vector_stores.files.list(
    vector_store_id="vs_abc123",
    filter="completed"
)

# Pagination
page1 = client.beta.vector_stores.files.list(
    vector_store_id="vs_abc123",
    limit=10,
    order="desc"
)

page2 = client.beta.vector_stores.files.list(
    vector_store_id="vs_abc123",
    limit=10,
    after=page1.data[-1].id
)
```

### Delete Vector Store File

Remove a file from a vector store (does not delete the file itself).

```python { .api }
def delete(
    self,
    file_id: str,
    *,
    vector_store_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFileDeleted:
    """
    Delete a vector store file.

    This removes the file from the vector store but does not delete the file
    itself. To delete the file, use client.files.delete().

    Args:
        file_id: The ID of the file.
        vector_store_id: The vector store ID.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFileDeleted: Deletion confirmation.
    """
```

Usage example:

```python
# Remove file from vector store
deleted = client.beta.vector_stores.files.delete(
    file_id="file-xyz789",
    vector_store_id="vs_abc123"
)

print(f"Deleted: {deleted.id}")

# To also delete the file itself:
client.files.delete(file_id="file-xyz789")
```

### Get Vector Store File Content

Retrieve the parsed contents of a vector store file.

```python { .api }
def content(
    self,
    file_id: str,
    *,
    vector_store_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncPage[FileContentResponse]:
    """
    Retrieve the parsed contents of a vector store file.

    Args:
        file_id: The ID of the file.
        vector_store_id: The vector store ID.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncPage[FileContentResponse]: Parsed file content with chunks.
    """
```

Usage example:

```python
# Get parsed file content
content_pages = client.beta.vector_stores.files.content(
    file_id="file-xyz789",
    vector_store_id="vs_abc123"
)

for page in content_pages:
    print(f"Content: {page.content}")
    print(f"Metadata: {page.metadata}")
```

### Helper: Create and Poll

Convenience method that combines create() and poll() - adds a file and waits for processing.

```python { .api }
def create_and_poll(
    self,
    file_id: str,
    *,
    vector_store_id: str,
    attributes: dict[str, str | float | bool] | None | Omit = omit,
    poll_interval_ms: int | Omit = omit,
    chunking_strategy: dict | Omit = omit,
) -> VectorStoreFile:
    """
    Attach a file to the given vector store and wait for it to be processed.

    Args:
        file_id: The file ID to add.
        vector_store_id: The vector store ID.
        attributes: Key-value pairs to attach to the file.
        poll_interval_ms: Polling interval in milliseconds. If not specified, uses server-suggested interval.
        chunking_strategy: Chunking configuration.

    Returns:
        VectorStoreFile: Processed file details (may be completed or failed).
    """
```

Usage example:

```python
# Add file and wait for processing
file = client.beta.vector_stores.files.create_and_poll(
    file_id="file-xyz789",
    vector_store_id="vs_abc123",
    poll_interval_ms=1000
)

print(f"Final status: {file.status}")
if file.status == "failed":
    print(f"Error: {file.last_error}")
```

### Helper: Poll Processing

Wait for a vector store file to finish processing.

```python { .api }
def poll(
    self,
    file_id: str,
    *,
    vector_store_id: str,
    poll_interval_ms: int | Omit = omit,
) -> VectorStoreFile:
    """
    Wait for the vector store file to finish processing.

    Note: this will return even if the file failed to process. Check
    file.status and file.last_error to handle failures.

    Args:
        file_id: The file ID.
        vector_store_id: The vector store ID.
        poll_interval_ms: Polling interval in milliseconds. If not specified, uses server-suggested interval.

    Returns:
        VectorStoreFile: File details after processing completes (or fails).
    """
```

Usage example:

```python
# First create the file
file = client.beta.vector_stores.files.create(
    file_id="file-xyz789",
    vector_store_id="vs_abc123"
)

# Then poll until processing completes
processed_file = client.beta.vector_stores.files.poll(
    file_id="file-xyz789",
    vector_store_id="vs_abc123"
)

print(f"Status: {processed_file.status}")
```

### Helper: Upload and Attach

Upload a new file to the Files API and attach it to the vector store.

```python { .api }
def upload(
    self,
    *,
    vector_store_id: str,
    file: FileTypes,
    chunking_strategy: dict | Omit = omit,
) -> VectorStoreFile:
    """
    Upload a file to the Files API and attach it to the given vector store.

    Note: The file will be asynchronously processed. Use upload_and_poll()
    to wait for processing to complete.

    Args:
        vector_store_id: The vector store ID.
        file: File to upload (path, file object, or bytes).
        chunking_strategy: Chunking configuration.

    Returns:
        VectorStoreFile: File details (status will be "in_progress").
    """
```

Usage example:

```python
# Upload and attach file
with open("document.pdf", "rb") as f:
    file = client.beta.vector_stores.files.upload(
        vector_store_id="vs_abc123",
        file=f
    )

print(f"Uploaded file ID: {file.id}")
print(f"Status: {file.status}")
```

### Helper: Upload and Poll

Complete workflow - upload a file, attach to vector store, and wait for processing.

```python { .api }
def upload_and_poll(
    self,
    *,
    vector_store_id: str,
    file: FileTypes,
    attributes: dict[str, str | float | bool] | None | Omit = omit,
    poll_interval_ms: int | Omit = omit,
    chunking_strategy: dict | Omit = omit,
) -> VectorStoreFile:
    """
    Upload a file and poll until processing is complete.

    This is the most convenient method for adding files - it handles
    the upload, attachment, and waiting in one call.

    Args:
        vector_store_id: The vector store ID.
        file: File to upload (path, file object, or bytes).
        attributes: Key-value pairs to attach to the file.
        poll_interval_ms: Polling interval in milliseconds.
        chunking_strategy: Chunking configuration.

    Returns:
        VectorStoreFile: Processed file details (may be completed or failed).
    """
```

Usage example:

```python
# Complete workflow in one call
with open("document.pdf", "rb") as f:
    file = client.beta.vector_stores.files.upload_and_poll(
        vector_store_id="vs_abc123",
        file=f,
        attributes={"type": "documentation", "version": "2.0"},
        poll_interval_ms=1000
    )

print(f"File ID: {file.id}")
print(f"Status: {file.status}")
print(f"Usage bytes: {file.usage_bytes}")

if file.status == "failed":
    print(f"Error: {file.last_error}")
```

### Search Vector Store

Search for relevant content in a vector store based on a query and optional file attributes filter.

```python { .api }
def search(
    self,
    vector_store_id: str,
    *,
    query: str | list[str],
    filters: dict | Omit = omit,
    max_num_results: int | Omit = omit,
    ranking_options: dict | Omit = omit,
    rewrite_query: bool | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncPage[VectorStoreSearchResponse]:
    """
    Search vector store for relevant content.

    Args:
        vector_store_id: The vector store ID.
        query: Search query text (string or list of strings).
        filters: A filter to apply based on file attributes.
        max_num_results: Maximum number of results to return (1-50 inclusive).
        ranking_options: Ranking options for search.
        rewrite_query: Whether to rewrite the natural language query for vector search.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncPage[VectorStoreSearchResponse]: Paginated search results with relevant chunks.
    """
```

Usage example:

```python
# Search vector store
results = client.beta.vector_stores.search(
    vector_store_id="vs_abc123",
    query="How do I install the SDK?",
    max_num_results=5
)

for result in results.data:
    print(f"Score: {result.score}")
    print(f"Content: {result.content}")
    print(f"File: {result.file_id}")
```

### File Batches

Batch operations for adding multiple files to a vector store efficiently. Accessed via `client.beta.vector_stores.file_batches`.

```python { .api }
def create(
    self,
    vector_store_id: str,
    *,
    file_ids: list[str] | Omit = omit,
    files: list[dict] | Omit = omit,
    attributes: dict[str, str | float | bool] | None | Omit = omit,
    chunking_strategy: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFileBatch:
    """
    Create a batch of files to add to vector store.

    Args:
        vector_store_id: The vector store ID.
        file_ids: List of file IDs to add (mutually exclusive with files).
        files: List of file objects with per-file metadata (mutually exclusive with file_ids).
        attributes: Metadata to apply to all files in batch.
        chunking_strategy: Strategy for chunking files.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFileBatch: Created batch object.
    """

def retrieve(
    self,
    batch_id: str,
    *,
    vector_store_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFileBatch:
    """
    Retrieve file batch status.

    Args:
        batch_id: The file batch ID.
        vector_store_id: The vector store ID.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFileBatch: Batch details.
    """

def cancel(
    self,
    batch_id: str,
    *,
    vector_store_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VectorStoreFileBatch:
    """
    Cancel an in-progress file batch.

    Args:
        batch_id: The file batch ID.
        vector_store_id: The vector store ID.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        VectorStoreFileBatch: Updated batch with cancelled status.
    """

def list_files(
    self,
    batch_id: str,
    *,
    vector_store_id: str,
    after: str | Omit = omit,
    before: str | Omit = omit,
    filter: Literal["in_progress", "completed", "failed", "cancelled"] | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[VectorStoreFile]:
    """
    List files in a vector store batch with pagination and filtering.

    Args:
        batch_id: The file batch ID to list files from.
        vector_store_id: The vector store ID.
        after: Cursor for pagination. Return files after this file ID.
        before: Cursor for pagination. Return files before this file ID.
        filter: Filter by file status. Options:
            - "in_progress": Files currently processing
            - "completed": Successfully processed files
            - "failed": Files that failed processing
            - "cancelled": Cancelled files
        limit: Number of files to retrieve. Default 20, max 100.
        order: Sort order. "asc" for ascending, "desc" for descending. Default "desc".
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[VectorStoreFile]: Paginated list of files in the batch.
    """
```

Usage examples:

```python
# Create file batch
batch = client.beta.vector_stores.file_batches.create(
    vector_store_id="vs_abc123",
    file_ids=["file-1", "file-2", "file-3"]
)

print(f"Batch ID: {batch.id}")
print(f"Status: {batch.status}")

# Check batch status
batch = client.beta.vector_stores.file_batches.retrieve(
    batch_id=batch.id,
    vector_store_id="vs_abc123"
)

# List files in batch
files = client.beta.vector_stores.file_batches.list_files(
    batch_id=batch.id,
    vector_store_id="vs_abc123"
)

for file in files.data:
    print(f"File ID: {file.id}, Status: {file.status}")

# Filter by status
completed_files = client.beta.vector_stores.file_batches.list_files(
    batch_id=batch.id,
    vector_store_id="vs_abc123",
    filter="completed"
)

# Cancel batch if needed
batch = client.beta.vector_stores.file_batches.cancel(
    batch_id=batch.id,
    vector_store_id="vs_abc123"
)
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class VectorStore(BaseModel):
    """Vector store for file search."""
    id: str
    created_at: int
    name: str
    usage_bytes: int
    file_counts: FileCounts
    status: Literal["expired", "in_progress", "completed"]
    expires_after: dict | None
    expires_at: int | None
    last_active_at: int | None
    metadata: dict[str, str] | None
    object: Literal["vector_store"]

class FileCounts(BaseModel):
    """File count statistics."""
    in_progress: int
    completed: int
    failed: int
    cancelled: int
    total: int

class VectorStoreDeleted(BaseModel):
    """Deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["vector_store.deleted"]

class VectorStoreFile(BaseModel):
    """File in vector store."""
    id: str
    created_at: int
    vector_store_id: str
    usage_bytes: int
    status: Literal["in_progress", "completed", "cancelled", "failed"]
    last_error: dict | None
    chunking_strategy: dict | None
    object: Literal["vector_store.file"]

class VectorStoreFileBatch(BaseModel):
    """Batch of files being added to vector store."""
    id: str
    created_at: int
    vector_store_id: str
    status: Literal["in_progress", "completed", "cancelled", "failed"]
    file_counts: FileCounts
    object: Literal["vector_store.files_batch"]

class VectorStoreSearchResponse(BaseModel):
    """Search results."""
    data: list[SearchResult]
    object: str

class SearchResult(BaseModel):
    """Single search result."""
    content: str
    file_id: str
    score: float
    metadata: dict | None
```

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Create vector store with appropriate files
# Upload files first
file_ids = []
for doc_path in ["doc1.pdf", "doc2.txt", "doc3.md"]:
    with open(doc_path, "rb") as f:
        file = client.files.create(file=f, purpose="assistants")
        file_ids.append(file.id)

# Create vector store
store = client.beta.vector_stores.create(
    name="Product Documentation",
    file_ids=file_ids
)

# 2. Wait for processing
import time

while store.status == "in_progress":
    time.sleep(2)
    store = client.beta.vector_stores.retrieve(store.id)

print(f"Status: {store.status}")
print(f"Completed files: {store.file_counts.completed}")

# 3. Use with Assistant
assistant = client.beta.assistants.create(
    name="Documentation Assistant",
    instructions="Help users find information in documentation.",
    model="gpt-4",
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [store.id]
        }
    }
)

# 4. Clean up expired stores
stores = client.beta.vector_stores.list()
for store in stores:
    if store.status == "expired":
        client.beta.vector_stores.delete(store.id)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_store():
    client = AsyncOpenAI()

    store = await client.beta.vector_stores.create(
        name="Async Store",
        file_ids=["file-abc123"]
    )

    return store.id

store_id = asyncio.run(create_store())
```
