# Anthropic Python SDK

The official Python library for the Anthropic REST API, providing type-safe access to Claude AI models with both sync and async support.

## Package Information

- **Package Name**: anthropic
- **Package Type**: Python SDK
- **Language**: Python 3.8+
- **Installation**: `pip install anthropic`
- **Repository**: https://github.com/anthropics/anthropic-sdk-python
- **License**: MIT

## Installation

```bash
pip install anthropic
```

Platform-specific extras:
- `pip install anthropic[bedrock]` - AWS Bedrock
- `pip install anthropic[vertex]` - Google Vertex AI
- `pip install anthropic[aiohttp]` - Alternative async client

## Quick Start

### Basic Message

```python { .api }
from anthropic import Anthropic

client = Anthropic()  # Reads ANTHROPIC_API_KEY from environment

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}]
)

print(message.content[0].text)
```

### Async Message

```python { .api }
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
message = await client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Stream Response

```python { .api }
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Available Models

**Claude 4.5 (Latest):**
- `claude-opus-4-5-20250929` - Most capable
- `claude-sonnet-4-5-20250929` - Balanced (recommended)

**Claude 3.5:**
- `claude-3-5-sonnet-20241022` - Previous Sonnet
- `claude-3-5-haiku-20241022` - Fast and cost-effective

**[→ Complete model list and selection guide](./api/models.md)**

## Common Tasks

Choose based on your use case:

**[Basic Messaging](./common-tasks/basic-messaging.md)**
- Simple text conversations
- System prompts
- Multi-turn conversations
- Temperature control

**[Multimodal Input](./common-tasks/multimodal-input.md)**
- Image analysis (JPG, PNG, GIF, WebP)
- PDF document processing
- Mixed content (text + images + documents)

**[Tool Integration](./common-tasks/tool-integration.md)**
- Function calling basics
- Auto-execution with tool_runner
- Async tools
- Error handling in tools

**[Streaming Responses](./common-tasks/streaming-responses.md)**
- Real-time text streaming
- Event-based processing
- Token usage tracking
- Error handling

**[Batch Processing](./guides/batch-processing.md)**
- Process thousands of requests
- 50% cost reduction
- High-throughput scenarios

## API Quick Reference

Fast lookup for method signatures and parameters:

**[Messages API](./quick-reference/messages.md)** - Core message creation
- `create()` - Create single message
- `stream()` - Stream message response
- `count_tokens()` - Estimate token usage

**[Streaming API](./quick-reference/streaming.md)** - Real-time response processing
- `stream()` - Context manager for streaming
- Event types and handling
- Helper methods

**[Tools API](./quick-reference/tools.md)** - Function calling
- `@beta_tool` decorator
- `tool_runner()` - Auto-execution
- Manual tool handling

**[Batches API](./quick-reference/batches.md)** - Async batch processing
- `create()` - Submit batch
- `retrieve()` - Check status
- `results()` - Get outputs

**[Models API](./quick-reference/models.md)** - Model information
- `retrieve()` - Get model details
- `list()` - Browse available models

## Detailed API Documentation

In-depth reference with all parameters, types, and examples:

### Core APIs

- **[Messages API](./api/messages.md)** - Complete messages API reference with all parameters, types, and examples
- **[Streaming API](./api/streaming.md)** - Detailed streaming architecture, events, and patterns
- **[Tools API](./api/tools.md)** - Function calling with decorators and manual definitions
- **[Batches API](./api/batches.md)** - Batch processing for high-throughput use cases
- **[Models API](./api/models.md)** - Model information and selection
- **[Completions API](./api/completions.md)** - Legacy text completions API (deprecated, use Messages API instead)

### Implementation Guides

- **[Getting Started](./guides/getting-started.md)** - Installation, authentication, and first steps
- **[Multimodal Content](./guides/multimodal.md)** - Working with images, documents, and PDFs
- **[Tool Usage](./guides/tool-usage.md)** - Building agentic workflows with function calling
- **[Streaming Guide](./guides/streaming-guide.md)** - Advanced streaming patterns and best practices
- **[Batch Processing](./guides/batch-processing.md)** - Large-scale async message processing
- **[Error Handling](./guides/error-handling.md)** - Robust error management and retry strategies

### Platform Integrations

- **[AWS Bedrock](./platforms/bedrock.md)** - Use Claude on AWS infrastructure
- **[Google Vertex AI](./platforms/vertex.md)** - Use Claude on GCP infrastructure
- **[Azure AI Foundry](./platforms/foundry.md)** - Use Claude on Azure infrastructure

### Reference Documentation

- **[Client Configuration](./reference/client-config.md)** - Client initialization, timeouts, retries, HTTP options
- **[Type System](./reference/types.md)** - Complete Pydantic type definitions
- **[Error Handling](./reference/errors.md)** - Exception hierarchy and error types
- **[Pagination](./reference/pagination.md)** - List operation pagination patterns
- **[Utilities](./reference/utilities.md)** - Helper functions and utilities

## Beta Features

Access experimental capabilities via `client.beta` namespace:

**[Beta Overview](./beta/index.md)** - Introduction to beta features

**Message Enhancement Features:**
- **[Extended Thinking](./beta/message-features.md#extended-thinking)** - Long-form reasoning with budget control
- **[Citations](./beta/message-features.md#citations)** - Source attribution for document-based responses
- **[Web Search](./beta/message-features.md#web-search)** - Real-time web information retrieval
- **[Code Execution](./beta/message-features.md#code-execution)** - Python sandbox execution
- **[Computer Use](./beta/message-features.md#computer-use)** - GUI interaction capabilities
- **[MCP Integration](./beta/message-features.md#mcp-integration)** - Model Context Protocol tools

**[→ All Message Features](./beta/message-features.md)**

**Resource Management:**
- **[Skills API](./beta/skills.md)** - Create and manage reusable capabilities
- **[Files API](./beta/files.md)** - Upload and manage document files
- **[Beta Batches](./beta/batches.md)** - Batch processing with beta features

## Client Configuration

### Basic Setup

```python { .api }
from anthropic import Anthropic

# Environment variable (recommended)
client = Anthropic()  # Uses ANTHROPIC_API_KEY

# Explicit API key
client = Anthropic(api_key="your-api-key")

# Context manager (automatic cleanup)
with Anthropic() as client:
    message = client.messages.create(...)
```

### Common Configurations

```python { .api }
import httpx

# Custom timeout
client = Anthropic(timeout=120.0)

# Granular timeout
client = Anthropic(
    timeout=httpx.Timeout(
        connect=10.0,
        read=60.0,
        write=10.0,
        pool=10.0
    )
)

# Retry configuration
client = Anthropic(max_retries=5)

# Custom headers
client = Anthropic(
    default_headers={"X-Custom": "value"}
)
```

**[→ Complete configuration reference](./reference/client-config.md)**

## Error Handling

### Basic Pattern

```python
from anthropic import APIError, RateLimitError

try:
    message = client.messages.create(...)
except RateLimitError as e:
    retry_after = e.response.headers.get("retry-after")
    print(f"Rate limited. Retry after {retry_after}s")
except APIError as e:
    print(f"API error: {e.message}")
```

### Exception Hierarchy

```python { .api }
AnthropicError
├── APIError
│   ├── APIStatusError
│   │   ├── BadRequestError (400)
│   │   ├── AuthenticationError (401)
│   │   ├── PermissionDeniedError (403)
│   │   ├── NotFoundError (404)
│   │   ├── RateLimitError (429)
│   │   ├── InternalServerError (≥500)
│   ├── APIConnectionError
│   ├── APITimeoutError
│   └── APIResponseValidationError
```

**[→ Complete error reference and retry patterns](./reference/errors.md)**

**[→ Error handling guide with advanced patterns](./guides/error-handling.md)**

## Environment Variables

- `ANTHROPIC_API_KEY` - API key for authentication (required)
- `ANTHROPIC_BASE_URL` - Override base URL (optional)
- `ANTHROPIC_AUTH_TOKEN` - Bearer token alternative (optional)

Platform-specific variables documented in platform guides.

## SDK Architecture

### Client Hierarchy

- **Anthropic / AsyncAnthropic** - Main clients for direct API access
- **AnthropicBedrock / AsyncAnthropicBedrock** - AWS Bedrock integration
- **AnthropicVertex / AsyncAnthropicVertex** - Google Vertex AI integration
- **AnthropicFoundry / AsyncAnthropicFoundry** - Azure AI Foundry integration

### Resource Structure

```python { .api }
client.messages          # Messages resource
  .create()              # Create message
  .stream()              # Stream message
  .count_tokens()        # Count tokens
  .batches               # Batches sub-resource
    .create()            # Create batch
    .retrieve()          # Get batch status
    .list()              # List batches
    .cancel()            # Cancel batch
    .delete()            # Delete batch
    .results()           # Get batch results

client.beta              # Beta features namespace
  .messages              # Beta messages with additional features
    .create()            # Create with beta features
    .stream()            # Stream with beta features
    .tool_runner()       # Auto-execute tools
  .skills                # Skills management
  .files                 # File management

client.models            # Models information
  .retrieve()            # Get model info
  .list()                # List models
```

## Type System

All requests and responses use Pydantic models for type safety:

```python { .api }
class Message(BaseModel):
    id: str
    type: Literal["message"]
    role: Literal["assistant"]
    content: list[ContentBlock]
    model: str
    stop_reason: StopReason | None
    usage: Usage

ContentBlock = Union[TextBlock, ToolUseBlock]
StopReason = Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]
```

**[→ Complete type definitions](./reference/types.md)**

## Decision Guide for Common Scenarios

### "I need to send a message to Claude"
→ **[Basic Messaging](./common-tasks/basic-messaging.md)** or **[Messages API](./api/messages.md)**

### "I need to process images or PDFs"
→ **[Multimodal Input](./common-tasks/multimodal-input.md)** or **[Multimodal Guide](./guides/multimodal.md)**

### "I need Claude to call functions/use tools"
→ **[Tool Integration](./common-tasks/tool-integration.md)** or **[Tools API](./api/tools.md)**

### "I need real-time streaming output"
→ **[Streaming Responses](./common-tasks/streaming-responses.md)** or **[Streaming API](./api/streaming.md)**

### "I need to process thousands of messages"
→ **[Batch Processing Guide](./guides/batch-processing.md)** or **[Batches API](./api/batches.md)**

### "I'm getting errors"
→ **[Error Reference](./reference/errors.md)** or **[Error Handling Guide](./guides/error-handling.md)**

### "I need extended reasoning/thinking"
→ **[Beta Overview](./beta/index.md)** → **[Extended Thinking](./beta/message-features.md#extended-thinking)**

### "I need web search or code execution"
→ **[Beta Overview](./beta/index.md)** → **[Message Features](./beta/message-features.md)**

### "I'm using AWS/GCP/Azure"
→ **[Platform Integrations](#platform-integrations)** → Choose your platform

## Package Constants

```python { .api }
# Client Configuration Constants
DEFAULT_TIMEOUT: float = 600.0  # 10 minutes default timeout for requests
DEFAULT_MAX_RETRIES: int = 2  # Default number of retry attempts
DEFAULT_CONNECTION_LIMITS: httpx.Limits  # Default HTTP connection pool limits

# Legacy Text Completion Prompt Constants
HUMAN_PROMPT: str = "\n\nHuman:"  # Legacy prompt marker for human messages
AI_PROMPT: str = "\n\nAssistant:"  # Legacy prompt marker for AI responses

# Sentinel Values
NOT_GIVEN: NotGiven  # Sentinel indicating parameter not provided
```

**Note**: `HUMAN_PROMPT` and `AI_PROMPT` are legacy constants for the deprecated Text Completions API. Use the Messages API instead for new applications.

## Support Resources

- **API Documentation**: https://docs.anthropic.com
- **SDK Repository**: https://github.com/anthropics/anthropic-sdk-python
- **Model Pricing**: https://anthropic.com/pricing
- **Rate Limits**: https://docs.anthropic.com/rate-limits
