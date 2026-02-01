# Model Information and Management

Retrieve and manage model information and capabilities. Access model metadata, update model settings, delete tuned models, and list available models.

## Capabilities

### Get Model

Retrieve information about a specific model including capabilities and configuration.

```python { .api }
def get(
    self,
    *,
    model: str,
    config: Optional[GetModelConfig] = None
) -> Model:
    """
    Get model information.

    Parameters:
        model (str): Model identifier (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro').
            For tuned models, use full resource name.
        config (GetModelConfig, optional): Get configuration.

    Returns:
        Model: Model information including:
            - Supported generation methods
            - Input/output token limits
            - Supported features (function calling, multimodal, etc.)
            - Model version

    Raises:
        ClientError: For client errors including 404 if model not found
        ServerError: For server errors (5xx status codes)
    """
    ...

async def get(
    self,
    *,
    model: str,
    config: Optional[GetModelConfig] = None
) -> Model:
    """Async version of get."""
    ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Get model info
model = client.models.get(model='gemini-2.0-flash')

print(f"Model: {model.name}")
print(f"Display name: {model.display_name}")
print(f"Description: {model.description}")
print(f"Input token limit: {model.input_token_limit}")
print(f"Output token limit: {model.output_token_limit}")
print(f"Supported methods: {model.supported_generation_methods}")

# Check capabilities
if 'generateContent' in model.supported_generation_methods:
    print("Supports content generation")
if 'embedContent' in model.supported_generation_methods:
    print("Supports embeddings")
```

### Update Model

Update mutable model metadata such as display name and description (for tuned models).

```python { .api }
def update(
    self,
    *,
    model: str,
    config: UpdateModelConfig
) -> Model:
    """
    Update model metadata (tuned models only).

    Parameters:
        model (str): Model resource name.
        config (UpdateModelConfig): Update configuration including:
            - display_name: New display name
            - description: New description

    Returns:
        Model: Updated model information.

    Raises:
        ClientError: For client errors
        ServerError: For server errors
    """
    ...

async def update(
    self,
    *,
    model: str,
    config: UpdateModelConfig
) -> Model:
    """Async version of update."""
    ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import UpdateModelConfig

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

config = UpdateModelConfig(
    display_name='My Custom Model v2',
    description='Updated description'
)

updated_model = client.models.update(
    model='projects/.../locations/.../models/my-model',
    config=config
)

print(f"Updated: {updated_model.display_name}")
```

### Delete Model

Delete a tuned model.

```python { .api }
def delete(
    self,
    *,
    model: str,
    config: Optional[DeleteModelConfig] = None
) -> DeleteModelResponse:
    """
    Delete a tuned model.

    Parameters:
        model (str): Model resource name to delete.
        config (DeleteModelConfig, optional): Delete configuration.

    Returns:
        DeleteModelResponse: Deletion confirmation.

    Raises:
        ClientError: For client errors including 404 if model not found
        ServerError: For server errors
    """
    ...

async def delete(
    self,
    *,
    model: str,
    config: Optional[DeleteModelConfig] = None
) -> DeleteModelResponse:
    """Async version of delete."""
    ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

response = client.models.delete(
    model='projects/.../locations/.../models/my-old-model'
)

print("Model deleted")
```

### List Models

List all available models with optional pagination and filtering.

```python { .api }
def list(
    self,
    *,
    config: Optional[ListModelsConfig] = None
) -> Union[Pager[Model], Iterator[Model]]:
    """
    List available models.

    Parameters:
        config (ListModelsConfig, optional): List configuration including:
            - page_size: Number of models per page
            - page_token: Token for pagination
            - filter: Filter expression

    Returns:
        Union[Pager[Model], Iterator[Model]]: Paginated model list.

    Raises:
        ClientError: For client errors
        ServerError: For server errors
    """
    ...

async def list(
    self,
    *,
    config: Optional[ListModelsConfig] = None
) -> Union[AsyncPager[Model], AsyncIterator[Model]]:
    """Async version of list."""
    ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# List all available models
print("Available models:")
for model in client.models.list():
    print(f"- {model.name}: {model.display_name}")
    print(f"  Methods: {', '.join(model.supported_generation_methods)}")

# List with pagination
from google.genai.types import ListModelsConfig

config = ListModelsConfig(page_size=10)
pager = client.models.list(config=config)

print(f"\nFirst page ({len(pager.page)} models):")
for model in pager.page:
    print(f"- {model.name}")
```

## Types

```python { .api }
from typing import Optional, List, Iterator, AsyncIterator, Union

# Configuration types
class GetModelConfig:
    """Configuration for getting model."""
    pass

class UpdateModelConfig:
    """
    Configuration for updating model.

    Attributes:
        display_name (str, optional): New display name.
        description (str, optional): New description.
    """
    display_name: Optional[str] = None
    description: Optional[str] = None

class DeleteModelConfig:
    """Configuration for deleting model."""
    pass

class ListModelsConfig:
    """
    Configuration for listing models.

    Attributes:
        page_size (int, optional): Number of models per page.
        page_token (str, optional): Token for pagination.
        filter (str, optional): Filter expression.
    """
    page_size: Optional[int] = None
    page_token: Optional[str] = None
    filter: Optional[str] = None

# Response types
class Model:
    """
    Model information and capabilities.

    Attributes:
        name (str): Model resource name (e.g., 'models/gemini-2.0-flash').
        base_model_id (str, optional): Base model identifier.
        version (str, optional): Model version.
        display_name (str): Human-readable display name.
        description (str): Model description.
        input_token_limit (int): Maximum input tokens.
        output_token_limit (int): Maximum output tokens.
        supported_generation_methods (list[str]): Supported methods:
            - 'generateContent': Text/multimodal generation
            - 'embedContent': Embeddings
            - 'generateImages': Image generation
            - 'generateVideos': Video generation
        temperature (float, optional): Default temperature.
        top_p (float, optional): Default top_p.
        top_k (int, optional): Default top_k.
        max_temperature (float, optional): Maximum allowed temperature.
        tuned_model_info (TunedModelInfo, optional): Info for tuned models.
    """
    name: str
    base_model_id: Optional[str] = None
    version: Optional[str] = None
    display_name: str
    description: str
    input_token_limit: int
    output_token_limit: int
    supported_generation_methods: list[str]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_temperature: Optional[float] = None
    tuned_model_info: Optional[TunedModelInfo] = None

class TunedModelInfo:
    """
    Information for tuned models.

    Attributes:
        tuning_job (str): Tuning job that created this model.
        base_model (str): Base model used for tuning.
        tuning_dataset (str, optional): Training dataset.
    """
    tuning_job: str
    base_model: str
    tuning_dataset: Optional[str] = None

class DeleteModelResponse:
    """
    Response from deleting a model.

    Attributes:
        deleted (bool): Whether deletion succeeded.
    """
    deleted: bool

# Pager types
class Pager[T]:
    """Synchronous pager."""
    page: list[T]
    def next_page(self) -> None: ...
    def __iter__(self) -> Iterator[T]: ...

class AsyncPager[T]:
    """Asynchronous pager."""
    page: list[T]
    async def next_page(self) -> None: ...
    async def __aiter__(self) -> AsyncIterator[T]: ...
```
