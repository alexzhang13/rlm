# File Search Stores and Documents

Create and manage file search stores with document retrieval for retrieval-augmented generation (RAG). File search stores enable semantic search over your documents, allowing models to ground responses in your own data sources.

## Capabilities

### Create File Search Store

Create a file search store to organize and search documents.

```python { .api }
class FileSearchStores:
    """Synchronous file search stores API."""

    def create(
        self,
        *,
        config: CreateFileSearchStoreConfig
    ) -> FileSearchStore:
        """
        Create a file search store.

        Parameters:
            config (CreateFileSearchStoreConfig): Store configuration including:
                - display_name: Display name for the store
                - description: Description of the store

        Returns:
            FileSearchStore: Created store with name and metadata.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

    @property
    def documents(self) -> Documents:
        """Access documents sub-API for managing documents within stores."""
        ...

class AsyncFileSearchStores:
    """Asynchronous file search stores API."""

    async def create(
        self,
        *,
        config: CreateFileSearchStoreConfig
    ) -> FileSearchStore:
        """Async version of create."""
        ...

    @property
    def documents(self) -> AsyncDocuments:
        """Access async documents sub-API."""
        ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import CreateFileSearchStoreConfig

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

config = CreateFileSearchStoreConfig(
    display_name='Product Documentation',
    description='Store for product manuals and guides'
)

store = client.file_search_stores.create(config=config)
print(f"Created store: {store.name}")
```

### Get File Search Store

Retrieve information about a file search store.

```python { .api }
class FileSearchStores:
    """Synchronous file search stores API."""

    def get(self, *, name: str) -> FileSearchStore:
        """
        Get file search store information.

        Parameters:
            name (str): Store name in format 'fileSearchStores/*'.

        Returns:
            FileSearchStore: Store information.
        """
        ...

class AsyncFileSearchStores:
    """Asynchronous file search stores API."""

    async def get(self, *, name: str) -> FileSearchStore:
        """Async version of get."""
        ...
```

### Delete File Search Store

Delete a file search store and all its documents.

```python { .api }
class FileSearchStores:
    """Synchronous file search stores API."""

    def delete(self, *, name: str) -> None:
        """
        Delete a file search store.

        Parameters:
            name (str): Store name in format 'fileSearchStores/*'.
        """
        ...

class AsyncFileSearchStores:
    """Asynchronous file search stores API."""

    async def delete(self, *, name: str) -> None:
        """Async version of delete."""
        ...
```

### Import File

Import a file into a file search store from GCS.

```python { .api }
class FileSearchStores:
    """Synchronous file search stores API."""

    def import_file(
        self,
        *,
        store: str,
        source: ImportFileSource,
        config: Optional[ImportFileConfig] = None
    ) -> ImportFileOperation:
        """
        Import file into store (returns long-running operation).

        Parameters:
            store (str): Store name.
            source (ImportFileSource): Import source (GCS URI).
            config (ImportFileConfig, optional): Import configuration.

        Returns:
            ImportFileOperation: Long-running operation for import.
        """
        ...

class AsyncFileSearchStores:
    """Asynchronous file search stores API."""

    async def import_file(
        self,
        *,
        store: str,
        source: ImportFileSource,
        config: Optional[ImportFileConfig] = None
    ) -> ImportFileOperation:
        """Async version of import_file."""
        ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import ImportFileSource

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

source = ImportFileSource(
    gcs_uri='gs://my-bucket/document.pdf'
)

operation = client.file_search_stores.import_file(
    store='fileSearchStores/abc123',
    source=source
)

# Poll for completion
while not operation.done:
    import time
    time.sleep(5)
    operation = client.operations.get(operation)

print("Import complete")
```

### Upload to File Search Store

Upload a local file directly to a file search store.

```python { .api }
class FileSearchStores:
    """Synchronous file search stores API."""

    def upload_to_file_search_store(
        self,
        *,
        store: str,
        file: Union[str, Path, IO],
        config: Optional[UploadToFileSearchStoreConfig] = None
    ) -> UploadToFileSearchStoreOperation:
        """
        Upload file to store (returns long-running operation).

        Parameters:
            store (str): Store name.
            file (Union[str, Path, IO]): File to upload.
            config (UploadToFileSearchStoreConfig, optional): Upload configuration including:
                - mime_type: File MIME type
                - display_name: Display name

        Returns:
            UploadToFileSearchStoreOperation: Long-running operation for upload.
        """
        ...

class AsyncFileSearchStores:
    """Asynchronous file search stores API."""

    async def upload_to_file_search_store(
        self,
        *,
        store: str,
        file: Union[str, Path, IO],
        config: Optional[UploadToFileSearchStoreConfig] = None
    ) -> UploadToFileSearchStoreOperation:
        """Async version of upload_to_file_search_store."""
        ...
```

### List File Search Stores

List all file search stores.

```python { .api }
class FileSearchStores:
    """Synchronous file search stores API."""

    def list(
        self,
        *,
        config: Optional[ListFileSearchStoresConfig] = None
    ) -> Union[Pager[FileSearchStore], Iterator[FileSearchStore]]:
        """
        List file search stores.

        Parameters:
            config (ListFileSearchStoresConfig, optional): List configuration.

        Returns:
            Union[Pager[FileSearchStore], Iterator[FileSearchStore]]: Paginated store list.
        """
        ...

class AsyncFileSearchStores:
    """Asynchronous file search stores API."""

    async def list(
        self,
        *,
        config: Optional[ListFileSearchStoresConfig] = None
    ) -> Union[AsyncPager[FileSearchStore], AsyncIterator[FileSearchStore]]:
        """Async version of list."""
        ...
```

### Documents Sub-API

Manage documents within file search stores.

```python { .api }
class Documents:
    """Synchronous documents API."""

    def get(self, *, name: str) -> Document:
        """
        Get document information.

        Parameters:
            name (str): Document name in format 'fileSearchStores/*/documents/*'.

        Returns:
            Document: Document information.
        """
        ...

    def delete(self, *, name: str) -> None:
        """
        Delete a document.

        Parameters:
            name (str): Document name.
        """
        ...

    def list(
        self,
        *,
        parent: str,
        config: Optional[ListDocumentsConfig] = None
    ) -> Union[Pager[Document], Iterator[Document]]:
        """
        List documents in a store.

        Parameters:
            parent (str): Store name in format 'fileSearchStores/*'.
            config (ListDocumentsConfig, optional): List configuration.

        Returns:
            Union[Pager[Document], Iterator[Document]]: Paginated document list.
        """
        ...

class AsyncDocuments:
    """Asynchronous documents API."""

    async def get(self, *, name: str) -> Document:
        """Async version of get."""
        ...

    async def delete(self, *, name: str) -> None:
        """Async version of delete."""
        ...

    async def list(
        self,
        *,
        parent: str,
        config: Optional[ListDocumentsConfig] = None
    ) -> Union[AsyncPager[Document], AsyncIterator[Document]]:
        """Async version of list."""
        ...
```

**Usage Example - Using File Search in RAG:**

```python
from google.genai import Client
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    FileSearch
)

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Configure file search tool
config = GenerateContentConfig(
    tools=[Tool(file_search=FileSearch(
        file_search_store='fileSearchStores/abc123'
    ))]
)

# Generate with grounding in documents
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the return policy for damaged items?',
    config=config
)

print(response.text)

# Check grounding metadata
if response.candidates[0].grounding_metadata:
    print("Grounded in store documents")
```

## Types

```python { .api }
from typing import Optional, Union, List, Iterator, AsyncIterator, IO, TypedDict
from pathlib import Path
from datetime import datetime
from enum import Enum

# Configuration types
class CreateFileSearchStoreConfig:
    """
    Configuration for creating file search store.

    Attributes:
        display_name (str, optional): Display name.
        description (str, optional): Description.
    """
    display_name: Optional[str] = None
    description: Optional[str] = None

class ImportFileConfig:
    """Configuration for importing files."""
    display_name: Optional[str] = None

class UploadToFileSearchStoreConfig:
    """
    Configuration for uploading files.

    Attributes:
        mime_type (str, optional): MIME type.
        display_name (str, optional): Display name.
    """
    mime_type: Optional[str] = None
    display_name: Optional[str] = None

class ListFileSearchStoresConfig:
    """Configuration for listing stores."""
    page_size: Optional[int] = None
    page_token: Optional[str] = None

class ListDocumentsConfig:
    """Configuration for listing documents."""
    page_size: Optional[int] = None
    page_token: Optional[str] = None

# Response types
class FileSearchStore:
    """
    File search store information.

    Attributes:
        name (str): Store resource name.
        display_name (str, optional): Display name.
        description (str, optional): Description.
        create_time (datetime): Creation time.
        update_time (datetime): Last update time.
    """
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    create_time: datetime
    update_time: datetime

class Document:
    """
    Document in file search store.

    Attributes:
        name (str): Document resource name.
        display_name (str, optional): Display name.
        mime_type (str): MIME type.
        size_bytes (int): Size in bytes.
        state (DocumentState): Processing state.
        create_time (datetime): Creation time.
        update_time (datetime): Last update time.
    """
    name: str
    display_name: Optional[str] = None
    mime_type: str
    size_bytes: int
    state: DocumentState
    create_time: datetime
    update_time: datetime

class DocumentState(Enum):
    """Document processing states."""
    STATE_UNSPECIFIED = 'STATE_UNSPECIFIED'
    PROCESSING = 'PROCESSING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'

class ImportFileSource:
    """
    Import source.

    Attributes:
        gcs_uri (str): GCS URI of file to import.
    """
    gcs_uri: str

# Operation types
class ImportFileOperation:
    """Long-running operation for file import."""
    name: str
    done: bool
    error: Optional[OperationError] = None
    response: Optional[dict] = None

class UploadToFileSearchStoreOperation:
    """Long-running operation for file upload."""
    name: str
    done: bool
    error: Optional[OperationError] = None
    response: Optional[dict] = None

class OperationError:
    """Operation error."""
    code: int
    message: str

# Tool types for RAG
class FileSearch:
    """
    File search tool configuration.

    Attributes:
        file_search_store (str, optional): Store name to search.
    """
    file_search_store: Optional[str] = None

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
