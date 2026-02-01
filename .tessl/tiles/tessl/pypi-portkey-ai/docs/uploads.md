# Uploads

Large file upload system with support for chunked uploads and multi-part file handling. Enables efficient upload of large files through resumable, chunked upload process with integrity verification.

## Capabilities

### Upload Management

Create, manage, and complete large file uploads using multi-part upload process for improved reliability and performance.

```python { .api }
class Uploads:
    def create(
        self,
        *,
        bytes: int,
        filename: str,
        mime_type: str,
        purpose: Any,
        **kwargs
    ) -> Upload:
        """
        Create a new upload session for large files.

        Args:
            bytes: Total size of the file in bytes
            filename: Name of the file being uploaded
            mime_type: MIME type of the file (e.g., "image/jpeg", "application/pdf")
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            **kwargs: Additional upload parameters

        Returns:
            Upload: Upload session object with upload ID and status
        """

    def upload_file_chunked(
        self,
        *,
        file: Union[os.PathLike[str], bytes],
        mime_type: str,
        purpose: Any,
        filename: Union[str, None] = None,
        bytes: Union[int, None] = None,
        part_size: Union[int, None] = None,
        md5: Union[str, NotGiven] = NOT_GIVEN
    ) -> Any:
        """
        Upload a file using automatic chunking for large files.

        Args:
            file: File path or file content bytes
            mime_type: MIME type of the file
            purpose: Purpose of the upload
            filename: Optional filename override
            bytes: Optional file size override
            part_size: Size of each chunk (default: 8MB)
            md5: MD5 hash for integrity verification

        Returns:
            File object after successful upload
        """

    def complete(
        self,
        upload_id: str,
        *,
        part_ids: List[str],
        md5: Union[str, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> Upload:
        """
        Complete a multi-part upload by assembling all parts.

        Args:
            upload_id: Upload session identifier
            part_ids: List of part IDs in order
            md5: MD5 hash of complete file for verification
            **kwargs: Additional completion parameters

        Returns:
            Upload: Completed upload object
        """

    def cancel(self, upload_id: str, **kwargs) -> Upload:
        """
        Cancel an in-progress upload session.

        Args:
            upload_id: Upload session identifier
            **kwargs: Additional cancellation parameters

        Returns:
            Upload: Cancelled upload object
        """

    parts: Parts

class AsyncUploads:
    async def create(
        self,
        *,
        bytes: int,
        filename: str,
        mime_type: str,
        purpose: Any,
        **kwargs
    ) -> Upload:
        """Async version of create method."""

    async def upload_file_chunked(
        self,
        *,
        file: Union[os.PathLike[str], bytes],
        mime_type: str,
        purpose: Any,
        filename: Union[str, None] = None,
        bytes: Union[int, None] = None,
        part_size: Union[int, None] = None,
        md5: Union[str, NotGiven] = NOT_GIVEN
    ) -> Any:
        """Async version of chunked upload method."""

    async def complete(
        self,
        upload_id: str,
        *,
        part_ids: List[str],
        md5: Union[str, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> Upload:
        """Async version of complete method."""

    async def cancel(self, upload_id: str, **kwargs) -> Upload:
        """Async version of cancel method."""

    parts: AsyncParts
```

### Part Management

Handle individual parts of multi-part uploads for fine-grained control over the upload process.

```python { .api }
class Parts:
    def create(
        self,
        upload_id: str,
        *,
        data: FileTypes,
        **kwargs
    ) -> UploadPart:
        """
        Upload a single part of a multi-part upload.

        Args:
            upload_id: Upload session identifier
            data: Part data as file-like object or bytes
            **kwargs: Additional part parameters

        Returns:
            UploadPart: Part object with part ID and status
        """

class AsyncParts:
    async def create(
        self,
        upload_id: str,
        *,
        data: FileTypes,
        **kwargs
    ) -> UploadPart:
        """Async version of part creation."""
```

### Usage Examples

```python
import os
from portkey_ai import Portkey

# Initialize client
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Simple chunked upload (recommended for most use cases)
with open("large_document.pdf", "rb") as f:
    uploaded_file = portkey.uploads.upload_file_chunked(
        file=f,
        mime_type="application/pdf",
        purpose="assistants",
        filename="large_document.pdf"
    )

print(f"File uploaded successfully: {uploaded_file.id}")

# Manual multi-part upload for advanced use cases
file_path = "very_large_file.zip"
file_size = os.path.getsize(file_path)

# Create upload session
upload = portkey.uploads.create(
    bytes=file_size,
    filename="very_large_file.zip",
    mime_type="application/zip",
    purpose="assistants"
)

print(f"Upload session created: {upload.id}")

# Upload parts manually (8MB chunks)
part_size = 8 * 1024 * 1024  # 8MB
part_ids = []

with open(file_path, "rb") as f:
    part_number = 1
    while True:
        chunk = f.read(part_size)
        if not chunk:
            break
            
        part = portkey.uploads.parts.create(
            upload_id=upload.id,
            data=chunk
        )
        part_ids.append(part.id)
        print(f"Uploaded part {part_number}: {part.id}")
        part_number += 1

# Complete the upload
completed_upload = portkey.uploads.complete(
    upload_id=upload.id,
    part_ids=part_ids
)

print(f"Upload completed: {completed_upload.status}")
print(f"File ID: {completed_upload.file.id}")
```

### Async Usage

```python
import asyncio
import os
from portkey_ai import AsyncPortkey

async def upload_large_file():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    # Async chunked upload
    with open("large_dataset.csv", "rb") as f:
        uploaded_file = await portkey.uploads.upload_file_chunked(
            file=f,
            mime_type="text/csv",
            purpose="fine-tune",
            part_size=16 * 1024 * 1024  # 16MB chunks
        )
    
    return uploaded_file

# Run async upload
uploaded_file = asyncio.run(upload_large_file())
print(f"Async upload completed: {uploaded_file.id}")
```

### Error Handling and Resumption

```python
import hashlib
import os

def upload_with_verification():
    file_path = "important_document.pdf"
    
    # Calculate MD5 for integrity verification
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    file_size = os.path.getsize(file_path)
    
    try:
        # Create upload with MD5
        upload = portkey.uploads.create(
            bytes=file_size,
            filename=os.path.basename(file_path),
            mime_type="application/pdf",
            purpose="assistants"
        )
        
        # Upload with chunked method including hash
        with open(file_path, "rb") as f:
            uploaded_file = portkey.uploads.upload_file_chunked(
                file=f,
                mime_type="application/pdf",
                purpose="assistants",
                md5=file_hash
            )
        
        print(f"Upload successful with verification: {uploaded_file.id}")
        return uploaded_file
        
    except Exception as e:
        print(f"Upload failed: {e}")
        # Cancel the upload session if it was created
        if 'upload' in locals():
            try:
                cancelled = portkey.uploads.cancel(upload.id)
                print(f"Upload cancelled: {cancelled.status}")
            except Exception as cancel_error:
                print(f"Failed to cancel upload: {cancel_error}")
        
        raise

# Example with retry logic
def upload_with_retry(file_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            return upload_with_verification()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            # Wait before retry
            import time
            time.sleep(2 ** attempt)
```

## Types

```python { .api }
class Upload:
    """Upload session object"""
    id: str  # Upload identifier
    object: str  # "upload"
    bytes: int  # Total file size
    created_at: int  # Unix timestamp
    filename: str  # Original filename
    purpose: str  # Upload purpose
    status: str  # Upload status ("pending", "completed", "cancelled", "failed")
    expires_at: int  # Session expiration timestamp
    file: Optional[FileObject]  # File object after completion
    _headers: Optional[dict]  # Response headers

class UploadPart:
    """Individual upload part"""
    id: str  # Part identifier
    object: str  # "upload.part"
    created_at: int  # Unix timestamp
    upload_id: str  # Parent upload identifier
    etag: str  # Part ETag for integrity
    _headers: Optional[dict]  # Response headers

class FileObject:
    """Completed file object"""
    id: str  # File identifier
    object: str  # "file"
    bytes: int  # File size
    created_at: int  # Unix timestamp
    filename: str  # File name
    purpose: str  # File purpose
    status: str  # Processing status
    status_details: Optional[str]  # Status details if applicable

FileTypes = Union[
    bytes,
    str,
    os.PathLike[str],
    typing.IO[bytes],
    typing.IO[str]
]
"""Supported file input types for uploads"""
```