# Batch Processing Guide

Process thousands of messages asynchronously with 50% cost reduction using the Message Batches API.

## Why Use Batches?

- **Cost Reduction**: 50% lower cost compared to standard API
- **High Throughput**: Process thousands of requests asynchronously
- **No Rate Limits**: Batch requests don't count against rate limits

## Basic Batch

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

## Check Status

```python
batch = client.messages.batches.retrieve("batch_abc123")

print(f"Status: {batch.processing_status}")
print(f"Succeeded: {batch.request_counts.succeeded}/{batch.request_counts.processing + batch.request_counts.succeeded}")
print(f"Errored: {batch.request_counts.errored}")
```

## Poll Until Complete

```python
import time

batch_id = "batch_abc123"

while True:
    batch = client.messages.batches.retrieve(batch_id)

    if batch.processing_status == "ended":
        break

    print(f"Processing: {batch.request_counts.processing} requests remaining")
    time.sleep(60)  # Check every minute

print("Batch complete!")
```

## Get Results

```python
results = client.messages.batches.results(batch_id)

for response in results:
    if response.result.type == "succeeded":
        print(f"{response.custom_id}: {response.result.message.content[0].text}")
    elif response.result.type == "errored":
        print(f"{response.custom_id}: Error - {response.result.error.message}")
```

## Process Results

```python
results_by_id = {}

for response in client.messages.batches.results(batch_id):
    if response.result.type == "succeeded":
        results_by_id[response.custom_id] = response.result.message.content[0].text
    elif response.result.type == "errored":
        results_by_id[response.custom_id] = f"Error: {response.result.error.message}"

# Access results by custom_id
print(results_by_id["request-1"])
```

## Large-Scale Batch

```python
# Generate batch requests
requests = []
for i, question in enumerate(questions):  # thousands of questions
    requests.append({
        "custom_id": f"question-{i}",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": question}]
        }
    })

# Create batch
batch = client.messages.batches.create(requests=requests)

# Poll for completion
while True:
    batch = client.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(60)

# Process results
for response in client.messages.batches.results(batch.id):
    save_result(response.custom_id, response.result)
```

## Cancel Batch

```python
batch = client.messages.batches.cancel("batch_abc123")
print(f"Status: {batch.processing_status}")  # "canceling"
```

## Delete Batch

```python
# Must be ended first
deleted = client.messages.batches.delete("batch_abc123")
print(f"Deleted: {deleted.id}")
```

## List Batches

```python
# List all batches
for batch in client.messages.batches.list(limit=10):
    print(f"{batch.id}: {batch.processing_status}")

# Paginate manually
page = client.messages.batches.list(limit=10)
for batch in page.data:
    print(batch.id)

if page.has_next_page():
    next_page = page.get_next_page()
```

## Batch with Tools

```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "weather-sf",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "tools": [{
                    "name": "get_weather",
                    "description": "Get weather",
                    "input_schema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"]
                    }
                }],
                "messages": [{"role": "user", "content": "What's the weather in SF?"}]
            }
        }
    ]
)
```

## Batch with Streaming Context

While batches don't stream, you can prepare stream-like prompts:

```python
requests = []
for doc in documents:
    requests.append({
        "custom_id": f"doc-{doc['id']}",
        "params": {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 2048,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": doc['data']}},
                    {"type": "text", "text": "Summarize this document"}
                ]
            }]
        }
    })
```

## Async Batch Operations

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    # Create batch
    batch = await client.messages.batches.create(requests=[...])

    # Poll until complete
    while True:
        batch = await client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        await asyncio.sleep(60)

    # Get results
    results = []
    async for response in client.messages.batches.results(batch.id):
        results.append(response)

    return results

results = asyncio.run(main())
```

## Best Practices

### 1. Use Meaningful Custom IDs

```python
requests = [{
    "custom_id": f"user-{user_id}-question-{question_id}",
    "params": {...}
}]
```

### 2. Handle Errors Gracefully

```python
for response in client.messages.batches.results(batch_id):
    if response.result.type == "succeeded":
        process_success(response)
    elif response.result.type == "errored":
        log_error(response.custom_id, response.result.error)
        retry_if_needed(response.custom_id)
```

### 3. Batch Size Considerations

- Batches can contain up to 10,000 requests
- Consider splitting very large workloads into multiple batches

### 4. Monitor Progress

```python
def monitor_batch(batch_id):
    while True:
        batch = client.messages.batches.retrieve(batch_id)

        total = sum([
            batch.request_counts.processing,
            batch.request_counts.succeeded,
            batch.request_counts.errored
        ])

        completed = batch.request_counts.succeeded + batch.request_counts.errored
        progress = (completed / total * 100) if total > 0 else 0

        print(f"Progress: {progress:.1f}% ({completed}/{total})")

        if batch.processing_status == "ended":
            break

        time.sleep(60)
```

## See Also

- [Batches API](../api/batches.md) - Complete API reference
- [Messages API](../api/messages.md) - Message creation
- [Beta Features](../beta/index.md) - Beta message batches
