# Text Completions

Legacy text completion API for non-chat models, supporting streaming and all OpenAI-compatible parameters with Portkey enhancements.

## Capabilities

### Text Completion Creation

Generate text completions using prompt-based models with support for streaming, multiple completions, and advanced parameters.

```python { .api }
class Completion:
    """Synchronous text completion API"""
    
    def create(
        self,
        *,
        prompt: Union[str, List[str]],
        model: str,
        best_of: Optional[int] = None,
        echo: Optional[bool] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[dict] = None,
        logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        stream: Optional[bool] = None,
        suffix: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        user: Optional[str] = None,
        **kwargs
    ) -> Union[TextCompletion, Iterator[TextCompletionChunk]]:
        """
        Create a text completion.
        
        Parameters:
        - prompt: Text prompt or list of prompts
        - model: Model identifier (e.g., 'text-davinci-003', 'gpt-3.5-turbo-instruct')
        - max_tokens: Maximum tokens to generate
        - temperature: Sampling temperature (0-2)
        - top_p: Nucleus sampling parameter (0-1)
        - n: Number of completions to generate
        - stream: Enable streaming responses
        - stop: Stop sequences
        - presence_penalty: Presence penalty (-2 to 2)
        - frequency_penalty: Frequency penalty (-2 to 2)
        - best_of: Generate best_of completions server-side and return the best
        - echo: Echo back the prompt in addition to the completion
        - logprobs: Include log probabilities on the logprobs most likely tokens
        - logit_bias: Modify likelihood of specified tokens
        - suffix: Suffix that comes after completion of inserted text
        - seed: Seed for deterministic generation
        - user: User identifier for tracking
        
        Returns:
        TextCompletion object or Iterator of TextCompletionChunk for streaming
        """

class AsyncCompletion:
    """Asynchronous text completion API"""
    
    async def create(
        self,
        *,
        prompt: Union[str, List[str]],
        model: str,
        **kwargs
    ) -> Union[TextCompletion, AsyncIterator[TextCompletionChunk]]:
        """Async version of text completion creation"""
```

## Usage Examples

### Basic Text Completion

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Simple text completion
response = portkey.completions.create(
    prompt="The future of artificial intelligence is",
    model="gpt-3.5-turbo-instruct",
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].text)
```

### Multiple Prompts

```python
# Multiple prompts in one request
prompts = [
    "The capital of France is",
    "The largest planet in our solar system is",
    "Python is a programming language that"
]

response = portkey.completions.create(
    prompt=prompts,
    model="gpt-3.5-turbo-instruct",
    max_tokens=50,
    temperature=0.5
)

for i, choice in enumerate(response.choices):
    print(f"Prompt {i+1}: {choice.text.strip()}")
```

### Streaming Completion

```python
# Streaming text completion
stream = portkey.completions.create(
    prompt="Write a short story about a robot discovering emotions:",
    model="gpt-3.5-turbo-instruct",
    max_tokens=200,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].text:
        print(chunk.choices[0].text, end="")
```

### Code Completion with Suffix

```python
# Code completion with suffix (fill-in-the-middle)
response = portkey.completions.create(
    prompt="def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    else:\n        ",
    suffix="\n    return result",
    model="gpt-3.5-turbo-instruct",
    max_tokens=100,
    temperature=0.2
)

print(response.choices[0].text)
```

### Advanced Parameters

```python
# Using advanced parameters
response = portkey.completions.create(
    prompt="Explain quantum computing in simple terms:",
    model="gpt-3.5-turbo-instruct",
    max_tokens=150,
    temperature=0.8,
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    best_of=3,  # Generate 3 completions, return the best
    n=1,        # Return 1 completion
    echo=True,  # Include the prompt in the response
    logprobs=3, # Include log probabilities for top 3 tokens
    stop=["\n\n", "###"],  # Stop at double newline or ###
    user="user123"
)

print("Full response with prompt:", response.choices[0].text)
if response.choices[0].logprobs:
    print("Token log probabilities:", response.choices[0].logprobs)
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def completion_example():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    # Async completion
    response = await portkey.completions.create(
        prompt="The benefits of renewable energy include:",
        model="gpt-3.5-turbo-instruct",
        max_tokens=100
    )
    
    print(response.choices[0].text)
    
    # Async streaming
    async for chunk in await portkey.completions.create(
        prompt="List the planets in our solar system:",
        model="gpt-3.5-turbo-instruct",
        max_tokens=100,
        stream=True
    ):
        if chunk.choices[0].text:
            print(chunk.choices[0].text, end="")

asyncio.run(completion_example())
```

### Deterministic Generation

```python
# Reproducible completions with seed
response1 = portkey.completions.create(
    prompt="Generate a random story idea:",
    model="gpt-3.5-turbo-instruct", 
    max_tokens=50,
    temperature=0.9,
    seed=42
)

response2 = portkey.completions.create(
    prompt="Generate a random story idea:",
    model="gpt-3.5-turbo-instruct",
    max_tokens=50, 
    temperature=0.9,
    seed=42
)

# These should be identical
print("Response 1:", response1.choices[0].text)
print("Response 2:", response2.choices[0].text)
```

### Logit Bias Control

```python
# Modify token probabilities with logit bias
response = portkey.completions.create(
    prompt="The weather today is",
    model="gpt-3.5-turbo-instruct",
    max_tokens=20,
    logit_bias={
        # Increase likelihood of positive weather words
        1180: 2,   # "sunny"
        4771: 2,   # "beautiful"
        # Decrease likelihood of negative weather words  
        21281: -2, # "rainy"
        4172: -2   # "cloudy"
    }
)

print(response.choices[0].text)
```

## Model Compatibility

### Supported Models

Text completions work with various model types:

```python
# GPT-3.5 Instruct models
model = "gpt-3.5-turbo-instruct"

# Legacy GPT-3 models (deprecated)
model = "text-davinci-003"
model = "text-curie-001" 
model = "text-babbage-001"
model = "text-ada-001"

# Code-specific models
model = "code-davinci-002"
model = "code-cushman-001"

# Provider-specific models through Portkey
model = "anthropic/claude-instant-1"
model = "cohere/command"
model = "huggingface/gpt2"
```

### Migration from Legacy Models

```python
# Old GPT-3 usage
response = portkey.completions.create(
    prompt="Translate to French: Hello, how are you?",
    model="text-davinci-003",
    max_tokens=60
)

# Recommended migration to GPT-3.5 Instruct
response = portkey.completions.create(
    prompt="Translate to French: Hello, how are you?", 
    model="gpt-3.5-turbo-instruct",
    max_tokens=60
)

# Or better: migrate to chat completions
response = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "Translate to French: Hello, how are you?"}
    ],
    model="gpt-3.5-turbo",
    max_tokens=60
)
```

## Common Use Cases

### Text Generation

```python
# Creative writing
response = portkey.completions.create(
    prompt="Write a haiku about programming:",
    model="gpt-3.5-turbo-instruct",
    max_tokens=30,
    temperature=0.8
)

# Technical documentation
response = portkey.completions.create(
    prompt="Function documentation for bubble sort algorithm:",
    model="gpt-3.5-turbo-instruct", 
    max_tokens=100,
    temperature=0.3
)
```

### Code Completion

```python
# Python function completion
response = portkey.completions.create(
    prompt="def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    \n    mid = len(arr) // 2\n    left = arr[:mid]\n    right = arr[mid:]\n    \n    ",
    model="gpt-3.5-turbo-instruct",
    max_tokens=200,
    temperature=0.2,
    stop=["\n\n"]
)
```

### Data Processing

```python
# Text classification
response = portkey.completions.create(
    prompt="Classify the sentiment of this text as positive, negative, or neutral:\n\n\"I absolutely love this new restaurant! The food was amazing.\"\n\nSentiment:",
    model="gpt-3.5-turbo-instruct",
    max_tokens=10,
    temperature=0
)
```