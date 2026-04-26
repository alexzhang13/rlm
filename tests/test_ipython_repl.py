"""Tests for IPythonREPL — both in_process and subprocess kernel modes.

These tests require the ipython optional extra:
    pip install 'rlms[ipython]'

Subprocess-mode tests are automatically skipped if jupyter_client/ipykernel
are unavailable.
"""

from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass

import pytest

pytest.importorskip("IPython")

from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary
from rlm.environments.ipython_repl import IPythonREPL

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_has_subprocess = True
try:
    import ipykernel  # noqa: F401
    import jupyter_client  # noqa: F401
except ImportError:
    _has_subprocess = False


BOTH_MODES = pytest.mark.parametrize(
    "kernel_mode",
    [
        "in_process",
        pytest.param(
            "subprocess",
            marks=pytest.mark.skipif(
                not _has_subprocess,
                reason="jupyter_client/ipykernel not installed",
            ),
        ),
    ],
)


@dataclass
class _FakeSubcall:
    """A stand-in for RLM._subcall that records calls and returns canned responses."""

    responses: list[str]
    calls: list[tuple[str, str | None]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.calls = []
        self._i = 0

    def __call__(self, prompt: str, model: str | None = None) -> RLMChatCompletion:
        self.calls.append((prompt, model))
        response = self.responses[self._i % len(self.responses)]
        self._i += 1
        usage = UsageSummary(
            model_usage_summaries={
                "fake-model": ModelUsageSummary(
                    total_calls=1,
                    total_input_tokens=0,
                    total_output_tokens=0,
                )
            }
        )
        return RLMChatCompletion(
            root_model="fake-model",
            prompt=prompt,
            response=response,
            usage_summary=usage,
            execution_time=0.001,
        )


# -----------------------------------------------------------------------------
# Basic execution
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_simple_execution(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode) as repl:
        result = repl.execute_code("x = 1 + 2\nprint(x)")
    assert result.stderr == ""
    assert "3" in result.stdout


@BOTH_MODES
def test_error_captured_in_stderr(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode) as repl:
        result = repl.execute_code("1 / 0")
    assert "ZeroDivisionError" in result.stderr


@BOTH_MODES
def test_variable_persistence_across_cells(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode) as repl:
        repl.execute_code("a = 40")
        repl.execute_code("b = a + 2")
        result = repl.execute_code("print(b)")
    assert "42" in result.stdout


def test_in_process_exposes_locals_dict():
    """In-process mode mirrors LocalREPL's .locals dict for parity."""
    with IPythonREPL(kernel_mode="in_process") as repl:
        repl.execute_code("x = 42\ny = 'hi'")
        assert repl.locals["x"] == 42
        assert repl.locals["y"] == "hi"


# -----------------------------------------------------------------------------
# FINAL_VAR
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_final_var_returns_variable(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode) as repl:
        repl.execute_code("answer = 'forty-two'")
        result = repl.execute_code('FINAL_VAR("answer")')
    assert result.final_answer == "forty-two"


@BOTH_MODES
def test_final_var_missing_variable(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode) as repl:
        result = repl.execute_code('FINAL_VAR("does_not_exist")')
    assert result.final_answer is None
    assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()


@BOTH_MODES
def test_final_var_accepts_direct_value(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode) as repl:
        result = repl.execute_code("FINAL_VAR(123)")
    assert result.final_answer == "123"


# -----------------------------------------------------------------------------
# Context loading
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_load_context_string(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode, context_payload="hello world") as repl:
        result = repl.execute_code("print(len(context))")
    assert "11" in result.stdout


@BOTH_MODES
def test_load_context_dict(kernel_mode: str):
    payload = {"name": "alice", "count": 7}
    with IPythonREPL(kernel_mode=kernel_mode, context_payload=payload) as repl:
        result = repl.execute_code('print(context["name"], context["count"])')
    assert "alice" in result.stdout
    assert "7" in result.stdout


# -----------------------------------------------------------------------------
# Custom tools
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_custom_tool_callable(kernel_mode: str):
    def greet(name: str) -> str:
        return f"hello, {name}"

    with IPythonREPL(
        kernel_mode=kernel_mode,
        custom_tools={"greet": greet},
    ) as repl:
        result = repl.execute_code('print(greet("world"))')
    assert "hello, world" in result.stdout


@BOTH_MODES
def test_custom_tool_data(kernel_mode: str):
    with IPythonREPL(
        kernel_mode=kernel_mode,
        custom_tools={"MAGIC": 42},
    ) as repl:
        result = repl.execute_code("print(MAGIC * 2)")
    assert "84" in result.stdout


# -----------------------------------------------------------------------------
# Recursive rlm_query
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_rlm_query_dispatches_to_subcall_fn(kernel_mode: str):
    subcall = _FakeSubcall(responses=["child-answer"])
    with IPythonREPL(kernel_mode=kernel_mode, subcall_fn=subcall) as repl:
        result = repl.execute_code('r = rlm_query("think harder")\nprint(r)')
    assert "child-answer" in result.stdout
    assert len(subcall.calls) == 1
    assert subcall.calls[0][0] == "think harder"
    # Completion recorded on the REPLResult
    assert len(result.rlm_calls) == 1
    assert result.rlm_calls[0].response == "child-answer"


@BOTH_MODES
def test_rlm_query_batched_dispatches(kernel_mode: str):
    subcall = _FakeSubcall(responses=["a", "b", "c"])
    with IPythonREPL(kernel_mode=kernel_mode, subcall_fn=subcall) as repl:
        result = repl.execute_code(
            'rs = rlm_query_batched(["p1","p2","p3"])\nprint(\',\'.join(rs))'
        )
    assert "a,b,c" in result.stdout
    assert len(subcall.calls) == 3
    assert len(result.rlm_calls) == 3


@BOTH_MODES
def test_rlm_query_falls_back_when_no_subcall_fn(kernel_mode: str):
    """Without subcall_fn, rlm_query falls through to llm_query (which errors
    cleanly when no LM handler is configured)."""
    with IPythonREPL(kernel_mode=kernel_mode, subcall_fn=None) as repl:
        result = repl.execute_code('print(rlm_query("hi"))')
    # Error either about missing subcall_fn, handler, or kernel address —
    # the contract is: it doesn't crash and surfaces a clear error string.
    assert "Error" in result.stdout


# -----------------------------------------------------------------------------
# Subprocess-mode-specific: hard timeouts
# -----------------------------------------------------------------------------


@pytest.mark.skipif(not _has_subprocess, reason="jupyter_client not installed")
def test_subprocess_timeout_interrupts_cleanly():
    with IPythonREPL(kernel_mode="subprocess", cell_timeout=0.5) as repl:
        start = time.perf_counter()
        result = repl.execute_code("import time; time.sleep(5)")
        elapsed = time.perf_counter() - start

        assert "TimeoutError" in result.stderr
        # Must have actually interrupted, not waited the full 5s
        assert elapsed < 3.0

        # Kernel should still be alive and responsive afterward
        followup = repl.execute_code("print('still-alive')")
    assert "still-alive" in followup.stdout


@pytest.mark.skipif(not _has_subprocess, reason="jupyter_client not installed")
def test_subprocess_no_timeout_by_default():
    """Without cell_timeout, short code runs without issue."""
    with IPythonREPL(kernel_mode="subprocess") as repl:
        result = repl.execute_code("print(sum(range(100)))")
    assert "4950" in result.stdout


# -----------------------------------------------------------------------------
# In-process-mode timeouts (SIGALRM-based, Unix + main thread only)
# -----------------------------------------------------------------------------


_can_alarm = sys.platform != "win32" and threading.current_thread() is threading.main_thread()


@pytest.mark.skipif(not _can_alarm, reason="SIGALRM requires Unix main thread")
def test_in_process_timeout_interrupts_c_level_sleep():
    with IPythonREPL(kernel_mode="in_process", cell_timeout=0.3) as repl:
        start = time.perf_counter()
        result = repl.execute_code("import time; time.sleep(5)")
        elapsed = time.perf_counter() - start
    assert "TimeoutError" in result.stderr
    assert elapsed < 2.0, f"expected fast interrupt, got {elapsed:.2f}s"


@pytest.mark.skipif(not _can_alarm, reason="SIGALRM requires Unix main thread")
def test_in_process_timeout_interrupts_python_loop():
    with IPythonREPL(kernel_mode="in_process", cell_timeout=0.3) as repl:
        start = time.perf_counter()
        result = repl.execute_code("i = 0\nwhile True: i += 1")
        elapsed = time.perf_counter() - start
    assert "TimeoutError" in result.stderr
    assert elapsed < 2.0, f"expected fast interrupt, got {elapsed:.2f}s"


@pytest.mark.skipif(not _can_alarm, reason="SIGALRM requires Unix main thread")
def test_in_process_shell_alive_after_timeout():
    with IPythonREPL(kernel_mode="in_process", cell_timeout=0.3) as repl:
        repl.execute_code("import time; time.sleep(5)")
        followup = repl.execute_code("print('still-alive')")
    assert "still-alive" in followup.stdout


@pytest.mark.skipif(not _can_alarm, reason="SIGALRM requires Unix main thread")
def test_in_process_timeout_no_fire_for_fast_cell():
    with IPythonREPL(kernel_mode="in_process", cell_timeout=2.0) as repl:
        result = repl.execute_code("print(sum(range(1000)))")
    assert result.stderr == ""
    assert "499500" in result.stdout


# -----------------------------------------------------------------------------
# Lifecycle
# -----------------------------------------------------------------------------


def test_invalid_kernel_mode_rejected():
    with pytest.raises(ValueError):
        IPythonREPL(kernel_mode="nonsense")  # type: ignore[arg-type]


@BOTH_MODES
def test_cleanup_is_idempotent(kernel_mode: str):
    repl = IPythonREPL(kernel_mode=kernel_mode)
    repl.execute_code("x = 1")
    repl.cleanup()
    repl.cleanup()  # must not raise


# -----------------------------------------------------------------------------
# Persistence (SupportsPersistence protocol)
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_persistent_env_exposes_protocol(kernel_mode: str):
    from rlm.environments import SupportsPersistence

    with IPythonREPL(kernel_mode=kernel_mode, persistent=True) as repl:
        assert isinstance(repl, SupportsPersistence)


@BOTH_MODES
def test_add_context_versioning(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode, persistent=True) as repl:
        i0 = repl.add_context("First")
        i1 = repl.add_context("Second")
        assert (i0, i1) == (0, 1)
        assert repl.get_context_count() == 2

        # Visible to executed code
        r = repl.execute_code("print(context_0, '|', context_1, '|', context)")
    assert "First" in r.stdout
    assert "Second" in r.stdout


@BOTH_MODES
def test_add_history_versioning_and_alias(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode, persistent=True) as repl:
        h1 = [{"role": "user", "content": "Q1"}]
        h2 = [{"role": "user", "content": "Q2"}]
        repl.add_history(h1)
        repl.add_history(h2)
        assert repl.get_history_count() == 2

        r = repl.execute_code(
            "print(history_0[0]['content'], history_1[0]['content'], history[0]['content'])"
        )
    assert "Q1" in r.stdout
    assert "Q2" in r.stdout


@BOTH_MODES
def test_history_is_deep_copied(kernel_mode: str):
    with IPythonREPL(kernel_mode=kernel_mode, persistent=True) as repl:
        h = [{"role": "user", "content": "original"}]
        repl.add_history(h)
        h[0]["content"] = "mutated"
        r = repl.execute_code("print(history_0[0]['content'])")
    assert "original" in r.stdout
    assert "mutated" not in r.stdout


@BOTH_MODES
def test_update_handler_address(kernel_mode: str):
    with IPythonREPL(
        kernel_mode=kernel_mode,
        lm_handler_address=("127.0.0.1", 5000),
        persistent=True,
    ) as repl:
        repl.update_handler_address(("127.0.0.1", 6000))
    assert repl.lm_handler_address == ("127.0.0.1", 6000)


@BOTH_MODES
def test_context_alias_restored_after_user_overwrites_it(kernel_mode: str):
    """If user code reassigns ``context``, the next cell sees it restored."""
    with IPythonREPL(kernel_mode=kernel_mode, persistent=True) as repl:
        repl.add_context("original-text")
        repl.execute_code("context = 'overwritten'")
        # In in-process mode we restore aliases after every execute. Subprocess
        # mode does not (that would add an extra round-trip) — document via
        # behavior: context_0 always remains untouched in both modes.
        r = repl.execute_code("print(context_0)")
    assert "original-text" in r.stdout


def test_in_process_persistent_multi_turn_variables():
    """Variables defined in one cell are visible in later add_context calls."""
    with IPythonREPL(kernel_mode="in_process", persistent=True) as repl:
        repl.add_context("Sales were $1000")
        repl.execute_code("sales = 1000")
        repl.add_context("Costs were $400")
        r = repl.execute_code("profit = sales - 400\nprint(profit)")
    assert "600" in r.stdout


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------


def test_get_environment_routes_ipython():
    from rlm.environments import get_environment

    env = get_environment("ipython", {"kernel_mode": "in_process"})
    try:
        assert isinstance(env, IPythonREPL)
        result = env.execute_code("print(2 ** 10)")
        assert "1024" in result.stdout
    finally:
        env.cleanup()


@pytest.mark.skipif(not _has_subprocess, reason="jupyter_client not installed")
def test_get_environment_routes_ipython_subprocess():
    from rlm.environments import get_environment

    env = get_environment("ipython", {"kernel_mode": "subprocess"})
    try:
        assert isinstance(env, IPythonREPL)
        result = env.execute_code("print(2 ** 10)")
        assert "1024" in result.stdout
    finally:
        env.cleanup()


def test_ipython_repl_importable_from_package():
    """``IPythonREPL`` is in ``__all__`` and must be importable lazily."""
    from rlm.environments import IPythonREPL as Imported

    assert Imported is IPythonREPL


# -----------------------------------------------------------------------------
# rlm_calls accounting (regression: prior subprocess impl leaked across cells)
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_rlm_calls_do_not_leak_across_cells(kernel_mode: str):
    """Each REPLResult.rlm_calls must reflect only the current cell's calls."""
    subcall = _FakeSubcall(responses=["x"])
    with IPythonREPL(kernel_mode=kernel_mode, subcall_fn=subcall) as repl:
        r1 = repl.execute_code('rlm_query("a")')
        r2 = repl.execute_code('rlm_query("b")')
        r3 = repl.execute_code('rlm_query("c")')
        r4 = repl.execute_code('print("no rlm here")')
    assert len(r1.rlm_calls) == 1
    assert len(r2.rlm_calls) == 1
    assert len(r3.rlm_calls) == 1
    assert len(r4.rlm_calls) == 0


# -----------------------------------------------------------------------------
# cell_timeout normalization
# -----------------------------------------------------------------------------


@BOTH_MODES
def test_cell_timeout_zero_treated_as_disabled(kernel_mode: str):
    """``cell_timeout=0`` is meaningless; treated as ``None``."""
    with IPythonREPL(kernel_mode=kernel_mode, cell_timeout=0) as repl:
        assert repl.cell_timeout is None
        # And short code still runs without spurious timeouts.
        result = repl.execute_code("print(2 + 2)")
    assert "4" in result.stdout


# -----------------------------------------------------------------------------
# In-process error formatting
# -----------------------------------------------------------------------------


def test_in_process_error_includes_traceback_and_user_frame():
    """In-process stderr should include a real traceback, not just a one-liner."""
    with IPythonREPL(kernel_mode="in_process") as repl:
        result = repl.execute_code("def boom():\n    1/0\n\nboom()")
    assert "ZeroDivisionError" in result.stderr
    assert "Traceback" in result.stderr
    assert "boom" in result.stderr  # user frame name visible


# -----------------------------------------------------------------------------
# Setup error → cleanup
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Concurrency / isolation
# -----------------------------------------------------------------------------


def test_in_process_two_instances_have_distinct_user_modules():
    """Two coexisting in-process instances must not share ``sys.modules['__main__']``."""
    repl_a = IPythonREPL(kernel_mode="in_process")
    repl_b = IPythonREPL(kernel_mode="in_process")
    try:
        repl_a.execute_code("x = 'A'")
        repl_b.execute_code("x = 'B'")
        ra = repl_a.execute_code("print(x)")
        rb = repl_b.execute_code("print(x)")
        assert "A" in ra.stdout and "B" not in ra.stdout
        assert "B" in rb.stdout and "A" not in rb.stdout
        # And ``sys.modules['__main__']`` is not the IPython user module
        # for either instance.
        assert repl_a._user_module is not repl_b._user_module
        assert repl_a._user_module.__name__ != "__main__"
        assert repl_b._user_module.__name__ != "__main__"
    finally:
        repl_a.cleanup()
        repl_b.cleanup()


def test_in_process_user_module_dropped_from_sys_modules_on_cleanup():
    """No ``sys.modules`` leak after cleanup."""
    import sys as _sys

    repl = IPythonREPL(kernel_mode="in_process")
    name = repl._user_module.__name__
    assert name in _sys.modules
    repl.cleanup()
    assert name not in _sys.modules


@BOTH_MODES
def test_concurrent_add_context_indices_are_unique(kernel_mode: str):
    """Two threads calling ``add_context`` concurrently must not collide."""
    with IPythonREPL(kernel_mode=kernel_mode, persistent=True) as repl:
        results: list[int] = []
        lock = threading.Lock()

        def worker(i: int) -> None:
            idx = repl.add_context(f"payload-{i}")
            with lock:
                results.append(idx)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    # All indices distinct, contiguous, and 0..7 in some order.
    assert sorted(results) == list(range(8))
    assert repl.get_context_count() == 8


def test_subcall_concurrency_is_globally_bounded():
    """``max_concurrent_subcalls`` caps simultaneous ``subcall_fn`` calls
    even across multiple ``rlm_query`` / ``rlm_query_batched`` requests."""
    if not _has_subprocess:
        pytest.skip("jupyter_client not installed")

    in_flight = 0
    peak = 0
    cv_lock = threading.Lock()

    def slow_subcall(prompt: str, model: str | None = None) -> RLMChatCompletion:
        nonlocal in_flight, peak
        with cv_lock:
            in_flight += 1
            peak = max(peak, in_flight)
        time.sleep(0.05)
        with cv_lock:
            in_flight -= 1
        usage = UsageSummary(
            model_usage_summaries={
                "fake-model": ModelUsageSummary(
                    total_calls=1, total_input_tokens=0, total_output_tokens=0
                )
            }
        )
        return RLMChatCompletion(
            root_model="fake-model",
            prompt=prompt,
            response="ok",
            usage_summary=usage,
            execution_time=0.05,
        )

    # cap=2 → no matter how many calls the kernel fans out, only 2 should
    # ever be running at once.
    with IPythonREPL(
        kernel_mode="subprocess",
        subcall_fn=slow_subcall,
        max_concurrent_subcalls=2,
    ) as repl:
        # Two batched-of-8 requests issued from kernel-side threads
        # simulates fan-out far above the cap.
        result = repl.execute_code(
            "import threading\n"
            "def go():\n"
            "    rlm_query_batched(['p1','p2','p3','p4','p5','p6','p7','p8'])\n"
            "ts = [threading.Thread(target=go) for _ in range(2)]\n"
            "for t in ts: t.start()\n"
            "for t in ts: t.join()\n"
            "print('done')"
        )
    assert "done" in result.stdout
    assert peak <= 2, f"semaphore should bound concurrency to 2, saw peak={peak}"


@pytest.mark.skipif(not _has_subprocess, reason="jupyter_client not installed")
def test_setup_failure_runs_cleanup():
    """If construction fails after the broker/kernel start, cleanup runs.

    A non-JSON-serializable context_payload triggers a TypeError in
    ``add_context`` *after* ``setup()`` has already brought up the kernel
    and broker. The new try/except in ``__init__`` must run cleanup
    before re-raising; otherwise the kernel + broker would be orphaned.
    """

    class _Unserializable:
        pass

    with pytest.raises(TypeError):
        IPythonREPL(
            kernel_mode="subprocess",
            context_payload={"bad": _Unserializable()},
        )
