import time
from contextlib import contextmanager
from typing import Any

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
    RLM_SYSTEM_PROMPT_COMPLETION,
    RLM_SYSTEM_PROMPT_SESSION,
    QueryMetadata,
    build_rlm_system_prompt,
    build_user_prompt,
)
from rlm.utils.rlm_utils import filter_sensitive_keys
from rlm.utils.trace_markdown import build_trace_markdown


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
            persistent: If True, reuse the environment across completion() calls for multi-turn conversations.
        """
        # Store config for spawning per-completion
        self.backend = backend
        self.backend_kwargs = backend_kwargs or {}
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
        if custom_system_prompt:
            self.system_prompt_completion = custom_system_prompt
            self.system_prompt_session = custom_system_prompt
        else:
            self.system_prompt_completion = RLM_SYSTEM_PROMPT_COMPLETION
            self.system_prompt_session = RLM_SYSTEM_PROMPT_SESSION
        self.system_prompt = self.system_prompt_session
        self.logger = logger
        self.verbose = VerbosePrinter(enabled=verbose)
        self.trace_markdown_history = ""
        self.persistent = persistent
        self._persistent_env: SupportsPersistence | None = None

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
    def _spawn_completion_context(
        self,
        prompt: str | dict[str, Any],
        *,
        session_mode: bool,
    ):
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
                    f"implement required methods (update_handler_address, add_context, "
                    f"get_context_count, add_history, get_history_count, set_completion_context). "
                    f"This should have been caught at initialization."
                )
            environment.update_handler_address((lm_handler.host, lm_handler.port))
            if session_mode:
                environment.add_context(prompt)
            else:
                environment.set_completion_context(prompt)
        else:
            env_kwargs = self.environment_kwargs.copy()
            env_kwargs["lm_handler_address"] = (lm_handler.host, lm_handler.port)
            env_kwargs["context_payload"] = prompt
            env_kwargs["context_scope"] = "session" if session_mode else "completion"
            env_kwargs["depth"] = self.depth + 1  # Environment depth is RLM depth + 1
            environment: BaseEnv = get_environment(self.environment_type, env_kwargs)
            if self.persistent:
                self._persistent_env = environment

        try:
            yield lm_handler, environment
        finally:
            lm_handler.stop()
            if not self.persistent and hasattr(environment, "cleanup"):
                environment.cleanup()

    def _setup_prompt(
        self, prompt: str | dict[str, Any], *, session_mode: bool = False
    ) -> list[dict[str, Any]]:
        """
        Setup the system prompt for the RLM. Also include metadata about the prompt and build
        up the initial message history.
        """
        metadata = QueryMetadata(prompt)
        system_prompt = (
            self.system_prompt_session if session_mode else self.system_prompt_completion
        )
        message_history = build_rlm_system_prompt(
            system_prompt=system_prompt, query_metadata=metadata
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
        self.trace_markdown_history = ""
        completion, _, trace_history = self._run_completion(
            prompt=prompt,
            root_prompt=root_prompt,
            message_history=None,
            trace_history="",
            session_mode=False,
        )
        self.trace_markdown_history = trace_history
        return completion

    def _run_completion(
        self,
        *,
        prompt: str | dict[str, Any],
        root_prompt: str | None,
        message_history: list[dict[str, Any]] | None,
        trace_history: str,
        session_mode: bool,
    ) -> tuple[RLMChatCompletion, list[dict[str, Any]], str]:
        time_start = time.perf_counter()

        run_context_entry = None
        if self.logger:
            run_context_entry = self.logger.log_run_context(
                prompt=prompt,
                root_prompt=root_prompt,
                environment_type=self.environment_type,
                environment_kwargs=filter_sensitive_keys(self.environment_kwargs),
                session_mode=session_mode,
            )

        run_context = run_context_entry or {
            "prompt": prompt,
            "root_prompt": root_prompt,
            "environment_type": self.environment_type,
            "environment_kwargs": filter_sensitive_keys(self.environment_kwargs),
            "session_mode": session_mode,
        }

        # If we're at max depth, the RLM is an LM, so we fallback to the regular LM.
        if self.depth >= self.max_depth:
            client: BaseLM = get_client(self.backend, self.backend_kwargs)
            fallback_start = time.perf_counter()
            response = client.completion(prompt)
            fallback_end = time.perf_counter()
            usage = client.get_last_usage()
            run_trace = build_trace_markdown(run_context, [])
            trace_history = append_trace_history(trace_history, run_trace)
            completion = RLMChatCompletion(
                root_model=self.backend_kwargs.get("model_name", "unknown")
                if self.backend_kwargs
                else "unknown",
                prompt=prompt,
                response=response,
                usage_summary=usage,
                execution_time=fallback_end - fallback_start,
                trace_markdown=trace_history,
            )
            if message_history is None:
                message_history = self._setup_prompt(prompt, session_mode=session_mode)
            return completion, message_history, trace_history

        with self._spawn_completion_context(
            prompt,
            session_mode=session_mode,
        ) as (lm_handler, environment):
            if message_history is None:
                message_history = self._setup_prompt(prompt, session_mode=session_mode)
            iterations: list[RLMIteration] = []

            for i in range(self.max_iterations):
                # Current prompt = message history + additional prompt suffix
                if session_mode and isinstance(environment, SupportsPersistence):
                    context_count = environment.get_context_count()
                    history_count = environment.get_history_count()
                else:
                    context_count = 1
                    history_count = 0
                current_prompt = message_history + [
                    build_user_prompt(
                        root_prompt, i, context_count, history_count, session_mode=session_mode
                    )
                ]

                iteration: RLMIteration = self._completion_turn(
                    prompt=current_prompt,
                    lm_handler=lm_handler,
                    environment=environment,
                    iteration_index=i + 1,
                )
                iterations.append(iteration)

                # Check if RLM is done and has a final answer.
                raw_final_answer = find_final_answer(iteration.response, environment=environment)
                final_answer = raw_final_answer or None
                iteration.final_answer = final_answer

                # If logger is used, log the iteration.
                if self.logger:
                    self.logger.log(iteration)

                # Verbose output for this iteration
                self.verbose.print_iteration(iteration, i + 1)

                if final_answer:
                    time_end = time.perf_counter()
                    usage = lm_handler.get_usage_summary()
                    self.verbose.print_final_answer(final_answer)
                    self.verbose.print_summary(i + 1, time_end - time_start, usage.to_dict())
                    # Store message history in persistent environment
                    if (
                        session_mode
                        and self.persistent
                        and isinstance(environment, SupportsPersistence)
                    ):
                        environment.add_history(message_history)

                    run_trace = build_trace_markdown(run_context, iterations)
                    trace_history = append_trace_history(trace_history, run_trace)
                    completion = RLMChatCompletion(
                        root_model=self.backend_kwargs.get("model_name", "unknown")
                        if self.backend_kwargs
                        else "unknown",
                        prompt=prompt,
                        response=final_answer,
                        usage_summary=usage,
                        execution_time=time_end - time_start,
                        trace_markdown=trace_history,
                    )
                    return completion, message_history, trace_history

                # Format the iteration for the next prompt.
                new_messages = format_iteration(iteration)

                # Update message history with the new messages.
                message_history.extend(new_messages)

            # Default behavior: we run out of iterations, provide one final answer
            time_end = time.perf_counter()
            default_iteration = self._default_answer(message_history, lm_handler)
            iterations.append(default_iteration)
            message_history.extend(format_iteration(default_iteration))
            final_answer = default_iteration.final_answer or ""
            usage = lm_handler.get_usage_summary()
            self.verbose.print_final_answer(final_answer)
            self.verbose.print_summary(self.max_iterations, time_end - time_start, usage.to_dict())
            # Store message history in persistent environment
            if session_mode and self.persistent and isinstance(environment, SupportsPersistence):
                environment.add_history(message_history)

            run_trace = build_trace_markdown(run_context, iterations)
            trace_history = append_trace_history(trace_history, run_trace)
            completion = RLMChatCompletion(
                root_model=self.backend_kwargs.get("model_name", "unknown")
                if self.backend_kwargs
                else "unknown",
                prompt=prompt,
                response=final_answer,
                usage_summary=usage,
                execution_time=time_end - time_start,
                trace_markdown=trace_history,
            )
            return completion, message_history, trace_history

    def _completion_turn(
        self,
        prompt: str | dict[str, Any],
        lm_handler: LMHandler,
        environment: BaseEnv,
        iteration_index: int,
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

    def _default_answer(
        self, message_history: list[dict[str, Any]], lm_handler: LMHandler
    ) -> RLMIteration:
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
        iteration = RLMIteration(
            prompt=current_prompt,
            response=response,
            final_answer=response,
            code_blocks=[],
        )

        if self.logger:
            self.logger.log(iteration)

        return iteration

    def start_session(self) -> "RLMSession":
        return RLMSession(self)


    def _validate_persistent_environment_support(self) -> None:
        """
        Validate that the configured environment type supports persistent mode.

        Persistent mode requires environments to implement:
        - update_handler_address(address): Update LM handler address between calls
        - add_context(payload, index): Add new session context for multi-turn conversations
        - get_context_count(): Return the number of loaded session contexts
        - add_history(message_history): Add session history entries
        - get_history_count(): Return the number of stored session histories
        - set_completion_context(payload): Set completion_context for completion calls

        Currently 'local' (LocalREPL) and 'jupyter' (JupyterREPL) support these methods.

        Raises:
            ValueError: If the environment type does not support persistent mode.
        """
        # Known environments that support persistence
        persistent_supported_environments = {"local", "jupyter"}

        if self.environment_type not in persistent_supported_environments:
            raise ValueError(
                f"persistent=True is not supported for environment type '{self.environment_type}'. "
                f"Persistent mode requires environments that implement update_handler_address(), "
                f"add_context(), get_context_count(), add_history(), get_history_count(), "
                f"and set_completion_context(). "
                f"Supported environments: {sorted(persistent_supported_environments)}"
            )

    @staticmethod
    def _env_supports_persistence(env: BaseEnv) -> bool:
        """Check if an environment instance supports persistent mode methods."""
        return isinstance(env, SupportsPersistence)

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


def append_trace_history(existing: str, new_trace: str) -> str:
    if not existing:
        return new_trace
    return f"{existing}\n\n---\n\n{new_trace}"


class RLMSession:
    def __init__(self, rlm: RLM):
        self.rlm = rlm
        self.message_history: list[dict[str, Any]] | None = None
        self.trace_markdown_history = ""

    def reset(self) -> None:
        self.message_history = None
        self.trace_markdown_history = ""

    def chat(
        self, prompt: str | dict[str, Any], root_prompt: str | None = None
    ) -> RLMChatCompletion:
        prompt_payload = prompt
        if self.message_history is None:
            self.message_history = self.rlm._setup_prompt(prompt_payload, session_mode=True)
        else:
            metadata_prompt = build_rlm_system_prompt(
                system_prompt=self.rlm.system_prompt_session,
                query_metadata=QueryMetadata(prompt_payload),
            )[1]
            self.message_history.append(metadata_prompt)

        completion, message_history, trace_history = self.rlm._run_completion(
            prompt=prompt_payload,
            root_prompt=root_prompt,
            message_history=self.message_history,
            trace_history=self.trace_markdown_history,
            session_mode=True,
        )
        self.message_history = message_history
        self.trace_markdown_history = trace_history
        return completion
