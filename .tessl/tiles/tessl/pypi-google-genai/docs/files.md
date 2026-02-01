# File Management

Upload, manage, and download files for use with multimodal content generation. File management is available in the Gemini Developer API only. Files can be images, audio, video, or documents that are referenced in content generation requests.

## Capabilities

### Upload File

Upload a file to be used in content generation. Files are stored temporarily and automatically deleted after a retention period.

```python { .api }
class Files:
    """Synchronous file management API."""

    def upload(
        self,
        *,
        file: Union[str, Path, IO],
        config: Optional[UploadFileConfig] = None
    ) -> File:
        """
        Upload a file for use in generation requests.

        Parameters:
            file (Union[str, Path, IO]): File to upload. Can be:
                - str or Path: File path to upload
                - IO: File-like object (must be opened in binary mode)
            config (UploadFileConfig, optional): Upload configuration including:
                - mime_type: MIME type of the file (auto-detected if not provided)
                - display_name: Display name for the file

        Returns:
            File: Uploaded file information including URI, name, and metadata.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncFiles:
    """Asynchronous file management API."""

    async def upload(
        self,
        *,
        file: Union[str, Path, IO],
        config: Optional[UploadFileConfig] = None
    ) -> File:
        """Async version of upload."""
        ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import UploadFileConfig

client = Client(api_key='YOUR_API_KEY')

# Upload from file path
config = UploadFileConfig(
    mime_type='image/jpeg',
    display_name='Product Photo'
)

file = client.files.upload(
    file='product.jpg',
    config=config
)

print(f"Uploaded file: {file.name}")
print(f"URI: {file.uri}")
print(f"State: {file.state}")

# Use in generation
from google.genai.types import Content, Part, FileData

content = Content(
    parts=[
        Part(text='Describe this image'),
        Part(file_data=FileData(file_uri=file.uri, mime_type=file.mime_type))
    ]
)

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=content
)
print(response.text)
```

### Get File

Retrieve information about an uploaded file.

```python { .api }
class Files:
    """Synchronous file management API."""

    def get(self, *, name: str) -> File:
        """
        Get file information.

        Parameters:
            name (str): File name (from File.name) in format 'files/{file_id}'.

        Returns:
            File: File information including state, size, and metadata.

        Raises:
            ClientError: For client errors including 404 if file not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncFiles:
    """Asynchronous file management API."""

    async def get(self, *, name: str) -> File:
        """Async version of get."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Get file info
file = client.files.get(name='files/abc123')

print(f"Name: {file.display_name}")
print(f"Size: {file.size_bytes} bytes")
print(f"State: {file.state}")
print(f"Created: {file.create_time}")
print(f"Expires: {file.expiration_time}")
```

### Delete File

Delete an uploaded file. Files are automatically deleted after their expiration time, but you can delete them earlier if needed.

```python { .api }
class Files:
    """Synchronous file management API."""

    def delete(self, *, name: str) -> None:
        """
        Delete a file.

        Parameters:
            name (str): File name in format 'files/{file_id}'.

        Raises:
            ClientError: For client errors including 404 if file not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncFiles:
    """Asynchronous file management API."""

    async def delete(self, *, name: str) -> None:
        """Async version of delete."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Delete file
client.files.delete(name='files/abc123')
print("File deleted")
```

### Download File

Download the contents of an uploaded file.

```python { .api }
class Files:
    """Synchronous file management API."""

    def download(self, *, name: str, path: Optional[str] = None) -> bytes:
        """
        Download file contents.

        Parameters:
            name (str): File name in format 'files/{file_id}'.
            path (str, optional): Local file path to save to. If not provided,
                returns file contents as bytes without saving.

        Returns:
            bytes: File contents. If path is provided, also saves to file.

        Raises:
            ClientError: For client errors including 404 if file not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncFiles:
    """Asynchronous file management API."""

    async def download(self, *, name: str, path: Optional[str] = None) -> bytes:
        """Async version of download."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Download to file
data = client.files.download(name='files/abc123', path='downloaded.jpg')
print(f"Downloaded {len(data)} bytes")

# Download to memory
data = client.files.download(name='files/abc123')
# Process data in memory
```

### List Files

List all uploaded files with optional pagination.

```python { .api }
class Files:
    """Synchronous file management API."""

    def list(
        self,
        *,
        config: Optional[ListFilesConfig] = None
    ) -> Union[Pager[File], Iterator[File]]:
        """
        List uploaded files.

        Parameters:
            config (ListFilesConfig, optional): List configuration including:
                - page_size: Number of files per page (default: 50, max: 100)
                - page_token: Token for pagination

        Returns:
            Union[Pager[File], Iterator[File]]: Paginated file list. If page_size
                is set, returns Pager for manual pagination. Otherwise, returns
                Iterator that automatically handles pagination.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncFiles:
    """Asynchronous file management API."""

    async def list(
        self,
        *,
        config: Optional[ListFilesConfig] = None
    ) -> Union[AsyncPager[File], AsyncIterator[File]]:
        """Async version of list."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# List all files (auto-pagination)
for file in client.files.list():
    print(f"{file.display_name}: {file.name} ({file.state})")

# Manual pagination
from google.genai.types import ListFilesConfig

config = ListFilesConfig(page_size=10)
pager = client.files.list(config=config)

print(f"Page 1: {len(pager.page)} files")
for file in pager.page:
    print(f"  {file.display_name}")

# Get next page
pager.next_page()
print(f"Page 2: {len(pager.page)} files")
```

## Types

```python { .api }
from typing import Optional, Union, IO, Iterator, AsyncIterator
from pathlib import Path
from enum import Enum
from datetime import datetime

# Configuration types
class UploadFileConfig:
    """
    Configuration for file upload.

    Attributes:
        mime_type (str, optional): MIME type of the file. If not provided, will be
            auto-detected from file extension or content.
        display_name (str, optional): Human-readable display name for the file.
    """
    mime_type: Optional[str] = None
    display_name: Optional[str] = None

class ListFilesConfig:
    """
    Configuration for listing files.

    Attributes:
        page_size (int, optional): Number of files per page (1-100). Default: 50.
        page_token (str, optional): Token from previous response for pagination.
    """
    page_size: Optional[int] = None
    page_token: Optional[str] = None

# Response types
class File:
    """
    Uploaded file information.

    Attributes:
        name (str): File resource name in format 'files/{file_id}'.
        display_name (str, optional): Display name for the file.
        mime_type (str): MIME type of the file.
        size_bytes (int): File size in bytes.
        create_time (datetime): When file was created.
        update_time (datetime): When file was last updated.
        expiration_time (datetime): When file will be automatically deleted.
        sha256_hash (bytes): SHA256 hash of file contents.
        uri (str): URI for referencing the file in API requests.
        state (FileState): Current processing state of the file.
        error (FileError, optional): Error if file processing failed.
    """
    name: str
    display_name: Optional[str] = None
    mime_type: str
    size_bytes: int
    create_time: datetime
    update_time: datetime
    expiration_time: datetime
    sha256_hash: bytes
    uri: str
    state: FileState
    error: Optional[FileError] = None

class FileState(Enum):
    """File processing state."""
    STATE_UNSPECIFIED = 'STATE_UNSPECIFIED'
    PROCESSING = 'PROCESSING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'

class FileError:
    """
    File processing error.

    Attributes:
        code (int): Error code.
        message (str): Error message.
    """
    code: int
    message: str

class FileData:
    """
    Reference to uploaded file for use in content.

    Attributes:
        file_uri (str): URI from File.uri.
        mime_type (str): MIME type from File.mime_type.
    """
    file_uri: str
    mime_type: str

# Pager types
class Pager[T]:
    """
    Synchronous pager for paginated results.

    Attributes:
        page (list[T]): Current page of items.
        page_size (int): Number of items per page.

    Methods:
        next_page(): Fetch next page of results.
    """
    page: list[T]
    page_size: int

    def next_page(self) -> None:
        """Fetch next page and update self.page."""
        ...

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items across pages."""
        ...

class AsyncPager[T]:
    """
    Asynchronous pager for paginated results.

    Attributes:
        page (list[T]): Current page of items.
        page_size (int): Number of items per page.

    Methods:
        next_page(): Fetch next page of results.
    """
    page: list[T]
    page_size: int

    async def next_page(self) -> None:
        """Fetch next page and update self.page."""
        ...

    async def __aiter__(self) -> AsyncIterator[T]:
        """Async iterate over all items across pages."""
        ...

# TypedDict variants
class UploadFileConfigDict(TypedDict, total=False):
    """TypedDict variant of UploadFileConfig."""
    mime_type: str
    display_name: str

class ListFilesConfigDict(TypedDict, total=False):
    """TypedDict variant of ListFilesConfig."""
    page_size: int
    page_token: str
```
