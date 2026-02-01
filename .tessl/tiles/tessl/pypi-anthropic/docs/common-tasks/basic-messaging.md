# Basic Messaging Tasks

Practical patterns for common messaging scenarios. For complete API reference, see **[Messages API](../api/messages.md)**.

## Send Simple Text Message

```python
from anthropic import Anthropic

client = Anthropic()  # Uses ANTHROPIC_API_KEY env var

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain quantum computing in simple terms"}
    ]
)

print(message.content[0].text)
```

## Use System Prompt

System prompts guide Claude's behavior and style:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful Python programming assistant. Be concise and provide code examples.",
    messages=[
        {"role": "user", "content": "How do I read a CSV file?"}
    ]
)
```

### System Prompt with Caching

Cache long system prompts to reduce costs:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert on Shakespeare's works. Here is context:\n\n" + long_context,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[
        {"role": "user", "content": "Analyze Hamlet's soliloquy"}
    ]
)

# Check cache usage
print(f"Cache hits: {message.usage.cache_read_input_tokens}")
print(f"Cache misses: {message.usage.cache_creation_input_tokens}")
```

## Multi-Turn Conversation

Maintain conversation history:

```python
conversation = []

# Turn 1
conversation.append({"role": "user", "content": "My name is Alice"})

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=conversation
)

conversation.append({
    "role": "assistant",
    "content": message.content
})

# Turn 2
conversation.append({"role": "user", "content": "What's my name?"})

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=conversation
)

print(message.content[0].text)  # "Your name is Alice"
```

### Conversation Manager Helper

```python
class ConversationManager:
    def __init__(self, client: Anthropic, model: str, system: str = None):
        self.client = client
        self.model = model
        self.system = system
        self.history = []

    def send(self, user_message: str) -> str:
        """Send message and update history"""
        self.history.append({"role": "user", "content": user_message})

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system,
            messages=self.history
        )

        assistant_message = message.content[0].text
        self.history.append({
            "role": "assistant",
            "content": message.content
        })

        return assistant_message

# Usage
conv = ConversationManager(
    client,
    model="claude-sonnet-4-5-20250929",
    system="You are a helpful assistant"
)

response1 = conv.send("Hello, I'm Bob")
response2 = conv.send("What's my name?")  # Remembers "Bob"
```

## Control Response Temperature

Temperature affects randomness (0.0 = deterministic, 1.0 = creative):

```python
# Deterministic/factual responses
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=0.0,
    messages=[{"role": "user", "content": "What is 2+2?"}]
)

# Creative/varied responses
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=1.0,
    messages=[{"role": "user", "content": "Write a creative story"}]
)
```

## Use Stop Sequences

Stop generation at specific strings:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    stop_sequences=["</response>", "\n\n---"],
    messages=[
        {
            "role": "user",
            "content": "List 5 colors, each on a new line. End with </response>"
        }
    ]
)

# Check if stop sequence was hit
if message.stop_reason == "stop_sequence":
    print(f"Stopped at: {message.stop_sequence}")
```

## Track Token Usage

Monitor input and output tokens for cost management:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

usage = message.usage
print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Total: {usage.input_tokens + usage.output_tokens}")

# With caching
if usage.cache_read_input_tokens:
    print(f"Cache hits: {usage.cache_read_input_tokens} tokens")
if usage.cache_creation_input_tokens:
    print(f"New cache entries: {usage.cache_creation_input_tokens} tokens")
```

## Count Tokens Before Sending

Estimate costs without creating a message:

```python
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-5-20250929",
    messages=[
        {"role": "user", "content": "Very long message..."}
    ]
)

print(f"This request will use {token_count.input_tokens} input tokens")

# Check if within budget
MAX_TOKENS = 100000
if token_count.input_tokens > MAX_TOKENS:
    print("Message too long, truncating...")
```

## Add Request Metadata

Track users for rate limiting and abuse prevention:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    metadata={"user_id": "user_12345"},
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Handle Max Tokens Limit

Deal with incomplete responses:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,  # Intentionally small
    messages=[{"role": "user", "content": "Write a long essay"}]
)

if message.stop_reason == "max_tokens":
    print("Response was truncated. Consider increasing max_tokens.")
    print(f"Partial response: {message.content[0].text}")

    # Continue generation
    continued = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Write a long essay"},
            {"role": "assistant", "content": message.content},
            {"role": "user", "content": "Please continue"}
        ]
    )
```

## Use Different Models

Choose model based on requirements:

```python
# Fast and cost-effective
message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Quick question"}]
)

# Balanced (recommended for most tasks)
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Standard query"}]
)

# Maximum capability for complex tasks
message = client.messages.create(
    model="claude-opus-4-5-20250929",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Complex reasoning task"}]
)
```

## Async Messaging

For async applications:

```python
import asyncio
from anthropic import AsyncAnthropic

async def send_message(content: str) -> str:
    client = AsyncAnthropic()

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}]
    )

    return message.content[0].text

# Run async function
response = asyncio.run(send_message("Hello"))

# Concurrent requests
async def send_multiple():
    client = AsyncAnthropic()

    tasks = [
        client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"Question {i}"}]
        )
        for i in range(5)
    ]

    responses = await asyncio.gather(*tasks)
    return [r.content[0].text for r in responses]

results = asyncio.run(send_multiple())
```

## See Also

- **[Messages API Reference](../api/messages.md)** - Complete API documentation
- **[Multimodal Input](./multimodal-input.md)** - Working with images and documents
- **[Streaming Responses](./streaming-responses.md)** - Real-time streaming
- **[Error Handling Guide](../guides/error-handling.md)** - Production error patterns
