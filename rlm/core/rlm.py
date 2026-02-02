import signal
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from rlm.clients import BaseLM, get_client
from rlm.core.lm_handler import LMHandler
from rlm.core.types import (
    ClientBackend,
    CodeBlock,
    EnvironmentType,
    REPLResult,
    RLMChatCompletion,
    RLMIteration,
    RLMMetadata,
)
from rlm.environments import BaseEnv, SupportsPersistence, get_environment
from rlm.logger import RLMLogger, VerbosePrinter
from rlm.utils.parsing import (
    find_code_blocks,
    find_final_answer,
    format_iteration,
)
from rlm.utils.prompts import (
    RLM_SYSTEM_PROMPT,
    QueryMetadata,
    build_rlm_system_prompt,
    build_user_prompt,
)
from rlm.utils.rlm_utils import filter_sensitive_keys


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
            message or f"Error threshold exceeded: {error_count} consecutive errors (limit: {threshold})"
        )


class CancellationError(Exception):
    """Raised when the RLM execution is cancelled by the user."""

    def __init__(self, partial_answer: str | None = None, message: str | None = None):
        self.partial_answer = partial_answer
        super().__init__(message or "Execution cancelled by user")


class RLM:
    """
    Recursive Language Model class that the user instantiates and runs on their tasks.

    Each completion() call spawns its own environment and LM handler, which are
    cleaned up when the call completes.
    """

    def __init__(
        self,
        backend: ClientBackend = "openai",
        backend_kwargs: dict[str, Any] | None = None,
        environment: EnvironmentType = "local",
        environment_kwargs: dict[str, Any] | None = None,
        depth: int = 0,
        max_depth: int = 1,
        max_iterations: int = 30,
        max_budget: float | None = None,
        max_timeout: float | None = None,
        max_tokens: int | None = None,
        max_errors: int | None = None,
        custom_system_prompt: str | None = None,
        other_backends: list[ClientBackend] | None = None,
        other_backend_kwargs: list[dict[str, Any]] | None = None,
        logger: RLMLogger | None = None,
        verbose: bool = False,
        persistent: bool = False,
        on_subcall_start: Callable[[int, str, str], None] | None = None,
        on_subcall_complete: Callable[[int, str, float, str | None], None] | None = None,
        on_iteration_start: Callable[[int, int], None] | None = None,
        on_iteration_complete: Callable[[int, int, float], None] | None = None,
    ):
        """
        Args:
            backend: The backend to use for the RLM.
            backend_kwargs: The kwargs to pass to the backend.
            environment: The environment to use for the RLM.
            environment_kwargs: The kwargs to pass to the environment.
            depth: The current depth of the RLM (0-indexed).
            max_depth: The maximum depth of recursion. When depth >= max_depth, falls back to plain LM completion.
            max_iterations: The maximum number of iterations of the RLM.
            max_budget: Maximum budget in USD. Execution stops if exceeded. Requires cost-tracking backend (e.g., OpenRouter).
            max_timeout: Maximum execution time in seconds. Execution stops if exceeded, returning best answer if available.
            max_tokens: Maximum total tokens (input + output). Execution stops if exceeded, returning best answer if available.
            max_errors: Maximum consecutive errors before stopping. Execution stops if exceeded, returning best answer if available.
            custom_system_prompt: The custom system prompt to use for the RLM.
            other_backends: A list of other client backends that the environments can use to make sub-calls.
            other_backend_kwargs: The kwargs to pass to the other client backends (ordered to match other_backends).
            logger: The logger to use for the RLM.
            verbose: Whether to print verbose output in rich to console.
            persistent: If True, reuse the environment across completion() calls for multi-turn conversations.
            on_subcall_start: Callback fired when a child RLM starts. Args: (depth, model, prompt_preview).
            on_subcall_complete: Callback fired when a child RLM completes. Args: (depth, model, duration, error_or_none).
            on_iteration_start: Callback fired when an iteration starts. Args: (depth, iteration_num).
            on_iteration_complete: Callback fired when an iteration completes. Args: (depth, iteration_num, duration).
        """
        # Store config for spawning per-completion
        self.backend = backend
        self.backend_kwargs = backend_kwargs
        self.environment_type = environment
        self.environment_kwargs = (
            environment_kwargs.copy() if environment_kwargs is not None else {}
        )
        # Validate other_backends: currently only support one additional backend
        if other_backends is not None:
            if len(other_backends) != 1:
                raise ValueError(
                    "We currently only support one additional backend for the recursive sub-calls! "
                    "This model will be the model used for recursive sub-calls, but this will change in the future"
                )

        self.other_backends = other_backends
        self.other_backend_kwargs = other_backend_kwargs

        self.depth = depth
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.max_budget = max_budget
        self.max_timeout = max_timeout
        self.max_tokens = max_tokens
        self.max_errors = max_errors
        self.system_prompt = custom_system_prompt if custom_system_prompt else RLM_SYSTEM_PROMPT
        self.logger = logger
        self.verbose = VerbosePrinter(enabled=verbose)

        # Event callbacks for live tree display
        self.on_subcall_start = on_subcall_start
        self.on_subcall_complete = on_subcall_complete
        self.on_iteration_start = on_iteration_start
        self.on_iteration_complete = on_iteration_complete

        # Tracking (cumulative across all calls including children)
        self._cumulative_cost: float = 0.0
        self._consecutive_errors: int = 0
        self._last_error: str | None = None
        self._best_partial_answer: str | None = None
        self._completion_start_time: float | None = None  # Set when completion() starts

        # Persistence support
        self.persistent = persistent
        self._persistent_env: SupportsPersistence | None = None

        # Early exit support (SIGUSR1)
        self._early_exit_requested: bool = False
        self._original_sigusr1_handler: signal.Handlers | None = None

        # Inject file support (update variables mid-run)
        inject_file_str = self.environment_kwargs.pop("inject_file", None)
        self._inject_file: Path | None = Path(inject_file_str) if inject_file_str else None
        self._inject_file_mtime: float = 0.0

        # Validate persistence support at initialization
        if self.persistent:
            self._validate_persistent_environment_support()

        # Log metadata if logger is provided
        if self.logger or verbose:
            metadata = RLMMetadata(
                root_model=backend_kwargs.get("model_name", "unknown")
                if backend_kwargs
                else "unknown",
                max_depth=max_depth,
                max_iterations=max_iterations,
                backend=backend,
                backend_kwargs=filter_sensitive_keys(backend_kwargs) if backend_kwargs else {},
                environment_type=environment,
                environment_kwargs=filter_sensitive_keys(environment_kwargs)
                if environment_kwargs
                else {},
                other_backends=other_backends,
            )
            if self.logger:
                self.logger.log_metadata(metadata)
            self.verbose.print_metadata(metadata)

    @contextmanager
    def _spawn_completion_context(self, prompt: str | dict[str, Any]):
        """
        Spawn an LM handler and environment for a single completion call.

        When persistent=True, the environment is reused across calls.
        When persistent=False (default), creates fresh environment each call.
        """
        # Create client and wrap in handler
        client: BaseLM = get_client(self.backend, self.backend_kwargs)

        # Create other_backend_client if provided (for depth=1 routing)
        other_backend_client: BaseLM | None = None
        if self.other_backends and self.other_backend_kwargs:
            other_backend_client = get_client(self.other_backends[0], self.other_backend_kwargs[0])

        lm_handler = LMHandler(client, other_backend_client=other_backend_client)

        # Register other clients to be available as sub-call options (by model name)
        if self.other_backends and self.other_backend_kwargs:
            for backend, kwargs in zip(self.other_backends, self.other_backend_kwargs, strict=True):
                other_client: BaseLM = get_client(backend, kwargs)
                lm_handler.register_client(other_client.model_name, other_client)

        lm_handler.start()

        # Environment: reuse if persistent, otherwise create fresh
        if self.persistent and self._persistent_env is not None:
            environment = self._persistent_env
            # Defensive check: ensure environment supports persistence methods
            if not self._env_supports_persistence(environment):
                raise RuntimeError(
                    f"Persistent environment of type '{type(environment).__name__}' does not "
                    f"implement required methods (update_handler_address, add_context, get_context_count). "
                    f"This should have been caught at initialization."
                )
            environment.update_handler_address((lm_handler.host, lm_handler.port))
            environment.add_context(prompt)
        else:
            env_kwargs = self.environment_kwargs.copy()
            env_kwargs["lm_handler_address"] = (lm_handler.host, lm_handler.port)
            env_kwargs["context_payload"] = prompt
            env_kwargs["depth"] = self.depth + 1  # Environment depth is RLM depth + 1
            # For local environment with max_depth > 1, pass subcall callback for recursive RLM calls
            if self.environment_type == "local" and self.max_depth > 1:
                env_kwargs["subcall_fn"] = self._subcall
            environment: BaseEnv = get_environment(self.environment_type, env_kwargs)

            if self.persistent:
                self._persistent_env = environment

        try:
            yield lm_handler, environment
        finally:
            lm_handler.stop()
            if not self.persistent and hasattr(environment, "cleanup"):
                environment.cleanup()

    def _setup_prompt(self, prompt: str | dict[str, Any]) -> list[dict[str, Any]]:
        """
        Setup the system prompt for the RLM. Also include metadata about the prompt and build
        up the initial message history.
        """
        metadata = QueryMetadata(prompt)
        message_history = build_rlm_system_prompt(
            system_prompt=self.system_prompt, query_metadata=metadata
        )

        return message_history

    def completion(
        self, prompt: str | dict[str, Any], root_prompt: str | None = None
    ) -> RLMChatCompletion:
        """
        Recursive Language Model completion call. This is the main entry point for querying an RLM, and
        can replace a regular LM completion call.

        Spawns its own environment and LM handler for the duration of this call.

        Args:
            prompt: A single string or dictionary of messages to pass as context to the model.
            root_prompt: We allow the RLM's root LM to see a (small) prompt that the user specifies. A common example of this
            is if the user is asking the RLM to answer a question, we can pass the question as the root prompt.
        Returns:
            A final answer as a string.
        """
        time_start = time.perf_counter()
        self._completion_start_time = time_start

        # Reset tracking state for this completion
        self._consecutive_errors = 0
        self._last_error = None
        self._best_partial_answer = None
        self._early_exit_requested = False

        # Install signal handlers for graceful early exit
        self._setup_signal_handlers()

        try:
            # If we're at max depth, the RLM is an LM, so we fallback to the regular LM.
            if self.depth >= self.max_depth:
                return self._fallback_answer(prompt)

            with self._spawn_completion_context(prompt) as (lm_handler, environment):
                message_history = self._setup_prompt(prompt)

                try:
                    for i in range(self.max_iterations):
                        # Check for early exit request (SIGUSR1)
                        if self._early_exit_requested:
                            self.verbose.print_limit_exceeded(
                                "early_exit", "User requested early exit (SIGUSR1)"
                            )
                            raise CancellationError(
                                partial_answer=self._best_partial_answer,
                                message="Early exit requested by user (SIGUSR1)",
                            )

                        # Check and execute inject file if changed (update variables mid-run)
                        self._check_and_execute_inject_file(environment)

                        # Check timeout before each iteration
                        if self.max_timeout is not None:
                            elapsed = time.perf_counter() - time_start
                            if elapsed > self.max_timeout:
                                self.verbose.print_limit_exceeded(
                                    "timeout",
                                    f"{elapsed:.1f}s of {self.max_timeout:.1f}s",
                                )
                                raise TimeoutExceededError(
                                    elapsed=elapsed,
                                    timeout=self.max_timeout,
                                    partial_answer=self._best_partial_answer,
                                    message=(
                                        f"Timeout exceeded after iteration {i}: "
                                        f"{elapsed:.1f}s of {self.max_timeout:.1f}s limit"
                                    ),
                                )

                        # Current prompt = message history + additional prompt suffix
                        context_count = (
                            environment.get_context_count()
                            if isinstance(environment, SupportsPersistence)
                            else 1
                        )
                        history_count = (
                            environment.get_history_count()
                            if isinstance(environment, SupportsPersistence)
                            else 0
                        )
                        current_prompt = message_history + [
                            build_user_prompt(root_prompt, i, context_count, history_count)
                        ]

                        iteration: RLMIteration = self._completion_turn(
                            prompt=current_prompt,
                            lm_handler=lm_handler,
                            environment=environment,
                        )

                        # Track errors from code execution (check stderr for errors)
                        iteration_had_error = False
                        for code_block in iteration.code_blocks:
                            if code_block.result and code_block.result.stderr:
                                iteration_had_error = True
                                self._last_error = code_block.result.stderr
                                break

                        if iteration_had_error:
                            self._consecutive_errors += 1
                        else:
                            self._consecutive_errors = 0  # Reset on success

                        # Check error threshold
                        if self.max_errors is not None and self._consecutive_errors >= self.max_errors:
                            self.verbose.print_limit_exceeded(
                                "errors",
                                f"{self._consecutive_errors} consecutive errors (limit: {self.max_errors})",
                            )
                            raise ErrorThresholdExceededError(
                                error_count=self._consecutive_errors,
                                threshold=self.max_errors,
                                last_error=self._last_error,
                                partial_answer=self._best_partial_answer,
                                message=(
                                    "Error threshold exceeded: "
                                    f"{self._consecutive_errors} consecutive errors "
                                    f"(limit: {self.max_errors})"
                                ),
                            )

                        # Check budget after each iteration
                        if self.max_budget is not None:
                            current_usage = lm_handler.get_usage_summary()
                            current_cost = current_usage.total_cost or 0.0
                            self._cumulative_cost = current_cost
                            if self._cumulative_cost > self.max_budget:
                                self.verbose.print_budget_exceeded(
                                    self._cumulative_cost, self.max_budget
                                )
                                raise BudgetExceededError(
                                    spent=self._cumulative_cost,
                                    budget=self.max_budget,
                                    message=(
                                        f"Budget exceeded after iteration {i + 1}: "
                                        f"spent ${self._cumulative_cost:.6f} "
                                        f"of ${self.max_budget:.6f} budget"
                                    ),
                                )

                        # Check token limit after each iteration
                        if self.max_tokens is not None:
                            current_usage = lm_handler.get_usage_summary()
                            total_tokens = (
                                current_usage.total_input_tokens + current_usage.total_output_tokens
                            )
                            if total_tokens > self.max_tokens:
                                self.verbose.print_limit_exceeded(
                                    "tokens",
                                    f"{total_tokens:,} of {self.max_tokens:,} tokens",
                                )
                                raise TokenLimitExceededError(
                                    tokens_used=total_tokens,
                                    token_limit=self.max_tokens,
                                    partial_answer=self._best_partial_answer,
                                    message=(
                                        f"Token limit exceeded after iteration {i + 1}: "
                                        f"{total_tokens:,} of {self.max_tokens:,} tokens"
                                    ),
                                )

                        # Check if RLM is done and has a final answer.
                        final_answer = find_final_answer(
                            iteration.response, environment=environment
                        )
                        iteration.final_answer = final_answer

                        # Store as best partial answer (most recent response with content)
                        if iteration.response and iteration.response.strip():
                            self._best_partial_answer = iteration.response

                        # If logger is used, log the iteration.
                        if self.logger:
                            self.logger.log(iteration)

                        # Verbose output for this iteration
                        self.verbose.print_iteration(iteration, i + 1)

                        if final_answer is not None:
                            time_end = time.perf_counter()
                            usage = lm_handler.get_usage_summary()
                            self.verbose.print_final_answer(final_answer)
                            self.verbose.print_summary(
                                i + 1, time_end - time_start, usage.to_dict()
                            )

                            # Store message history in persistent environment
                            if self.persistent and isinstance(environment, SupportsPersistence):
                                environment.add_history(message_history)

                            return RLMChatCompletion(
                                root_model=self.backend_kwargs.get("model_name", "unknown")
                                if self.backend_kwargs
                                else "unknown",
                                prompt=prompt,
                                response=final_answer,
                                usage_summary=usage,
                                execution_time=time_end - time_start,
                            )

                        # Format the iteration for the next prompt.
                        new_messages = format_iteration(iteration)

                        # Update message history with the new messages.
                        message_history.extend(new_messages)

                except KeyboardInterrupt:
                    self.verbose.print_limit_exceeded(
                        "cancelled", "User interrupted execution"
                    )
                    raise CancellationError(
                        partial_answer=self._best_partial_answer,
                        message="Execution cancelled by user (Ctrl+C)",
                    )

                # Default behavior: we run out of iterations, provide one final answer
                time_end = time.perf_counter()
                final_answer = self._default_answer(message_history, lm_handler)
                usage = lm_handler.get_usage_summary()
                self.verbose.print_final_answer(final_answer)
                self.verbose.print_summary(
                    self.max_iterations, time_end - time_start, usage.to_dict()
                )

                # Store message history in persistent environment
                if self.persistent and isinstance(environment, SupportsPersistence):
                    environment.add_history(message_history)

                return RLMChatCompletion(
                    root_model=self.backend_kwargs.get("model_name", "unknown")
                    if self.backend_kwargs
                    else "unknown",
                    prompt=prompt,
                    response=final_answer,
                    usage_summary=usage,
                    execution_time=time_end - time_start,
                )
        finally:
            # Restore original signal handlers
            self._restore_signal_handlers()

    def _completion_turn(
        self,
        prompt: str | dict[str, Any],
        lm_handler: LMHandler,
        environment: BaseEnv,
    ) -> RLMIteration:
        """
        Perform a single iteration of the RLM, including prompting the model
        and code execution + tool execution.
        """
        iter_start = time.perf_counter()
        response = lm_handler.completion(prompt)
        code_block_strs = find_code_blocks(response)
        code_blocks = []

        for code_block_str in code_block_strs:
            code_result: REPLResult = environment.execute_code(code_block_str)
            code_blocks.append(CodeBlock(code=code_block_str, result=code_result))

        iteration_time = time.perf_counter() - iter_start
        return RLMIteration(
            prompt=prompt,
            response=response,
            code_blocks=code_blocks,
            iteration_time=iteration_time,
        )

    def _default_answer(self, message_history: list[dict[str, Any]], lm_handler: LMHandler) -> str:
        """
        Default behavior if the RLM runs out of iterations and does not find a final answer.
        It will take the message history, and try to generate a final answer from it.
        """
        current_prompt = message_history + [
            {
                "role": "assistant",
                "content": "Please provide a final answer to the user's question based on the information provided.",
            }
        ]
        response = lm_handler.completion(current_prompt)

        if self.logger:
            self.logger.log(
                RLMIteration(
                    prompt=current_prompt,
                    response=response,
                    final_answer=response,
                    code_blocks=[],
                )
            )

        return response

    def _fallback_answer(self, message: str | dict[str, Any]) -> str:
        """
        Fallback behavior if the RLM is actually at max depth, and should be treated as an LM.
        """
        client: BaseLM = get_client(self.backend, self.backend_kwargs)
        response = client.completion(message)
        return response

    def _subcall(self, prompt: str, model: str | None = None) -> str:
        """
        Handle a subcall from the environment, potentially spawning a child RLM.

        This method is passed as a callback to LocalREPL to enable recursive RLM calls.
        When depth allows, it spawns a child RLM with its own REPL. At max depth,
        it falls back to a plain LM completion.

        Args:
            prompt: The prompt to process.
            model: Optional model name. If specified, the child RLM will use this model
                instead of inheriting the parent's default backend.

        Returns:
            The response string from either a child RLM or plain LM completion.
            On error, returns an error message string (does not raise).
        """
        next_depth = self.depth + 1

        # Determine which backend/kwargs to use (model override or parent's default)
        if model is not None:
            child_backend_kwargs = (self.backend_kwargs or {}).copy()
            child_backend_kwargs["model_name"] = model
        else:
            child_backend_kwargs = self.backend_kwargs

        # If we'd hit/exceed the cap, do a normal LM completion (no REPL)
        if next_depth >= self.max_depth:
            # Use other_backend if available, otherwise use main backend
            if self.other_backends and self.other_backend_kwargs:
                client = get_client(self.other_backends[0], self.other_backend_kwargs[0])
            else:
                client = get_client(self.backend, child_backend_kwargs or {})
            try:
                return client.completion(prompt)
            except Exception as e:
                return f"Error: LM query failed at max depth - {e}"

        # Calculate remaining budget for child (if budget tracking enabled)
        remaining_budget = None
        if self.max_budget is not None:
            remaining_budget = self.max_budget - self._cumulative_cost
            if remaining_budget <= 0:
                return f"Error: Budget exhausted (spent ${self._cumulative_cost:.6f} of ${self.max_budget:.6f})"

        # Calculate remaining timeout for child (if timeout tracking enabled)
        remaining_timeout = None
        if self.max_timeout is not None and self._completion_start_time is not None:
            elapsed = time.perf_counter() - self._completion_start_time
            remaining_timeout = self.max_timeout - elapsed
            if remaining_timeout <= 0:
                return f"Error: Timeout exhausted ({elapsed:.1f}s of {self.max_timeout:.1f}s)"

        # Resolve the model name for callbacks
        resolved_model = model or (child_backend_kwargs or {}).get("model_name", "unknown")
        prompt_preview = prompt[:80] if len(prompt) > 80 else prompt

        # Fire subcall start callback
        if self.on_subcall_start:
            try:
                self.on_subcall_start(next_depth, str(resolved_model), prompt_preview)
            except Exception:
                pass  # Don't let callback errors break execution

        subcall_start = time.perf_counter()
        error_msg: str | None = None

        # Spawn a child RLM with its own LocalREPL
        child = RLM(
            backend=self.backend,
            backend_kwargs=child_backend_kwargs,
            environment=self.environment_type,
            environment_kwargs=self.environment_kwargs,
            depth=next_depth,
            max_depth=self.max_depth,
            max_iterations=self.max_iterations,
            max_budget=remaining_budget,
            max_timeout=remaining_timeout,
            max_tokens=self.max_tokens,
            max_errors=self.max_errors,
            custom_system_prompt=self.system_prompt,
            other_backends=self.other_backends,
            other_backend_kwargs=self.other_backend_kwargs,
            # Don't propagate logger/verbose to children to reduce noise
            logger=None,
            verbose=False,
            # Propagate callbacks to children for nested tracking
            on_subcall_start=self.on_subcall_start,
            on_subcall_complete=self.on_subcall_complete,
        )
        try:
            result = child.completion(prompt, root_prompt=None)
            # Track child's cost in parent's cumulative cost
            if result.usage_summary and result.usage_summary.total_cost:
                self._cumulative_cost += result.usage_summary.total_cost
            return result.response
        except BudgetExceededError as e:
            # Propagate child's spending to parent
            self._cumulative_cost += e.spent
            error_msg = f"Budget exceeded - {e}"
            return f"Error: Child RLM budget exceeded - {e}"
        except Exception as e:
            error_msg = str(e)
            return f"Error: Child RLM completion failed - {e}"
        finally:
            # Ensure child resources are cleaned up
            child.close()
            # Fire subcall complete callback
            if self.on_subcall_complete:
                try:
                    duration = time.perf_counter() - subcall_start
                    self.on_subcall_complete(next_depth, str(resolved_model), duration, error_msg)
                except Exception:
                    pass  # Don't let callback errors break execution

    def _validate_persistent_environment_support(self) -> None:
        """
        Validate that the configured environment type supports persistent mode.

        Persistent mode requires environments to implement:
        - update_handler_address(address): Update LM handler address between calls
        - add_context(payload, index): Add new context for multi-turn conversations
        - get_context_count(): Return the number of loaded contexts

        Currently only 'local' (LocalREPL) supports these methods.

        Raises:
            ValueError: If the environment type does not support persistent mode.
        """
        # Known environments that support persistence
        persistent_supported_environments = {"local"}

        if self.environment_type not in persistent_supported_environments:
            raise ValueError(
                f"persistent=True is not supported for environment type '{self.environment_type}'. "
                f"Persistent mode requires environments that implement update_handler_address(), "
                f"add_context(), and get_context_count(). "
                f"Supported environments: {sorted(persistent_supported_environments)}"
            )

    @staticmethod
    def _env_supports_persistence(env: BaseEnv) -> bool:
        """Check if an environment instance supports persistent mode methods."""
        return isinstance(env, SupportsPersistence)

    def _setup_signal_handlers(self) -> None:
        """Install SIGUSR1 handler for graceful early exit (Unix only)."""
        if not hasattr(signal, "SIGUSR1"):
            return  # Windows doesn't have SIGUSR1
        try:
            self._original_sigusr1_handler = signal.signal(
                signal.SIGUSR1, self._handle_sigusr1
            )
        except (ValueError, OSError):
            # Can't set signal handler (e.g., not in main thread)
            pass

    def _restore_signal_handlers(self) -> None:
        """Restore original SIGUSR1 handler."""
        if not hasattr(signal, "SIGUSR1"):
            return
        if self._original_sigusr1_handler is not None:
            try:
                signal.signal(signal.SIGUSR1, self._original_sigusr1_handler)
            except (ValueError, OSError):
                pass
            self._original_sigusr1_handler = None

    def _handle_sigusr1(self, signum: int, frame: Any) -> None:
        """Handle SIGUSR1 by setting early exit flag."""
        self._early_exit_requested = True

    def _check_and_execute_inject_file(self, environment: BaseEnv) -> None:
        """Check if inject file changed and execute its contents in the REPL.

        This allows users to update variables mid-run by modifying the inject file.
        The code is executed exactly like LLM-generated code would be.
        """
        if self._inject_file is None:
            return
        if not self._inject_file.exists():
            return

        try:
            current_mtime = self._inject_file.stat().st_mtime
            if current_mtime > self._inject_file_mtime:
                code = self._inject_file.read_text()
                if code.strip():
                    self.verbose.print_limit_exceeded(
                        "inject", f"Executing inject file: {self._inject_file}"
                    )
                    environment.execute_code(code)
                self._inject_file_mtime = current_mtime
        except (OSError, IOError) as e:
            # Log error but don't fail the iteration
            self.verbose.print_limit_exceeded(
                "inject_error", f"Failed to read inject file: {e}"
            )

    def close(self) -> None:
        """Clean up persistent environment. Call when done with multi-turn conversations."""
        if self._persistent_env is not None:
            if hasattr(self._persistent_env, "cleanup"):
                self._persistent_env.cleanup()
            self._persistent_env = None

    def __enter__(self) -> "RLM":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False
