"""Claude Agent SDK backend — OAuth via CLAUDE_CODE_OAUTH_TOKEN.

Runs the async SDK `query()` on a dedicated background event loop so the
rest of RLM (which is synchronous) can call `completion()` without sprinkling
`asyncio.run` through the scaffold.

Notes on accounting:
- The Agent SDK wraps each call in a Claude Code default system preamble (~16K
  tokens). This is constant across all arms, so relative comparisons are still
  valid. Absolute costs are higher than raw-API baselines; we report Sonnet-only
  cost in Table 1 and footnote the overhead.
- The SDK also spins up a background Haiku orchestrator (~340 in / 10 out per
  call, ≈$0.0004). We record but exclude Haiku from the headline Sonnet cost.
- The SDK auto-caches the system preamble. We don't need an extra cache_control
  patch for the system prompt.
"""

from __future__ import annotations

import asyncio
import os as _os
import sys as _sys
import threading
from collections import defaultdict
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary


class _LoopThread:
    """Singleton background thread running a single asyncio loop.

    The Agent SDK is async-only; RLM's main path is synchronous, and so is
    RLM's `acompletion` caller (it awaits a single coroutine). We can serve
    both by running all SDK queries on this dedicated loop.
    """

    _lock = threading.Lock()
    _instance: "_LoopThread | None" = None

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, daemon=True, name="agent-sdk-loop")
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    @classmethod
    def get(cls) -> "_LoopThread":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def run(self, coro, timeout: float | None):
        fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return fut.result(timeout=timeout)


class AgentSDKClient(BaseLM):
    """LM client backed by claude_agent_sdk.query() (OAuth-authenticated)."""

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-6",
        max_tokens: int = 32768,
        primary_model: str = "claude-sonnet-4-6",
        max_turns: int = 5,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.max_tokens = max_tokens
        # Which model's usage counts as "primary" in cost summaries. The SDK
        # also invokes a background Haiku orchestrator; we still record its
        # usage but this is the one Table 1 reports.
        self.primary_model = primary_model
        # Agent SDK "turns" differ from RLM iterations — one of our logical
        # completions can take 2+ internal turns when the model emits an
        # intermediate thinking/tool-probe step. 5 is enough in practice; we
        # don't want tools executed (allowed_tools=[]) but we do want the
        # completion to reach end_turn.
        self.max_turns = max_turns

        # Per-model usage tracking (same shape the AnthropicClient uses).
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_cache_creation_tokens: dict[str, int] = defaultdict(int)
        self.model_cache_read_tokens: dict[str, int] = defaultdict(int)
        self.model_cost: dict[str, float] = defaultdict(float)

        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    # ------------------------------------------------------------------
    # Prompt prep — the SDK takes a single system string and a single user
    # string. RLM sometimes passes a chat-style list; collapse it the same
    # way the Anthropic client does.
    # ------------------------------------------------------------------
    def _prepare(self, prompt: str | list[dict[str, Any]]) -> tuple[str, str | None]:
        if isinstance(prompt, str):
            return prompt, None
        if isinstance(prompt, list):
            system = None
            user_parts: list[str] = []
            for msg in prompt:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "system":
                    # If multiple system messages, concatenate — the SDK only
                    # takes one.
                    system = (system + "\n\n" + content) if system else content
                else:
                    user_parts.append(str(content))
            user = "\n\n".join(user_parts)
            return user, system
        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    # ------------------------------------------------------------------
    # Core async call — one completion. Returns (text, ResultMessage).
    # ------------------------------------------------------------------
    async def _acall(
        self, prompt: str | list[dict[str, Any]], model: str | None
    ) -> tuple[str, ResultMessage | None]:
        user, system = self._prepare(prompt)
        model = model or self.model_name

        opts_kwargs: dict[str, Any] = {
            "allowed_tools": [],
            "max_turns": self.max_turns,
            "model": model,
            # CLI defaults max_buffer_size to 1MB; long prompts blow past
            # that silently (subprocess exits with code 1, no stderr). Raise
            # to 16MB so ~150K-token user payloads go through.
            "max_buffer_size": 16 * 1024 * 1024,
        }
        if system is not None:
            opts_kwargs["system_prompt"] = system

        # RLM_AGENT_SDK_DEBUG=1 → print prompt metadata + CLI stderr to stderr.
        if _os.environ.get("RLM_AGENT_SDK_DEBUG"):
            print(
                f"[agent_sdk] user_len={len(user)} system_len={len(system or '')} "
                f"max_turns={self.max_turns} model={model}",
                file=_sys.stderr,
            )
            print(f"[agent_sdk] user[:300]={user[:300]!r}", file=_sys.stderr)
            opts_kwargs["stderr"] = lambda line: print(
                f"[cli-stderr] {line}", file=_sys.stderr
            )

        opts = ClaudeAgentOptions(**opts_kwargs)

        text = ""
        result: ResultMessage | None = None
        async for msg in query(prompt=user, options=opts):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text += block.text
            elif isinstance(msg, ResultMessage):
                result = msg
        return text, result

    # ------------------------------------------------------------------
    # Sync + async public API
    # ------------------------------------------------------------------
    def completion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        text, result = _LoopThread.get().run(self._acall(prompt, model), timeout=self.timeout)
        self._track(result, model or self.model_name)
        return text

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        # If already inside an event loop, run on our dedicated thread anyway
        # — the SDK spawns subprocesses that don't like being entered from an
        # arbitrary loop context.
        loop = asyncio.get_event_loop()
        fut = asyncio.run_coroutine_threadsafe(
            self._acall(prompt, model), _LoopThread.get().loop
        )
        text, result = await asyncio.wrap_future(fut, loop=loop)
        self._track(result, model or self.model_name)
        return text

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------
    def _track(self, result: ResultMessage | None, primary_model: str) -> None:
        if result is None:
            return
        model_usage = result.model_usage or {}
        for model_name, use in model_usage.items():
            in_tok = int(use.get("inputTokens") or 0)
            out_tok = int(use.get("outputTokens") or 0)
            cr_read = int(use.get("cacheReadInputTokens") or 0)
            cr_create = int(use.get("cacheCreationInputTokens") or 0)
            cost = float(use.get("costUSD") or 0.0)

            self.model_call_counts[model_name] += 1
            self.model_input_tokens[model_name] += in_tok
            self.model_output_tokens[model_name] += out_tok
            self.model_cache_read_tokens[model_name] += cr_read
            self.model_cache_creation_tokens[model_name] += cr_create
            self.model_cost[model_name] += cost

        # Last-call accounting reflects primary model (for LMHandler's token
        # reporting path). If primary not in model_usage, sum across whatever
        # was reported.
        if primary_model in model_usage:
            u = model_usage[primary_model]
            self.last_prompt_tokens = int(u.get("inputTokens") or 0) + int(
                u.get("cacheReadInputTokens") or 0
            ) + int(u.get("cacheCreationInputTokens") or 0)
            self.last_completion_tokens = int(u.get("outputTokens") or 0)
        else:
            self.last_prompt_tokens = sum(
                int(u.get("inputTokens") or 0)
                + int(u.get("cacheReadInputTokens") or 0)
                + int(u.get("cacheCreationInputTokens") or 0)
                for u in model_usage.values()
            )
            self.last_completion_tokens = sum(
                int(u.get("outputTokens") or 0) for u in model_usage.values()
            )

    def get_usage_summary(self) -> UsageSummary:
        summaries = {}
        for model in self.model_call_counts:
            summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model]
                + self.model_cache_read_tokens[model]
                + self.model_cache_creation_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
                total_cost=self.model_cost[model],
            )
        return UsageSummary(model_usage_summaries=summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
        )
