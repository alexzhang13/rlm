# Embeddings

Create vector embeddings for text inputs to use in semantic search, clustering, recommendations, and other machine learning applications. Embeddings are numerical representations of text that capture semantic meaning.

## Capabilities

### Create Embeddings

Generate vector embeddings for one or more text inputs.

```python { .api }
def create(
    self,
    *,
    input: str | list[str] | list[int] | list[list[int]],
    model: str | EmbeddingModel,
    dimensions: int | Omit = omit,
    encoding_format: Literal["float", "base64"] | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> CreateEmbeddingResponse:
    """
    Create embedding vectors representing the input text.

    Args:
        input: Text to embed. Can be:
            - Single string: "Hello world"
            - List of strings: ["Hello", "world"]
            - Token array: [123, 456, 789]
            - List of token arrays: [[123, 456], [789, 012]]
            Max 8192 tokens per input, 2048 dimensions max for arrays.
            Total limit: 300,000 tokens across all inputs per request.

        model: Embedding model ID. Options:
            - "text-embedding-3-large": Most capable, 3072 dimensions
            - "text-embedding-3-small": Fast and efficient, 1536 dimensions
            - "text-embedding-ada-002": Legacy model, 1536 dimensions

        dimensions: Number of dimensions for output embeddings.
            Only supported in text-embedding-3 models. Allows reducing
            embedding size for storage/performance. Must be ≤ model's max.

        encoding_format: Output format for embeddings.
            - "float": List of floats (default)
            - "base64": Base64-encoded bytes for space efficiency

        user: Unique end-user identifier for abuse monitoring.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        CreateEmbeddingResponse: Contains embedding vectors and usage info.

    Raises:
        BadRequestError: Invalid input or exceeds token limits
        AuthenticationError: Invalid API key
        RateLimitError: Rate limit exceeded
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Single text embedding
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="The quick brown fox jumps over the lazy dog"
)

embedding = response.data[0].embedding
print(f"Embedding dimension: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")

# Multiple texts at once
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=[
        "Machine learning is fascinating",
        "I love natural language processing",
        "The weather is nice today"
    ]
)

for i, item in enumerate(response.data):
    print(f"Embedding {i}: {len(item.embedding)} dimensions")

# Using larger model with custom dimensions
response = client.embeddings.create(
    model="text-embedding-3-large",
    input="Semantic search with embeddings",
    dimensions=1024  # Reduce from default 3072
)

# Base64 encoding for space efficiency
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Compressed embedding format",
    encoding_format="base64"
)

# Decode base64 embedding
import base64
import array

encoded = response.data[0].embedding
decoded_bytes = base64.b64decode(encoded)
floats = array.array('f', decoded_bytes)
print(f"Decoded embedding: {list(floats)[:5]}")

# Token-based input (pre-tokenized)
import tiktoken

enc = tiktoken.encoding_for_model("text-embedding-3-small")
tokens = enc.encode("Hello world")

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=tokens
)

# Semantic search example
def cosine_similarity(a, b):
    import math
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    return dot / (mag_a * mag_b)

# Embed documents
documents = [
    "Python is a programming language",
    "Machine learning uses algorithms",
    "The cat sat on the mat"
]

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=documents
)

doc_embeddings = [item.embedding for item in response.data]

# Embed query
query = "Tell me about programming"
query_response = client.embeddings.create(
    model="text-embedding-3-small",
    input=query
)
query_embedding = query_response.data[0].embedding

# Find most similar document
similarities = [
    cosine_similarity(query_embedding, doc_emb)
    for doc_emb in doc_embeddings
]

best_match_idx = similarities.index(max(similarities))
print(f"Most similar document: {documents[best_match_idx]}")
print(f"Similarity score: {similarities[best_match_idx]:.4f}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class CreateEmbeddingResponse(BaseModel):
    """Response from embeddings endpoint."""
    data: list[Embedding]
    model: str
    object: Literal["list"]
    usage: Usage

class Embedding(BaseModel):
    """Single embedding vector."""
    embedding: list[float] | str  # list[float] for "float", str for "base64"
    index: int
    object: Literal["embedding"]

class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    total_tokens: int

# Model type
EmbeddingModel = Literal[
    "text-embedding-3-large",
    "text-embedding-3-small",
    "text-embedding-ada-002"
]
```

## Model Comparison

| Model | Dimensions | Performance | Use Case |
|-------|-----------|-------------|----------|
| text-embedding-3-large | 3072 (default) | Highest quality | Production semantic search, highest accuracy needed |
| text-embedding-3-small | 1536 (default) | Good quality, faster | General purpose, cost-sensitive applications |
| text-embedding-ada-002 | 1536 (fixed) | Legacy performance | Backwards compatibility |

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Batch similar requests for efficiency
texts = ["text1", "text2", "text3"]  # Up to 2048 inputs
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts
)

# 2. Use dimensions parameter to reduce storage
response = client.embeddings.create(
    model="text-embedding-3-large",
    input="Sample text",
    dimensions=256  # Much smaller than default 3072
)

# 3. Handle errors gracefully
try:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="x" * 10000  # Too long
    )
except Exception as e:
    print(f"Error: {e}")

# 4. Use base64 for space efficiency in storage
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Efficient storage",
    encoding_format="base64"
)
# Store base64 string directly, decode when needed
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def get_embeddings():
    client = AsyncOpenAI()

    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input="Async embedding creation"
    )

    return response.data[0].embedding

# Run async
embeddings = asyncio.run(get_embeddings())
```
