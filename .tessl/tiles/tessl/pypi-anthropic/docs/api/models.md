# Models API Reference

Retrieve information about available Claude models and their capabilities.

## Retrieve Model

```python { .api }
def retrieve(
    self,
    model_id: str,
    **kwargs
) -> ModelInfo:
    """
    Retrieve model information.

    Parameters:
        model_id: Model identifier (e.g., "claude-sonnet-4-5-20250929")

    Returns:
        ModelInfo with model metadata and capabilities
    """
    ...

async def retrieve(...) -> ModelInfo: ...
```

## List Models

```python { .api }
def list(
    self,
    *,
    before_id: str = NOT_GIVEN,
    after_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    **kwargs
) -> SyncPage[ModelInfo]:
    """
    List available models with pagination.

    Returns:
        SyncPage of ModelInfo objects with auto-pagination
    """
    ...

def list(...) -> AsyncPage[ModelInfo]: ...
```

## Response Type

```python { .api }
class ModelInfo(BaseModel):
    """Model information and capabilities."""
    id: str
    type: Literal["model"]
    display_name: str
    created_at: str
```

## Available Models

### Claude 4.5 (Latest)

```python { .api }
"claude-opus-4-5-20250929"    # Most capable model
"claude-sonnet-4-5-20250929"  # Balanced intelligence and speed
```

### Claude 3.5

```python { .api }
"claude-3-5-sonnet-20241022"  # Previous Sonnet version
"claude-3-5-sonnet-20240620"  # Earlier Sonnet version
"claude-3-5-haiku-20241022"   # Fast, cost-effective
```

### Claude 3

```python { .api }
"claude-3-opus-20240229"   # Powerful, intelligent
"claude-3-sonnet-20240229" # Balanced
"claude-3-haiku-20240307"  # Fast and efficient
```

### Legacy (Claude 2)

```python { .api }
"claude-2.1"          # Legacy Claude 2.1
"claude-2.0"          # Legacy Claude 2.0
"claude-instant-1.2"  # Legacy instant model
```

## Quick Examples

### Retrieve Specific Model

```python
model = client.models.retrieve("claude-sonnet-4-5-20250929")
print(f"Model: {model.display_name}")
print(f"Created: {model.created_at}")
```

### List All Models

```python
for model in client.models.list():
    print(f"{model.id}: {model.display_name}")
```

### Check Model Availability

```python
from anthropic import NotFoundError

def model_exists(model_id: str) -> bool:
    try:
        client.models.retrieve(model_id)
        return True
    except NotFoundError:
        return False

if model_exists("claude-sonnet-4-5-20250929"):
    print("Model is available")
```

### Filter Models by Family

```python
def get_models_by_family(family: str) -> list[ModelInfo]:
    """Get all models in a family (e.g., 'sonnet', 'opus', 'haiku')."""
    return [m for m in client.models.list() if family.lower() in m.id.lower()]

sonnet_models = get_models_by_family("sonnet")
for model in sonnet_models:
    print(model.display_name)
```

### Model Selection Helper

```python
def select_model(capability: str = "balanced") -> str:
    """
    Select appropriate model based on requirements.

    Args:
        capability: "maximum" (opus), "balanced" (sonnet), "fast" (haiku)
    """
    if capability == "maximum":
        return "claude-opus-4-5-20250929"
    elif capability == "fast":
        return "claude-3-5-haiku-20241022"
    else:  # balanced
        return "claude-sonnet-4-5-20250929"

model_id = select_model("balanced")
```

## See Also

- [Messages API](./messages.md) - Core message creation
- [Type System](../reference/types.md) - Complete type definitions
