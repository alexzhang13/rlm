# Long-Running Operations

Monitor and retrieve status of long-running operations like video generation, file imports, and other asynchronous tasks. Operations provide a way to track progress and retrieve results for tasks that take significant time to complete.

## Capabilities

### Get Operation

Retrieve the current status and result of a long-running operation.

```python { .api }
class Operations:
    """Synchronous long-running operations API."""

    def get(self, operation: Union[Operation, str]) -> Operation:
        """
        Get operation status and result.

        Parameters:
            operation (Union[Operation, str]): Operation to check. Can be:
                - Operation: Operation object to refresh
                - str: Operation name/resource name

        Returns:
            Operation: Updated operation with current status. Check operation.done
                to see if complete. If done, check operation.error for errors or
                operation.response for results.

        Raises:
            ClientError: For client errors including 404 if operation not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncOperations:
    """Asynchronous long-running operations API."""

    async def get(self, operation: Union[Operation, str]) -> Operation:
        """Async version of get."""
        ...
```

**Usage Example - Video Generation:**

```python
import time
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Start video generation
operation = client.models.generate_videos(
    model='veo-2.0-generate-001',
    prompt='A cat playing with a ball'
)

print(f"Operation started: {operation.name}")
print(f"Done: {operation.done}")

# Poll for completion
while not operation.done:
    print("Waiting for completion...")
    time.sleep(10)

    # Refresh operation status
    operation = client.operations.get(operation)
    print(f"Done: {operation.done}")

# Check result
if operation.error:
    print(f"Operation failed: {operation.error.message}")
else:
    print("Operation succeeded!")
    response = operation.response

    # Access video generation response
    for i, video in enumerate(response.generated_videos):
        with open(f'video_{i}.mp4', 'wb') as f:
            f.write(video.video.data)
        print(f"Saved video_{i}.mp4")
```

**Usage Example - File Import:**

```python
from google.genai import Client
from google.genai.types import ImportFileSource

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Start file import
source = ImportFileSource(gcs_uri='gs://my-bucket/document.pdf')
operation = client.file_search_stores.import_file(
    store='fileSearchStores/abc123',
    source=source
)

print(f"Import operation: {operation.name}")

# Poll until done
while not operation.done:
    import time
    time.sleep(5)
    operation = client.operations.get(operation)

if operation.error:
    print(f"Import failed: {operation.error.message}")
else:
    print("Import completed successfully")
```

**Usage Example - Async Polling:**

```python
import asyncio
from google.genai import Client

async def wait_for_operation():
    client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

    # Start operation
    operation = await client.aio.models.generate_videos(
        model='veo-2.0-generate-001',
        prompt='A sunset over mountains'
    )

    print(f"Operation: {operation.name}")

    # Poll asynchronously
    while not operation.done:
        print("Checking status...")
        await asyncio.sleep(10)
        operation = await client.aio.operations.get(operation)

    if operation.error:
        print(f"Failed: {operation.error.message}")
    else:
        print(f"Success! Generated {len(operation.response.generated_videos)} video(s)")

asyncio.run(wait_for_operation())
```

**Usage Example - Operation Metadata:**

```python
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Get operation
operation = client.operations.get('operations/abc123')

print(f"Operation: {operation.name}")
print(f"Done: {operation.done}")

# Check metadata for progress
if operation.metadata:
    print(f"Metadata: {operation.metadata}")
    # Metadata structure varies by operation type
    # May include progress percentage, timestamps, etc.

# Check if operation completed
if operation.done:
    if operation.error:
        print(f"Error code: {operation.error.code}")
        print(f"Error message: {operation.error.message}")
        if operation.error.details:
            print(f"Details: {operation.error.details}")
    else:
        print("Operation completed successfully")
        # Access operation.response for results
```

## Types

```python { .api }
from typing import Optional, Union, Any, Dict

# Operation base class
class Operation:
    """
    Long-running operation.

    This is an abstract base class. Specific operation types inherit from it
    (e.g., GenerateVideosOperation, ImportFileOperation).

    Attributes:
        name (str): Operation resource name for polling.
            Format varies by operation type (e.g., 'operations/{id}').
        done (bool): Whether operation has completed (successfully or with error).
        error (OperationError, optional): Error if operation failed. Only set if
            done=True and operation failed.
        response (Any, optional): Operation result if successful. Only set if
            done=True and operation succeeded. Type depends on operation:
            - GenerateVideosOperation.response: GenerateVideosResponse
            - ImportFileOperation.response: ImportFileResponse
            - etc.
        metadata (Dict[str, Any], optional): Operation metadata including:
            - Progress information
            - Timestamps
            - Operation-specific data
            Structure varies by operation type.
    """
    name: str
    done: bool
    error: Optional[OperationError] = None
    response: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

class OperationError:
    """
    Error information for failed operation.

    Attributes:
        code (int): Error code (HTTP status code or gRPC code).
        message (str): Human-readable error message.
        details (list, optional): Additional error details. Structure varies by
            error type and may include:
            - Error metadata
            - Retry information
            - Debugging information
    """
    code: int
    message: str
    details: Optional[list] = None

# Specific operation types (inherit from Operation)
class GenerateVideosOperation(Operation):
    """
    Video generation operation.

    Attributes:
        response (GenerateVideosResponse, optional): Video generation response when done.
    """
    response: Optional[GenerateVideosResponse] = None

class ImportFileOperation(Operation):
    """
    File import operation.

    Attributes:
        response (Dict, optional): Import response when done.
    """
    response: Optional[Dict] = None

class UploadToFileSearchStoreOperation(Operation):
    """
    File upload operation for file search stores.

    Attributes:
        response (Dict, optional): Upload response when done.
    """
    response: Optional[Dict] = None

# Response types (referenced by operations)
class GenerateVideosResponse:
    """
    Video generation response (from GenerateVideosOperation).

    Attributes:
        generated_videos (list[GeneratedVideo]): Generated videos.
        rai_media_filtered_count (int, optional): Safety-filtered count.
        rai_media_filtered_reasons (list[str], optional): Filter reasons.
    """
    generated_videos: list[GeneratedVideo]
    rai_media_filtered_count: Optional[int] = None
    rai_media_filtered_reasons: Optional[list[str]] = None

class GeneratedVideo:
    """
    Generated video with metadata.

    Attributes:
        video (Video): Video object with data.
        generation_seed (int, optional): Generation seed.
    """
    video: Video
    generation_seed: Optional[int] = None

class Video:
    """
    Video data.

    Attributes:
        data (bytes): Video binary data.
        mime_type (str): MIME type (e.g., 'video/mp4').
    """
    data: bytes
    mime_type: str
```
