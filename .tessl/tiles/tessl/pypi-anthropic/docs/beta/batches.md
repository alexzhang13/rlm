# Beta Message Batches

Process multiple beta message requests in batch mode with support for all beta features including thinking, citations, web search, code execution, and more.

## Overview

Beta message batches extend standard message batches with support for beta features. They provide:
- 50% cost reduction compared to standard API
- Support for all beta features (thinking, citations, web search, etc.)
- Same interface as standard batches
- Asynchronous processing of thousands of requests

## API Reference

### Create Batch

```python { .api }
def create(
    self,
    *,
    requests: Iterable[Request],
    betas: list[AnthropicBetaParam] = NOT_GIVEN,
    **kwargs
) -> BetaMessageBatch:
    """
    Create a batch of beta message requests.

    Parameters:
        requests: List of beta message creation requests
                  Each request includes custom_id and params dict
        betas: Additional beta features to enable beyond default batch support

    Returns:
        BetaMessageBatch with batch ID and processing status
    """
    ...

async def create(
    self,
    **kwargs
) -> BetaMessageBatch:
    """Async version of create."""
    ...
```

### Retrieve Batch

```python { .api }
def retrieve(
    self,
    message_batch_id: str,
    *,
    betas: list[AnthropicBetaParam] = NOT_GIVEN,
    **kwargs
) -> BetaMessageBatch:
    """
    Retrieve beta message batch status and metadata.

    Parameters:
        message_batch_id: ID of the batch to retrieve
        betas: Optional beta features header

    Returns:
        BetaMessageBatch with current processing status
    """
    ...

async def retrieve(
    self,
    message_batch_id: str,
    **kwargs
) -> BetaMessageBatch:
    """Async version of retrieve."""
    ...
```

### List Batches

```python { .api }
def list(
    self,
    *,
    after_id: str = NOT_GIVEN,
    before_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    betas: list[AnthropicBetaParam] = NOT_GIVEN,
    **kwargs
) -> SyncPage[BetaMessageBatch]:
    """
    List beta message batches with pagination.

    Parameters:
        after_id: Return batches after this ID
        before_id: Return batches before this ID
        limit: Maximum number of batches to return (1-1000, default 20)
        betas: Optional beta features header

    Returns:
        Paginated list of BetaMessageBatch objects
    """
    ...

def list(
    self,
    **kwargs
) -> AsyncPaginator[BetaMessageBatch, AsyncPage[BetaMessageBatch]]:
    """Async version of list."""
    ...
```

### Cancel Batch

```python { .api }
def cancel(
    self,
    message_batch_id: str,
    *,
    betas: list[AnthropicBetaParam] = NOT_GIVEN,
    **kwargs
) -> BetaMessageBatch:
    """
    Cancel a beta message batch before processing completes.

    Parameters:
        message_batch_id: ID of the batch to cancel
        betas: Optional beta features header

    Returns:
        BetaMessageBatch with canceling status
    """
    ...

async def cancel(
    self,
    message_batch_id: str,
    **kwargs
) -> BetaMessageBatch:
    """Async version of cancel."""
    ...
```

### Delete Batch

```python { .api }
def delete(
    self,
    message_batch_id: str,
    *,
    betas: list[AnthropicBetaParam] = NOT_GIVEN,
    **kwargs
) -> BetaDeletedMessageBatch:
    """
    Delete a completed beta message batch.

    Batches must be finished processing before deletion.
    Cancel in-progress batches first if needed.

    Parameters:
        message_batch_id: ID of the batch to delete
        betas: Optional beta features header

    Returns:
        BetaDeletedMessageBatch confirming deletion
    """
    ...

async def delete(
    self,
    message_batch_id: str,
    **kwargs
) -> BetaDeletedMessageBatch:
    """Async version of delete."""
    ...
```

### Get Results

```python { .api }
def results(
    self,
    message_batch_id: str,
    *,
    betas: list[AnthropicBetaParam] = NOT_GIVEN,
    **kwargs
) -> JSONLDecoder[BetaMessageBatchIndividualResponse]:
    """
    Stream beta message batch results as JSONL.

    Each line contains one request's result with custom_id for matching.
    Results order is not guaranteed to match request order.

    Parameters:
        message_batch_id: ID of the batch
        betas: Optional beta features header

    Returns:
        JSONLDecoder streaming individual responses
    """
    ...

async def results(
    self,
    message_batch_id: str,
    **kwargs
) -> AsyncJSONLDecoder[BetaMessageBatchIndividualResponse]:
    """Async version of results."""
    ...
```

## Examples

### Basic Batch with Beta Features

```python
batch = client.beta.messages.batches.create(
    requests=[
        {
            "custom_id": "request-1",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 2048,
                "thinking": {"type": "enabled"},
                "messages": [
                    {"role": "user", "content": "Solve this problem..."}
                ],
            },
        },
        {
            "custom_id": "request-2",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 2048,
                "web_search": {"type": "enabled"},
                "messages": [
                    {"role": "user", "content": "What are the latest news?"}
                ],
            },
        }
    ]
)

print(f"Batch ID: {batch.id}")
```

### Wait for Completion and Get Results

```python
import time

# Wait for completion
while True:
    batch = client.beta.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    print(f"Processing: {batch.request_counts.processing} requests remaining")
    time.sleep(60)

# Process results
for response in client.beta.messages.batches.results(batch.id):
    if response.result.type == "succeeded":
        print(f"{response.custom_id}: Success")
        # Access beta feature content
        for block in response.result.message.content:
            if block.type == "thinking":
                print(f"  Reasoning: {block.thinking[:100]}...")
            elif block.type == "text":
                print(f"  Response: {block.text[:100]}...")
    elif response.result.type == "errored":
        print(f"{response.custom_id}: Error - {response.result.error.message}")
```

### Mixed Beta Features in Batch

```python
# Create batch with different features per request
requests = [
    {
        "custom_id": "thinking-1",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "thinking": {"type": "enabled", "budget_tokens": 2000},
            "messages": [{"role": "user", "content": "Complex reasoning task"}]
        }
    },
    {
        "custom_id": "citations-1",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 2048,
            "citations": {"type": "enabled"},
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
                    {"type": "text", "text": "Summarize with citations"}
                ]
            }]
        }
    },
    {
        "custom_id": "web-search-1",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 2048,
            "web_search": {"type": "enabled"},
            "messages": [{"role": "user", "content": "Latest AI news"}]
        }
    },
    {
        "custom_id": "combined-1",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "thinking": {"type": "enabled"},
            "web_search": {"type": "enabled"},
            "code_execution": {"type": "enabled"},
            "messages": [{"role": "user", "content": "Research and code solution"}]
        }
    }
]

batch = client.beta.messages.batches.create(requests=requests)
```

### Large-Scale Beta Batch

```python
# Process thousands of requests with beta features
requests = []
for i in range(5000):
    requests.append({
        "custom_id": f"request-{i}",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 2048,
            "thinking": {"type": "enabled"},
            "messages": [{"role": "user", "content": f"Task {i}: ..."}]
        }
    })

batch = client.beta.messages.batches.create(requests=requests)
print(f"Created batch {batch.id} with {len(requests)} requests")

# Monitor progress
while True:
    batch = client.beta.messages.batches.retrieve(batch.id)
    completed = batch.request_counts.succeeded + batch.request_counts.errored
    total = completed + batch.request_counts.processing
    progress = (completed / total * 100) if total > 0 else 0

    print(f"Progress: {progress:.1f}% ({completed}/{total})")

    if batch.processing_status == "ended":
        break
    time.sleep(60)

# Process all results
results_by_id = {}
for response in client.beta.messages.batches.results(batch.id):
    results_by_id[response.custom_id] = response.result

print(f"Processed {len(results_by_id)} results")
```

### Async Batch Operations

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    # Create batch
    batch = await client.beta.messages.batches.create(
        requests=[
            {
                "custom_id": "async-1",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 2048,
                    "thinking": {"type": "enabled"},
                    "messages": [{"role": "user", "content": "Task 1"}]
                }
            },
            {
                "custom_id": "async-2",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 2048,
                    "web_search": {"type": "enabled"},
                    "messages": [{"role": "user", "content": "Task 2"}]
                }
            }
        ]
    )

    # Poll until complete
    while True:
        batch = await client.beta.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        await asyncio.sleep(60)

    # Get results
    results = []
    async for response in client.beta.messages.batches.results(batch.id):
        results.append(response)

    return results

results = asyncio.run(main())
```

### Cancel Batch

```python
# Cancel batch in progress
batch = client.beta.messages.batches.cancel("batch_abc123")
print(f"Status: {batch.processing_status}")  # "canceling"

# Wait for cancellation to complete
while True:
    batch = client.beta.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(30)

print(f"Canceled: {batch.request_counts.canceled} requests")
```

### Delete Batch

```python
# Delete completed batch
deleted = client.beta.messages.batches.delete("batch_abc123")
print(f"Deleted batch: {deleted.id}")
```

### List All Batches

```python
# List recent batches
for batch in client.beta.messages.batches.list(limit=10):
    print(f"{batch.id}: {batch.processing_status}")
    print(f"  Succeeded: {batch.request_counts.succeeded}")
    print(f"  Errored: {batch.request_counts.errored}")
    print(f"  Processing: {batch.request_counts.processing}")
```

### Error Handling

```python
from anthropic import APIError

try:
    batch = client.beta.messages.batches.create(requests=[...])
except APIError as e:
    print(f"Failed to create batch: {e.message}")

# Process results with error handling
for response in client.beta.messages.batches.results(batch.id):
    if response.result.type == "succeeded":
        try:
            # Process successful result
            message = response.result.message
            ...
        except Exception as e:
            print(f"Error processing {response.custom_id}: {e}")
    elif response.result.type == "errored":
        print(f"Request {response.custom_id} failed: {response.result.error.message}")
    elif response.result.type == "canceled":
        print(f"Request {response.custom_id} was canceled")
    elif response.result.type == "expired":
        print(f"Request {response.custom_id} expired")
```

## Best Practices

### 1. Use Meaningful Custom IDs

```python
# Good - descriptive IDs
custom_id = f"user-{user_id}-task-{task_id}-{timestamp}"

# Bad - generic IDs
custom_id = f"request-{i}"
```

### 2. Batch Similar Requests

Group requests with similar beta features:

```python
# Batch 1: Thinking-heavy tasks
thinking_requests = [...]

# Batch 2: Web search tasks
search_requests = [...]

batch1 = client.beta.messages.batches.create(requests=thinking_requests)
batch2 = client.beta.messages.batches.create(requests=search_requests)
```

### 3. Monitor Progress

```python
def monitor_batch(batch_id):
    """Monitor batch with progress updates."""
    last_progress = 0

    while True:
        batch = client.beta.messages.batches.retrieve(batch_id)

        total = sum([
            batch.request_counts.processing,
            batch.request_counts.succeeded,
            batch.request_counts.errored,
            batch.request_counts.canceled
        ])
        completed = batch.request_counts.succeeded + batch.request_counts.errored
        progress = (completed / total * 100) if total > 0 else 0

        if progress > last_progress + 5:  # Log every 5%
            print(f"Progress: {progress:.1f}%")
            last_progress = progress

        if batch.processing_status == "ended":
            break

        time.sleep(60)

    return batch

batch = monitor_batch("batch_abc123")
```

### 4. Handle All Result Types

```python
success_count = 0
error_count = 0
canceled_count = 0
expired_count = 0

for response in client.beta.messages.batches.results(batch.id):
    if response.result.type == "succeeded":
        success_count += 1
        process_success(response)
    elif response.result.type == "errored":
        error_count += 1
        log_error(response)
    elif response.result.type == "canceled":
        canceled_count += 1
    elif response.result.type == "expired":
        expired_count += 1

print(f"Results: {success_count} success, {error_count} errors, {canceled_count} canceled, {expired_count} expired")
```

### 5. Batch Size Considerations

- Maximum 10,000 requests per batch
- Consider splitting very large workloads
- Balance batch size with monitoring needs

```python
def create_batches_chunked(requests, chunk_size=5000):
    """Split large request list into multiple batches."""
    batches = []

    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i+chunk_size]
        batch = client.beta.messages.batches.create(requests=chunk)
        batches.append(batch)

    return batches

all_requests = [...]  # 20,000 requests
batches = create_batches_chunked(all_requests)
```

## Limitations and Considerations

### Beta Feature Support
- All beta features supported in batches
- Same limitations apply as in standard requests
- Token budgets apply per request

### Processing Time
- Batches typically complete within 24 hours
- Large batches may take longer
- Complexity affects processing time

### Cost Optimization
- 50% cost reduction vs standard API
- Beta features may have additional costs
- Calculate total cost including beta feature usage

### Rate Limits
- Batch requests don't count against rate limits
- Batch creation has its own limits
- Monitor batch creation rate

## See Also

- [Beta Overview](./index.md) - Overview of all beta features
- [Message Features](./message-features.md) - Beta feature documentation
- [Standard Batches](../api/batches.md) - Standard batch processing
- [Messages API](../api/messages.md) - Core message creation
