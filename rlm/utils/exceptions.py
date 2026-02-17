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


class CancellationError(Exception):
    """Raised when the RLM execution is cancelled by the user."""

    def __init__(self, partial_answer: str | None = None, message: str | None = None):
        self.partial_answer = partial_answer
        super().__init__(message or "Execution cancelled by user")
