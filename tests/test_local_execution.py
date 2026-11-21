"""Process isolation keeps a detected lock-order deadlock from poisoning pytest."""

import subprocess
import sys
import textwrap


def test_same_repl_cells_serialize_without_blocking_a_tool_wait():
    script = textwrap.dedent("""
        import threading
        import time
        from rlm.core.types import RLMChatCompletion, UsageSummary
        from rlm.environments.local_repl import LocalREPL

        started = threading.Event()
        release = threading.Event()
        second_entered = threading.Event()
        results = {}

        def child(instruction, context, model=None):
            started.set()
            assert release.wait(3)
            return RLMChatCompletion('mock', context, 'first', UsageSummary({}), 0)

        with LocalREPL(subcall_fn=child) as repl:
            def first():
                results['first'] = repl.execute_code("print(rlm_query('task', 'data'))")
            def second():
                second_entered.set()
                results['second'] = repl.execute_code("print('second')")
            a = threading.Thread(target=first, daemon=True)
            b = threading.Thread(target=second, daemon=True)
            a.start()
            assert started.wait(3)
            b.start()
            assert second_entered.wait(3)
            # Let the second cell reach its execution/capture lock while the
            # first cell's tool is deliberately blocked.
            time.sleep(0.05)
            release.set()
            a.join(3)
            b.join(3)
            assert not a.is_alive() and not b.is_alive(), 'cell/tool lock-order deadlock'
            assert results['first'].stdout == 'first\\n'
            assert results['second'].stdout == 'second\\n'
            assert len(results['first'].rlm_calls) == 1
            assert results['second'].rlm_calls == []
    """)
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
