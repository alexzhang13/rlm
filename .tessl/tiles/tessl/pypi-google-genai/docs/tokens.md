# Token Operations and Local Tokenizer

Count tokens and compute detailed token information for content, with support for local tokenization without API calls. Token counting helps estimate costs, manage context limits, and optimize prompts.

## Capabilities

### Count Tokens

Count the number of tokens in content using the API.

```python { .api }
def count_tokens(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[CountTokensConfig] = None
) -> CountTokensResponse:
    """
    Count tokens in content via API.

    Parameters:
        model (str): Model identifier (e.g., 'gemini-2.0-flash').
        contents (Union[str, list[Content], Content]): Content to count tokens for.
        config (CountTokensConfig, optional): Configuration including:
            - generation_config: Generation config to count with
            - system_instruction: System instruction to include
            - tools: Tools to include

    Returns:
        CountTokensResponse: Token count including prompt tokens.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def count_tokens(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[CountTokensConfig] = None
) -> CountTokensResponse:
    """Async version of count_tokens."""
    ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Count tokens in text
response = client.models.count_tokens(
    model='gemini-2.0-flash',
    contents='How many tokens is this sentence?'
)

print(f"Total tokens: {response.total_tokens}")

# Count tokens with context
from google.genai.types import CountTokensConfig, Content, Part

config = CountTokensConfig(
    system_instruction='You are a helpful assistant.'
)

response = client.models.count_tokens(
    model='gemini-2.0-flash',
    contents=[
        Content(role='user', parts=[Part(text='Hello')]),
        Content(role='model', parts=[Part(text='Hi there!')]),
        Content(role='user', parts=[Part(text='How are you?')])
    ],
    config=config
)

print(f"Total tokens including context: {response.total_tokens}")
```

### Compute Tokens

Compute detailed token information including token IDs via API.

```python { .api }
def compute_tokens(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[ComputeTokensConfig] = None
) -> ComputeTokensResponse:
    """
    Compute detailed token information via API.

    Parameters:
        model (str): Model identifier.
        contents (Union[str, list[Content], Content]): Content to tokenize.
        config (ComputeTokensConfig, optional): Configuration.

    Returns:
        ComputeTokensResponse: Detailed token information including token IDs.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def compute_tokens(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[ComputeTokensConfig] = None
) -> ComputeTokensResponse:
    """Async version of compute_tokens."""
    ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

response = client.models.compute_tokens(
    model='gemini-2.0-flash',
    contents='Hello world'
)

print(f"Total tokens: {response.total_tokens}")

for token_info in response.tokens_info:
    for token in token_info.tokens:
        print(f"Token: '{token.token}' (ID: {token.token_id})")
```

### Local Tokenizer

Perform token counting locally without API calls (Experimental). The local tokenizer downloads model tokenizer data once and performs tokenization locally, useful for offline scenarios or reducing API calls.

```python { .api }
class LocalTokenizer:
    """Local tokenizer for text-only token counting (Experimental)."""

    def __init__(self, model_name: str):
        """
        Initialize local tokenizer for a model.

        Parameters:
            model_name (str): Model name (e.g., 'gemini-2.0-flash').
                Downloads tokenizer data on first use.

        Raises:
            ValueError: If model doesn't support local tokenization
        """
        ...

    def count_tokens(
        self,
        contents: Union[str, list[Content], Content],
        *,
        config: Optional[CountTokensConfig] = None
    ) -> CountTokensResult:
        """
        Count tokens locally (text-only).

        Parameters:
            contents (Union[str, list[Content], Content]): Content to count.
                Only text parts are counted; images/audio are ignored.
            config (CountTokensConfig, optional): Configuration.

        Returns:
            CountTokensResult: Token count. Note: May differ slightly from API
                count due to local approximation.
        """
        ...

    def compute_tokens(
        self,
        contents: Union[str, list[Content], Content]
    ) -> ComputeTokensResult:
        """
        Compute detailed token information locally.

        Parameters:
            contents (Union[str, list[Content], Content]): Content to tokenize.

        Returns:
            ComputeTokensResult: Detailed token information with IDs.
        """
        ...
```

**Usage Example:**

```python
from google.genai.local_tokenizer import LocalTokenizer

# Initialize tokenizer (downloads data on first use)
tokenizer = LocalTokenizer('gemini-2.0-flash')

# Count tokens locally
result = tokenizer.count_tokens('How many tokens is this?')
print(f"Total tokens (local): {result.total_tokens}")

# Compute detailed tokens
result = tokenizer.compute_tokens('Hello world')
for token_info in result.tokens_info:
    for token in token_info.tokens:
        print(f"Token: '{token.token}' (ID: {token.token_id})")
```

## Types

```python { .api }
from typing import Optional, Union, List

# Configuration types
class CountTokensConfig:
    """
    Configuration for token counting.

    Attributes:
        generation_config (GenerationConfig, optional): Generation config to include.
        system_instruction (Union[str, Content], optional): System instruction to include.
        tools (list[Tool], optional): Tools to include in count.
    """
    generation_config: Optional[GenerationConfig] = None
    system_instruction: Optional[Union[str, Content]] = None
    tools: Optional[list[Tool]] = None

class ComputeTokensConfig:
    """Configuration for computing tokens."""
    pass

# Response types
class CountTokensResponse:
    """
    Response from count_tokens API.

    Attributes:
        total_tokens (int): Total number of tokens.
        total_billable_characters (int, optional): Billable characters count (for embeddings).
    """
    total_tokens: int
    total_billable_characters: Optional[int] = None

class ComputeTokensResponse:
    """
    Response from compute_tokens API.

    Attributes:
        tokens_info (list[TokensInfo]): Detailed token information per content part.
        total_tokens (int): Total number of tokens.
    """
    tokens_info: list[TokensInfo]
    total_tokens: int

class TokensInfo:
    """
    Token information for content.

    Attributes:
        tokens (list[Token]): Individual tokens.
        role (str, optional): Content role.
    """
    tokens: list[Token]
    role: Optional[str] = None

class Token:
    """
    Individual token.

    Attributes:
        token (str): Token string.
        token_id (int): Token ID in model vocabulary.
    """
    token: str
    token_id: int

# Local tokenizer result types
class CountTokensResult:
    """
    Result from local token counting.

    Attributes:
        total_tokens (int): Total number of tokens.
    """
    total_tokens: int

class ComputeTokensResult:
    """
    Result from local token computation.

    Attributes:
        tokens_info (list[TokensInfo]): Detailed token information.
        total_tokens (int): Total number of tokens.
    """
    tokens_info: list[TokensInfo]
    total_tokens: int

# Core types (shared)
class Content:
    """Content container."""
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """Content part."""
    text: Optional[str] = None
    inline_data: Optional[Blob] = None

class Blob:
    """Binary data."""
    mime_type: str
    data: bytes

class GenerationConfig:
    """Generation configuration."""
    pass

class Tool:
    """Tool definition."""
    pass
```
