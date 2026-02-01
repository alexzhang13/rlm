# Batch Processing

Submit batch requests for asynchronous processing of multiple API calls. Process large volumes of requests cost-effectively with 50% discount on costs and 24-hour completion window.

## Capabilities

### Create Batch

Create a batch request for async processing.

```python { .api }
def create(
    self,
    *,
    completion_window: str,
    endpoint: str,
    input_file_id: str,
    metadata: dict[str, str] | Omit = omit,
    output_expires_after: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Batch:
    """
    Create a batch request for asynchronous processing.

    Args:
        completion_window: Time frame for completion. Currently only "24h".

        endpoint: API endpoint for batch requests. Supported:
            - "/v1/responses": Response API (structured outputs)
            - "/v1/chat/completions": Chat completions
            - "/v1/embeddings": Embeddings (max 50,000 inputs per batch)
            - "/v1/completions": Text completions
            - "/v1/moderations": Moderations

        input_file_id: ID of uploaded JSONL file with requests.
            Each line: {"custom_id": "...", "method": "POST", "url": "...", "body": {...}}

        metadata: Optional key-value pairs (max 16). Keys max 64 chars, values max 512 chars.

        output_expires_after: Expiration policy for output and error files.
            Dict with keys:
            - anchor: "created_at" (file creation time)
            - seconds: int (3600-2592000, i.e., 1 hour to 30 days)

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Batch: Created batch with status "validating".

    Raises:
        BadRequestError: Invalid file format or endpoint
        NotFoundError: Input file not found
    """
```

Usage examples:

```python
from openai import OpenAI
import json

client = OpenAI()

# Create batch input file (JSONL format)
batch_requests = [
    {
        "custom_id": "request-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "What is 2+2?"}]
        }
    },
    {
        "custom_id": "request-2",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "What is the capital of France?"}]
        }
    }
]

# Write to JSONL file
with open("batch_requests.jsonl", "w") as f:
    for request in batch_requests:
        f.write(json.dumps(request) + "\n")

# Upload file
with open("batch_requests.jsonl", "rb") as f:
    batch_file = client.files.create(file=f, purpose="batch")

# Create batch
batch = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print(f"Batch ID: {batch.id}")
print(f"Status: {batch.status}")

# With metadata
batch = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "experiment": "test-run-1",
        "dataset": "evaluation-set"
    }
)

# With output file expiration (e.g., 7 days)
batch = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    output_expires_after={
        "anchor": "created_at",
        "seconds": 604800  # 7 days
    }
)

# Embeddings batch
embeddings_requests = [
    {
        "custom_id": "embed-1",
        "method": "POST",
        "url": "/v1/embeddings",
        "body": {
            "model": "text-embedding-3-small",
            "input": "Sample text 1"
        }
    },
    {
        "custom_id": "embed-2",
        "method": "POST",
        "url": "/v1/embeddings",
        "body": {
            "model": "text-embedding-3-small",
            "input": "Sample text 2"
        }
    }
]

with open("embed_requests.jsonl", "w") as f:
    for request in embeddings_requests:
        f.write(json.dumps(request) + "\n")

with open("embed_requests.jsonl", "rb") as f:
    embed_file = client.files.create(file=f, purpose="batch")

batch = client.batches.create(
    input_file_id=embed_file.id,
    endpoint="/v1/embeddings",
    completion_window="24h"
)
```

### Retrieve Batch

Get batch status and results.

```python { .api }
def retrieve(
    self,
    batch_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Batch:
    """
    Retrieve batch details and status.

    Args:
        batch_id: The ID of the batch.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Batch: Batch details with current status.

    Raises:
        NotFoundError: Batch not found
    """
```

Usage example:

```python
# Check batch status
batch = client.batches.retrieve("batch_abc123")

print(f"Status: {batch.status}")
print(f"Total: {batch.request_counts.total}")
print(f"Completed: {batch.request_counts.completed}")
print(f"Failed: {batch.request_counts.failed}")

if batch.status == "completed":
    # Download results
    if batch.output_file_id:
        result_content = client.files.content(batch.output_file_id)

        # Parse JSONL results
        import json
        results = []
        for line in result_content.text.split("\n"):
            if line.strip():
                results.append(json.loads(line))

        for result in results:
            custom_id = result["custom_id"]
            response = result["response"]
            print(f"{custom_id}: {response}")

    # Check error file if any failed
    if batch.error_file_id:
        error_content = client.files.content(batch.error_file_id)
        print("Errors:", error_content.text)
```

### List Batches

List batch requests with pagination.

```python { .api }
def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Batch]:
    """
    List batches with pagination.

    Args:
        after: Cursor for pagination. Return batches after this batch ID.
        limit: Number of batches to retrieve (max 100). Default 20.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[Batch]: Paginated list of batches.
    """
```

Usage example:

```python
# List all batches
batches = client.batches.list()

for batch in batches:
    print(f"{batch.id}: {batch.status}")

# Pagination
page1 = client.batches.list(limit=10)
page2 = client.batches.list(limit=10, after=page1.data[-1].id)

# Filter by status
completed_batches = [
    b for b in client.batches.list()
    if b.status == "completed"
]
```

### Cancel Batch

Cancel an in-progress batch.

```python { .api }
def cancel(
    self,
    batch_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Batch:
    """
    Cancel a batch that is in progress.

    Args:
        batch_id: The ID of the batch to cancel.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Batch: Batch with status "cancelling" or "cancelled".

    Raises:
        NotFoundError: Batch not found
        BadRequestError: Batch not in cancellable state
    """
```

Usage example:

```python
# Cancel batch
batch = client.batches.cancel("batch_abc123")

print(f"Status: {batch.status}")  # "cancelling" or "cancelled"
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Batch(BaseModel):
    """Batch request."""
    id: str
    completion_window: str
    created_at: int
    endpoint: str
    input_file_id: str
    object: Literal["batch"]
    status: Literal[
        "validating", "failed", "in_progress",
        "finalizing", "completed", "expired", "cancelling", "cancelled"
    ]
    cancelled_at: int | None
    cancelling_at: int | None
    completed_at: int | None
    error_file_id: str | None
    errors: dict | None
    expired_at: int | None
    expires_at: int | None
    failed_at: int | None
    finalizing_at: int | None
    in_progress_at: int | None
    metadata: dict[str, str] | None
    output_file_id: str | None
    request_counts: BatchRequestCounts

class BatchRequestCounts(BaseModel):
    """Request count statistics."""
    completed: int
    failed: int
    total: int

class OutputExpiresAfter(BaseModel):
    """Expiration policy for batch output files."""
    anchor: Literal["created_at"]  # File creation time anchor
    seconds: int  # Expiration time in seconds (3600-2592000)

# Pagination
class SyncCursorPage[T](BaseModel):
    data: list[T]
    object: str
    first_id: str | None
    last_id: str | None
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...
```

## Input File Format

Batch input JSONL format:

```jsonl
{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}}
{"custom_id": "request-2", "method": "POST", "url": "/v1/embeddings", "body": {"model": "text-embedding-3-small", "input": "Hello world"}}
```

## Output File Format

Batch output JSONL format:

```jsonl
{"id": "batch_req_abc", "custom_id": "request-1", "response": {"status_code": 200, "request_id": "req_xyz", "body": {"id": "chatcmpl-123", "object": "chat.completion", ...}}, "error": null}
{"id": "batch_req_def", "custom_id": "request-2", "response": {"status_code": 200, "request_id": "req_uvw", "body": {"object": "list", "data": [...]}}, "error": null}
```

## Best Practices

```python
from openai import OpenAI
import json
import time

client = OpenAI()

# 1. Monitor batch progress
def wait_for_batch(batch_id: str, poll_interval: int = 60):
    """Wait for batch to complete."""
    while True:
        batch = client.batches.retrieve(batch_id)

        if batch.status in ["completed", "failed", "cancelled", "expired"]:
            return batch

        print(f"Status: {batch.status}")
        print(f"Progress: {batch.request_counts.completed}/{batch.request_counts.total}")
        time.sleep(poll_interval)

# 2. Process results efficiently
def process_batch_results(batch_id: str):
    """Download and process batch results."""
    batch = client.batches.retrieve(batch_id)

    if batch.status != "completed":
        raise Exception(f"Batch not completed: {batch.status}")

    # Download results
    result_content = client.files.content(batch.output_file_id)

    results = {}
    for line in result_content.text.split("\n"):
        if line.strip():
            result = json.loads(line)
            custom_id = result["custom_id"]
            response = result["response"]["body"]
            results[custom_id] = response

    return results

# 3. Handle errors
def get_batch_errors(batch_id: str):
    """Get failed requests from batch."""
    batch = client.batches.retrieve(batch_id)

    if not batch.error_file_id:
        return []

    error_content = client.files.content(batch.error_file_id)

    errors = []
    for line in error_content.text.split("\n"):
        if line.strip():
            errors.append(json.loads(line))

    return errors

# 4. Retry failed requests
def retry_failed_requests(batch_id: str):
    """Create new batch with failed requests."""
    errors = get_batch_errors(batch_id)

    if not errors:
        return None

    # Create retry input file
    with open("retry_requests.jsonl", "w") as f:
        for error in errors:
            # Reconstruct request from error
            request = {
                "custom_id": error["custom_id"],
                "method": error["method"],
                "url": error["url"],
                "body": error["body"]
            }
            f.write(json.dumps(request) + "\n")

    # Upload and create new batch
    with open("retry_requests.jsonl", "rb") as f:
        retry_file = client.files.create(file=f, purpose="batch")

    return client.batches.create(
        input_file_id=retry_file.id,
        endpoint=errors[0]["url"],
        completion_window="24h",
        metadata={"retry_of": batch_id}
    )

# Complete workflow
# 1. Create batch
batch = create_batch()

# 2. Wait for completion
completed_batch = wait_for_batch(batch.id)

# 3. Process results
if completed_batch.status == "completed":
    results = process_batch_results(batch.id)
    print(f"Processed {len(results)} results")

    # Check for failures
    if completed_batch.request_counts.failed > 0:
        retry_batch = retry_failed_requests(batch.id)
        print(f"Created retry batch: {retry_batch.id}")
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_batch():
    client = AsyncOpenAI()

    batch = await client.batches.create(
        input_file_id="file-abc123",
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    return batch.id

batch_id = asyncio.run(create_batch())
```
