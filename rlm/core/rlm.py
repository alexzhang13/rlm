import time
from contextlib import contextmanager
from typing import Any

from rlm.clients import BaseLM, get_client
from rlm.core.lm_handler import LMHandler
from rlm.core.types import (
    ClientBackend,
    CodeBlock,
    EnvironmentType,
    IterationRecord,
    REPLResult,
    RLMChatCompletion,
    RLMIteration,
    RLMMetadata,
    TaskHistoryEntry,
)
from rlm.environments import BaseEnv, get_environment
from rlm.logger import RLMLogger, VerbosePrinter
from rlm.utils.parsing import (
    find_code_blocks,
    find_final_answer,
    format_iteration,
)
from rlm.utils.prompts import (
    RLM_SYSTEM_PROMPT,
    RLM_PERSISTENT_SYSTEM_PROMPT,
    QueryMetadata,
    build_rlm_system_prompt,
    build_user_prompt,
)
from rlm.utils.rlm_utils import filter_sensitive_keys


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
        custom_system_prompt: str | None = None,
        other_backends: list[ClientBackend] | None = None,
        other_backend_kwargs: list[dict[str, Any]] | None = None,
        logger: RLMLogger | None = None,
        verbose: bool = False,
        persistent: bool = False,
        persist_repl_state: bool = False,
    ):
        """
        Args:
            backend: The backend to use for the RLM.
            backend_kwargs: The kwargs to pass to the backend.
            environment: The environment to use for the RLM.
            environment_kwargs: The kwargs to pass to the environment.
            depth: The current depth of the RLM (0-indexed).
            max_depth: The maximum depth of the RLM. Currently, only depth 1 is supported.
            max_iterations: The maximum number of iterations of the RLM.
            custom_system_prompt: The custom system prompt to use for the RLM.
            other_backends: A list of other client backends that the environments can use to make sub-calls.
            other_backend_kwargs: The kwargs to pass to the other client backends (ordered to match other_backends).
            logger: The logger to use for the RLM.
            verbose: Whether to print verbose output in rich to console.
            persistent: Enable multi-turn persistence mode. When True, the RLM maintains
                conversation/task history across multiple completion() calls, storing
                previous tasks and answers in the context variable (not the model's context window).
            persist_repl_state: When persistent=True, also preserve REPL local variables across turns.
                This allows subsequent tasks to reference variables created in previous turns.
        """
        # Store config for spawning per-completion
        self.backend = backend
        self.backend_kwargs = backend_kwargs
        self.environment_type = environment
        self.environment_kwargs = (
            environment_kwargs.copy() if environment_kwargs is not None else {}
        )
        self.other_backends = other_backends
        self.other_backend_kwargs = other_backend_kwargs

        self.depth = depth
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.logger = logger
        self.verbose = VerbosePrinter(enabled=verbose)

        # Multi-turn persistence state
        self.persistent = persistent
        self.persist_repl_state = persist_repl_state
        self.turn_count = 0
        self.task_history: list[TaskHistoryEntry] = []
        self.persistent_locals: dict[str, Any] = {}  # REPL state across turns

        # Choose system prompt based on persistence mode
        if custom_system_prompt:
            self.system_prompt = custom_system_prompt
        elif persistent:
            self.system_prompt = RLM_PERSISTENT_SYSTEM_PROMPT
        else:
            self.system_prompt = RLM_SYSTEM_PROMPT

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
        Cleans up both when the context exits.
        """
        # Create client and wrap in handler
        client: BaseLM = get_client(self.backend, self.backend_kwargs)
        lm_handler = LMHandler(client)

        # Register other clients to be available as sub-call options
        if self.other_backends and self.other_backend_kwargs:
            for backend, kwargs in zip(self.other_backends, self.other_backend_kwargs, strict=True):
                other_client: BaseLM = get_client(backend, kwargs)
                lm_handler.register_client(other_client.model_name, other_client)

        lm_handler.start()

        # Build context payload - in persistent mode, wrap with turn info
        context_payload = self._build_context_payload(prompt)

        # Pass handler address to environment so it can make llm_query() calls
        env_kwargs = self.environment_kwargs.copy()
        env_kwargs["lm_handler_address"] = (lm_handler.host, lm_handler.port)
        env_kwargs["context_payload"] = context_payload

        # Initialize the environment
        environment: BaseEnv = get_environment(self.environment_type, env_kwargs)

        # Restore persistent REPL state if enabled
        if self.persistent and self.persist_repl_state and self.persistent_locals:
            if hasattr(environment, "locals"):
                environment.locals.update(self.persistent_locals)

        try:
            yield lm_handler, environment
        finally:
            # Save REPL state before cleanup if persistence is enabled
            if self.persistent and self.persist_repl_state:
                if hasattr(environment, "locals"):
                    # Save non-internal variables for next turn
                    self.persistent_locals = {
                        k: v
                        for k, v in environment.locals.items()
                        if not k.startswith("_") and k != "context"
                    }

            # Cleanup
            lm_handler.stop()
            if hasattr(environment, "cleanup"):
                environment.cleanup()

    def _build_context_payload(self, prompt: str | dict[str, Any]) -> dict[str, Any]:
        """
        Build the context payload for the REPL environment.

        In persistent mode, structures the context to include:
        - task_history: List of previous tasks and their answers
        - context_{turn_id}: The current turn's input context

        This keeps conversation history in the context variable (RLM philosophy)
        rather than the model's context window.
        """
        if not self.persistent:
            # Non-persistent mode: pass prompt directly
            return prompt

        # Persistent mode: structure context with history and versioned contexts
        context_data = {
            "turn_id": self.turn_count,
            "task_history": [entry.to_dict() for entry in self.task_history],
            f"context_{self.turn_count}": prompt,
        }

        return context_data

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

        In persistent mode, tracks task history across calls and includes it in the context variable.

        Args:
            prompt: A single string or dictionary of messages to pass as context to the model.
            root_prompt: We allow the RLM's root LM to see a (small) prompt that the user specifies. A common example of this
            is if the user is asking the RLM to answer a question, we can pass the question as the root prompt.
        Returns:
            A final answer as a string.
        """
        time_start = time.perf_counter()

        # If we're at max depth, the RLM is an LM, so we fallback to the regular LM.
        if self.depth >= self.max_depth:
            return self._fallback_answer(prompt)

        with self._spawn_completion_context(prompt) as (lm_handler, environment):
            message_history = self._setup_prompt(prompt)
            iterations_list: list[RLMIteration] = []

            for i in range(self.max_iterations):
                # Current prompt = message history + additional prompt suffix
                # In persistent mode, pass turn info for context-aware prompting
                current_prompt = message_history + [
                    build_user_prompt(
                        root_prompt,
                        i,
                        turn_id=self.turn_count if self.persistent else None,
                        has_history=len(self.task_history) > 0 if self.persistent else False,
                    )
                ]

                iteration: RLMIteration = self._completion_turn(
                    prompt=current_prompt,
                    lm_handler=lm_handler,
                    environment=environment,
                )

                # Check if RLM is done and has a final answer.
                final_answer = find_final_answer(iteration.response, environment=environment)
                iteration.final_answer = final_answer

                # Collect iteration for history
                iterations_list.append(iteration)

                # If logger is used, log the iteration.
                if self.logger:
                    self.logger.log(
                        iteration,
                        turn_id=self.turn_count if self.persistent else None,
                    )

                # Verbose output for this iteration
                self.verbose.print_iteration(iteration, i + 1)

                if final_answer is not None:
                    time_end = time.perf_counter()
                    execution_time = time_end - time_start
                    usage = lm_handler.get_usage_summary()
                    self.verbose.print_final_answer(final_answer)
                    self.verbose.print_summary(i + 1, execution_time, usage.to_dict())

                    # In persistent mode, save this turn to history
                    if self.persistent:
                        self._save_to_history(prompt, final_answer, iterations_list, execution_time, usage)

                    return RLMChatCompletion(
                        root_model=self.backend_kwargs.get("model_name", "unknown")
                        if self.backend_kwargs
                        else "unknown",
                        prompt=prompt,
                        response=final_answer,
                        usage_summary=usage,
                        execution_time=execution_time,
                    )

                # Format the iteration for the next prompt.
                new_messages = format_iteration(iteration)

                # Update message history with the new messages.
                message_history.extend(new_messages)

            # Default behavior: we run out of iterations, provide one final answer
            time_end = time.perf_counter()
            execution_time = time_end - time_start
            final_answer = self._default_answer(message_history, lm_handler)
            usage = lm_handler.get_usage_summary()
            self.verbose.print_final_answer(final_answer)
            self.verbose.print_summary(self.max_iterations, execution_time, usage.to_dict())

            # In persistent mode, save this turn to history
            if self.persistent:
                self._save_to_history(prompt, final_answer, iterations_list, execution_time, usage)

            return RLMChatCompletion(
                root_model=self.backend_kwargs.get("model_name", "unknown")
                if self.backend_kwargs
                else "unknown",
                prompt=prompt,
                response=final_answer,
                usage_summary=usage,
                execution_time=execution_time,
            )

    def _save_to_history(
        self,
        prompt: str | dict[str, Any],
        answer: str,
        iterations: list[RLMIteration],
        execution_time: float,
        usage: Any,
    ):
        """Save a completed turn to the task history for multi-turn persistence."""
        # Extract task description from prompt
        if isinstance(prompt, str):
            task = prompt
        elif isinstance(prompt, dict):
            # Try to get a meaningful task description
            task = str(prompt.get("task", prompt.get("query", str(prompt))))
        else:
            task = str(prompt)

        # Truncate very long tasks for history (keep first 1000 chars)
        if len(task) > 1000:
            task = task[:1000] + "..."

        # Convert RLMIterations to lightweight IterationRecords
        iteration_records = [
            IterationRecord.from_rlm_iteration(it) for it in iterations
        ]

        entry = TaskHistoryEntry(
            turn_id=self.turn_count,
            task=task,
            answer=answer,
            iterations=iteration_records,
            execution_time=execution_time,
            usage_summary=usage,
        )
        self.task_history.append(entry)
        self.turn_count += 1

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
                ),
                turn_id=self.turn_count if self.persistent else None,
            )

        return response

    def _fallback_answer(self, message: str | dict[str, Any]) -> str:
        """
        Fallback behavior if the RLM is actually at max depth, and should be treated as an LM.
        """
        client: BaseLM = get_client(self.backend, self.backend_kwargs)
        response = client.completion(message)
        return response

    # =========================================================================
    # Multi-Turn Persistence API
    # =========================================================================

    def get_task_history(self) -> list[TaskHistoryEntry]:
        """
        Get the full task history for this persistent RLM session.

        Returns:
            List of TaskHistoryEntry objects, one per completed turn.
        """
        return self.task_history.copy()

    def get_history_summary(self) -> str:
        """
        Get a human-readable summary of the conversation history.

        Returns:
            Formatted string summarizing all previous turns.
        """
        if not self.task_history:
            return "No conversation history yet."

        lines = [f"=== Conversation History ({len(self.task_history)} turns) ===\n"]
        for entry in self.task_history:
            lines.append(entry.to_context_summary())
            lines.append("")  # Blank line between entries
        return "\n".join(lines)

    def clear_history(self):
        """
        Clear the conversation history and reset turn count.

        Useful for starting a fresh conversation while keeping the same RLM instance.
        """
        self.task_history = []
        self.turn_count = 0
        self.persistent_locals = {}

    def get_turn_count(self) -> int:
        """Get the current turn number (0-indexed, incremented after each completion)."""
        return self.turn_count

    def get_persistent_locals(self) -> dict[str, Any]:
        """
        Get the persistent REPL local variables (only meaningful if persist_repl_state=True).

        Returns:
            Dictionary of variable names to their values from previous turns.
        """
        return self.persistent_locals.copy()

    def set_persistent_local(self, name: str, value: Any):
        """
        Manually set a persistent REPL variable that will be available in subsequent turns.

        Args:
            name: Variable name
            value: Variable value
        """
        self.persistent_locals[name] = value
