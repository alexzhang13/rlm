# Models API - Quick Reference

Compact API signatures for model information. For examples, see **[Models API Reference](../api/models.md)**.

## retrieve()

```python { .api }
def retrieve(
    self,
    model_id: str,  # Required: Model identifier
    **kwargs
) -> ModelInfo
```

**Async:** `async def retrieve(...) -> ModelInfo`

## list()

```python { .api }
def list(
    self,
    *,
    before_id: str = NOT_GIVEN,
    after_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    **kwargs
) -> SyncPage[ModelInfo]
```

**Async:** `async def list(...) -> AsyncPage[ModelInfo]`

## Response Type

```python { .api }
class ModelInfo(BaseModel):
    id: str              # Model identifier
    type: Literal["model"]
    display_name: str    # Human-readable name
    created_at: str      # ISO 8601 timestamp
```

## Available Model IDs

```python { .api }
# Claude 4.5 (Latest)
"claude-opus-4-5-20250929"      # Most capable model
"claude-sonnet-4-5-20250929"    # Balanced intelligence and speed

# Claude 3.5
"claude-3-5-sonnet-20241022"    # Previous Sonnet version
"claude-3-5-sonnet-20240620"    # Earlier Sonnet version
"claude-3-5-haiku-20241022"     # Fast, cost-effective

# Claude 3
"claude-3-opus-20240229"        # Powerful, intelligent
"claude-3-sonnet-20240229"      # Balanced
"claude-3-haiku-20240307"       # Fast and efficient

# Legacy (Claude 2)
"claude-2.1"
"claude-2.0"
"claude-instant-1.2"
```

## Common Patterns

```python
# Get specific model info
model = client.models.retrieve("claude-sonnet-4-5-20250929")
print(f"{model.display_name} created: {model.created_at}")

# List all models
for model in client.models.list():
    print(f"{model.id}: {model.display_name}")

# Check if model exists
from anthropic import NotFoundError

def model_exists(model_id: str) -> bool:
    try:
        client.models.retrieve(model_id)
        return True
    except NotFoundError:
        return False
```

## Model Selection Guide

**Choose based on requirements:**

- **claude-opus-4-5-20250929** - Complex tasks requiring maximum capability and reasoning
- **claude-sonnet-4-5-20250929** - Balanced performance for most use cases (recommended)
- **claude-3-5-haiku-20241022** - Fast responses and cost-effective for simple tasks
- **claude-3-5-sonnet-20241022** - Previous Sonnet version for compatibility

## See Also

- **[Complete Models Documentation](../api/models.md)** - Full details and selection examples
