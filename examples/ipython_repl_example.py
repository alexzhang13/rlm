"""IPython REPL environment example.

Runs user code inside a real IPython session. Two kernel modes:

- ``in_process``: IPython InteractiveShell in the same Python process as RLM.
  Fast, zero-overhead subcalls, full Python object interop.
- ``subprocess``: ipykernel subprocess managed via jupyter_client. Gives you
  real per-cell timeouts via kernel interrupt, and full isolation from the
  host namespace.

Setup:
    pip install 'rlms[ipython]'
    python -m examples.ipython_repl_example
"""

from __future__ import annotations

from rlm.clients.base_lm import BaseLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import ModelUsageSummary, UsageSummary
from rlm.environments.ipython_repl import IPythonREPL


class MockLM(BaseLM):
    def __init__(self):
        super().__init__(model_name="mock")

    def completion(self, prompt):
        return f"Mock: {str(prompt)[:50]}"

    async def acompletion(self, prompt):
        return self.completion(prompt)

    def get_usage_summary(self):
        return UsageSummary({"mock": ModelUsageSummary(1, 10, 10)})

    def get_last_usage(self):
        return self.get_usage_summary()


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def demo_in_process() -> None:
    section("[1] In-process IPython kernel")
    with IPythonREPL(kernel_mode="in_process") as repl:
        r = repl.execute_code("x = 40\ny = 2\nprint(x + y)")
        print(f"  stdout: {r.stdout.strip()}")
        print(f"  locals: x={repl.locals['x']}, y={repl.locals['y']}")

        # FINAL_VAR captures the final answer out-of-band.
        repl.execute_code('answer = "forty-two"')
        r = repl.execute_code('FINAL_VAR("answer")')
        print(f"  FINAL_VAR → {r.final_answer}")


def demo_subprocess() -> None:
    section("[2] Subprocess ipykernel — real timeouts")
    with IPythonREPL(kernel_mode="subprocess", cell_timeout=1.0) as repl:
        r = repl.execute_code("import sys; print(sys.executable)")
        print(f"  kernel python: {r.stdout.strip()}")

        r = repl.execute_code("xs = [i*i for i in range(5)]; print(xs)")
        print(f"  stdout: {r.stdout.strip()}")

        print("  -- running a 5s sleep with cell_timeout=1.0s --")
        r = repl.execute_code("import time; time.sleep(5); print('never')")
        print(f"  elapsed: {r.execution_time:.2f}s")
        print(f"  stderr: {r.stderr.strip()}")

        # Kernel survives the interrupt and still responds.
        r = repl.execute_code("print('kernel still alive')")
        print(f"  follow-up: {r.stdout.strip()}")


def demo_llm_query() -> None:
    section("[3] llm_query plumbing via LMHandler")
    with LMHandler(client=MockLM()) as handler:
        for mode in ("in_process", "subprocess"):
            print(f"\n  -- kernel_mode={mode} --")
            with IPythonREPL(
                kernel_mode=mode,
                lm_handler_address=handler.address,
            ) as repl:
                r = repl.execute_code('r = llm_query("ping"); print(r)')
                print(f"  response: {r.stdout.strip()}")

                r = repl.execute_code('print(llm_query_batched(["a", "b"]))')
                print(f"  batched:  {r.stdout.strip()}")


def demo_recursion() -> None:
    section("[4] rlm_query — recursive RLM subcalls")
    # Stand-in for RLM._subcall: returns a canned reply for the demo.
    from rlm.core.types import RLMChatCompletion

    class _FakeSubcall:
        def __call__(self, prompt: str, model=None) -> RLMChatCompletion:
            return RLMChatCompletion(
                root_model="fake",
                prompt=prompt,
                response=f"child-answer[{prompt}]",
                usage_summary=UsageSummary({"fake": ModelUsageSummary(1, 0, 0)}),
                execution_time=0.0,
            )

    subcall = _FakeSubcall()
    for mode in ("in_process", "subprocess"):
        print(f"\n  -- kernel_mode={mode} --")
        with IPythonREPL(kernel_mode=mode, subcall_fn=subcall) as repl:
            r = repl.execute_code('print(rlm_query("deep-think-topic-A"))')
            print(f"  single:  {r.stdout.strip()}")
            r = repl.execute_code('print(rlm_query_batched(["t1","t2","t3"]))')
            print(f"  batched: {r.stdout.strip()}")


def main() -> None:
    demo_in_process()
    demo_subprocess()
    demo_llm_query()
    demo_recursion()
    print("\nDone.")


if __name__ == "__main__":
    main()
