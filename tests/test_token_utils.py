"""Tests for token estimation and context-window validation helpers."""

import pytest

from rlm.utils.exceptions import ContextWindowExceededError
from rlm.utils.token_utils import (
    CHARS_PER_TOKEN_ESTIMATE,
    DEFAULT_CONTEXT_LIMIT,
    count_prompt_tokens,
    count_tokens,
    estimate_text_tokens,
    get_context_limit,
    validate_prompt_fits_context_window,
)


def test_get_context_limit_uses_longest_matching_key():
    """Model aliases should resolve to the most specific configured limit."""
    assert get_context_limit("@openai/gpt-4o-mini") == 128_000


def test_get_context_limit_falls_back_for_unknown_models():
    """Unknown models should use the conservative default context limit."""
    assert get_context_limit("my-custom-model") == DEFAULT_CONTEXT_LIMIT


def test_estimate_text_tokens_uses_character_fallback_for_unknown_models():
    """Unknown models should use the character-based estimator."""
    text = "x" * (CHARS_PER_TOKEN_ESTIMATE * 10 + 1)
    assert estimate_text_tokens(text, "unknown") == 11


def test_count_prompt_tokens_accepts_message_lists():
    """Message-list prompts should be counted with the shared message estimator."""
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Summarize this."},
    ]
    assert count_prompt_tokens(messages, "unknown") == count_tokens(messages, "unknown")


def test_validate_prompt_fits_context_window_allows_small_prompt():
    """Validation should pass silently when prompt fits the selected model."""
    validate_prompt_fits_context_window("short prompt", "gpt-4")


def test_validate_prompt_fits_context_window_raises_with_metadata():
    """Validation should raise a descriptive error for oversized prompts."""
    prompt = "x" * (CHARS_PER_TOKEN_ESTIMATE * 9_000)

    with pytest.raises(ContextWindowExceededError) as exc_info:
        validate_prompt_fits_context_window(prompt, "gpt-4")

    error = exc_info.value
    assert error.model_name == "gpt-4"
    assert error.context_limit == 8_192
    assert error.estimated_input_tokens > error.context_limit
    assert error.prompt_kind == "string"
    assert "Context window exceeded" in str(error)
