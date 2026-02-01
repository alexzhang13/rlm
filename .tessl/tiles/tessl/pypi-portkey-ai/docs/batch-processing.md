# Batch Processing

Batch API for processing large volumes of requests efficiently with cost optimization and result management.

## Capabilities

```python { .api }
class Batches:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def cancel(self, **kwargs): ...
```

## Usage Examples

```python
# Create batch job
batch = portkey.batches.create(
    input_file_id="file-123",
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# Check batch status
batch_status = portkey.batches.retrieve(batch.id)
```