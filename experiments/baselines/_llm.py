"""Thin async-to-sync Sonnet caller for baselines — same backend as the RLM
runs (Agent SDK + CLAUDE_CODE_OAUTH_TOKEN) so cost/accuracy are comparable.

Re-uses the dedicated event-loop thread from rlm/clients/agent_sdk.py, so
all 8 methods share a single subprocess pool and cache.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from rlm.clients.agent_sdk import _LoopThread


@dataclass
class LLMCall:
    text: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float


async def _acall(user: str, system: str | None, model: str, max_turns: int) -> LLMCall:
    import os, sys
    opts_kwargs: dict[str, Any] = {
        "allowed_tools": [],
        "max_turns": max_turns,
        "model": model,
        # CLI defaults max_buffer_size to 1MB; long prompts (BrowseComp+,
        # long S-NIAH tiers) blow past that. 16MB is enough for 150K
        # token user payloads.
        "max_buffer_size": 16 * 1024 * 1024,
    }
    if system is not None:
        opts_kwargs["system_prompt"] = system
    if os.environ.get("RLM_AGENT_SDK_DEBUG"):
        opts_kwargs["stderr"] = lambda line: print(f"[cli-stderr] {line}", file=sys.stderr)
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

    in_tok = out_tok = cr = cc = 0
    cost = 0.0
    if result and result.model_usage:
        for _, u in result.model_usage.items():
            in_tok += int(u.get("inputTokens") or 0)
            out_tok += int(u.get("outputTokens") or 0)
            cr += int(u.get("cacheReadInputTokens") or 0)
            cc += int(u.get("cacheCreationInputTokens") or 0)
            cost += float(u.get("costUSD") or 0.0)
    return LLMCall(text, in_tok, out_tok, cr, cc, cost)


def sonnet_call(
    user: str,
    system: str | None = None,
    model: str = "claude-sonnet-4-6",
    max_turns: int = 5,
    timeout: float | None = 300.0,
) -> LLMCall:
    """Sync wrapper — runs the async call on the shared loop thread."""
    return _LoopThread.get().run(
        _acall(user=user, system=system, model=model, max_turns=max_turns),
        timeout=timeout,
    )
