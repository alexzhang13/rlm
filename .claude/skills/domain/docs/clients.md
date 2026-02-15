# Clients Domain

LM client implementations live in `rlm/clients/`. All clients inherit from `BaseLM`.

## BaseLM Interface

**File**: `rlm/clients/base_lm.py`

| Method | Purpose |
|--------|---------|
| `completion(prompt, model=None)` | Synchronous LLM call |
| `acompletion(prompt, model=None)` | Async LLM call |
| `get_usage_summary()` | Aggregated usage across all calls |
| `get_last_usage()` | Usage from most recent call |

### Prompt Format
Clients must handle both:
- `str` - Plain text prompt
- `list[dict[str, Any]]` - Message list format (`[{"role": "user", "content": "..."}]`)

## Available Clients

| Client | File | Provider | Extra |
|--------|------|----------|-------|
| `OpenAIClient` | `openai.py` | OpenAI | core |
| `AzureOpenAIClient` | `azure_openai.py` | Azure OpenAI | core |
| `AnthropicClient` | `anthropic.py` | Anthropic | core |
| `GeminiClient` | `gemini.py` | Google Gemini | core |
| `PortkeyClient` | `portkey.py` | Portkey (multi-provider) | core |
| `LiteLLMClient` | `litellm.py` | LiteLLM (multi-provider) | core |

## Implementing a New Client

### Requirements
- Inherit from `BaseLM` in `rlm/clients/base_lm.py`
- Implement all abstract methods: `completion`, `acompletion`, `get_usage_summary`, `get_last_usage`
- Track per-model usage (calls, input/output tokens)
- Handle both string and message list prompts
- Register client in `rlm/clients/__init__.py`

### Example Structure

```python
from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

class MyClient(BaseLM):
    def __init__(self, api_key: str, model_name: str, **kwargs):
        super().__init__(model_name=model_name, **kwargs)
        # Initialize your client

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        # Handle both str and message list formats
        # Track usage with _track_cost()
        # Return response string

    def get_usage_summary(self) -> UsageSummary:
        # Return aggregated usage across all calls
```

### Configuration Guidelines
- **Environment variables**: ONLY for API keys (document in README)
- **Hardcode**: Default base URLs, reasonable defaults
- **Arguments**: Essential customization via `__init__()`

### Error Handling
- Missing API key -> immediate `ValueError`, not graceful fallback
- Rate limit / API error -> let it propagate (caller handles retry)
- Invalid prompt format -> `TypeError`

## Usage Tracking

**Types**: `rlm/core/types.py`

- `ModelUsageSummary`: Per-model stats (calls, input_tokens, output_tokens)
- `UsageSummary`: Aggregated across all models

Clients track usage internally and expose via `get_usage_summary()` / `get_last_usage()`.

## Dependencies
- Avoid new core dependencies
- Use optional extras for non-essential features (e.g., `modal` extra in pyproject.toml)
- Exception: tiny deps that simplify widely-used code

## Learnings

<!-- Claude: Add discoveries here as you work with clients -->
