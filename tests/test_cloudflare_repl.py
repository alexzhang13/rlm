"""Tests for CloudflareREPL environment.

These tests use mocked HTTP responses since CloudflareREPL communicates
with a Cloudflare Worker via HTTP API rather than a local process.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from rlm.environments.cloudflare_repl import CloudflareREPL, _build_exec_script


class TestBuildExecScript:
    """Tests for the execution script builder."""

    def test_script_contains_code(self):
        """Test that the script contains the encoded code."""
        script = _build_exec_script("print('hello')")
        assert "base64" in script
        assert "exec(code" in script

    def test_script_has_state_management(self):
        """Test that the script includes state management."""
        script = _build_exec_script("x = 1")
        assert "load_state" in script
        assert "save_state" in script
        assert "STATE_FILE" in script

    def test_script_has_llm_functions(self):
        """Test that the script includes LLM query functions."""
        script = _build_exec_script("x = 1")
        assert "def llm_query" in script
        assert "def llm_query_batched" in script

    def test_script_has_final_var(self):
        """Test that the script includes FINAL_VAR helper."""
        script = _build_exec_script("x = 1")
        assert "def FINAL_VAR" in script

    def test_script_with_broker_url(self):
        """Test that broker URL is included when provided."""
        script = _build_exec_script("x = 1", broker_url="http://localhost:8080")
        assert "http://localhost:8080" in script

    def test_script_without_broker_url(self):
        """Test that broker URL is None when not provided."""
        script = _build_exec_script("x = 1")
        assert "BROKER_URL = None" in script


class TestCloudflareREPLInit:
    """Tests for CloudflareREPL initialization."""

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_init_sets_attributes(self, mock_session_class):
        """Test that __init__ sets required attributes."""
        mock_session = MagicMock()
        mock_session.post.return_value.json.return_value = {
            "stdout": "Python 3.11.0",
            "stderr": "",
            "exitCode": 0,
        }
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
            sandbox_id="test-sandbox",
        )

        assert repl.worker_url == "https://test.workers.dev"
        assert repl.auth_token == "test-token"
        assert repl.sandbox_id == "test-sandbox"
        repl.cleanup()

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_init_generates_sandbox_id(self, mock_session_class):
        """Test that sandbox_id is generated if not provided."""
        mock_session = MagicMock()
        mock_session.post.return_value.json.return_value = {
            "stdout": "Python 3.11.0",
            "stderr": "",
            "exitCode": 0,
        }
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
        )

        assert repl.sandbox_id.startswith("rlm-")
        repl.cleanup()

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_init_strips_trailing_slash(self, mock_session_class):
        """Test that trailing slash is stripped from worker_url."""
        mock_session = MagicMock()
        mock_session.post.return_value.json.return_value = {
            "stdout": "Python 3.11.0",
            "stderr": "",
            "exitCode": 0,
        }
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev/",
            auth_token="test-token",
        )

        assert repl.worker_url == "https://test.workers.dev"
        repl.cleanup()


class TestCloudflareREPLExecute:
    """Tests for CloudflareREPL.execute_code()."""

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_execute_simple_code(self, mock_session_class):
        """Test executing simple code returns REPLResult."""
        mock_session = MagicMock()

        # Setup response - first call for setup, then write, then exec
        mock_session.post.return_value.json.side_effect = [
            # setup() call
            {"stdout": "Python 3.11.0", "stderr": "", "exitCode": 0},
            # write file call
            {"success": True},
            # exec call - returns JSON with result
            {
                "stdout": json.dumps({
                    "stdout": "4\n",
                    "stderr": "",
                    "locals": {"x": "4"},
                }),
                "stderr": "",
                "exitCode": 0,
            },
        ]
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
        )

        result = repl.execute_code("x = 2 + 2\nprint(x)")

        assert result.stdout == "4\n"
        assert result.stderr == ""
        assert "x" in result.locals
        repl.cleanup()

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_execute_with_error(self, mock_session_class):
        """Test that errors are captured in stderr."""
        mock_session = MagicMock()

        mock_session.post.return_value.json.side_effect = [
            # setup() call
            {"stdout": "Python 3.11.0", "stderr": "", "exitCode": 0},
            # write file call
            {"success": True},
            # exec call
            {
                "stdout": json.dumps({
                    "stdout": "",
                    "stderr": "ZeroDivisionError: division by zero",
                    "locals": {},
                }),
                "stderr": "",
                "exitCode": 0,
            },
        ]
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
        )

        result = repl.execute_code("1 / 0")

        assert "ZeroDivisionError" in result.stderr
        repl.cleanup()


class TestCloudflareREPLContext:
    """Tests for context loading."""

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_load_string_context(self, mock_session_class):
        """Test loading string context."""
        mock_session = MagicMock()

        mock_session.post.return_value.json.side_effect = [
            # setup() call
            {"stdout": "Python 3.11.0", "stderr": "", "exitCode": 0},
            # write file call (context loading)
            {"success": True},
            # exec call (context loading)
            {
                "stdout": json.dumps({
                    "stdout": "",
                    "stderr": "",
                    "locals": {"context": "test data"},
                }),
                "stderr": "",
                "exitCode": 0,
            },
        ]
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
            context_payload="test data",
        )

        # Context should have been loaded via execute_code
        assert mock_session.post.call_count >= 3
        repl.cleanup()

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_load_dict_context(self, mock_session_class):
        """Test loading dict context."""
        mock_session = MagicMock()

        mock_session.post.return_value.json.side_effect = [
            # setup() call
            {"stdout": "Python 3.11.0", "stderr": "", "exitCode": 0},
            # write file call
            {"success": True},
            # exec call
            {
                "stdout": json.dumps({
                    "stdout": "",
                    "stderr": "",
                    "locals": {"context": "{'key': 'value'}"},
                }),
                "stderr": "",
                "exitCode": 0,
            },
        ]
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
            context_payload={"key": "value"},
        )

        repl.cleanup()


class TestCloudflareREPLCleanup:
    """Tests for cleanup behavior."""

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_cleanup_closes_session(self, mock_session_class):
        """Test that cleanup closes the HTTP session."""
        mock_session = MagicMock()
        mock_session.post.return_value.json.return_value = {
            "stdout": "Python 3.11.0",
            "stderr": "",
            "exitCode": 0,
        }
        mock_session_class.return_value = mock_session

        repl = CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
        )

        repl.cleanup()

        mock_session.close.assert_called_once()

    @patch("rlm.environments.cloudflare_repl.requests.Session")
    def test_context_manager(self, mock_session_class):
        """Test using CloudflareREPL as context manager."""
        mock_session = MagicMock()
        mock_session.post.return_value.json.return_value = {
            "stdout": "Python 3.11.0",
            "stderr": "",
            "exitCode": 0,
        }
        mock_session_class.return_value = mock_session

        with CloudflareREPL(
            worker_url="https://test.workers.dev",
            auth_token="test-token",
        ) as repl:
            assert repl.worker_url == "https://test.workers.dev"

        # Session should be closed after context manager exits
        mock_session.close.assert_called()


class TestCloudflareREPLInterface:
    """Tests for IsolatedEnv interface compliance."""

    def test_has_required_methods(self):
        """Test that CloudflareREPL has all required IsolatedEnv methods."""
        assert hasattr(CloudflareREPL, "setup")
        assert hasattr(CloudflareREPL, "load_context")
        assert hasattr(CloudflareREPL, "execute_code")

    def test_is_isolated_env_subclass(self):
        """Test that CloudflareREPL is a subclass of IsolatedEnv."""
        from rlm.environments.base_env import IsolatedEnv

        assert issubclass(CloudflareREPL, IsolatedEnv)
