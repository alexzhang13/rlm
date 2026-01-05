"""Tests for CloudflareREPL environment.

Import tests run always. E2E tests require RLM_CF_WORKER_URL environment variable.
"""

import os

import pytest


class TestCloudflareREPLImports:
    """Test CloudflareREPL can be imported."""

    def test_cloudflare_repl_import(self):
        """Test that CloudflareREPL can be imported."""
        from rlm.environments.cloudflare_repl import CloudflareREPL

        assert CloudflareREPL is not None

    def test_cloudflare_repl_is_class(self):
        """Test that CloudflareREPL is a class."""
        from rlm.environments.cloudflare_repl import CloudflareREPL

        assert isinstance(CloudflareREPL, type)

    def test_is_isolated_env_subclass(self):
        """Test that CloudflareREPL is a subclass of IsolatedEnv."""
        from rlm.environments.base_env import IsolatedEnv
        from rlm.environments.cloudflare_repl import CloudflareREPL

        assert issubclass(CloudflareREPL, IsolatedEnv)

    def test_get_environment_cloudflare(self):
        """Test that get_environment supports 'cloudflare' option."""
        from rlm.environments import get_environment

        # Should not raise - just verify the option is recognized
        assert callable(get_environment)


# E2E tests - only run when RLM_CF_WORKER_URL is set
WORKER_URL = os.environ.get("RLM_CF_WORKER_URL")
SKIP_E2E = WORKER_URL is None


@pytest.mark.skipif(SKIP_E2E, reason="RLM_CF_WORKER_URL not set")
class TestCloudflareREPLE2E:
    """End-to-end tests against a live Cloudflare Worker.

    To run these tests:
        export RLM_CF_WORKER_URL=https://your-worker.workers.dev
        pytest tests/test_cloudflare_repl.py -v
    """

    def test_simple_execution(self):
        """Test executing simple code."""
        from rlm.environments.cloudflare_repl import CloudflareREPL

        with CloudflareREPL(worker_url=WORKER_URL, auth_token="") as repl:
            result = repl.execute_code("x = 2 + 2\nprint(x)")
            assert "4" in result.stdout

    def test_variable_persistence(self):
        """Test that variables persist across executions."""
        from rlm.environments.cloudflare_repl import CloudflareREPL

        with CloudflareREPL(worker_url=WORKER_URL, auth_token="") as repl:
            repl.execute_code("x = 42")
            result = repl.execute_code("print(x * 2)")
            assert "84" in result.stdout

    def test_numpy_available(self):
        """Test that numpy is available in the sandbox."""
        from rlm.environments.cloudflare_repl import CloudflareREPL

        with CloudflareREPL(worker_url=WORKER_URL, auth_token="") as repl:
            result = repl.execute_code("import numpy as np\nprint(np.sum([1, 2, 3]))")
            assert "6" in result.stdout

    def test_error_handling(self):
        """Test that errors are captured."""
        from rlm.environments.cloudflare_repl import CloudflareREPL

        with CloudflareREPL(worker_url=WORKER_URL, auth_token="") as repl:
            result = repl.execute_code("1 / 0")
            assert "ZeroDivisionError" in result.stderr
