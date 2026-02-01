# Uploads

Upload large files in chunks for use with Assistants, Fine-tuning, and Batch processing. The Uploads API enables efficient multipart upload of files up to 8 GB, splitting them into 64 MB parts that can be uploaded in parallel.

## Capabilities

### Create Upload

Create an intermediate Upload object that accepts multiple parts.

```python { .api }
def create(
    self,
    *,
    bytes: int,
    filename: str,
    mime_type: str,
    purpose: FilePurpose,
    expires_after: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Upload:
    """
    Create an intermediate Upload object for adding file parts.

    Args:
        bytes: Total number of bytes in the file being uploaded.

        filename: Name of the file to upload.

        mime_type: MIME type of the file. Must be supported for the specified purpose.
            See https://platform.openai.com/docs/assistants/tools/file-search#supported-files

        purpose: Intended purpose of the file. Options:
            - "assistants": For use with Assistants API
            - "batch": For batch processing
            - "fine-tune": For fine-tuning
            - "vision": For vision capabilities
            See https://platform.openai.com/docs/api-reference/files/create#files-create-purpose

        expires_after: Expiration policy for the file. Default: files with purpose=batch
            expire after 30 days, others persist until manually deleted.
            {"anchor": "created_at", "days": 7} expires 7 days after creation.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Upload: Upload object with ID to use for adding parts.
            Contains status, expires_at, and other metadata.

    Notes:
        - Maximum upload size: 8 GB
        - Upload expires 1 hour after creation
        - Must complete upload before expiration
        - Each part can be at most 64 MB
    """
```

### Complete Upload

Finalize the upload after all parts have been added.

```python { .api }
def complete(
    self,
    upload_id: str,
    *,
    part_ids: list[str],
    md5: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Upload:
    """
    Complete the Upload and create a File object.

    Args:
        upload_id: ID of the Upload to complete.

        part_ids: Ordered list of Part IDs. Order determines how parts are assembled.

        md5: Optional MD5 checksum to verify uploaded bytes match expectations.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Upload: Completed Upload object containing a nested File object
            ready for use in the rest of the platform.

    Notes:
        - Total bytes uploaded must match bytes specified in create()
        - No parts can be added after completion
        - Upload must not be cancelled or expired
    """
```

### Cancel Upload

Cancel an upload that is no longer needed.

```python { .api }
def cancel(
    self,
    upload_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Upload:
    """
    Cancel an Upload.

    Args:
        upload_id: ID of the Upload to cancel.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Upload: Cancelled Upload object with status="cancelled".

    Notes:
        - No parts can be added after cancellation
        - Previously uploaded parts are discarded
    """
```

### Upload File Chunked

High-level helper that handles the entire upload process automatically.

```python { .api }
def upload_file_chunked(
    self,
    *,
    file: str | os.PathLike | bytes,
    mime_type: str,
    purpose: FilePurpose,
    filename: str | None = None,
    bytes: int | None = None,
    part_size: int | None = None,
    md5: str | Omit = omit,
) -> Upload:
    """
    Upload a file in chunks automatically.

    This convenience method handles:
    1. Creating the Upload
    2. Splitting file into parts
    3. Uploading each part sequentially
    4. Completing the Upload

    Args:
        file: File to upload. Can be:
            - Path-like object: Path("my-paper.pdf")
            - String path: "my-paper.pdf"
            - bytes: In-memory file data (requires filename and bytes args)

        mime_type: MIME type of the file (e.g., "application/pdf").

        purpose: Intended purpose ("assistants", "batch", "fine-tune", "vision").

        filename: Filename (required if file is bytes, optional otherwise).

        bytes: Total file size in bytes (required if file is bytes, optional otherwise).
            If not provided for path, automatically determined from file.

        part_size: Size of each part in bytes. Default: 64 MB (64 * 1024 * 1024).
            Each part uploads as a separate request.

        md5: Optional MD5 checksum for verification.

    Returns:
        Upload: Completed Upload object containing the File.

    Raises:
        TypeError: If filename or bytes not provided for in-memory files.
        ValueError: If file path is invalid or file cannot be read.
    """
```

Usage examples:

```python
from pathlib import Path
from openai import OpenAI

client = OpenAI()

# Upload a file from disk (simplest approach)
upload = client.uploads.upload_file_chunked(
    file=Path("training_data.jsonl"),
    mime_type="application/jsonl",
    purpose="fine-tune"
)

print(f"Upload complete! File ID: {upload.file.id}")

# Upload with custom part size (e.g., 32 MB parts)
upload = client.uploads.upload_file_chunked(
    file="large_dataset.jsonl",
    mime_type="application/jsonl",
    purpose="batch",
    part_size=32 * 1024 * 1024
)

# Upload in-memory bytes
file_data = b"..."  # Your file data
upload = client.uploads.upload_file_chunked(
    file=file_data,
    filename="document.pdf",
    bytes=len(file_data),
    mime_type="application/pdf",
    purpose="assistants"
)

# Upload with MD5 verification
upload = client.uploads.upload_file_chunked(
    file="important_data.csv",
    mime_type="text/csv",
    purpose="assistants",
    md5="5d41402abc4b2a76b9719d911017c592"
)
```

### Create Part

Add a single part to an Upload.

```python { .api }
def create(
    self,
    upload_id: str,
    *,
    data: FileTypes,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> UploadPart:
    """
    Add a Part to an Upload.

    Args:
        upload_id: ID of the Upload to add this Part to.

        data: Chunk of bytes for this Part. Maximum 64 MB.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        UploadPart: Part object with ID to use when completing the Upload.

    Notes:
        - Each Part can be at most 64 MB
        - Total size across all parts cannot exceed 8 GB
        - Parts can be added in parallel for faster uploads
        - Order is determined when completing the Upload
    """
```

Advanced manual upload example:

```python
from openai import OpenAI
import io

client = OpenAI()

# Step 1: Create the Upload
file_path = "large_file.pdf"
file_size = os.path.getsize(file_path)

upload = client.uploads.create(
    bytes=file_size,
    filename="large_file.pdf",
    mime_type="application/pdf",
    purpose="assistants"
)

print(f"Created upload: {upload.id}")

# Step 2: Upload parts
part_size = 64 * 1024 * 1024  # 64 MB
part_ids = []

with open(file_path, "rb") as f:
    while True:
        chunk = f.read(part_size)
        if not chunk:
            break

        part = client.uploads.parts.create(
            upload_id=upload.id,
            data=chunk
        )
        part_ids.append(part.id)
        print(f"Uploaded part {len(part_ids)}: {part.id}")

# Step 3: Complete the Upload
completed = client.uploads.complete(
    upload_id=upload.id,
    part_ids=part_ids
)

print(f"Upload complete! File ID: {completed.file.id}")

# Handle errors by cancelling
try:
    # ... upload process ...
    pass
except Exception as e:
    print(f"Error during upload: {e}")
    client.uploads.cancel(upload_id=upload.id)
    print("Upload cancelled")
```

Parallel upload example:

```python
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import io

client = OpenAI()

def upload_part(upload_id: str, part_data: bytes) -> str:
    """Upload a single part and return its ID."""
    part = client.uploads.parts.create(
        upload_id=upload_id,
        data=part_data
    )
    return part.id

# Create upload
file_path = "large_file.pdf"
file_size = os.path.getsize(file_path)

upload = client.uploads.create(
    bytes=file_size,
    filename="large_file.pdf",
    mime_type="application/pdf",
    purpose="assistants"
)

# Split file into chunks
part_size = 64 * 1024 * 1024
chunks = []

with open(file_path, "rb") as f:
    while True:
        chunk = f.read(part_size)
        if not chunk:
            break
        chunks.append(chunk)

# Upload parts in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    part_ids = list(executor.map(
        lambda chunk: upload_part(upload.id, chunk),
        chunks
    ))

# Complete upload
completed = client.uploads.complete(
    upload_id=upload.id,
    part_ids=part_ids
)

print(f"Parallel upload complete! File ID: {completed.file.id}")
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def upload_file():
    client = AsyncOpenAI()

    # Async upload
    upload = await client.uploads.upload_file_chunked(
        file="data.jsonl",
        mime_type="application/jsonl",
        purpose="fine-tune"
    )

    return upload.file.id

file_id = asyncio.run(upload_file())
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Upload(BaseModel):
    """Upload object containing metadata and status."""
    id: str
    bytes: int
    created_at: int
    expires_at: int
    filename: str
    object: Literal["upload"]
    purpose: FilePurpose
    status: Literal["pending", "completed", "cancelled", "expired"]
    file: FileObject | None  # Present when status="completed"

class UploadPart(BaseModel):
    """Part object representing a chunk of an upload."""
    id: str
    created_at: int
    object: Literal["upload.part"]
    upload_id: str

FilePurpose = Literal["assistants", "batch", "fine-tune", "vision"]

FileTypes = Union[
    FileContent,
    Tuple[Optional[str], FileContent],
    Tuple[Optional[str], FileContent, Optional[str]]
]

class Omit:
    """Sentinel value for omitted parameters."""
```

## Access Pattern

```python
# Synchronous
from openai import OpenAI
client = OpenAI()
client.uploads.create(...)
client.uploads.complete(...)
client.uploads.cancel(...)
client.uploads.upload_file_chunked(...)
client.uploads.parts.create(...)

# Asynchronous
from openai import AsyncOpenAI
client = AsyncOpenAI()
await client.uploads.create(...)
await client.uploads.complete(...)
await client.uploads.cancel(...)
await client.uploads.upload_file_chunked(...)
await client.uploads.parts.create(...)
```
