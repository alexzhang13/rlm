# Embeddings

Generate text embeddings for semantic search, clustering, similarity comparisons, and other natural language understanding tasks. Embeddings convert text into high-dimensional numerical vectors that capture semantic meaning, enabling mathematical operations on text.

## Capabilities

### Embed Content

Generate embeddings for text content. Supports single or multiple content inputs and various embedding tasks including retrieval, classification, and semantic similarity.

```python { .api }
def embed_content(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[EmbedContentConfig] = None
) -> EmbedContentResponse:
    """
    Generate embeddings for content.

    Parameters:
        model (str): Model identifier for embeddings (e.g., 'text-embedding-004',
            'text-multilingual-embedding-002'). Use models optimized for embeddings.
        contents (Union[str, list[Content], Content]): Content to embed. Can be:
            - str: Simple text to embed
            - Content: Content object with text parts
            - list[Content]: Multiple content objects to embed in batch
        config (EmbedContentConfig, optional): Embedding configuration including:
            - task_type: Type of embedding task (retrieval, classification, etc.)
            - title: Document title for RETRIEVAL_DOCUMENT task
            - output_dimensionality: Desired embedding dimension (model-dependent)

    Returns:
        EmbedContentResponse: Response containing embeddings and metadata.
            Each embedding is a list of float values representing the vector.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def embed_content(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[EmbedContentConfig] = None
) -> EmbedContentResponse:
    """Async version of embed_content."""
    ...
```

**Usage Example - Simple Embedding:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Generate embedding for a single text
response = client.models.embed_content(
    model='text-embedding-004',
    contents='What is the capital of France?'
)

# Access the embedding vector
embedding = response.embeddings[0].values
print(f"Embedding dimension: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
```

**Usage Example - Batch Embeddings:**

```python
from google.genai import Client
from google.genai.types import Content, Part

client = Client(api_key='YOUR_API_KEY')

# Embed multiple texts at once
texts = [
    'Machine learning is a subset of AI',
    'Deep learning uses neural networks',
    'Natural language processing handles text'
]

contents = [Content(parts=[Part(text=text)]) for text in texts]

response = client.models.embed_content(
    model='text-embedding-004',
    contents=contents
)

print(f"Generated {len(response.embeddings)} embeddings")
for i, embedding in enumerate(response.embeddings):
    print(f"Text {i+1}: dimension={len(embedding.values)}")
```

**Usage Example - Semantic Similarity:**

```python
import numpy as np
from google.genai import Client

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

client = Client(api_key='YOUR_API_KEY')

# Embed query and documents
query = "machine learning algorithms"
documents = [
    "Neural networks are a type of machine learning model",
    "The weather today is sunny and warm",
    "Supervised learning requires labeled training data"
]

# Get embeddings
query_response = client.models.embed_content(
    model='text-embedding-004',
    contents=query
)
query_embedding = query_response.embeddings[0].values

doc_embeddings = []
for doc in documents:
    response = client.models.embed_content(
        model='text-embedding-004',
        contents=doc
    )
    doc_embeddings.append(response.embeddings[0].values)

# Calculate similarities
for i, doc in enumerate(documents):
    similarity = cosine_similarity(query_embedding, doc_embeddings[i])
    print(f"Doc {i+1} similarity: {similarity:.4f}")
    print(f"  {doc}\n")
```

**Usage Example - Task-Specific Embeddings:**

```python
from google.genai import Client
from google.genai.types import EmbedContentConfig, TaskType

client = Client(api_key='YOUR_API_KEY')

# Embed for retrieval query
query_config = EmbedContentConfig(
    task_type=TaskType.RETRIEVAL_QUERY
)

query_response = client.models.embed_content(
    model='text-embedding-004',
    contents='How does photosynthesis work?',
    config=query_config
)

# Embed documents for retrieval
doc_config = EmbedContentConfig(
    task_type=TaskType.RETRIEVAL_DOCUMENT,
    title='Biology Textbook Chapter 3'
)

doc_response = client.models.embed_content(
    model='text-embedding-004',
    contents='Photosynthesis is the process by which plants convert light energy into chemical energy...',
    config=doc_config
)

print("Query embedding generated")
print("Document embedding generated")
```

**Usage Example - Reduced Dimensionality:**

```python
from google.genai import Client
from google.genai.types import EmbedContentConfig

client = Client(api_key='YOUR_API_KEY')

# Generate embeddings with reduced dimensionality for efficiency
config = EmbedContentConfig(
    output_dimensionality=256  # Reduce from default dimension
)

response = client.models.embed_content(
    model='text-embedding-004',
    contents='Text to embed with reduced dimensions',
    config=config
)

embedding = response.embeddings[0].values
print(f"Embedding dimension: {len(embedding)}")
```

## Types

```python { .api }
from typing import Optional, Union, List, TypedDict
from enum import Enum

# Configuration types
class EmbedContentConfig:
    """
    Configuration for embedding generation.

    Attributes:
        task_type (TaskType, optional): Type of embedding task. Different tasks may
            produce optimized embeddings for specific use cases:
            - RETRIEVAL_QUERY: Optimize for search queries
            - RETRIEVAL_DOCUMENT: Optimize for searchable documents
            - SEMANTIC_SIMILARITY: Optimize for similarity comparisons
            - CLASSIFICATION: Optimize for text classification
            - CLUSTERING: Optimize for clustering tasks
            - QUESTION_ANSWERING: Optimize for QA tasks
            - FACT_VERIFICATION: Optimize for fact checking
        title (str, optional): Document title, used with RETRIEVAL_DOCUMENT task
            to provide context for the embedding.
        output_dimensionality (int, optional): Desired output dimension for the embedding.
            Some models support dimensionality reduction. Smaller dimensions can reduce
            storage and computation costs. Check model documentation for supported values.
    """
    task_type: Optional[TaskType] = None
    title: Optional[str] = None
    output_dimensionality: Optional[int] = None

class TaskType(Enum):
    """Embedding task types for optimization."""
    TASK_TYPE_UNSPECIFIED = 'TASK_TYPE_UNSPECIFIED'
    RETRIEVAL_QUERY = 'RETRIEVAL_QUERY'
    RETRIEVAL_DOCUMENT = 'RETRIEVAL_DOCUMENT'
    SEMANTIC_SIMILARITY = 'SEMANTIC_SIMILARITY'
    CLASSIFICATION = 'CLASSIFICATION'
    CLUSTERING = 'CLUSTERING'
    QUESTION_ANSWERING = 'QUESTION_ANSWERING'
    FACT_VERIFICATION = 'FACT_VERIFICATION'
    CODE_RETRIEVAL_QUERY = 'CODE_RETRIEVAL_QUERY'

# Response types
class EmbedContentResponse:
    """
    Response from embedding generation.

    Attributes:
        embeddings (list[ContentEmbedding]): List of embeddings, one for each input content.
            Each embedding contains the vector values and optional statistics.
        metadata (EmbedContentMetadata, optional): Metadata about the embedding operation.
    """
    embeddings: list[ContentEmbedding]
    metadata: Optional[EmbedContentMetadata] = None

class ContentEmbedding:
    """
    Individual content embedding.

    Attributes:
        values (list[float]): Embedding vector as a list of float values. The length
            depends on the model and optional output_dimensionality configuration.
            Typical dimensions: 768, 1024, 1536, or custom reduced dimensions.
        statistics (ContentEmbeddingStatistics, optional): Statistics about the embedding.
    """
    values: list[float]
    statistics: Optional[ContentEmbeddingStatistics] = None

class ContentEmbeddingStatistics:
    """
    Statistics about an embedding.

    Attributes:
        token_count (int, optional): Number of tokens in the input content.
        truncated (bool, optional): Whether the input was truncated to fit model limits.
    """
    token_count: Optional[int] = None
    truncated: Optional[bool] = None

class EmbedContentMetadata:
    """
    Metadata about the embedding operation.

    Attributes:
        model_version (str, optional): Version of the model used for embedding.
    """
    model_version: Optional[str] = None

# Content types (shared with other capabilities)
class Content:
    """
    Container for content with role and parts.

    Attributes:
        parts (list[Part]): List of content parts
        role (str, optional): Role ('user' or 'model')
    """
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """
    Individual content part.

    For embeddings, typically only text parts are used.

    Attributes:
        text (str, optional): Text content to embed
        inline_data (Blob, optional): Inline binary data (rarely used for embeddings)
        file_data (FileData, optional): Reference to file (rarely used for embeddings)
    """
    text: Optional[str] = None
    inline_data: Optional[Blob] = None
    file_data: Optional[FileData] = None

class Blob:
    """
    Binary data with MIME type.

    Attributes:
        mime_type (str): MIME type
        data (bytes): Binary data
    """
    mime_type: str
    data: bytes

class FileData:
    """
    Reference to uploaded file.

    Attributes:
        file_uri (str): URI of uploaded file
        mime_type (str): MIME type
    """
    file_uri: str
    mime_type: str

# TypedDict variants for flexible usage
class EmbedContentConfigDict(TypedDict, total=False):
    """TypedDict variant of EmbedContentConfig."""
    task_type: TaskType
    title: str
    output_dimensionality: int
```
