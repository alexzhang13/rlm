import asyncio
import os
import shutil
import subprocess
from collections import defaultdict
from typing import Any

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

# Characters-per-token estimate (CLI doesn't return usage data)
_CHARS_PER_TOKEN = 4


class ClaudeCodeCLI(BaseLM):
    """
    LM Client that shells out to the ``claude`` CLI (``claude --print``)
    instead of calling an HTTP API.

    Designed for use inside cc-dirigent's RLM integration so that the full
    RLM REPL loop can run without any API keys — Claude Code handles auth.

    Model names use CLI aliases: ``sonnet``, ``opus``, ``haiku``.
    """

    def __init__(
        self,
        model_name: str = "sonnet",
        max_budget_usd: float | None = None,
        permission_mode: str = "bypassPermissions",
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.model_name = model_name
        self.max_budget_usd = max_budget_usd
        self.permission_mode = permission_mode

        # Verify ``claude`` is on PATH
        if not shutil.which("claude"):
            raise FileNotFoundError(
                "claude CLI not found on PATH. Install Claude Code first: "
                "https://docs.anthropic.com/en/docs/claude-code"
            )

        # Per-model usage tracking (estimated)
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)

        self.last_prompt_tokens: int = 0
        self.last_completion_tokens: int = 0

        # Build a clean env that allows nested claude invocations.
        # CLAUDECODE env var blocks nested sessions — strip it.
        self._env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    # ── helpers ────────────────────────────────────────────

    def _build_cmd(self, system: str | None, model: str | None) -> list[str]:
        """Build the ``claude`` CLI argument list."""
        model = model or self.model_name
        cmd = [
            "claude",
            "--print",
            "--model", model,
            "--no-session-persistence",
            "--permission-mode", self.permission_mode,
        ]
        if system:
            cmd.extend(["--system-prompt", system])
        if self.max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(self.max_budget_usd)])
        return cmd

    def _prepare_prompt(
        self, prompt: str | list[dict[str, Any]]
    ) -> tuple[str, str | None]:
        """
        Convert a prompt (string or message list) into ``(user_text, system)``
        for piping to ``claude --print``.

        Mirrors ``AnthropicClient._prepare_messages`` — system messages are
        extracted and passed via ``--system-prompt``.
        """
        system: str | None = None

        if isinstance(prompt, str):
            return prompt, None

        if isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
            parts: list[str] = []
            for msg in prompt:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    system = content
                else:
                    parts.append(str(content))
            return "\n\n".join(parts), system

        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN

    def _track_usage(self, prompt_text: str, response_text: str, model: str) -> None:
        input_tokens = self._estimate_tokens(prompt_text)
        output_tokens = self._estimate_tokens(response_text)

        self.model_call_counts[model] += 1
        self.model_input_tokens[model] += input_tokens
        self.model_output_tokens[model] += output_tokens

        self.last_prompt_tokens = input_tokens
        self.last_completion_tokens = output_tokens

    # ── BaseLM interface ──────────────────────────────────

    def completion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        user_text, system = self._prepare_prompt(prompt)
        model = model or self.model_name
        cmd = self._build_cmd(system, model)

        # Uses subprocess.run with explicit argument list (no shell=True)
        # to prevent command injection. User input is passed via stdin only.
        result = subprocess.run(
            cmd,
            input=user_text,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            env=self._env,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"claude CLI exited with code {result.returncode}: {result.stderr.strip()}"
            )

        response = result.stdout.strip()
        self._track_usage(user_text, response, model)
        return response

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        user_text, system = self._prepare_prompt(prompt)
        model = model or self.model_name
        cmd = self._build_cmd(system, model)

        # Uses asyncio.create_subprocess_exec (not _shell) with explicit
        # argument list to prevent command injection. Input via stdin only.
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=user_text.encode()),
            timeout=self.timeout,
        )

        if proc.returncode != 0:
            raise RuntimeError(
                f"claude CLI exited with code {proc.returncode}: {stderr.decode().strip()}"
            )

        response = stdout.decode().strip()
        self._track_usage(user_text, response, model)
        return response

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
        )
