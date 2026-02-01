# Batches API - Quick Reference

Compact API signatures for batch processing. For examples, see **[Batches API Reference](../api/batches.md)**.

## create()

```python { .api }
def create(
    self,
    *,
    requests: list[MessageBatchIndividualRequest],  # Required: Batch requests
    **kwargs
) -> MessageBatch
```

**Async:** `async def create(...) -> MessageBatch`

## retrieve()

```python { .api }
def retrieve(
    self,
    message_batch_id: str,  # Required: Batch ID
    **kwargs
) -> MessageBatch
```

**Async:** `async def retrieve(...) -> MessageBatch`

## list()

```python { .api }
def list(
    self,
    *,
    before_id: str = NOT_GIVEN,
    after_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    **kwargs
) -> SyncPage[MessageBatch]
```

**Async:** `async def list(...) -> AsyncPage[MessageBatch]`

## cancel()

```python { .api }
def cancel(
    self,
    message_batch_id: str,  # Required: Batch ID to cancel
    **kwargs
) -> MessageBatch
```

**Async:** `async def cancel(...) -> MessageBatch`

## delete()

```python { .api }
def delete(
    self,
    message_batch_id: str,  # Required: Batch ID to delete
    **kwargs
) -> DeletedMessageBatch
```

**Async:** `async def delete(...) -> DeletedMessageBatch`

## results()

```python { .api }
def results(
    self,
    message_batch_id: str,  # Required: Batch ID
    **kwargs
) -> JSONLDecoder[MessageBatchIndividualResponse]:
    """Stream batch results as JSONL"""
    ...
```

**Async:** `async def results(...) -> AsyncJSONLDecoder[MessageBatchIndividualResponse]`

## Key Types

```python { .api }
class MessageBatchIndividualRequest(TypedDict):
    custom_id: str                # Your request identifier
    params: MessageCreateParams   # Same as messages.create() params

class MessageBatch(BaseModel):
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
    processing: int
    succeeded: int
    errored: int
    canceled: int
    expired: int

class MessageBatchIndividualResponse(BaseModel):
    custom_id: str
    result: MessageBatchSucceededResult | MessageBatchErroredResult

class MessageBatchSucceededResult(BaseModel):
    type: Literal["succeeded"]
    message: Message

class MessageBatchErroredResult(BaseModel):
    type: Literal["errored"]
    error: ErrorObject
```

## Common Patterns

```python
# Create batch
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "req-1",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}]
            }
        }
    ]
)

# Poll until complete
import time
while True:
    batch = client.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(60)

# Process results
for response in client.messages.batches.results(batch.id):
    if response.result.type == "succeeded":
        print(response.result.message.content[0].text)
    elif response.result.type == "errored":
        print(f"Error: {response.result.error.message}")
```

## See Also

- **[Complete Batches Documentation](../api/batches.md)** - Full details and examples
- **[Batch Processing Guide](../guides/batch-processing.md)** - Advanced patterns and best practices
