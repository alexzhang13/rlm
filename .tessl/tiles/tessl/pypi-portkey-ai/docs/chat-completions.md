# Chat Completions

OpenAI-compatible chat completion API with support for all major providers, streaming, function calling, and advanced Portkey features like fallbacks and load balancing.

## Capabilities

### Chat Completion Creation

Primary method for generating chat completions with support for multi-turn conversations, function calling, and streaming responses.

```python { .api }
class ChatCompletion:
    """Synchronous chat completion API"""
    completions: Completions

class Completions:
    """Chat completions endpoint"""
    
    def create(
        self,
        *,
        messages: Iterable[dict],
        model: Optional[str] = "portkey-default",
        stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        audio: Optional[Any] = None,
        max_completion_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        modalities: Optional[List[Any]] = None,
        prediction: Optional[Any] = None,
        reasoning_effort: Optional[Any] = None,
        store: Optional[bool] = None,
        **kwargs
    ) -> Union[ChatCompletions, Iterator[ChatCompletionChunk]]:
        """
        Create a chat completion.
        
        Parameters:
        - messages: List of message objects with 'role' and 'content'
        - model: Model identifier (defaults to 'portkey-default')
        - max_tokens: Maximum tokens to generate
        - temperature: Sampling temperature
        - stream: Enable streaming responses
        - top_p: Nucleus sampling parameter
        - audio: Audio configuration for multimodal models
        - max_completion_tokens: Maximum completion tokens
        - metadata: Custom metadata for request
        - modalities: Supported modalities (text, audio, etc.)
        - prediction: Prediction configuration
        - reasoning_effort: Reasoning effort level
        - store: Whether to store the conversation
        
        Returns:
        ChatCompletions object or Iterator of ChatCompletionChunk for streaming
        """
    
    messages: ChatCompletionsMessages

class AsyncChatCompletion:
    """Asynchronous chat completion API"""
    completions: AsyncCompletions

class AsyncCompletions:
    """Async chat completions endpoint"""
    
    async def create(
        self,
        *,
        messages: Iterable[dict],
        model: Optional[str] = "portkey-default",
        **kwargs
    ) -> Union[ChatCompletions, AsyncIterator[ChatCompletionChunk]]:
        """Async version of chat completion creation"""
```

### Message Management

Handle multi-turn conversations with proper message formatting and conversation context management.

```python { .api }
class ChatCompletionsMessages:
    """Message handling utilities for chat completions"""
    
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...

class AsyncChatCompletionsMessages:
    """Async message handling utilities"""
    
    async def create(self, **kwargs): ...
    async def list(self, **kwargs): ...
    async def retrieve(self, **kwargs): ...
    async def update(self, **kwargs): ...
    async def delete(self, **kwargs): ...
```

## Usage Examples

### Basic Chat Completion

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Simple chat completion
response = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "What is machine learning?"}
    ],
    model="gpt-4"
)

print(response.choices[0].message.content)
```

### Multi-turn Conversation

```python
# Multi-turn conversation
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing"},
    {"role": "assistant", "content": "Quantum computing is..."},
    {"role": "user", "content": "What are its main applications?"}
]

response = portkey.chat.completions.create(
    messages=messages,
    model="gpt-4",
    max_tokens=500,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### Streaming Response

```python
# Streaming chat completion
stream = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "Write a story about AI"}
    ],
    model="gpt-4",
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Function Calling

```python
# Function calling with tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ],
    model="gpt-4",
    tools=tools,
    tool_choice="auto"
)

# Handle function call
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    function_args = tool_call.function.arguments
    print(f"Function called: {function_name} with args: {function_args}")
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def chat_example():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    response = await portkey.chat.completions.create(
        messages=[
            {"role": "user", "content": "Hello, how are you?"}
        ],
        model="gpt-4"
    )
    
    print(response.choices[0].message.content)
    
    # Async streaming
    async for chunk in await portkey.chat.completions.create(
        messages=[{"role": "user", "content": "Count to 10"}],
        model="gpt-4",
        stream=True
    ):
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")

asyncio.run(chat_example())
```

### Response Format Control

```python
# JSON response format
response = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "List 3 colors in JSON format"}
    ],
    model="gpt-4",
    response_format={"type": "json_object"}
)

# Structured output with seed for reproducibility
response = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "Generate a random number"}
    ],
    model="gpt-4",
    seed=12345,
    temperature=0
)
```

## Message Format

### Message Structure

```python
# Message object structure
message = {
    "role": "user" | "assistant" | "system" | "tool",
    "content": str | List[dict],  # Text or multimodal content
    "name": str,                  # Optional message name
    "tool_calls": List[dict],     # Tool calls (assistant messages)
    "tool_call_id": str          # Tool call ID (tool messages)
}
```

### Multimodal Content

```python
# Text and image message
message = {
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "What's in this image?"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://example.com/image.jpg",
                "detail": "high"
            }
        }
    ]
}
```

## Advanced Features

### Provider-Specific Parameters

Different providers support various additional parameters:

```python
# OpenAI-specific parameters
response = portkey.chat.completions.create(
    messages=messages,
    model="gpt-4",
    logprobs=True,
    top_logprobs=3,
    logit_bias={50256: -100}  # Reduce likelihood of specific tokens
)

# Anthropic-specific parameters  
response = portkey.chat.completions.create(
    messages=messages,
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    anthropic_version="2023-06-01"
)
```

### Portkey-Specific Features

```python
# Multiple providers with fallback
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    config={
        "strategy": {"mode": "fallback"},
        "targets": [
            {"provider": "openai", "api_key": "OPENAI_KEY"},
            {"provider": "anthropic", "api_key": "ANTHROPIC_KEY"}
        ]
    }
)

# Load balancing across providers
portkey = Portkey(
    api_key="PORTKEY_API_KEY", 
    config={
        "strategy": {"mode": "loadbalance"},
        "targets": [
            {"provider": "openai", "api_key": "OPENAI_KEY", "weight": 0.7},
            {"provider": "anthropic", "api_key": "ANTHROPIC_KEY", "weight": 0.3}
        ]
    }
)

# Request with custom metadata
response = portkey.chat.completions.create(
    messages=messages,
    model="gpt-4",
    metadata={
        "user_id": "user123",
        "session_id": "session456",
        "environment": "production"
    }
)
```