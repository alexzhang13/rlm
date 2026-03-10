"""Tests for ClaudeCodeCLI client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rlm.core.types import ModelUsageSummary, UsageSummary


@pytest.fixture
def cli_client():
    """Create a ClaudeCodeCLI instance with mocked shutil.which."""
    with patch("rlm.clients.claude_cli.shutil.which", return_value="/usr/local/bin/claude"):
        from rlm.clients.claude_cli import ClaudeCodeCLI

        return ClaudeCodeCLI(model_name="sonnet")


@pytest.fixture
def cli_client_custom():
    """Create a ClaudeCodeCLI with custom options."""
    with patch("rlm.clients.claude_cli.shutil.which", return_value="/usr/local/bin/claude"):
        from rlm.clients.claude_cli import ClaudeCodeCLI

        return ClaudeCodeCLI(
            model_name="opus",
            max_budget_usd=5.0,
            permission_mode="plan",
        )


class TestInit:
    def test_defaults(self, cli_client):
        assert cli_client.model_name == "sonnet"
        assert cli_client.max_budget_usd is None
        assert cli_client.permission_mode == "bypassPermissions"

    def test_custom_options(self, cli_client_custom):
        assert cli_client_custom.model_name == "opus"
        assert cli_client_custom.max_budget_usd == 5.0
        assert cli_client_custom.permission_mode == "plan"

    def test_missing_cli_raises(self):
        with patch("rlm.clients.claude_cli.shutil.which", return_value=None):
            from rlm.clients.claude_cli import ClaudeCodeCLI

            with pytest.raises(FileNotFoundError, match="claude CLI not found"):
                ClaudeCodeCLI()

    def test_env_strips_claudecode(self, cli_client):
        assert "CLAUDECODE" not in cli_client._env


class TestBuildCmd:
    def test_basic_cmd(self, cli_client):
        cmd = cli_client._build_cmd(system=None, model="sonnet")
        assert cmd == [
            "claude", "--print",
            "--model", "sonnet",
            "--no-session-persistence",
            "--permission-mode", "bypassPermissions",
        ]

    def test_with_system_prompt(self, cli_client):
        cmd = cli_client._build_cmd(system="You are helpful.", model="sonnet")
        assert "--system-prompt" in cmd
        idx = cmd.index("--system-prompt")
        assert cmd[idx + 1] == "You are helpful."

    def test_with_budget(self, cli_client_custom):
        cmd = cli_client_custom._build_cmd(system=None, model="opus")
        assert "--max-budget-usd" in cmd
        idx = cmd.index("--max-budget-usd")
        assert cmd[idx + 1] == "5.0"

    def test_model_override(self, cli_client):
        cmd = cli_client._build_cmd(system=None, model="haiku")
        assert cmd[cmd.index("--model") + 1] == "haiku"


class TestPreparePrompt:
    def test_string_prompt(self, cli_client):
        text, system = cli_client._prepare_prompt("Hello")
        assert text == "Hello"
        assert system is None

    def test_message_list_no_system(self, cli_client):
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        text, system = cli_client._prepare_prompt(messages)
        assert text == "Hi\n\nHello"
        assert system is None

    def test_message_list_with_system(self, cli_client):
        messages = [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hi"},
        ]
        text, system = cli_client._prepare_prompt(messages)
        assert text == "Hi"
        assert system == "Be concise."

    def test_invalid_prompt_type(self, cli_client):
        with pytest.raises(ValueError, match="Invalid prompt type"):
            cli_client._prepare_prompt(12345)


class TestEstimateTokens:
    def test_basic_estimate(self):
        from rlm.clients.claude_cli import ClaudeCodeCLI

        assert ClaudeCodeCLI._estimate_tokens("abcd") == 1  # 4 chars / 4
        assert ClaudeCodeCLI._estimate_tokens("abcde") == 2  # 5 chars -> ceil(5/4)
        assert ClaudeCodeCLI._estimate_tokens("") == 0

    def test_longer_text(self):
        from rlm.clients.claude_cli import ClaudeCodeCLI

        text = "a" * 100
        assert ClaudeCodeCLI._estimate_tokens(text) == 25


class TestCompletion:
    def test_successful_completion(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello, world!\n"
        mock_result.stderr = ""

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result) as mock_run:
            result = cli_client.completion("Say hello")

        assert result == "Hello, world!"
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["input"] == "Say hello"
        assert call_kwargs["capture_output"] is True
        assert call_kwargs["text"] is True
        assert call_kwargs["timeout"] == cli_client.timeout

    def test_completion_with_model_override(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "response"
        mock_result.stderr = ""

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result) as mock_run:
            cli_client.completion("test", model="opus")

        cmd = mock_run.call_args[0][0]
        assert cmd[cmd.index("--model") + 1] == "opus"

    def test_completion_nonzero_exit(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: something went wrong"

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="claude CLI exited with code 1"):
                cli_client.completion("test")

    def test_completion_tracks_usage(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "response text"
        mock_result.stderr = ""

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result):
            cli_client.completion("input text")

        assert cli_client.model_call_counts["sonnet"] == 1
        assert cli_client.model_input_tokens["sonnet"] > 0
        assert cli_client.model_output_tokens["sonnet"] > 0

    def test_completion_with_message_list(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        messages = [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": "Hi"},
        ]

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result) as mock_run:
            cli_client.completion(messages)

        cmd = mock_run.call_args[0][0]
        assert "--system-prompt" in cmd
        assert mock_run.call_args[1]["input"] == "Hi"


class TestAcompletion:
    def test_successful_acompletion(self, cli_client):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Hello async!", b""))

        with patch("rlm.clients.claude_cli.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            result = asyncio.run(cli_client.acompletion("Say hello"))

        assert result == "Hello async!"

    def test_acompletion_nonzero_exit(self, cli_client):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"async error"))

        with patch("rlm.clients.claude_cli.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            with pytest.raises(RuntimeError, match="claude CLI exited with code 1"):
                asyncio.run(cli_client.acompletion("test"))

    def test_acompletion_tracks_usage(self, cli_client):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"async response", b""))

        with patch("rlm.clients.claude_cli.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            asyncio.run(cli_client.acompletion("async input"))

        assert cli_client.model_call_counts["sonnet"] == 1


class TestUsageSummary:
    def test_get_usage_summary_empty(self, cli_client):
        summary = cli_client.get_usage_summary()
        assert isinstance(summary, UsageSummary)
        assert summary.model_usage_summaries == {}

    def test_get_usage_summary_after_calls(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "resp"
        mock_result.stderr = ""

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result):
            cli_client.completion("a]")
            cli_client.completion("b")

        summary = cli_client.get_usage_summary()
        assert "sonnet" in summary.model_usage_summaries
        assert summary.model_usage_summaries["sonnet"].total_calls == 2

    def test_get_last_usage(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "response"
        mock_result.stderr = ""

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result):
            cli_client.completion("input")

        last = cli_client.get_last_usage()
        assert isinstance(last, ModelUsageSummary)
        assert last.total_calls == 1
        assert last.total_input_tokens > 0
        assert last.total_output_tokens > 0

    def test_multi_model_tracking(self, cli_client):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        with patch("rlm.clients.claude_cli.subprocess.run", return_value=mock_result):
            cli_client.completion("a", model="sonnet")
            cli_client.completion("b", model="opus")

        summary = cli_client.get_usage_summary()
        assert "sonnet" in summary.model_usage_summaries
        assert "opus" in summary.model_usage_summaries
        assert summary.model_usage_summaries["sonnet"].total_calls == 1
        assert summary.model_usage_summaries["opus"].total_calls == 1


class TestGetClient:
    def test_get_client_claude_cli(self):
        with patch("rlm.clients.claude_cli.shutil.which", return_value="/usr/local/bin/claude"):
            from rlm.clients import get_client

            client = get_client("claude_cli", {})
            from rlm.clients.claude_cli import ClaudeCodeCLI

            assert isinstance(client, ClaudeCodeCLI)
