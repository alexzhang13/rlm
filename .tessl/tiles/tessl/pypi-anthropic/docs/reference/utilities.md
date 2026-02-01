# Utilities Reference

Helper functions for file handling, schema transformation, and HTTP client customization.

## File Utilities

```python { .api }
def file_from_path(path: str | Path) -> FileTypes:
    """
    Load single file from filesystem path.

    Parameters:
        path: File path (string or Path object)

    Returns:
        File-like object for API requests (tuple of filename, content, mime-type)

    Raises:
        FileNotFoundError: If path does not exist
        IsADirectoryError: If path is a directory
    """
    ...

def files_from_dir(directory: str | os.PathLike[str]) -> list[FileTypes]:
    """
    Load all files from a directory recursively.

    Recursively walks through directory and loads all files, returning them
    as a list suitable for batch file upload operations.

    Parameters:
        directory: Directory path (string or PathLike object)

    Returns:
        List of file objects, each as (filename, content, mime-type) tuple

    Raises:
        FileNotFoundError: If directory does not exist
        NotADirectoryError: If path is not a directory
    """
    ...

async def async_files_from_dir(directory: str | os.PathLike[str]) -> list[FileTypes]:
    """
    Async version of files_from_dir().

    Asynchronously loads all files from directory recursively. Useful for
    large directories or when loading many files in async context.

    Parameters:
        directory: Directory path (string or PathLike object)

    Returns:
        List of file objects, each as (filename, content, mime-type) tuple

    Raises:
        FileNotFoundError: If directory does not exist
        NotADirectoryError: If path is not a directory
    """
    ...
```

## Schema Transformation

```python { .api }
def transform_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Transform JSON schema for structured outputs.

    Parameters:
        schema: JSON Schema dictionary

    Returns:
        Transformed schema for API
    """
    ...
```

## HTTP Client Factories

```python { .api }
class DefaultHttpxClient:
    """Default synchronous HTTP client."""
    def __init__(
        self,
        *,
        proxy: str | httpx.Proxy | None = None,
        transport: httpx.HTTPTransport | None = None,
        **kwargs
    ): ...

class DefaultAsyncHttpxClient:
    """Default asynchronous HTTP client."""
    def __init__(
        self,
        *,
        proxy: str | httpx.Proxy | None = None,
        transport: httpx.AsyncHTTPTransport | None = None,
        **kwargs
    ): ...

class DefaultAioHttpClient:
    """Alternative async HTTP client using aiohttp."""
    def __init__(self, **kwargs): ...
```

## Quick Examples

### Load Single File

```python
from anthropic._utils import file_from_path

file = file_from_path("document.pdf")
uploaded = client.beta.files.upload(file, purpose="batch")
```

### Load Multiple Files from Directory

```python
from anthropic._utils import files_from_dir

# Load all files from a directory
files = files_from_dir("./documents")
print(f"Loaded {len(files)} files")

# Upload all files for batch processing
for file in files:
    uploaded = client.beta.files.upload(file, purpose="batch")
    print(f"Uploaded: {uploaded.id}")
```

### Async Load Files from Directory

```python
import asyncio
from anthropic._utils import async_files_from_dir

async def upload_directory():
    client = AsyncAnthropic()

    # Asynchronously load all files
    files = await async_files_from_dir("./documents")

    # Upload concurrently
    tasks = [client.beta.files.upload(f, purpose="batch") for f in files]
    results = await asyncio.gather(*tasks)

    print(f"Uploaded {len(results)} files")

asyncio.run(upload_directory())
```

### Transform Schema

```python
from pydantic import BaseModel
from anthropic.lib._parse._transform import transform_schema

class Response(BaseModel):
    answer: str
    confidence: float

schema = transform_schema(Response.model_json_schema())
```

## See Also

- [Client Configuration](./client-config.md) - Client initialization
