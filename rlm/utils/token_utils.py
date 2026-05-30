"""
Token counting and model context limits for compaction and context sizing.

Uses tiktoken for OpenAI-style models when available; otherwise estimates
with ~4 characters per token.
"""

from typing import Any

from rlm.utils.exceptions import ContextWindowExceededError

# Default context limit when model is unknown (tokens)
DEFAULT_CONTEXT_LIMIT = 128_000

# Characters per token when tokenizer is unavailable (conservative estimate)
CHARS_PER_TOKEN_ESTIMATE = 4

# Model context limits (max input context in tokens).
# Match: key contained in model_name (e.g. "gpt-4o" matches "@openai/gpt-4o").
# Longest matching key wins.
MODEL_CONTEXT_LIMITS: dict[str, int] = {
    # OpenAI (GPT-5: 272k input, 128k reasoning+output)
    "gpt-5-nano": 272_000,
    "gpt-5": 272_000,
    "gpt-4o-mini": 128_000,
    "gpt-4o-2024": 128_000,
    "gpt-4o": 128_000,
    "gpt-4-turbo-preview": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4-32k": 32_768,
    "gpt-4": 8_192,
    "gpt-3.5-turbo-16k": 16_385,
    "gpt-3.5-turbo": 16_385,
    "o1-mini": 128_000,
    "o1-preview": 128_000,
    "o1": 200_000,
    # Anthropic
    "claude-3-5-sonnet": 200_000,
    "claude-3-5-haiku": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
    "claude-2.1": 200_000,
    "claude-2": 100_000,
    # Gemini
    "gemini-2.5-flash": 1_000_000,
    "gemini-2.5-pro": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    "gemini-1.5-pro": 1_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-1.0-pro": 30_720,
    # Qwen (Alibaba)
    "qwen3-max": 256_000,
    "qwen3-72b": 128_000,
    "qwen3-32b": 128_000,
    "qwen3-8b": 32_768,
    "qwen3": 128_000,
    # Kimi (Moonshot)
    "kimi-k2.5": 262_000,
    "kimi-k2-0905": 256_000,
    "kimi-k2-thinking": 256_000,
    "kimi-k2": 128_000,
    "kimi": 128_000,
    # GLM (Zhipu)
    "glm-4.6": 200_000,
    "glm-4-9b": 1_000_000,
    "glm-4": 128_000,
    "glm": 128_000,
}


def get_context_limit(model_name: str) -> int:
    """
    Return max context size in tokens for a model.

    Matches when the dict key is contained in model_name (e.g. "gpt-4o" matches
    "@openai/gpt-4o"). Longest matching key wins. Falls back to DEFAULT_CONTEXT_LIMIT
    for unknown models.
    """
    if not model_name or model_name == "unknown":
        return DEFAULT_CONTEXT_LIMIT
    exact = MODEL_CONTEXT_LIMITS.get(model_name)
    if exact is not None:
        return exact
    best = 0
    best_limit = DEFAULT_CONTEXT_LIMIT
    for key, limit in MODEL_CONTEXT_LIMITS.items():
        if key in model_name and len(key) > best:
            best = len(key)
            best_limit = limit
    return best_limit


def _count_tokens_tiktoken(messages: list[dict[str, Any]], model_name: str) -> int | None:
    """Count tokens with tiktoken if available. Returns None on failure."""
    try:
        import tiktoken
    except ImportError:
        return None
    try:
        enc = tiktoken.encoding_for_model(model_name)
    except Exception:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None
    total = 0
    # Approximate OpenAI message format overhead per message
    tokens_per_message = 3
    tokens_per_name = 1
    for m in messages:
        total += tokens_per_message
        content = m.get("content")
        if isinstance(content, str):
            total += len(enc.encode(content))
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += len(enc.encode(part.get("text", "") or ""))
        elif content is not None and content != "":
            total += len(enc.encode(str(content)))
        if m.get("name"):
            total += tokens_per_name
    return total


def _count_text_tokens_tiktoken(text: str, model_name: str) -> int | None:
    """Count text tokens with tiktoken if available. Returns None on failure."""
    try:
        import tiktoken
    except ImportError:
        return None
    try:
        enc = tiktoken.encoding_for_model(model_name)
    except Exception:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None
    return len(enc.encode(text))


def _estimate_text_tokens_with_method(text: str, model_name: str) -> tuple[int, str]:
    """Estimate token count for raw text and report the estimation method used."""
    if model_name and model_name != "unknown":
        n = _count_text_tokens_tiktoken(text, model_name)
        if n is not None:
            return n, "tiktoken estimate"
    return (
        (len(text) + CHARS_PER_TOKEN_ESTIMATE - 1) // CHARS_PER_TOKEN_ESTIMATE,
        f"character estimate ({CHARS_PER_TOKEN_ESTIMATE} chars/token)",
    )


def _estimate_message_tokens_with_method(
    messages: list[dict[str, Any]], model_name: str
) -> tuple[int, str]:
    """Estimate token count for a chat-style message list."""
    if not messages:
        return 0, "empty prompt"
    if model_name and model_name != "unknown":
        n = _count_tokens_tiktoken(messages, model_name)
        if n is not None:
            return n, "tiktoken estimate"
    total_chars = 0
    for m in messages:
        raw = m.get("content", "") or ""
        total_chars += len(raw) if isinstance(raw, str) else len(str(raw))
    return (
        (total_chars + CHARS_PER_TOKEN_ESTIMATE - 1) // CHARS_PER_TOKEN_ESTIMATE,
        f"character estimate ({CHARS_PER_TOKEN_ESTIMATE} chars/token)",
    )


def estimate_text_tokens(text: str, model_name: str) -> int:
    """Estimate token count for raw text."""
    return _estimate_text_tokens_with_method(text, model_name)[0]


def count_tokens(messages: list[dict[str, Any]], model_name: str) -> int:
    """
    Count tokens in a list of message dicts (role, content).

    Uses tiktoken for OpenAI-style models when the package is available;
    otherwise estimates with character length / CHARS_PER_TOKEN_ESTIMATE.
    """
    return _estimate_message_tokens_with_method(messages, model_name)[0]


def count_prompt_tokens(prompt: str | list[dict[str, Any]], model_name: str) -> int:
    """Estimate token count for a plain prompt string or a chat message list."""
    return _count_prompt_tokens_with_method(prompt, model_name)[0]


def validate_prompt_fits_context_window(
    prompt: str | list[dict[str, Any]], model_name: str
) -> None:
    """Raise ContextWindowExceededError when a prompt is too large for the model."""
    estimated_tokens, estimation_method, prompt_kind = _count_prompt_tokens_with_method(
        prompt, model_name
    )
    context_limit = get_context_limit(model_name)
    if estimated_tokens > context_limit:
        raise ContextWindowExceededError(
            model_name=model_name,
            estimated_input_tokens=estimated_tokens,
            context_limit=context_limit,
            prompt_kind=prompt_kind,
            estimation_method=estimation_method,
        )


def _count_prompt_tokens_with_method(
    prompt: str | list[dict[str, Any]], model_name: str
) -> tuple[int, str, str]:
    """Estimate prompt tokens and return (count, method, prompt_kind)."""
    if isinstance(prompt, str):
        count, method = _estimate_message_tokens_with_method(
            [{"role": "user", "content": prompt}], model_name
        )
        return count, method, "string"
    if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
        count, method = _estimate_message_tokens_with_method(prompt, model_name)
        return count, method, "message-list"
    raise ValueError(f"Invalid prompt type: {type(prompt)}")
