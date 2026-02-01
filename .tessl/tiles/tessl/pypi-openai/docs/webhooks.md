# Webhooks

Verify and handle webhook events from OpenAI for asynchronous notifications about fine-tuning jobs, batch completions, and other events.

## Capabilities

### Verify Webhook Signature

Verify that a webhook request came from OpenAI.

```python { .api }
def verify_signature(
    payload: str | bytes,
    headers: dict[str, str] | list[tuple[str, str]],
    *,
    secret: str | None = None,
    tolerance: int = 300
) -> None:
    """
    Verify webhook signature to ensure authenticity.

    Args:
        payload: Raw request body (bytes or string).
        headers: Request headers containing webhook-signature, webhook-timestamp,
            and webhook-id. Can be dict or list of tuples.
        secret: Webhook secret from OpenAI dashboard. If None, uses client's
            webhook_secret or OPENAI_WEBHOOK_SECRET environment variable.
        tolerance: Maximum age of webhook in seconds (default: 300).
            Used to prevent replay attacks.

    Returns:
        None: If signature is valid.

    Raises:
        InvalidWebhookSignatureError: If signature is invalid or timestamp is too old/new.
        ValueError: If secret is not provided and not set on client.
    """
```

Usage example:

```python
from openai import OpenAI, InvalidWebhookSignatureError

client = OpenAI(webhook_secret="your-webhook-secret")

# In your webhook endpoint
def webhook_handler(request):
    payload = request.body  # Raw bytes
    headers = request.headers  # Headers dict or list

    try:
        # Verify signature
        client.webhooks.verify_signature(
            payload=payload,
            headers=headers,
            secret="your-webhook-secret"  # Optional if set on client
        )

        # Signature valid, process webhook
        event = json.loads(payload)
        handle_webhook_event(event)

    except InvalidWebhookSignatureError:
        # Invalid signature, reject request
        return {"error": "Invalid signature"}, 401
```

### Unwrap Webhook Event

Verify signature and parse webhook event in one call.

```python { .api }
def unwrap(
    payload: str | bytes,
    headers: dict[str, str] | list[tuple[str, str]],
    *,
    secret: str | None = None
) -> UnwrapWebhookEvent:
    """
    Verify signature and parse webhook event.

    Args:
        payload: Raw request body (bytes or string).
        headers: Request headers containing webhook-signature, webhook-timestamp,
            and webhook-id. Can be dict or list of tuples.
        secret: Webhook secret from OpenAI dashboard. If None, uses client's
            webhook_secret or OPENAI_WEBHOOK_SECRET environment variable.

    Returns:
        UnwrapWebhookEvent: Parsed and verified webhook event.

    Raises:
        InvalidWebhookSignatureError: If signature is invalid.
        ValueError: If secret is not provided and not set on client.
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI(webhook_secret="your-webhook-secret")

# In webhook endpoint
def webhook_handler(request):
    try:
        # Verify and parse in one call
        event = client.webhooks.unwrap(
            payload=request.body,
            headers=request.headers,
            secret="your-webhook-secret"  # Optional if set on client
        )

        # Handle different event types
        if event.type == "fine_tuning.job.succeeded":
            handle_fine_tuning_success(event.data)

        elif event.type == "batch.completed":
            handle_batch_completion(event.data)

        return {"status": "ok"}, 200

    except Exception as e:
        return {"error": str(e)}, 400
```

## Webhook Event Types

### Fine-tuning Events

```python
# Job succeeded
{
    "type": "fine_tuning.job.succeeded",
    "data": {
        "id": "ftjob-abc123",
        "fine_tuned_model": "ft:gpt-3.5-turbo:org:model:abc",
        "status": "succeeded"
    }
}

# Job failed
{
    "type": "fine_tuning.job.failed",
    "data": {
        "id": "ftjob-abc123",
        "status": "failed",
        "error": {...}
    }
}

# Job cancelled
{
    "type": "fine_tuning.job.cancelled",
    "data": {
        "id": "ftjob-abc123",
        "status": "cancelled"
    }
}
```

### Batch Events

```python
# Batch completed
{
    "type": "batch.completed",
    "data": {
        "id": "batch_abc123",
        "status": "completed",
        "output_file_id": "file-xyz789"
    }
}

# Batch failed
{
    "type": "batch.failed",
    "data": {
        "id": "batch_abc123",
        "status": "failed",
        "errors": {...}
    }
}

# Batch cancelled
{
    "type": "batch.cancelled",
    "data": {
        "id": "batch_abc123",
        "status": "cancelled"
    }
}

# Batch expired
{
    "type": "batch.expired",
    "data": {
        "id": "batch_abc123",
        "status": "expired"
    }
}
```

### Eval Events

```python
# Eval run succeeded
{
    "type": "eval.run.succeeded",
    "data": {
        "id": "eval_run_abc123",
        "status": "succeeded",
        "results": {...}
    }
}

# Eval run failed
{
    "type": "eval.run.failed",
    "data": {
        "id": "eval_run_abc123",
        "status": "failed",
        "error": {...}
    }
}
```

## Types

```python { .api }
from typing import Union, Literal
from typing_extensions import TypeAlias

# UnwrapWebhookEvent is a union of all possible webhook event types
UnwrapWebhookEvent: TypeAlias = Union[
    BatchCancelledWebhookEvent,
    BatchCompletedWebhookEvent,
    BatchExpiredWebhookEvent,
    BatchFailedWebhookEvent,
    EvalRunCanceledWebhookEvent,
    EvalRunFailedWebhookEvent,
    EvalRunSucceededWebhookEvent,
    FineTuningJobCancelledWebhookEvent,
    FineTuningJobFailedWebhookEvent,
    FineTuningJobSucceededWebhookEvent,
    RealtimeCallIncomingWebhookEvent,
    ResponseCancelledWebhookEvent,
    ResponseCompletedWebhookEvent,
    ResponseFailedWebhookEvent,
    ResponseIncompleteWebhookEvent,
]

# Fine-tuning event types
class FineTuningJobSucceededWebhookEvent:
    type: Literal["fine_tuning.job.succeeded"]
    data: dict

class FineTuningJobFailedWebhookEvent:
    type: Literal["fine_tuning.job.failed"]
    data: dict

class FineTuningJobCancelledWebhookEvent:
    type: Literal["fine_tuning.job.cancelled"]
    data: dict

# Batch event types
class BatchCompletedWebhookEvent:
    type: Literal["batch.completed"]
    data: dict

class BatchFailedWebhookEvent:
    type: Literal["batch.failed"]
    data: dict

class BatchCancelledWebhookEvent:
    type: Literal["batch.cancelled"]
    data: dict

class BatchExpiredWebhookEvent:
    type: Literal["batch.expired"]
    data: dict

# Eval event types
class EvalRunSucceededWebhookEvent:
    type: Literal["eval.run.succeeded"]
    data: dict

class EvalRunFailedWebhookEvent:
    type: Literal["eval.run.failed"]
    data: dict

class EvalRunCanceledWebhookEvent:
    type: Literal["eval.run.canceled"]
    data: dict

# Response event types
class ResponseCompletedWebhookEvent:
    type: Literal["response.completed"]
    data: dict

class ResponseFailedWebhookEvent:
    type: Literal["response.failed"]
    data: dict

class ResponseCancelledWebhookEvent:
    type: Literal["response.cancelled"]
    data: dict

class ResponseIncompleteWebhookEvent:
    type: Literal["response.incomplete"]
    data: dict

# Realtime event types
class RealtimeCallIncomingWebhookEvent:
    type: Literal["realtime.call.incoming"]
    data: dict
```

## Complete Webhook Handler

```python
from openai import OpenAI, InvalidWebhookSignatureError
from flask import Flask, request, jsonify

app = Flask(__name__)
client = OpenAI()

WEBHOOK_SECRET = "your-webhook-secret"

@app.route("/webhooks/openai", methods=["POST"])
def handle_webhook():
    # Get headers and payload
    payload = request.data
    headers = request.headers

    # Verify and parse
    try:
        event = client.webhooks.unwrap(
            payload=payload,
            headers=headers,
            secret=WEBHOOK_SECRET
        )
    except InvalidWebhookSignatureError:
        return jsonify({"error": "Invalid signature"}), 401

    # Handle event
    if event.type == "fine_tuning.job.succeeded":
        job_id = event.data["id"]
        model = event.data["fine_tuned_model"]
        print(f"Fine-tuning succeeded: {job_id} -> {model}")

        # Deploy model or notify user
        deploy_model(model)

    elif event.type == "batch.completed":
        batch_id = event.data["id"]
        output_file = event.data["output_file_id"]
        print(f"Batch completed: {batch_id}")

        # Process results
        process_batch_results(batch_id, output_file)

    elif event.type == "fine_tuning.job.failed":
        job_id = event.data["id"]
        error = event.data.get("error")
        print(f"Fine-tuning failed: {job_id}, Error: {error}")

        # Notify user of failure
        notify_failure(job_id, error)

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    app.run(port=8080)
```

## Best Practices

```python
from openai import OpenAI, InvalidWebhookSignatureError
import hmac
import hashlib

client = OpenAI()

# 1. Always verify signatures
def is_valid_webhook(payload: bytes, headers: dict, secret: str) -> bool:
    try:
        client.webhooks.verify_signature(payload, headers, secret=secret)
        return True
    except InvalidWebhookSignatureError:
        return False

# 2. Handle replay attacks with timestamp
def is_recent_webhook(timestamp: str, max_age_seconds: int = 300) -> bool:
    import time

    event_time = int(timestamp)
    current_time = int(time.time())

    return (current_time - event_time) < max_age_seconds

# 3. Process events idempotently
processed_events = set()

def process_webhook_event(event_id: str, event_data: dict):
    if event_id in processed_events:
        print(f"Duplicate event: {event_id}")
        return

    # Process event
    handle_event(event_data)

    # Mark as processed
    processed_events.add(event_id)

# 4. Return 200 quickly, process async
from threading import Thread

def handle_webhook_async(event):
    # Process in background
    thread = Thread(target=process_event, args=(event,))
    thread.start()

    # Return immediately
    return {"status": "accepted"}, 200

# 5. Retry on failure
import time

def process_with_retry(event, max_retries=3):
    for attempt in range(max_retries):
        try:
            process_event(event)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                log_failure(event, e)
                raise
            time.sleep(2 ** attempt)
```

## Testing Webhooks

```python
# Generate test signature for development
import hmac
import hashlib
import json
import time

def generate_test_signature(payload: dict, secret: str) -> tuple[str, str]:
    """Generate signature for testing."""
    timestamp = str(int(time.time()))
    payload_str = json.dumps(payload)

    # Create signature
    message = f"{timestamp}.{payload_str}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature, timestamp

# Test webhook handler
test_payload = {
    "type": "fine_tuning.job.succeeded",
    "data": {
        "id": "ftjob-test123",
        "fine_tuned_model": "ft:gpt-3.5-turbo:test"
    }
}

# Create test headers (actual implementation would vary)
test_headers = {
    "webhook-signature": "v1,test_signature",
    "webhook-timestamp": str(int(time.time())),
    "webhook-id": "test_webhook_id"
}

# Note: In production, signatures are generated by OpenAI
# This is a simplified example for testing
event = client.webhooks.unwrap(
    payload=json.dumps(test_payload),
    headers=test_headers,
    secret=WEBHOOK_SECRET
)

print(f"Test event: {event.type}")
```

## Security Considerations

1. **Always verify signatures** - Never trust webhook data without verification
2. **Use HTTPS** - Only accept webhooks over HTTPS
3. **Check timestamps** - Reject old events to prevent replay attacks
4. **Rate limit** - Limit webhook endpoint to prevent abuse
5. **Store secrets securely** - Use environment variables or secret management
6. **Log failures** - Track verification failures for security monitoring
