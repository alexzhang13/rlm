# Models

Model management and information retrieval for accessing available AI models across different providers. Provides unified interface to list, retrieve details, and manage models from various AI providers.

## Capabilities

### Model Listing

Retrieves list of available models from the configured provider(s), including model capabilities, permissions, and availability status.

```python { .api }
class Models:
    def list(self, **kwargs) -> ModelList:
        """
        List available models from the configured provider.

        Args:
            **kwargs: Additional provider-specific parameters

        Returns:
            ModelList: List of available models with metadata
        """

    def retrieve(
        self,
        model: str,
        *,
        timeout: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> Model:
        """
        Retrieve detailed information about a specific model.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-opus")
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters

        Returns:
            Model: Detailed model information and capabilities
        """

    def delete(
        self,
        model: str, 
        *,
        timeout: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> ModelDeleted:
        """
        Delete a custom model (if supported by provider).

        Args:
            model: Model identifier to delete
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters

        Returns:
            ModelDeleted: Confirmation of model deletion
        """

class AsyncModels:
    async def list(self, **kwargs) -> ModelList:
        """Async version of list method."""

    async def retrieve(
        self,
        model: str,
        *,
        timeout: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> Model:
        """Async version of retrieve method."""

    async def delete(
        self,
        model: str,
        *,
        timeout: Union[float, NotGiven] = NOT_GIVEN, 
        **kwargs
    ) -> ModelDeleted:
        """Async version of delete method."""
```

### Usage Examples

```python
from portkey_ai import Portkey

# Initialize client
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# List all available models
models = portkey.models.list()
print(f"Available models: {len(models.data)}")

for model in models.data:
    print(f"- {model.id}: {model.owned_by}")

# Get details for a specific model
model_info = portkey.models.retrieve("gpt-4")
print(f"Model: {model_info.id}")
print(f"Created: {model_info.created}")
print(f"Owned by: {model_info.owned_by}")
print(f"Permissions: {model_info.permission}")

# Filter models by provider (provider-specific)
openai_models = portkey.models.list(provider="openai")
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def list_models():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    # List models asynchronously
    models = await portkey.models.list()
    
    # Get model details
    model_details = await portkey.models.retrieve("gpt-4")
    
    return models, model_details

models, details = asyncio.run(list_models())
print(f"Found {len(models.data)} models")
print(f"GPT-4 details: {details.id}")
```

### Multi-Provider Model Discovery

```python
# List models across multiple providers using Portkey configuration
config = {
    "mode": "fallback",
    "options": [
        {"provider": "openai", "api_key": "openai_key"},
        {"provider": "anthropic", "api_key": "anthropic_key"},
        {"provider": "cohere", "api_key": "cohere_key"}
    ]
}

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    config=config
)

# This will list models from the primary provider in the fallback chain
all_models = portkey.models.list()

# Access models by capability
chat_models = [m for m in all_models.data if "chat" in m.id.lower()]
completion_models = [m for m in all_models.data if "text" in m.id.lower()]
```

## Types

```python { .api }
class ModelList:
    """List of available models"""
    object: str  # "list"
    data: List[Model]
    _headers: Optional[dict]  # Response headers

class Model:
    """Individual model information"""
    id: str  # Model identifier
    object: str  # "model"
    created: int  # Unix timestamp of creation
    owned_by: str  # Organization that owns the model
    permission: List[ModelPermission]  # Model permissions
    root: Optional[str]  # Root model identifier
    parent: Optional[str]  # Parent model identifier
    _headers: Optional[dict]  # Response headers

class ModelPermission:
    """Model permission details"""
    id: str
    object: str  # "model_permission"
    created: int
    allow_create_engine: bool
    allow_sampling: bool
    allow_logprobs: bool
    allow_search_indices: bool
    allow_view: bool
    allow_fine_tuning: bool
    organization: str
    group: Optional[str]
    is_blocking: bool

class ModelDeleted:
    """Model deletion confirmation"""
    id: str  # Deleted model identifier
    object: str  # "model"
    deleted: bool  # True if successfully deleted
    _headers: Optional[dict]  # Response headers
```