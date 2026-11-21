"""Expansive robustness / bug-hunting tests for DockerREPL.

Focus areas:
  - sub-calling behavior (llm_query / rlm_query, batched, fallback, errors,
    ordering, concurrency bounds, call tracking)
  - scaffold restoration (model overwriting reserved names)
  - answer-dict semantics + the per-turn reset regression
  - custom-tool injection edge cases
  - REPL state / output robustness
  - multi-instance isolation and lifecycle

All tests use a mock LM + mock subcall_fn (no API cost). Requires a working
Docker daemon; skipped otherwise.
"""

import asyncio
import shutil
import subprocess
import threading
import time

import pytest

from rlm.clients.base_lm import BaseLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=15).returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_available(), reason="Docker not available")


# --------------------------------------------------------------------------- #
# Mock LM + helpers
# --------------------------------------------------------------------------- #
class EchoLM(BaseLM):
    """Deterministic mock LM. Optional delay to exercise concurrency."""

    def __init__(self, delay: float = 0.0):
        super().__init__(model_name="echo")
        self.delay = delay

    def completion(self, prompt, model=None):
        if self.delay:
            time.sleep(self.delay)
        return f"echo:{str(prompt)[:40]}"

    async def acompletion(self, prompt, model=None):
        if self.delay:
            await asyncio.sleep(self.delay)
        return f"echo:{str(prompt)[:40]}"

    def get_usage_summary(self):
        return UsageSummary({"echo": ModelUsageSummary(1, 10, 10)})

    def get_last_usage(self):
        return ModelUsageSummary(1, 10, 10)


def _completion(response: str, model: str | None = None) -> RLMChatCompletion:
    return RLMChatCompletion(
        root_model=model or "child",
        prompt="p",
        response=response,
        usage_summary=UsageSummary(model_usage_summaries={}),
        execution_time=0.0,
    )


def make_repl(subcall_fn=None, with_handler=True, **kwargs):
    """Create a DockerREPL (optionally) wired to an EchoLM handler."""
    from rlm.environments.docker_repl import DockerREPL

    handler = None
    addr = None
    if with_handler:
        handler = LMHandler(client=kwargs.pop("lm_client", EchoLM()))
        handler.start()
        addr = handler.address
    repl = DockerREPL(lm_handler_address=addr, subcall_fn=subcall_fn, **kwargs)
    repl._test_handler = handler  # keep a ref so we can stop it on cleanup
    return repl


def teardown_repl(repl):
    repl.cleanup()
    if getattr(repl, "_test_handler", None) is not None:
        repl._test_handler.stop()


# =========================================================================== #
# Sub-calling: llm_query / llm_query_batched
# =========================================================================== #
class TestLLMQuery:
    def test_llm_query_and_tracking(self):
        repl = make_repl()
        try:
            r = repl.execute_code("print(llm_query('hi'))")
            assert r.stdout.strip() == "echo:hi", (r.stdout, r.stderr)
            assert len(r.rlm_calls) == 1
        finally:
            teardown_repl(repl)

    def test_llm_query_batched_order_and_tracking(self):
        repl = make_repl()
        try:
            r = repl.execute_code("print(llm_query_batched(['a', 'b', 'c']))")
            assert "echo:a" in r.stdout and "echo:c" in r.stdout
            assert len(r.rlm_calls) == 3
        finally:
            teardown_repl(repl)

    def test_pending_calls_cleared_between_executions(self):
        """A subsequent execution with no LM calls must report zero rlm_calls."""
        repl = make_repl()
        try:
            r1 = repl.execute_code("llm_query('one')")
            assert len(r1.rlm_calls) == 1
            r2 = repl.execute_code("x = 5")
            assert len(r2.rlm_calls) == 0, "stale pending calls leaked into next execution"
        finally:
            teardown_repl(repl)

    def test_llm_query_no_handler_errors_gracefully(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("print(llm_query('hi'))")
            assert "Error" in r.stdout
            assert len(r.rlm_calls) == 0
        finally:
            teardown_repl(repl)

    def test_concurrent_llm_query_from_container_threads(self):
        """Many concurrent llm_query calls from container threads must all
        complete (no serialization/deadlock) and all be tracked. Uses a slow
        LM so serialization would blow the time budget."""
        repl = make_repl(lm_client=EchoLM(delay=0.3))
        code = (
            "import threading\n"
            "res = {}\n"
            "def w(i):\n"
            "    res[i] = llm_query(f'q{i}')\n"
            "ts = [threading.Thread(target=w, args=(i,)) for i in range(5)]\n"
            "[t.start() for t in ts]\n"
            "[t.join() for t in ts]\n"
            "print(sorted(res.keys()))\n"
            "print(all(v.startswith('echo:') for v in res.values()))"
        )
        try:
            t0 = time.monotonic()
            r = repl.execute_code(code)
            dt = time.monotonic() - t0
            lines = r.stdout.strip().split("\n")
            assert lines[0] == "[0, 1, 2, 3, 4]", (r.stdout, r.stderr)
            assert lines[1] == "True"
            assert len(r.rlm_calls) == 5
            # 5 x 0.3s sequential = 1.5s; concurrent should be well under.
            assert dt < 1.2, f"concurrent llm_query appears serialized: {dt:.2f}s"
        finally:
            teardown_repl(repl)


# =========================================================================== #
# Sub-calling: rlm_query / rlm_query_batched
# =========================================================================== #
class TestRLMQuery:
    def test_rlm_query_uses_subcall_fn(self):
        repl = make_repl(
            subcall_fn=lambda p, context, m=None: _completion(f"child:{p}:{context['value']}")
        )
        try:
            r = repl.execute_code("print(rlm_query('task', context={'value': 'data'}))")
            assert r.stdout.strip() == "child:task:data", (r.stdout, r.stderr)
            assert len(r.rlm_calls) == 1
        finally:
            teardown_repl(repl)

    def test_rlm_query_model_override_propagates(self):
        seen = {}

        def sub(p, context, m=None):
            seen["model"] = m
            return _completion("ok", model=m)

        repl = make_repl(subcall_fn=sub)
        try:
            repl.execute_code("rlm_query('task', dict(), model='custom-1')")
            assert seen["model"] == "custom-1"
        finally:
            teardown_repl(repl)

    def test_rlm_query_fallback_to_llm_when_no_subcall(self):
        """No subcall_fn but a handler -> rlm_query degrades to a plain LM call."""
        repl = make_repl(subcall_fn=None, with_handler=True)
        try:
            r = repl.execute_code("print(rlm_query('task', dict()))")
            assert r.stdout.strip() == "echo:task\n\nContext:\n{}", (r.stdout, r.stderr)
            assert len(r.rlm_calls) == 1
        finally:
            teardown_repl(repl)

    def test_rlm_query_error_is_caught(self):
        def boom(p, context, m=None):
            raise RuntimeError("subcall exploded")

        repl = make_repl(subcall_fn=boom)
        try:
            r = repl.execute_code("print(rlm_query('task', dict()))")
            assert "Error" in r.stdout and "subcall exploded" in r.stdout
            assert r.stderr.strip() == "", "error should be returned as value, not raised"
            assert len(r.rlm_calls) == 0
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_basic_order_and_tracking(self):
        repl = make_repl(subcall_fn=lambda p, context, m=None: _completion(f"c:{p}"))
        try:
            r = repl.execute_code(
                "print(rlm_query_batched([(p, dict()) for p in ['p0', 'p1', 'p2']]))"
            )
            assert "['c:p0', 'c:p1', 'c:p2']" in r.stdout, (r.stdout, r.stderr)
            assert [c.response for c in r.rlm_calls] == ["c:p0", "c:p1", "c:p2"]
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_empty(self):
        called = []
        repl = make_repl(subcall_fn=lambda p, context, m=None: called.append(p) or _completion("x"))
        try:
            r = repl.execute_code("print(rlm_query_batched([]))")
            assert r.stdout.strip() == "[]"
            assert called == []
            assert len(r.rlm_calls) == 0
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_single(self):
        repl = make_repl(subcall_fn=lambda p, context, m=None: _completion(f"c:{p}"))
        try:
            r = repl.execute_code("print(rlm_query_batched([(p, dict()) for p in ['only']]))")
            assert r.stdout.strip() == "['c:only']"
            assert len(r.rlm_calls) == 1
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_order_preserved_under_varying_delays(self):
        def sub(p, context, m=None):
            # earlier prompts sleep longer so completion order != input order
            delay = {"p0": 0.3, "p1": 0.2, "p2": 0.1, "p3": 0.0}[p]
            time.sleep(delay)
            return _completion(f"r:{p}")

        repl = make_repl(subcall_fn=sub, max_concurrent_subcalls=4)
        try:
            r = repl.execute_code(
                "print(rlm_query_batched([(p, dict()) for p in ['p0', 'p1', 'p2', 'p3']]))"
            )
            assert "['r:p0', 'r:p1', 'r:p2', 'r:p3']" in r.stdout, (r.stdout, r.stderr)
            # tracked metadata also in prompt order
            assert [c.response for c in r.rlm_calls] == ["r:p0", "r:p1", "r:p2", "r:p3"]
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_partial_failure_excludes_from_tracking(self):
        def sub(p, context, m=None):
            if p == "bad":
                raise ValueError("nope")
            return _completion(f"ok:{p}")

        repl = make_repl(subcall_fn=sub, max_concurrent_subcalls=4)
        try:
            r = repl.execute_code(
                "print(rlm_query_batched([(p, dict()) for p in ['good1', 'bad', 'good2']]))"
            )
            assert "ok:good1" in r.stdout and "ok:good2" in r.stdout
            assert "Error" in r.stdout and "nope" in r.stdout
            # only successful completions tracked, in order
            assert [c.response for c in r.rlm_calls] == ["ok:good1", "ok:good2"]
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_respects_max_concurrent(self):
        active = [0]
        peak = [0]
        lk = threading.Lock()

        def sub(p, context, m=None):
            with lk:
                active[0] += 1
                peak[0] = max(peak[0], active[0])
            time.sleep(0.1)
            with lk:
                active[0] -= 1
            return _completion(f"ok:{p}")

        repl = make_repl(subcall_fn=sub, max_concurrent_subcalls=2)
        try:
            r = repl.execute_code(
                "print(len(rlm_query_batched([(p, dict()) for p in ['a', 'b', 'c', 'd', 'e', 'f']])))"
            )
            assert r.stdout.strip() == "6", (r.stdout, r.stderr)
            assert peak[0] <= 2, f"concurrency bound violated: peak={peak[0]}"
            assert len(r.rlm_calls) == 6
        finally:
            teardown_repl(repl)

    def test_rlm_query_batched_fallback_when_no_subcall(self):
        repl = make_repl(subcall_fn=None, with_handler=True)
        try:
            r = repl.execute_code("print(rlm_query_batched([(p, dict()) for p in ['a', 'b']]))")
            assert "echo:a" in r.stdout and "echo:b" in r.stdout
            assert len(r.rlm_calls) == 2
        finally:
            teardown_repl(repl)

    def test_malformed_subcall_result_does_not_hang(self):
        """If subcall_fn returns a non-completion object, the container must get
        a structured error promptly (not hang on a dropped connection), and the
        bad result must not be tracked."""
        repl = make_repl(subcall_fn=lambda p, context, m=None: 12345)  # no .response attr
        try:
            t0 = time.monotonic()
            r = repl.execute_code("print(rlm_query('task', dict()))")
            dt = time.monotonic() - t0
            assert "Error" in r.stdout, (r.stdout, r.stderr)
            assert dt < 30, f"appears to have hung: {dt:.1f}s"
            assert len(r.rlm_calls) == 0
        finally:
            teardown_repl(repl)

    def test_mixed_llm_and_rlm_calls_tracked_in_order(self):
        repl = make_repl(subcall_fn=lambda p, context, m=None: _completion(f"c:{p}"))
        try:
            r = repl.execute_code(
                "llm_query('first')\nrlm_query_batched([(p, dict()) for p in ['b', 'c']])\nllm_query('last')"
            )
            responses = [c.response for c in r.rlm_calls]
            assert responses == ["echo:first", "c:b", "c:c", "echo:last"], responses
        finally:
            teardown_repl(repl)


# =========================================================================== #
# Scaffold restoration (model overwriting reserved names)
# =========================================================================== #
class TestScaffoldRestoration:
    def test_overwritten_llm_query_restored_next_cell(self):
        repl = make_repl()
        try:
            repl.execute_code("llm_query = lambda *a, **k: 'HIJACKED'")
            r = repl.execute_code("print(llm_query('hi'))")
            assert r.stdout.strip() == "echo:hi", "llm_query not restored after overwrite"
        finally:
            teardown_repl(repl)

    def test_overwritten_rlm_query_restored_next_cell(self):
        repl = make_repl(subcall_fn=lambda p, context, m=None: _completion("real"))
        try:
            repl.execute_code("rlm_query = 'garbage'")
            r = repl.execute_code("print(rlm_query('x', dict()))")
            assert r.stdout.strip() == "real", "rlm_query not restored after overwrite"
        finally:
            teardown_repl(repl)

    def test_overwritten_show_vars_restored(self):
        repl = make_repl(with_handler=False)
        try:
            repl.execute_code("SHOW_VARS = 123")
            r = repl.execute_code("print(SHOW_VARS())")
            assert "variables" in r.stdout.lower(), r.stdout
        finally:
            teardown_repl(repl)

    def test_context_alias_restored_after_overwrite(self):
        repl = make_repl(with_handler=False, context_payload="ORIGINAL")
        try:
            repl.execute_code("context = 'clobbered'")
            r = repl.execute_code("print(context)")
            assert r.stdout.strip() == "ORIGINAL", "context alias not restored to context_0"
        finally:
            teardown_repl(repl)


# =========================================================================== #
# answer dict semantics
# =========================================================================== #
class TestAnswerSemantics:
    def test_answer_ready_surfaces_final_answer(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("answer['content'] = 'done'; answer['ready'] = True")
            assert r.final_answer == "done"
        finally:
            teardown_repl(repl)

    def test_answer_not_ready_is_none(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("answer['content'] = 'partial'")
            assert r.final_answer is None
        finally:
            teardown_repl(repl)

    def test_answer_empty_content_surfaces_empty_string(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("answer['ready'] = True")
            assert r.final_answer == "", f"expected '' got {r.final_answer!r}"
        finally:
            teardown_repl(repl)

    def test_answer_nonstring_content_coerced(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("answer['content'] = 1234; answer['ready'] = True")
            assert r.final_answer == "1234"
        finally:
            teardown_repl(repl)

    def test_answer_plain_dict_reassignment_surfaces(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("answer = {'content': 'X', 'ready': True}")
            assert r.final_answer == "X"
        finally:
            teardown_repl(repl)

    def test_update_handler_address_resets_stale_answer(self):
        """Regression: stale answer.ready from a prior turn must not leak into
        the next turn (persistent multi-turn)."""
        repl = make_repl()
        try:
            r1 = repl.execute_code("answer['content'] = 'stale'; answer['ready'] = True")
            assert r1.final_answer == "stale"
            repl.update_handler_address(repl.lm_handler_address)
            r2 = repl.execute_code("print(answer['ready'], repr(answer['content']))")
            assert r2.stdout.strip() == "False ''", r2.stdout
            assert r2.final_answer is None
        finally:
            teardown_repl(repl)


# =========================================================================== #
# Custom tools
# =========================================================================== #
class TestCustomTools:
    def test_reserved_name_rejected(self):
        from rlm.environments.docker_repl import DockerREPL

        with pytest.raises(ValueError, match="reserved"):
            DockerREPL(custom_tools={"llm_query": "def llm_query(): pass"})

    def test_code_string_and_data_tools(self):
        repl = make_repl(
            with_handler=False,
            custom_tools={
                "square": "def square(x):\n    return x * x",
                "CFG": {"mode": "t", "vals": [1, 2, 3]},
            },
        )
        try:
            r = repl.execute_code("print(square(CFG['vals'][2]))")
            assert r.stdout.strip() == "9", (r.stdout, r.stderr)
        finally:
            teardown_repl(repl)

    def test_host_callable_tool_skipped_without_crash(self):
        repl = make_repl(with_handler=False, custom_tools={"hostfn": lambda x: x})
        try:
            # The repl still builds and runs; the tool is simply absent.
            r = repl.execute_code("print('ok')")
            assert r.stdout.strip() == "ok"
            r2 = repl.execute_code("print(hostfn(1))")
            assert "NameError" in r2.stderr or "Error" in r2.stderr
        finally:
            teardown_repl(repl)

    def test_data_tool_with_special_characters_roundtrips(self):
        tricky = {"q": 'he said "hi"', "s": "a'b\\c", "nl": "x\ny", "u": "café ☕"}
        repl = make_repl(with_handler=False, custom_tools={"DATA": tricky})
        try:
            r = repl.execute_code(
                "print(DATA['q']); print(DATA['s']); print(repr(DATA['nl'])); print(DATA['u'])"
            )
            lines = r.stdout.split("\n")
            assert lines[0] == 'he said "hi"', (r.stdout, r.stderr)
            assert lines[1] == "a'b\\c"
            assert lines[2] == "'x\\ny'"
            assert lines[3] == "café ☕"
        finally:
            teardown_repl(repl)


# =========================================================================== #
# REPL state / output robustness
# =========================================================================== #
class TestStateAndOutput:
    def test_unpicklable_dropped_picklable_survives(self):
        # A generator is genuinely unserializable (even by dill); it must be
        # dropped from persisted state without crashing, while picklable state
        # survives across executions.
        repl = make_repl(with_handler=False)
        try:
            repl.execute_code("gen = (i for i in range(3))\nkeep = 42")
            r = repl.execute_code("print(keep)")
            assert r.stdout.strip() == "42", "picklable var lost across executions"
            r2 = repl.execute_code("print('gen' in dir())")
            assert r2.stdout.strip() == "False", "unpicklable var unexpectedly persisted"
        finally:
            teardown_repl(repl)

    def test_unicode_stdout(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("print('café ☕ 日本語')")
            assert r.stdout.strip() == "café ☕ 日本語", repr(r.stdout)
        finally:
            teardown_repl(repl)

    def test_output_that_looks_like_json_is_preserved(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code('print(\'{"fake": "json", "n": 1}\')\nprint("second line")')
            assert '{"fake": "json", "n": 1}' in r.stdout
            assert "second line" in r.stdout
        finally:
            teardown_repl(repl)

    def test_exception_produces_stderr_not_crash(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("print('before')\nraise ValueError('kaboom')")
            assert "before" in r.stdout
            assert "ValueError" in r.stderr and "kaboom" in r.stderr
            assert r.final_answer is None
        finally:
            teardown_repl(repl)

    def test_empty_code(self):
        repl = make_repl(with_handler=False)
        try:
            r = repl.execute_code("")
            assert r.stderr.strip() == "", r.stderr
        finally:
            teardown_repl(repl)

    def test_large_context_via_mount(self):
        big = "\n".join(f"line {i}" for i in range(20000))
        repl = make_repl(with_handler=False, context_payload=big)
        try:
            r = repl.execute_code(
                "print(len(context.splitlines())); print(context.splitlines()[12345])"
            )
            lines = r.stdout.strip().split("\n")
            assert lines[0] == "20000", (r.stdout, r.stderr)
            assert lines[1] == "line 12345"
        finally:
            teardown_repl(repl)

    def test_dict_context_nested_access(self):
        repl = make_repl(with_handler=False, context_payload={"a": {"b": [10, 20, 30]}})
        try:
            r = repl.execute_code("print(context['a']['b'][1])")
            assert r.stdout.strip() == "20"
        finally:
            teardown_repl(repl)


# =========================================================================== #
# Multi-instance isolation & lifecycle
# =========================================================================== #
class TestIsolationAndLifecycle:
    def test_two_repls_isolated_state_and_tracking(self):
        r1 = make_repl(subcall_fn=lambda p, context, m=None: _completion("A"))
        r2 = make_repl(subcall_fn=lambda p, context, m=None: _completion("B"))
        try:
            r1.execute_code("shared = 'from_r1'")
            r2.execute_code("shared = 'from_r2'")
            o1 = r1.execute_code("print(shared)")
            o2 = r2.execute_code("print(shared)")
            assert o1.stdout.strip() == "from_r1"
            assert o2.stdout.strip() == "from_r2"
            # call tracking is independent
            t1 = r1.execute_code("rlm_query('x', dict())")
            assert [c.response for c in t1.rlm_calls] == ["A"]
            t2 = r2.execute_code("rlm_query('x', dict())")
            assert [c.response for c in t2.rlm_calls] == ["B"]
            assert r1.proxy_port != r2.proxy_port
            assert r1.container_id != r2.container_id
        finally:
            teardown_repl(r1)
            teardown_repl(r2)

    def test_double_cleanup_idempotent(self):
        repl = make_repl(with_handler=False)
        repl.execute_code("x = 1")
        cid = repl.container_id
        repl.cleanup()
        repl.cleanup()  # must not raise
        if repl._test_handler is not None:
            repl._test_handler.stop()
        # container removed
        out = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", f"id={cid}"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert out == "", f"container not removed: {out!r}"

    def test_context_manager_cleans_up(self):
        from rlm.environments.docker_repl import DockerREPL

        with DockerREPL() as repl:
            cid = repl.container_id
            tmp = repl.temp_dir
            repl.execute_code("x = 1")
        out = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", f"id={cid}"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert out == ""
        import os

        assert not os.path.exists(tmp)
