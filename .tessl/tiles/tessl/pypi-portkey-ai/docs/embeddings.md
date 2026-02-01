# Embeddings

Text embedding generation for converting text into numerical vectors for semantic similarity, search, and machine learning applications. Supports multiple providers through Portkey's unified interface.

## Capabilities

### Embedding Creation

Creates vector embeddings from input text using the specified model. Supports various embedding models from different providers with consistent interface.

```python { .api }
class Embeddings:
    def create(
        self,
        *,
        input: str,
        model: Optional[str] = "portkey-default",
        dimensions: Union[int, NotGiven] = NOT_GIVEN,
        encoding_format: Union[str, NotGiven] = NOT_GIVEN,
        user: Union[str, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> CreateEmbeddingResponse:
        """
        Create embeddings for the given input text.

        Args:
            input: Input text to create embeddings for
            model: Embedding model to use (defaults to "portkey-default")
            dimensions: Number of dimensions for the embedding vectors (model-dependent)
            encoding_format: Format for encoding the embeddings (e.g., "float", "base64")
            user: User identifier for tracking and analytics
            **kwargs: Additional provider-specific parameters

        Returns:
            CreateEmbeddingResponse: Response containing embedding vectors and metadata
        """

class AsyncEmbeddings:
    async def create(
        self,
        *,
        input: str,
        model: Optional[str] = "portkey-default",  
        dimensions: Union[int, NotGiven] = NOT_GIVEN,
        encoding_format: Union[str, NotGiven] = NOT_GIVEN,
        user: Union[str, NotGiven] = NOT_GIVEN,
        **kwargs
    ) -> CreateEmbeddingResponse:
        """Async version of create method."""
```

### Usage Examples

```python
from portkey_ai import Portkey

# Initialize client
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"  
)

# Create embeddings for single text
response = portkey.embeddings.create(
    input="Hello, world!",
    model="text-embedding-ada-002"
)

# Access the embedding vector
embedding = response.data[0].embedding
print(f"Embedding dimensions: {len(embedding)}")

# Create embeddings with specific dimensions
response = portkey.embeddings.create(
    input="Text to embed",
    model="text-embedding-3-small",
    dimensions=512
)

# Batch embedding creation (provider-dependent)
texts = [
    "First text to embed",
    "Second text to embed", 
    "Third text to embed"
]

for text in texts:
    response = portkey.embeddings.create(
        input=text,
        model="text-embedding-ada-002",
        user="user-123"
    )
    print(f"Embedding for '{text}': {len(response.data[0].embedding)} dimensions")
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def create_embeddings():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    response = await portkey.embeddings.create(
        input="Async embedding creation",
        model="text-embedding-ada-002"
    )
    
    return response.data[0].embedding

# Run async function
embedding = asyncio.run(create_embeddings())
```

## Types

```python { .api }
class CreateEmbeddingResponse:
    """Response from embedding creation request"""
    object: str  # "list"
    data: List[EmbeddingObject]
    model: str
    usage: EmbeddingUsage
    _headers: Optional[dict]  # Response headers for debugging

class EmbeddingObject:
    """Individual embedding object"""
    object: str  # "embedding"
    embedding: List[float]  # The embedding vector
    index: int  # Index in the input list

class EmbeddingUsage:
    """Token usage information"""
    prompt_tokens: int
    total_tokens: int
```