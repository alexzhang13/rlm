# Models

Retrieve information about available models and manage fine-tuned models. List models, get model details, and delete custom models.

## Capabilities

### Retrieve Model

Get details about a specific model.

```python { .api }
def retrieve(
    self,
    model: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Model:
    """
    Retrieve model information.

    Args:
        model: Model ID (e.g., "gpt-4", "gpt-3.5-turbo", custom fine-tuned model).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Model: Model details including ID, owner, and capabilities.

    Raises:
        NotFoundError: Model not found
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Get model details
model = client.models.retrieve("gpt-4")

print(f"ID: {model.id}")
print(f"Owner: {model.owned_by}")
print(f"Created: {model.created}")
```

### List Models

List all available models.

```python { .api }
def list(
    self,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncPage[Model]:
    """
    List all available models.

    Args:
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncPage[Model]: Paginated list of models.
    """
```

Usage examples:

```python
# List all models
models = client.models.list()

for model in models.data:
    print(f"{model.id} - {model.owned_by}")

# Filter for specific models
gpt4_models = [m for m in client.models.list() if "gpt-4" in m.id]

# Find fine-tuned models
fine_tuned = [m for m in client.models.list() if "ft:" in m.id]

for model in fine_tuned:
    print(f"Fine-tuned model: {model.id}")
```

### Delete Model

Delete a fine-tuned model.

```python { .api }
def delete(
    self,
    model: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ModelDeleted:
    """
    Delete a fine-tuned model. Only works with custom fine-tuned models.

    Args:
        model: The model ID to delete (must be a fine-tuned model you own).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ModelDeleted: Deletion confirmation.

    Raises:
        NotFoundError: Model not found
        BadRequestError: Cannot delete base models
    """
```

Usage example:

```python
# Delete fine-tuned model
result = client.models.delete("ft:gpt-3.5-turbo:custom:abc123")

print(f"Deleted: {result.id}")
print(f"Success: {result.deleted}")

# Note: Cannot delete base models
try:
    client.models.delete("gpt-4")  # Will fail
except Exception as e:
    print(f"Error: {e}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Model(BaseModel):
    """Model information."""
    id: str
    created: int
    object: Literal["model"]
    owned_by: str

class ModelDeleted(BaseModel):
    """Model deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["model"]

# Pagination
class SyncPage[T](BaseModel):
    data: list[T]
    object: str
    def __iter__(self) -> Iterator[T]: ...
```

## Common Models

### Chat Models
- `gpt-4o`: Most capable GPT-4 Omni model
- `gpt-4-turbo`: Fast GPT-4 with 128K context
- `gpt-4`: Original GPT-4 model
- `gpt-3.5-turbo`: Fast and cost-effective

### Reasoning Models
- `o1`: Advanced reasoning model
- `o3`: Latest reasoning model

### Embedding Models
- `text-embedding-3-large`: Largest embedding model
- `text-embedding-3-small`: Efficient embedding model
- `text-embedding-ada-002`: Legacy embedding model

### Other Models
- `whisper-1`: Audio transcription/translation
- `tts-1`, `tts-1-hd`: Text-to-speech
- `dall-e-3`, `dall-e-2`: Image generation
- `text-moderation-latest`: Content moderation

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Cache model list to reduce API calls
def get_available_models():
    return [m.id for m in client.models.list()]

# 2. Verify model availability before use
def is_model_available(model_id: str) -> bool:
    try:
        client.models.retrieve(model_id)
        return True
    except:
        return False

# 3. List your fine-tuned models
def get_my_fine_tuned_models():
    return [
        m for m in client.models.list()
        if "ft:" in m.id
    ]

# 4. Clean up old fine-tuned models
old_models = get_my_fine_tuned_models()
for model in old_models:
    if should_delete(model):
        client.models.delete(model.id)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def list_models():
    client = AsyncOpenAI()
    models = await client.models.list()
    return [m.id for m in models.data]

model_ids = asyncio.run(list_models())
```
