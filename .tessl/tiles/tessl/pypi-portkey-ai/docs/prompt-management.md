# Prompt Management

Advanced prompt management system with templating, rendering, versioning, and prompt execution capabilities.

## Capabilities

### Prompt Rendering and Execution

Advanced prompt management with templating, versioning, and execution capabilities.

```python { .api }
class Prompts:
    def render(
        self,
        *,
        prompt_id: str,
        variables: Mapping[str, Any]
    ) -> PromptRender:
        """
        Render a prompt template with variables.

        Args:
            prompt_id: Unique identifier for the prompt template
            variables: Dictionary of variables to substitute in template

        Returns:
            PromptRender: Rendered prompt content
        """

    def completions(
        self,
        *,
        prompt_id: str,
        variables: Optional[Mapping[str, Any]] = None,
        **kwargs
    ) -> Union[PromptCompletion, Stream[PromptCompletionChunk]]:
        """
        Execute a prompt template and generate completion.

        Args:
            prompt_id: Unique identifier for the prompt template
            variables: Variables for template substitution
            **kwargs: Additional completion parameters (model, temperature, etc.)

        Returns:  
            PromptCompletion: Completion response or streaming chunks
        """

    completions: Completions
    versions: PromptVersions
    partials: PromptPartials

class AsyncPrompts:
    async def render(
        self,
        *,
        prompt_id: str,
        variables: Mapping[str, Any]
    ) -> PromptRender:
        """Async version of render method."""

    async def completions(
        self,
        *,
        prompt_id: str,
        variables: Optional[Mapping[str, Any]] = None,
        **kwargs
    ) -> Union[PromptCompletion, AsyncStream[PromptCompletionChunk]]:
        """Async version of completions method."""

    completions: AsyncCompletions
    versions: AsyncPromptVersions
    partials: AsyncPromptPartials
```

### Prompt Versions

Manage different versions of prompt templates for A/B testing and iterative improvement.

```python { .api }
class PromptVersions:
    def list(self, prompt_id: str, **kwargs): ...
    def retrieve(self, prompt_id: str, version_id: str, **kwargs): ...
    def create(self, prompt_id: str, **kwargs): ...
    def update(self, prompt_id: str, version_id: str, **kwargs): ...

class AsyncPromptVersions:
    async def list(self, prompt_id: str, **kwargs): ...
    async def retrieve(self, prompt_id: str, version_id: str, **kwargs): ...
    async def create(self, prompt_id: str, **kwargs): ...
    async def update(self, prompt_id: str, version_id: str, **kwargs): ...
```

### Prompt Partials

Handle partial prompt rendering and composition for complex prompt structures.

```python { .api }
class PromptPartials:
    def render(self, **kwargs): ...
    def create(self, **kwargs): ...

class AsyncPromptPartials:
    async def render(self, **kwargs): ...
    async def create(self, **kwargs): ...
```

### Generation Management (Deprecated)

Legacy prompt generation API - use Prompts API instead for new implementations.

```python { .api }
class Generations:
    def create(
        self,
        *,
        prompt_id: str,
        config: Optional[Union[Mapping, str]] = None,
        variables: Optional[Mapping[str, Any]] = None
    ) -> Union[GenericResponse, Stream[GenericResponse]]:
        """
        DEPRECATED: Create prompt generation.
        Use portkey.prompts.completions() instead.
        """

class AsyncGenerations:
    async def create(
        self,
        *,
        prompt_id: str,
        config: Optional[Union[Mapping, str]] = None,
        variables: Optional[Mapping[str, Any]] = None
    ) -> Union[GenericResponse, AsyncStream[GenericResponse]]:
        """DEPRECATED: Async version of create method."""
```

## Usage Examples

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Render prompt template
rendered = portkey.prompts.render(
    prompt_id="template_123",
    variables={"name": "Alice", "topic": "AI"}
)

print(f"Rendered prompt: {rendered.prompt}")

# Execute prompt with completion
response = portkey.prompts.completions(
    prompt_id="template_123",
    variables={"name": "Alice", "topic": "AI"},
    model="gpt-4",
    temperature=0.7,
    max_tokens=150
)

print(f"Response: {response.choices[0].message.content}")

# Work with prompt versions
versions = portkey.prompts.versions.list("template_123")
print(f"Available versions: {[v.id for v in versions.data]}")

# Get specific version
version = portkey.prompts.versions.retrieve("template_123", "v2")
print(f"Version details: {version.prompt}")

# Stream completion responses
for chunk in portkey.prompts.completions(
    prompt_id="template_123",
    variables={"name": "Alice", "topic": "AI"},
    model="gpt-4",
    stream=True
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def manage_prompts():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    # Render prompt asynchronously
    rendered = await portkey.prompts.render(
        prompt_id="template_123",
        variables={"name": "Bob", "topic": "Machine Learning"}
    )
    
    # Execute prompt completion
    response = await portkey.prompts.completions(
        prompt_id="template_123",
        variables={"name": "Bob", "topic": "Machine Learning"},
        model="gpt-4"
    )
    
    return rendered, response

rendered, response = asyncio.run(manage_prompts())
```

## Types

```python { .api }
class PromptRender:
    """Rendered prompt content"""
    prompt: str  # Rendered prompt text
    variables: dict  # Variables used in rendering
    prompt_id: str  # Source prompt template ID

class PromptCompletion:
    """Prompt completion response"""
    id: str  # Completion ID
    object: str  # "prompt.completion"
    created: int  # Unix timestamp
    model: str  # Model used
    choices: List[PromptChoice]  # Response choices
    usage: dict  # Token usage information
    prompt_id: str  # Source prompt ID

class PromptCompletionChunk:
    """Streaming prompt completion chunk"""
    id: str  # Completion ID
    object: str  # "prompt.completion.chunk"
    created: int  # Unix timestamp
    model: str  # Model used
    choices: List[PromptChoiceDelta]  # Response deltas
    prompt_id: str  # Source prompt ID

class PromptChoice:
    """Prompt completion choice"""
    index: int  # Choice index
    message: dict  # Response message
    finish_reason: Optional[str]  # Completion reason

class PromptChoiceDelta:
    """Streaming choice delta"""
    index: int  # Choice index
    delta: dict  # Content delta
    finish_reason: Optional[str]  # Completion reason
```