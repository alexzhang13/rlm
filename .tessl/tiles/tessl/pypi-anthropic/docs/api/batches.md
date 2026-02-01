# Batches API Reference

Process multiple messages asynchronously in batches for high-throughput use cases with 50% cost reduction.

## Create Batch

```python { .api }
def create(
    self,
    *,
    requests: list[MessageBatchIndividualRequest],
    **kwargs
) -> MessageBatch:
    """
    Create a batch of message requests.

    Parameters:
        requests: List of individual message requests with custom_id

    Returns:
        MessageBatch with id, processing_status, request counts
    """
    ...

async def create(...) -> MessageBatch: ...
```

## Retrieve Batch

```python { .api }
def retrieve(
    self,
    message_batch_id: str,
    **kwargs
) -> MessageBatch:
    """Retrieve batch status and metadata."""
    ...

async def retrieve(...) -> MessageBatch: ...
```

## List Batches

```python { .api }
def list(
    self,
    *,
    before_id: str = NOT_GIVEN,
    after_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    **kwargs
) -> SyncPage[MessageBatch]:
    """List batches with pagination."""
    ...

def list(...) -> AsyncPage[MessageBatch]: ...
```

## Cancel Batch

```python { .api }
def cancel(
    self,
    message_batch_id: str,
    **kwargs
) -> MessageBatch:
    """Cancel a batch in progress."""
    ...

async def cancel(...) -> MessageBatch: ...
```

## Delete Batch

```python { .api }
def delete(
    self,
    message_batch_id: str,
    **kwargs
) -> DeletedMessageBatch:
    """Delete a batch."""
    ...

async def delete(...) -> DeletedMessageBatch: ...
```

## Get Results

```python { .api }
def results(
    self,
    message_batch_id: str,
    **kwargs
) -> JSONLDecoder[MessageBatchIndividualResponse]:
    """Stream batch results as JSONL."""
    ...

def results(...) -> AsyncJSONLDecoder[MessageBatchIndividualResponse]: ...
```

## Response Types

```python { .api }
class MessageBatch(BaseModel):
    """Batch metadata and status."""
    id: str
    type: Literal["message_batch"]
    processing_status: Literal["in_progress", "canceling", "ended"]
    request_counts: MessageBatchRequestCounts
    ended_at: str | None
    created_at: str
    expires_at: str
    cancel_initiated_at: str | None
    results_url: str | None

class MessageBatchRequestCounts(BaseModel):
    """Request count statistics."""
    processing: int
    succeeded: int
    errored: int
    canceled: int
    expired: int
```

## Request Types

```python { .api }
class MessageBatchIndividualRequest(TypedDict):
    """Individual request in batch."""
    custom_id: str
    params: MessageCreateParams
```

## Quick Examples

### Create Basic Batch

```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "request-1",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "What is AI?"}]
            }
        },
        {
            "custom_id": "request-2",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "What is ML?"}]
            }
        }
    ]
)
print(f"Batch ID: {batch.id}")
```

### Check Status

```python
batch = client.messages.batches.retrieve("batch_abc123")
print(f"Status: {batch.processing_status}")
print(f"Succeeded: {batch.request_counts.succeeded}")
print(f"Errored: {batch.request_counts.errored}")
```

### Poll Until Complete

```python
import time

while True:
    batch = client.messages.batches.retrieve(batch_id)
    if batch.processing_status == "ended":
        break
    time.sleep(60)
```

### Get Results

```python
results = client.messages.batches.results("batch_abc123")

for response in results:
    if response.result.type == "succeeded":
        print(f"{response.custom_id}: {response.result.message.content[0].text}")
    elif response.result.type == "errored":
        print(f"{response.custom_id}: Error - {response.result.error.message}")
```

## See Also

- [Messages API](./messages.md) - Core message creation
- [Batch Processing Guide](../guides/batch-processing.md) - Advanced batch patterns
- [Type System](../reference/types.md) - Complete type definitions
