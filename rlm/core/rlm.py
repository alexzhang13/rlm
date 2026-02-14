import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
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
from rlm.environments.local_repl import DirectREPL, SocketREPL
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
        on_request: Any | None = None,
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
            on_request: Optional callback for LMHandler requests (e.g. for Inngest integration).
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
        self.system_prompt = custom_system_prompt if custom_system_prompt else RLM_SYSTEM_PROMPT
        self.logger = logger
        self.verbose = VerbosePrinter(enabled=verbose)
        self.on_request = on_request

        # Persistence support
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
    def _spawn_completion_context(self, prompt: str | dict[str, Any], metadata: dict[str, Any] | None = None):
        """
        Spawn an LM handler and environment for a single completion call.
        """
        # Create client and wrap in handler
        client: BaseLM = get_client(self.backend, self.backend_kwargs)

        # Create other_backend_client if provided (for depth=1 routing)
        other_backend_client: BaseLM | None = None
        if self.other_backends and self.other_backend_kwargs:
            other_backend_client = get_client(self.other_backends[0], self.other_backend_kwargs[0])

        lm_handler = LMHandler(
            client, other_backend_client=other_backend_client, on_request=self.on_request
        )

        # Register other clients
        if self.other_backends and self.other_backend_kwargs:
            for backend, kwargs in zip(self.other_backends, self.other_backend_kwargs, strict=True):
                other_client: BaseLM = get_client(backend, kwargs)
                lm_handler.register_client(other_client.model_name, other_client)

        # Environment: reuse if persistent, otherwise create fresh
        if self.persistent and self._persistent_env is not None:
            environment = self._persistent_env
            if not self._env_supports_persistence(environment):
                raise RuntimeError(f"Persistent environment '{type(environment).__name__}' not supported.")
            
            if isinstance(environment, SocketREPL):
                lm_handler.start()
                environment.update_handler_address((lm_handler.host, lm_handler.port))
            
            environment.add_context(prompt)
        else:
            env_kwargs = self.environment_kwargs.copy()
            env_kwargs["context_payload"] = prompt
            env_kwargs["depth"] = self.depth + 1
            env_kwargs["metadata"] = metadata or {}

            # Strategy: If local, default to DirectREPL (no socket)
            # If backend is explicitly set to 'socket', use SocketREPL
            env_backend = env_kwargs.pop("env_backend", "direct")
            
            if self.environment_type == "local" and env_backend == "direct":
                environment = DirectREPL(lm_handler=lm_handler, **env_kwargs)
            else:
                lm_handler.start()
                env_kwargs["lm_handler_address"] = (lm_handler.host, lm_handler.port)
                environment: BaseEnv = get_environment(self.environment_type, env_kwargs)

            if self.persistent:
                self._persistent_env = environment

        try:
            yield lm_handler, environment
        finally:
            lm_handler.stop()
            if not self.persistent and hasattr(environment, "cleanup"):
                environment.cleanup()

    @asynccontextmanager
    async def _spawn_acompletion_context(self, prompt: str | dict[str, Any], metadata: dict[str, Any] | None = None):
        """
        Spawn an LM handler and environment for a single completion call (async version).
        """
        # Create client and wrap in handler
        client: BaseLM = get_client(self.backend, self.backend_kwargs)

        # Create other_backend_client if provided (for depth=1 routing)
        other_backend_client: BaseLM | None = None
        if self.other_backends and self.other_backend_kwargs:
            other_backend_client = get_client(self.other_backends[0], self.other_backend_kwargs[0])

        lm_handler = LMHandler(
            client, other_backend_client=other_backend_client, on_request=self.on_request
        )

        # Register other clients
        if self.other_backends and self.other_backend_kwargs:
            for backend, kwargs in zip(self.other_backends, self.other_backend_kwargs, strict=True):
                other_client: BaseLM = get_client(backend, kwargs)
                lm_handler.register_client(other_client.model_name, other_client)

        # Environment: reuse if persistent, otherwise create fresh
        if self.persistent and self._persistent_env is not None:
            environment = self._persistent_env
            if not self._env_supports_persistence(environment):
                raise RuntimeError(f"Persistent environment '{type(environment).__name__}' not supported.")
            
            if isinstance(environment, SocketREPL):
                lm_handler.start()
                environment.update_handler_address((lm_handler.host, lm_handler.port))
            
            environment.add_context(prompt)
        else:
            env_kwargs = self.environment_kwargs.copy()
            env_kwargs["context_payload"] = prompt
            env_kwargs["depth"] = self.depth + 1
            env_kwargs["metadata"] = metadata or {}

            env_backend = env_kwargs.pop("env_backend", "direct")
            
            if self.environment_type == "local" and env_backend == "direct":
                environment = DirectREPL(lm_handler=lm_handler, **env_kwargs)
            else:
                lm_handler.start()
                env_kwargs["lm_handler_address"] = (lm_handler.host, lm_handler.port)
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
        self,
        prompt: str | dict[str, Any],
        root_prompt: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RLMChatCompletion:
        """
        Recursive Language Model completion call.

        Args:
            prompt: Context for the model.
            root_prompt: Optional user-specified prompt for the root LM.
            metadata: Optional metadata for tracing/observability.
        Returns:
            RLMChatCompletion object.
        """
        time_start = time.perf_counter()

        if self.depth >= self.max_depth:
            return self._fallback_answer(prompt)

        with self._spawn_completion_context(prompt, metadata=metadata) as (lm_handler, environment):
            message_history = self._setup_prompt(prompt)
            code_executed = False  # Track whether any REPL code has run
            last_response_id = None
            next_delta: list[dict[str, Any]] = []

            for i in range(self.max_iterations):
                # Current prompt logic:
                # If we have a last_response_id, we only send the delta from the last turn.
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
                user_prompt = build_user_prompt(root_prompt, i, context_count, history_count)

                if last_response_id:
                    # Chained mode: delta is previous turn's REPL results + current user prompt.
                    current_prompt = next_delta + [user_prompt]
                else:
                    # Initial mode or fallback: send whole history.
                    current_prompt = message_history + [user_prompt]

                iteration: RLMIteration = self._completion_turn(
                    prompt=current_prompt,
                    lm_handler=lm_handler,
                    environment=environment,
                    previous_response_id=last_response_id,
                )

                # Update last_response_id if available (Responses API)
                if iteration.response_id:
                    last_response_id = iteration.response_id

                # Update code execution tracking
                if iteration.code_blocks:
                    code_executed = True

                # Check if RLM is done and has a final answer.
                final_answer = find_final_answer(iteration.response, environment=environment)
                iteration.final_answer = final_answer

                # Guard: reject FINAL_VAR if no REPL code has been executed yet.
                # Catches LLM echoing FINAL_VAR from prompt without running code.
                if final_answer is not None and not code_executed:
                    final_answer = None
                    iteration.final_answer = None

                # If logger is used, log the iteration.
                if self.logger:
                    self.logger.log(iteration)

                # Verbose output for this iteration
                self.verbose.print_iteration(iteration, i + 1)

                if final_answer is not None:
                    time_end = time.perf_counter()
                    usage = lm_handler.get_usage_summary()
                    self.verbose.print_final_answer(final_answer)
                    self.verbose.print_summary(i + 1, time_end - time_start, usage.to_dict())

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
                        response_id=last_response_id,
                    )

                # Format the iteration for the next prompt.
                new_messages = format_iteration(iteration)
                
                # If we are chaining, next_delta is everything BUT the first message (the assistant response)
                if last_response_id:
                    next_delta = new_messages[1:]
                
                # Update message history with the new messages.
                message_history.extend(new_messages)

            # Default behavior: we run out of iterations, provide one final answer
            time_end = time.perf_counter()
            final_answer = self._default_answer(message_history, lm_handler)
            usage = lm_handler.get_usage_summary()
            self.verbose.print_final_answer(final_answer)
            self.verbose.print_summary(self.max_iterations, time_end - time_start, usage.to_dict())

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

    async def acompletion(
        self,
        prompt: str | dict[str, Any],
        root_prompt: str | None = None,
        on_iteration: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RLMChatCompletion:
        """
        Async Recursive Language Model completion call.
        """
        time_start = time.perf_counter()

        # If we're at max depth, the RLM is an LM, so we fallback to the regular LM.
        if self.depth >= self.max_depth:
            return await self._afallback_answer(prompt)

        async with self._spawn_acompletion_context(prompt, metadata=metadata) as (lm_handler, environment):
            message_history = self._setup_prompt(prompt)
            code_executed = False  # Track whether any REPL code has run
            last_response_id = None
            next_delta: list[dict[str, Any]] = []

            for i in range(self.max_iterations):
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
                user_prompt = build_user_prompt(root_prompt, i, context_count, history_count)

                if last_response_id:
                    current_prompt = next_delta + [user_prompt]
                else:
                    current_prompt = message_history + [user_prompt]

                iteration: RLMIteration = await self._acompletion_turn(
                    prompt=current_prompt,
                    lm_handler=lm_handler,
                    environment=environment,
                    previous_response_id=last_response_id,
                )

                if iteration.response_id:
                    last_response_id = iteration.response_id

                # Update code execution tracking
                if iteration.code_blocks:
                    code_executed = True

                # Check if RLM is done and has a final answer.
                final_answer = find_final_answer(iteration.response, environment=environment)
                iteration.final_answer = final_answer

                # Guard: reject FINAL_VAR if no REPL code has been executed yet.
                if final_answer is not None and not code_executed:
                    final_answer = None
                    iteration.final_answer = None

                # If logger is used, log the iteration.
                if self.logger:
                    self.logger.log(iteration)

                # Callback for iteration (can be async)
                if on_iteration:
                    if asyncio.iscoroutinefunction(on_iteration):
                        await on_iteration(iteration, i + 1)
                    else:
                        on_iteration(iteration, i + 1)

                # Verbose output for this iteration
                self.verbose.print_iteration(iteration, i + 1)

                if final_answer is not None:
                    time_end = time.perf_counter()
                    usage = lm_handler.get_usage_summary()
                    self.verbose.print_final_answer(final_answer)
                    self.verbose.print_summary(i + 1, time_end - time_start, usage.to_dict())

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
                        response_id=last_response_id,
                    )

                # Format the iteration for the next prompt.
                new_messages = format_iteration(iteration)

                # If we are chaining, next_delta is everything BUT the first message (the assistant response)
                if last_response_id:
                    next_delta = new_messages[1:]

                # Update message history with the new messages.
                message_history.extend(new_messages)

            # Default behavior: we run out of iterations, provide one final answer
            time_end = time.perf_counter()
            final_answer = await self._adefault_answer(message_history, lm_handler)
            usage = lm_handler.get_usage_summary()
            self.verbose.print_final_answer(final_answer)
            self.verbose.print_summary(self.max_iterations, time_end - time_start, usage.to_dict())

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

    def _completion_turn(
        self,
        prompt: str | dict[str, Any],
        lm_handler: LMHandler,
        environment: BaseEnv,
        previous_response_id: str | None = None,
    ) -> RLMIteration:
        """
        Perform a single iteration of the RLM, including prompting the model
        and code execution + tool execution.
        """
        iter_start = time.perf_counter()
        chat_completion = lm_handler.completion_full(prompt, previous_response_id=previous_response_id)
        response = chat_completion.response
        thought = chat_completion.thought
        response_id = chat_completion.response_id

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
            thought=thought,
            response_id=response_id,
            iteration_time=iteration_time,
        )

    async def _acompletion_turn(
        self,
        prompt: str | dict[str, Any],
        lm_handler: LMHandler,
        environment: BaseEnv,
        previous_response_id: str | None = None,
    ) -> RLMIteration:
        """
        Perform a single iteration of the RLM (async version).
        """
        iter_start = time.perf_counter()
        chat_completion = await lm_handler.acompletion_full(
            prompt, previous_response_id=previous_response_id
        )
        response = chat_completion.response
        thought = chat_completion.thought
        response_id = chat_completion.response_id

        code_block_strs = find_code_blocks(response)
        code_blocks = []

        for code_block_str in code_block_strs:
            # environment.execute_code is currently sync, run in thread to avoid blocking loop
            code_result: REPLResult = await asyncio.to_thread(environment.execute_code, code_block_str)
            code_blocks.append(CodeBlock(code=code_block_str, result=code_result))

        iteration_time = time.perf_counter() - iter_start
        return RLMIteration(
            prompt=prompt,
            response=response,
            code_blocks=code_blocks,
            thought=thought,
            response_id=response_id,
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

    async def _adefault_answer(
        self, message_history: list[dict[str, Any]], lm_handler: LMHandler
    ) -> str:
        """
        Default behavior if the RLM runs out of iterations (async version).
        """
        current_prompt = message_history + [
            {
                "role": "assistant",
                "content": "Please provide a final answer to the user's question based on the information provided.",
            }
        ]
        response = await lm_handler.acompletion(current_prompt)

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

    async def _afallback_answer(self, message: str | dict[str, Any]) -> str:
        """
        Fallback behavior (async version).
        """
        client: BaseLM = get_client(self.backend, self.backend_kwargs)
        response = await client.acompletion(message)
        return response

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
