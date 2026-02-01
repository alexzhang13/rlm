# Beta Features Overview

Access experimental capabilities through the `client.beta` namespace including extended thinking, citations, web search, code execution, computer use, and more.

## What Are Beta Features?

Beta features provide experimental functionality that may change in future releases. They enable advanced capabilities beyond standard message creation.

## Available Beta Features

### Message Enhancement Features

Add advanced capabilities to message creation:

- **[Extended Thinking](./message-features.md#extended-thinking)** - Enable Claude to show detailed reasoning with configurable token budget
- **[Citations](./message-features.md#citations)** - Source attribution for responses when working with documents
- **[Web Search](./message-features.md#web-search)** - Real-time web information retrieval
- **[Code Execution](./message-features.md#code-execution)** - Python code execution in secure sandbox
- **[Computer Use](./message-features.md#computer-use)** - GUI interaction capabilities (screenshots, mouse, keyboard)
- **[Bash Commands](./message-features.md#bash-commands)** - Shell command execution
- **[Text Editor](./message-features.md#text-editor)** - Text file editing capabilities
- **[MCP Integration](./message-features.md#mcp-integration)** - Model Context Protocol tool integration
- **[Memory Tools](./message-features.md#memory-tools)** - Persistent memory across conversations

**[→ Message Features Documentation](./message-features.md)**

### Resource APIs

Manage resources and process messages at scale:

- **[Skills API](./skills.md)** - Create and manage reusable capabilities with version control
- **[Files API](./files.md)** - Upload and manage files for use in conversations
- **[Beta Message Batches](./batches.md)** - Process multiple beta messages asynchronously with all features

## Quick Start

### Enable Extended Thinking

```python
from anthropic import Anthropic

client = Anthropic()

message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    thinking={"type": "enabled", "budget_tokens": 2000},
    messages=[
        {"role": "user", "content": "Solve this complex problem: ..."}
    ]
)

# Access thinking and response
for block in message.content:
    if block.type == "thinking":
        print(f"Reasoning: {block.thinking}")
    elif block.type == "text":
        print(f"Answer: {block.text}")
```

### Combine Multiple Features

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    thinking={"type": "enabled"},
    web_search={"type": "enabled"},
    citations={"type": "enabled"},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {"type": "text", "text": "Analyze this paper and find related research"}
            ]
        }
    ]
)
```

## Beta Messages API

The beta messages API extends the standard messages API with additional parameters.

```python { .api }
def create(
    self,
    *,
    model: str,
    messages: list[BetaMessageParam],
    max_tokens: int,
    # Standard parameters
    system: str | list[BetaTextBlockParam] = NOT_GIVEN,
    metadata: MetadataParam = NOT_GIVEN,
    stop_sequences: list[str] = NOT_GIVEN,
    stream: bool = False,
    temperature: float = NOT_GIVEN,
    top_p: float = NOT_GIVEN,
    top_k: int = NOT_GIVEN,
    tools: list[BetaToolParam] = NOT_GIVEN,
    tool_choice: BetaToolChoice = NOT_GIVEN,
    # Beta feature parameters
    thinking: ThinkingConfigParam = NOT_GIVEN,
    citations: CitationsConfigParam = NOT_GIVEN,
    web_search: WebSearchConfigParam = NOT_GIVEN,
    code_execution: CodeExecutionConfigParam = NOT_GIVEN,
    bash: BashConfigParam = NOT_GIVEN,
    text_editor: TextEditorConfigParam = NOT_GIVEN,
    computer_use: ComputerUseConfigParam = NOT_GIVEN,
    mcp: MCPConfigParam = NOT_GIVEN,
    memory: MemoryConfigParam = NOT_GIVEN,
    context: ContextConfigParam = NOT_GIVEN,
    **kwargs
) -> BetaMessage:
    """
    Create message with beta features.

    All standard message parameters are supported, plus beta feature configurations.
    Multiple beta features can be enabled simultaneously.

    Returns:
        BetaMessage with beta content blocks
    """
    ...

async def create(self, **kwargs) -> BetaMessage:
    """Async version of create."""
    ...
```

### Streaming

```python { .api }
def stream(
    self,
    **kwargs
) -> BetaMessageStreamManager:
    """Stream message with beta features."""
    ...

def stream(self, **kwargs) -> BetaAsyncMessageStreamManager:
    """Async version of stream."""
    ...
```

### Count Tokens

```python { .api }
def count_tokens(
    self,
    *,
    model: str,
    messages: list[BetaMessageParam],
    system: str | list[BetaTextBlockParam] = NOT_GIVEN,
    tools: list[BetaToolParam] = NOT_GIVEN,
    tool_choice: BetaToolChoice = NOT_GIVEN,
    **kwargs
) -> BetaMessageTokensCount:
    """Count tokens for beta message."""
    ...
```

### Tool Runner

```python { .api }
def tool_runner(
    self,
    *,
    model: str,
    messages: list[BetaMessageParam],
    max_tokens: int,
    tools: list[BetaToolParam | BetaFunctionTool],
    **kwargs
) -> Iterator[BetaMessage]:
    """Automatically execute tools in beta messages."""
    ...
```

## Beta Models API

Retrieve model information with beta feature support.

```python { .api }
def retrieve(
    self,
    model_id: str,
    **kwargs
) -> BetaModelInfo:
    """Get information about a specific model."""
    ...

def list(
    self,
    *,
    before_id: str = NOT_GIVEN,
    after_id: str = NOT_GIVEN,
    limit: int = NOT_GIVEN,
    **kwargs
) -> SyncPage[BetaModelInfo]:
    """List available models with pagination."""
    ...
```

## Architecture

Beta features are organized into three categories:

### 1. Message Enhancement Features
Parameters that enhance `client.beta.messages.create()`:
- Enable advanced reasoning (thinking)
- Add real-time information (web search)
- Enable code execution
- Support document citations
- Enable computer interaction

**[→ Full Documentation](./message-features.md)**

### 2. Batch Processing
Process multiple beta messages with all features:
- Create batches with thinking, citations, web search, etc.
- Same interface as standard batches
- 50% cost reduction

**[→ Batches Documentation](./batches.md)**

### 3. Resource Management
Manage files and skills:
- Upload files for document analysis
- Create reusable skills
- Version control for skills

**[→ Skills Documentation](./skills.md)** | **[→ Files Documentation](./files.md)**

## Feature Comparison

| Feature | Standard API | Beta API |
|---------|-------------|----------|
| Basic messaging | ✓ | ✓ |
| Streaming | ✓ | ✓ |
| Tool use | ✓ | ✓ |
| Extended thinking | ✗ | ✓ |
| Citations | ✗ | ✓ |
| Web search | ✗ | ✓ |
| Code execution | ✗ | ✓ |
| Computer use | ✗ | ✓ |
| Batches | ✓ | ✓ (with beta features) |
| Skills management | ✗ | ✓ |
| File management | ✗ | ✓ |

## Important Notes

### Stability and Changes
- **Beta features may change without notice**
- APIs may be modified or removed
- Breaking changes possible between releases
- Not recommended for production-critical features

### Availability
- Not all features available in all regions
- Some features require specific model versions
- Check current documentation for availability

### Usage and Costs
- Rate limits may differ for beta features
- Beta features may have additional usage costs
- Token budgets (e.g., thinking) are approximate
- Web search adds latency to requests

### Technical Limitations
- Citations work best with document inputs (PDFs, text files)
- Code execution runs in isolated sandbox with limited packages
- Computer use requires display configuration and has security restrictions
- Web search requires internet connectivity
- Skills must include a SKILL.md file at the root
- File uploads have size limits (check API documentation)

### Best Practices
- Test beta features in development before deploying
- Handle feature deprecation gracefully
- Monitor for API changes and updates
- Use appropriate error handling for experimental features
- Check feature availability before use

## Migration from Standard API

Most code using the standard API can be upgraded to beta with minimal changes:

```python
# Standard API
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

# Beta API (backward compatible)
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

# Beta API (with features)
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    thinking={"type": "enabled"},  # Add beta features
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Documentation Structure

### Message Enhancement Features
**[message-features.md](./message-features.md)** - Comprehensive guide to all message enhancement parameters:
- Extended thinking with budget control
- Citations configuration and usage
- Web search integration
- Code execution in sandbox
- Computer use capabilities
- Bash, text editor, MCP, memory tools
- Combined features examples
- Streaming with beta features

### Resource APIs
**[batches.md](./batches.md)** - Beta message batches:
- Create batches with beta features
- Retrieve, list, cancel, delete operations
- Process results with JSONL decoder
- All beta features supported in batches

**[skills.md](./skills.md)** - Skills management:
- Create and manage reusable skills
- Version control for skills
- List, retrieve, delete operations
- Skill file requirements

**[files.md](./files.md)** - File management:
- Upload files for document analysis
- Download and list files
- Delete file operations
- File size limits and formats

## See Also

- [Messages API](../api/messages.md) - Core message creation
- [Tool Use API](../api/tools.md) - Tool integration
- [Streaming API](../api/streaming.md) - Streaming responses
- [Batches API](../api/batches.md) - Standard batch processing
- [Getting Started](../guides/getting-started.md) - Basic SDK usage
