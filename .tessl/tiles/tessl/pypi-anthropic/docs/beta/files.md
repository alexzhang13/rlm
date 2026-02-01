# Beta Files API

Upload and manage files for use in conversations and batch processing.

## Overview

The Files API enables you to upload, manage, and download files for use with Claude. Files can be used for document analysis, batch processing input, or general user data.

## Key Features

- Upload files with specified purpose (batch or user_data)
- Retrieve file metadata
- List uploaded files with pagination
- Download file content
- Delete files when no longer needed

## Files API

### Upload File

```python { .api }
def upload(
    self,
    *,
    file: FileTypes,
    purpose: Literal["batch", "user_data"],
    **kwargs
) -> FileMetadata:
    """
    Upload file.

    Parameters:
        file: File to upload (bytes, file path, or file object)
        purpose: Purpose of file
                 "batch" - For batch processing requests/results
                 "user_data" - For general document analysis and user data

    Returns:
        FileMetadata with file ID, size, created timestamp, and purpose
    """
    ...
```

### Retrieve File Metadata

```python { .api }
def retrieve(
    self,
    file_id: str,
    **kwargs
) -> FileMetadata:
    """
    Get file metadata.

    Parameters:
        file_id: Unique identifier for the file

    Returns:
        FileMetadata with file details (ID, filename, size, purpose, created_at)
    """
    ...
```

### List Files

```python { .api }
def list(
    self,
    *,
    before_id: str = NOT_GIVEN,
    after_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    **kwargs
) -> SyncPage[FileMetadata]:
    """
    List uploaded files with pagination.

    Parameters:
        before_id: Return files before this ID (for reverse pagination)
        after_id: Return files after this ID (for forward pagination)
        limit: Maximum number of files to return (default varies by API)

    Returns:
        SyncPage[FileMetadata] with paginated file list
    """
    ...
```

### Delete File

```python { .api }
def delete(
    self,
    file_id: str,
    **kwargs
) -> DeletedFile:
    """
    Delete a file.

    Parameters:
        file_id: Unique identifier for the file to delete

    Returns:
        DeletedFile confirming deletion
    """
    ...
```

### Download File

```python { .api }
def download(
    self,
    file_id: str,
    **kwargs
) -> bytes:
    """
    Download file content.

    Parameters:
        file_id: Unique identifier for the file

    Returns:
        bytes: Raw file content
    """
    ...
```

## Examples

### Upload File from Path

```python
from anthropic import Anthropic
from anthropic._utils import file_from_path

client = Anthropic()

# Upload PDF for document analysis
file = file_from_path("document.pdf")
uploaded = client.beta.files.upload(
    file=file,
    purpose="user_data"
)

print(f"Uploaded: {uploaded.id}")
print(f"Filename: {uploaded.filename}")
print(f"Size: {uploaded.size} bytes")
print(f"Created: {uploaded.created_at}")
```

### Upload File from Bytes

```python
# Upload file from bytes
file_content = b"Sample document content..."
uploaded = client.beta.files.upload(
    file=("document.txt", file_content),
    purpose="user_data"
)

print(f"Uploaded file ID: {uploaded.id}")
```

### Upload for Batch Processing

```python
import json

# Prepare batch requests
batch_requests = [
    {
        "custom_id": "request-1",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": "Hello"}]
        }
    }
]

# Convert to JSONL format
jsonl_content = "\n".join(json.dumps(req) for req in batch_requests)

# Upload batch file
batch_file = client.beta.files.upload(
    file=("batch_requests.jsonl", jsonl_content.encode()),
    purpose="batch"
)

print(f"Batch file uploaded: {batch_file.id}")
```

### Retrieve File Metadata

```python
# Get file details
file_metadata = client.beta.files.retrieve("file_abc123")

print(f"ID: {file_metadata.id}")
print(f"Filename: {file_metadata.filename}")
print(f"Size: {file_metadata.size} bytes")
print(f"Purpose: {file_metadata.purpose}")
print(f"Created: {file_metadata.created_at}")
```

### List All Files

```python
# List all uploaded files
for file in client.beta.files.list():
    print(f"{file.filename} ({file.id}) - {file.purpose}")
```

### List Files with Pagination

```python
# List files with limit
page1 = client.beta.files.list(limit=10)
for file in page1:
    print(f"File: {file.filename}")

# Get next page
if page1.has_next_page():
    page2 = client.beta.files.list(limit=10, after_id=page1.data[-1].id)
    for file in page2:
        print(f"File: {file.filename}")

# List files in reverse
recent_files = client.beta.files.list(limit=5)
older_files = client.beta.files.list(
    limit=5,
    before_id=recent_files.data[0].id
)
```

### Download File

```python
# Download file content
file_id = "file_abc123"
content = client.beta.files.download(file_id)

# Save to disk
with open("downloaded_file.pdf", "wb") as f:
    f.write(content)

print(f"Downloaded {len(content)} bytes")
```

### Delete File

```python
# Delete file
deleted = client.beta.files.delete("file_abc123")
print(f"Deleted file: {deleted.id}")
print(f"Deleted: {deleted.deleted}")
```

### Use File in Message

```python
# Upload document
file = file_from_path("research_paper.pdf")
uploaded = client.beta.files.upload(
    file=file,
    purpose="user_data"
)

# Use file in message with citations
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    citations={"type": "enabled"},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": uploaded.id  # Use file ID
                    }
                },
                {
                    "type": "text",
                    "text": "Summarize this document with citations"
                }
            ]
        }
    ]
)

# Process citations
for block in message.content:
    if hasattr(block, 'citations'):
        for citation in block.citations:
            print(f"Citation: {citation.cited_text}")
```

### Manage Multiple Files

```python
from anthropic._utils import file_from_path

# Upload multiple files
files_to_upload = [
    "document1.pdf",
    "document2.pdf",
    "data.csv"
]

uploaded_files = []
for filepath in files_to_upload:
    file = file_from_path(filepath)
    uploaded = client.beta.files.upload(
        file=file,
        purpose="user_data"
    )
    uploaded_files.append(uploaded)
    print(f"Uploaded {uploaded.filename}: {uploaded.id}")

# Track uploaded files
file_ids = [f.id for f in uploaded_files]
print(f"Uploaded {len(file_ids)} files: {file_ids}")

# Later: clean up files
for file_id in file_ids:
    client.beta.files.delete(file_id)
    print(f"Deleted {file_id}")
```

### Async File Operations

```python
import asyncio
from anthropic import AsyncAnthropic
from anthropic._utils import file_from_path

async def main():
    client = AsyncAnthropic()

    # Upload file
    file = file_from_path("document.pdf")
    uploaded = await client.beta.files.upload(
        file=file,
        purpose="user_data"
    )
    print(f"Uploaded: {uploaded.id}")

    # List files
    files = await client.beta.files.list(limit=10)
    async for file in files:
        print(f"File: {file.filename}")

    # Download file
    content = await client.beta.files.download(uploaded.id)
    print(f"Downloaded {len(content)} bytes")

    # Delete file
    deleted = await client.beta.files.delete(uploaded.id)
    print(f"Deleted: {deleted.id}")

asyncio.run(main())
```

### Error Handling

```python
from anthropic import APIError, NotFoundError, BadRequestError

# Upload with error handling
try:
    file = file_from_path("large_document.pdf")
    uploaded = client.beta.files.upload(
        file=file,
        purpose="user_data"
    )
    print(f"Uploaded: {uploaded.id}")
except BadRequestError as e:
    if "size" in str(e).lower():
        print(f"File too large: {e.message}")
    else:
        print(f"Invalid file: {e.message}")
except APIError as e:
    print(f"Upload failed: {e.message}")

# Download with error handling
try:
    content = client.beta.files.download("file_abc123")
    with open("output.pdf", "wb") as f:
        f.write(content)
except NotFoundError:
    print("File not found")
except APIError as e:
    print(f"Download failed: {e.message}")

# Delete with validation
file_id = "file_abc123"
try:
    # Check if file exists
    file_metadata = client.beta.files.retrieve(file_id)
    print(f"Deleting {file_metadata.filename}")

    # Delete file
    deleted = client.beta.files.delete(file_id)
    print(f"Deleted: {deleted.deleted}")
except NotFoundError:
    print(f"File {file_id} not found")
except APIError as e:
    print(f"Deletion failed: {e.message}")
```

### File Lifecycle Management

```python
class FileManager:
    """Manage file uploads with automatic cleanup."""

    def __init__(self, client):
        self.client = client
        self.uploaded_files = []

    def upload(self, filepath, purpose="user_data"):
        """Upload file and track it."""
        file = file_from_path(filepath)
        uploaded = self.client.beta.files.upload(
            file=file,
            purpose=purpose
        )
        self.uploaded_files.append(uploaded.id)
        return uploaded

    def cleanup(self):
        """Delete all tracked files."""
        for file_id in self.uploaded_files:
            try:
                self.client.beta.files.delete(file_id)
                print(f"Deleted {file_id}")
            except APIError as e:
                print(f"Failed to delete {file_id}: {e.message}")
        self.uploaded_files.clear()

# Usage
manager = FileManager(client)

try:
    # Upload files
    file1 = manager.upload("doc1.pdf")
    file2 = manager.upload("doc2.pdf")

    # Use files...
    print(f"Using files: {file1.id}, {file2.id}")

finally:
    # Always cleanup
    manager.cleanup()
```

### Check File Before Use

```python
def safe_file_operation(file_id):
    """Safely perform operations on a file."""
    try:
        # Verify file exists
        metadata = client.beta.files.retrieve(file_id)

        # Check file properties
        if metadata.purpose != "user_data":
            print(f"Warning: File has purpose '{metadata.purpose}'")

        # Download if needed
        content = client.beta.files.download(file_id)
        print(f"File size: {len(content)} bytes")

        return content

    except NotFoundError:
        print(f"File {file_id} not found")
        return None
    except APIError as e:
        print(f"Error: {e.message}")
        return None

# Use safely
content = safe_file_operation("file_abc123")
if content:
    # Process content
    pass
```

## File Purposes

### batch

Used for batch processing operations:
- Batch request files (JSONL format)
- Batch result files
- Structured data for bulk operations

Example:
```python
batch_file = client.beta.files.upload(
    file=("requests.jsonl", jsonl_data),
    purpose="batch"
)
```

### user_data

Used for general document analysis and conversation:
- PDF documents
- Text files
- Images
- CSV data
- Any user-provided content

Example:
```python
doc_file = client.beta.files.upload(
    file=file_from_path("document.pdf"),
    purpose="user_data"
)
```

## Best Practices

### 1. Use Appropriate Purpose

Choose the right purpose for your use case:
```python
# For batch processing
client.beta.files.upload(file=batch_data, purpose="batch")

# For document analysis
client.beta.files.upload(file=document, purpose="user_data")
```

### 2. Track Uploaded Files

Keep track of file IDs for cleanup:
```python
uploaded_ids = []
for doc in documents:
    uploaded = client.beta.files.upload(file=doc, purpose="user_data")
    uploaded_ids.append(uploaded.id)

# Later cleanup
for file_id in uploaded_ids:
    client.beta.files.delete(file_id)
```

### 3. Handle Errors Gracefully

Always handle file operation errors:
```python
try:
    uploaded = client.beta.files.upload(file=large_file, purpose="user_data")
except BadRequestError as e:
    # Handle validation errors (size, format, etc.)
    handle_validation_error(e)
except APIError as e:
    # Handle other API errors
    handle_api_error(e)
```

### 4. Clean Up Unused Files

Delete files when no longer needed:
```python
# After processing
client.beta.files.delete(file_id)
```

### 5. Use file_from_path Helper

Leverage the SDK helper for file uploads:
```python
from anthropic._utils import file_from_path

# Automatically handles file reading and metadata
file = file_from_path("document.pdf")
uploaded = client.beta.files.upload(file=file, purpose="user_data")
```

### 6. Validate Before Upload

Check file properties before uploading:
```python
import os

def validate_and_upload(filepath, max_size_mb=10):
    """Validate file before upload."""
    if not os.path.exists(filepath):
        raise ValueError(f"File not found: {filepath}")

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"File too large: {size_mb:.1f}MB (max {max_size_mb}MB)")

    return client.beta.files.upload(
        file=file_from_path(filepath),
        purpose="user_data"
    )
```

### 7. Pagination for Large Lists

Use pagination for many files:
```python
def list_all_files(client):
    """List all files with pagination."""
    all_files = []
    after_id = None

    while True:
        page = client.beta.files.list(limit=100, after_id=after_id)
        all_files.extend(page.data)

        if not page.has_next_page():
            break

        after_id = page.data[-1].id

    return all_files
```

## Limitations and Considerations

### File Size Limits

- Check API documentation for current file size limits
- Limits may vary by purpose (batch vs user_data)
- Consider splitting large files if possible

### Supported Formats

- PDFs (for document analysis)
- Text files (plain text, markdown, etc.)
- Images (PNG, JPEG, etc.)
- JSONL (for batch processing)
- CSV and other structured data formats

### File Retention

- Files persist until explicitly deleted
- No automatic cleanup
- Monitor storage usage

### Purpose-Specific Constraints

- batch: Must be valid JSONL format for batch requests
- user_data: General content, validated by API

### Rate Limits

- File upload operations count against rate limits
- Large files may take longer to process
- Consider rate limiting for bulk uploads

## See Also

- [Beta Overview](./index.md) - Overview of all beta features
- [Skills API](./skills.md) - Create and manage reusable skills
- [Beta Batches](./batches.md) - Batch processing with files
- [Message Features](./message-features.md) - Using files in messages with citations
