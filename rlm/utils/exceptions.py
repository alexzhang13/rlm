"""Custom exceptions for RLM execution limits and cancellation."""


class BudgetExceededError(Exception):
    """Raised when the RLM execution exceeds the maximum budget."""

    def __init__(self, spent: float, budget: float, message: str | None = None):
        self.spent = spent
        self.budget = budget
        super().__init__(message or f"Budget exceeded: spent ${spent:.6f} of ${budget:.6f} budget")


class TimeoutExceededError(Exception):
    """Raised when the RLM execution exceeds the maximum timeout."""

    def __init__(
        self,
        elapsed: float,
        timeout: float,
        partial_answer: str | None = None,
        message: str | None = None,
    ):
        self.elapsed = elapsed
        self.timeout = timeout
        self.partial_answer = partial_answer
        super().__init__(message or f"Timeout exceeded: {elapsed:.1f}s of {timeout:.1f}s limit")


class TokenLimitExceededError(Exception):
    """Raised when the RLM execution exceeds the maximum token limit."""

    def __init__(
        self,
        tokens_used: int,
        token_limit: int,
        partial_answer: str | None = None,
        message: str | None = None,
    ):
        self.tokens_used = tokens_used
        self.token_limit = token_limit
        self.partial_answer = partial_answer
        super().__init__(
            message or f"Token limit exceeded: {tokens_used:,} of {token_limit:,} tokens"
        )


class ErrorThresholdExceededError(Exception):
    """Raised when the RLM encounters too many consecutive errors."""

    def __init__(
        self,
        error_count: int,
        threshold: int,
        last_error: str | None = None,
        partial_answer: str | None = None,
        message: str | None = None,
    ):
        self.error_count = error_count
        self.threshold = threshold
        self.last_error = last_error
        self.partial_answer = partial_answer
        super().__init__(
            message
            or f"Error threshold exceeded: {error_count} consecutive errors (limit: {threshold})"
        )


class ContextWindowExceededError(Exception):
    """Raised when a prompt is estimated to exceed a model's context window."""

    def __init__(
        self,
        model_name: str,
        estimated_input_tokens: int,
        context_limit: int,
        prompt_kind: str,
        estimation_method: str,
        message: str | None = None,
    ):
        self.model_name = model_name
        self.estimated_input_tokens = estimated_input_tokens
        self.context_limit = context_limit
        self.prompt_kind = prompt_kind
        self.estimation_method = estimation_method
        super().__init__(
            message
            or (
                f"Context window exceeded for model '{model_name}': estimated "
                f"{estimated_input_tokens:,} input tokens for {prompt_kind} prompt exceeds "
                f"{context_limit:,}-token limit ({estimation_method}). Reduce, chunk, or "
                "summarize the prompt first, or use rlm_query(...) where recursive subcalls "
                "are supported."
            )
        )


class CancellationError(Exception):
    """Raised when the RLM execution is cancelled by the user."""

    def __init__(self, partial_answer: str | None = None, message: str | None = None):
        self.partial_answer = partial_answer
        super().__init__(message or "Execution cancelled by user")
