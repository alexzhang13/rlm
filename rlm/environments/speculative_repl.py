"""Experimental spec-ptc adapter. Only this module knows the library's lifecycle."""

from __future__ import annotations

import inspect
import json
import sys
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import CancelledError, ThreadPoolExecutor
from contextlib import contextmanager
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion, UsageSummary
from rlm.environments.base_env import extract_tool_value
from rlm.environments.local_execution import tool_execution
from rlm.environments.local_repl import _SAFE_BUILTINS, LocalREPL
from rlm.utils.prompts import format_rlm_query
from rlm.utils.usage import merge_usage_summaries

if TYPE_CHECKING:
    from spec_ptc import SpecSession, StreamTurn


def validate_spec_ptc(environment: str) -> None:
    if environment != "local":
        raise ValueError("experimental_spec_ptc currently requires environment='local'")
    if sys.version_info < (3, 12):
        raise ValueError("experimental_spec_ptc requires Python 3.12 or later")
    if find_spec("spec_ptc") is None:
        raise ImportError("Install speculative tool calling with: pip install 'rlms[spec-ptc]'")


class QueryResponse(str):
    """A string in the shadow; its completion is recorded only when really consumed."""

    calls: tuple[RLMChatCompletion, ...]

    def __new__(cls, text: str, calls: tuple[RLMChatCompletion, ...] = ()) -> QueryResponse:
        value = super().__new__(cls, text)
        value.calls = calls
        return value


class SpeculativeLocalREPL(LocalREPL):
    def __init__(
        self,
        *args: Any,
        spec_max_inflight: int = 16,
        spec_max_inflight_chars: int = 120_000,
        spec_max_dispatches_per_turn: int = 64,
        speculation_observer: Callable[[dict[str, int]], None] | None = None,
        **kwargs: Any,
    ) -> None:
        validate_spec_ptc("local")
        if spec_max_inflight < 1:
            raise ValueError("spec_max_inflight must be positive")
        self.spec_max_inflight = spec_max_inflight
        if spec_max_inflight_chars < 1:
            raise ValueError("spec_max_inflight_chars must be positive")
        self.spec_max_inflight_chars = spec_max_inflight_chars
        if spec_max_dispatches_per_turn < 1:
            raise ValueError("spec_max_dispatches_per_turn must be positive")
        self.spec_session: SpecSession | None = None
        self.claim_hooks: dict[str, Callable] = {}
        self.recursive_calls: list[RLMChatCompletion] = []
        self.calls_lock = threading.Lock()
        self.spec_max_dispatches_per_turn = spec_max_dispatches_per_turn
        self.speculation_observer = speculation_observer
        super().__init__(*args, **kwargs)
        self.recursive_slots = threading.BoundedSemaphore(self.max_concurrent_subcalls)

    def recursive_usage_summary(self) -> UsageSummary:
        with self.calls_lock:
            return merge_usage_summaries([call.usage_summary for call in self.recursive_calls])

    def update_handler_address(self, address: tuple[str, int]) -> None:
        super().update_handler_address(address)
        self.recursive_calls.clear()

    def run_llm(self, prompt: str, model: str | None = None) -> QueryResponse:
        if self.lm_handler_address is None:
            return QueryResponse("Error: No LM handler configured")
        try:
            response = send_lm_request(
                self.lm_handler_address, LMRequest(prompt=prompt, model=model, depth=self.depth)
            )
            if not response.success:
                return QueryResponse(f"Error: {response.error}")
            completion = response.chat_completion
            assert completion is not None
            return QueryResponse(completion.response, (completion,))
        except Exception as exc:
            return QueryResponse(f"Error: LM query failed - {exc}")

    def run_llm_batched(self, prompts: list[str], model: str | None = None) -> list[QueryResponse]:
        if self.lm_handler_address is None:
            return [QueryResponse("Error: No LM handler configured")] * len(prompts)
        try:
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
            )
            results = []
            for response in responses:
                if response.success:
                    completion = response.chat_completion
                    assert completion is not None
                    results.append(QueryResponse(completion.response, (completion,)))
                else:
                    results.append(QueryResponse(f"Error: {response.error}"))
            return results
        except Exception as exc:
            return [QueryResponse(f"Error: LM query failed - {exc}")] * len(prompts)

    def run_rlm(
        self, instruction: str, context: str | list | dict, model: str | None = None
    ) -> QueryResponse:
        if self.subcall_fn is None:
            return self.run_llm(format_rlm_query(instruction, context), model)
        try:
            with self.recursive_slots:
                completion = self.subcall_fn(instruction, context, model)
            with self.calls_lock:
                self.recursive_calls.append(completion)
            return QueryResponse(completion.response, (completion,))
        except Exception as exc:
            return QueryResponse(f"Error: RLM query failed - {exc}")

    def run_rlm_batched(
        self, queries: list[tuple[str, str | list | dict]], model: str | None = None
    ) -> list[QueryResponse]:
        if not queries:
            return []
        with ThreadPoolExecutor(
            max_workers=min(len(queries), self.max_concurrent_subcalls)
        ) as pool:
            futures = [pool.submit(self.run_rlm, *query, model) for query in queries]
            return [future.result() for future in futures]

    def record_response(self, response: QueryResponse | list[QueryResponse]) -> str | list[str]:
        if isinstance(response, list):
            for item in response:
                self._pending_llm_calls.extend(item.calls)
            return [str(item) for item in response]
        self._pending_llm_calls.extend(response.calls)
        return str(response)

    @contextmanager
    def speculation_turn(self) -> Iterator[StreamTurn]:
        from spec_ptc import SpecSession, ToolRegistry

        registry = ToolRegistry()
        # Existing functions and custom tools must never run in the shadow.
        namespace = {**self.globals, **self.locals}
        for name, value in namespace.items():
            if callable(value):
                registry.register(name, value)
        recursive_is_pure = not any(
            callable(extract_tool_value(tool)) for tool in self.custom_sub_tools.values()
        )
        functions = {
            "llm_query": self.run_llm,
            "llm_query_batched": self.run_llm_batched,
            "rlm_query": self.run_rlm,
            "rlm_query_batched": self.run_rlm_batched,
        }
        for name, function in functions.items():
            signature = inspect.signature(function)

            def key(args, kwargs, signature=signature):
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                # Context dict order is observable in Python; the library's
                # default sort_keys hash would erase it.
                return json.dumps(bound.arguments, default=repr)

            def speculate(*args, _spec, function=function, **kwargs):
                # The library's character-pressure gate can delay a worker after
                # eviction. Do not start an API call that is already discarded.
                if _spec.state == "evicted":
                    raise CancelledError("speculation evicted before tool execution")
                return function(*args, **kwargs)

            speculate.wants_spec = True
            registry.register(
                name,
                function,
                spec_fn=speculate,
                pure=True,
                speculatable=not name.startswith("rlm_") or recursive_is_pure,
                # Recursive batches contain argument pairs, not single prompts.
                batched=name == "llm_query_batched",
                key_fn=key,
            )
        session = SpecSession(
            registry,
            max_inflight=self.spec_max_inflight,
            max_dispatches_per_turn=self.spec_max_dispatches_per_turn,
        )
        session.launcher.budget.max_inflight_chars = self.spec_max_inflight_chars
        self.spec_session = session
        hooks = session.real_hooks()
        for name in functions:

            def claim(*args, hook=hooks[name], **kwargs):
                with tool_execution():
                    response = hook(*args, **kwargs)
                return self.record_response(response)

            self.claim_hooks[name] = claim
        self.globals.update(self.claim_hooks)
        namespace = {
            name: value
            for name, value in namespace.items()
            if not callable(value) and not name.startswith("__")
        }
        namespace["answer"] = dict(self.locals["answer"])
        turn = session.begin_stream_turn(namespace, _SAFE_BUILTINS)
        try:
            yield turn
        finally:
            # Stop shadow dispatches before taking the final work/accounting snapshot.
            turn.shadow.abort("real turn finished")
            turn.shadow.finish()
            turn.shadow.join()
            session.end_turn()
            # Eviction cannot cancel synchronous LM calls. Drain them before the
            # LM handler goes away and before reporting usage, including wasted calls.
            for speculation in session.store.all:
                speculation.done.wait()
            metrics = {
                kind: sum(event.kind == kind for event in session.bus.history)
                for kind in ("dispatch", "claim_hit", "claim_miss", "evict")
            }
            session.close()
            self.spec_session = None
            self.claim_hooks.clear()
            self._restore_scaffold()
            if self.speculation_observer is not None:
                self.speculation_observer(metrics)

    def execute_code(self, code: str) -> REPLResult:
        self.globals.update(self.claim_hooks)
        result = super().execute_code(code)
        self.globals.update(self.claim_hooks)
        return result
