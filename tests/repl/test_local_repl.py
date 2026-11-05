from rlm.environments.local_repl import LocalREPL


def test_persistent_execution():
    """Test that variables persist across multiple code executions."""
    repl = LocalREPL()

    # Set a variable
    result1 = repl.execute_code("x = 42")
    assert result1.stderr == ""
    assert "x" in repl.locals
    assert repl.locals["x"] == 42

    # Use the variable in a subsequent execution
    result2 = repl.execute_code("y = x + 8")
    assert result2.stderr == ""
    assert repl.locals["y"] == 50

    # Print the variable
    result3 = repl.execute_code("print(y)")
    assert "50" in result3.stdout

    repl.cleanup()


def test_failed_block_preserves_prior_assignments():
    repl = LocalREPL()
    result = repl.execute_code("a = 1\nb = 2\nraise ValueError('boom at item 3')\nc = 3")
    # assignments before the raise survive
    assert repl.locals["a"] == 1
    assert repl.locals["b"] == 2
    # the line after the raise never ran
    assert "c" not in repl.locals
    # error still surfaced to the model, plus the salvage note
    assert "ValueError" in result.stderr
    assert "boom at item 3" in result.stderr
    assert "preserved" in result.stderr
    # REPL still usable afterwards (scaffold intact)
    follow = repl.execute_code("d = a + b")
    assert follow.stderr == ""
    assert repl.locals["d"] == 3
    repl.cleanup()


def test_failed_block_restores_shadowed_scaffold():
    repl = LocalREPL()
    repl.load_context("the real context")
    # shadow a reserved name, then raise
    repl.execute_code("context = 'clobbered'\nraise RuntimeError('x')")
    # scaffold name restored despite the failure
    assert repl.locals.get("context") != "clobbered"
    # llm_query still callable (a plain follow-up block runs cleanly)
    follow = repl.execute_code("z = 5")
    assert follow.stderr == ""
    repl.cleanup()


def test_salvaged_results_reused_after_midloop_failure():
    """Integration: a loop that fails at item N can resume from N, not re-run."""
    repl = LocalREPL()
    # fake sub-call that raises on its 8th invocation, counting every call
    repl.execute_code(
        "calls = []\n"
        "def fake_query(i):\n"
        "    calls.append(i)\n"
        "    if len(calls) == 8:\n"
        "        raise RuntimeError('transient failure')\n"
        "    return f'label-{i}'\n"
    )
    # first attempt dies mid-loop; 7 paid-for results must survive
    result = repl.execute_code(
        "results = []\nfor i in range(10):\n    results.append(fake_query(i))\n"
    )
    assert "transient failure" in result.stderr
    assert repl.locals["results"] == [f"label-{i}" for i in range(7)]
    # second block resumes from where it left off — no re-paying for items 0-6
    follow = repl.execute_code(
        "for i in range(len(results), 10):\n    results.append(fake_query(i))\n"
    )
    assert follow.stderr == ""
    assert repl.locals["results"] == [f"label-{i}" for i in range(10)]
    # 10 successful calls + 1 failed call = 11 total, not 17+
    assert len(repl.locals["calls"]) == 11
    repl.cleanup()
