"""
Docker REPL example with code execution, LLM queries, recursive sub-RLM calls,
and custom tools.

Setup:
    1. Ensure Docker is running
    2. Run: python -m examples.docker_repl_example

The default image (python:3.11-slim) will be pulled automatically.

Persistence and compaction:
    DockerREPL also supports multi-turn persistence and compaction. Drive them
    through the RLM rather than the env directly, e.g.:

        rlm = RLM(backend=..., environment="docker", persistent=True)   # multi-turn
        rlm = RLM(backend=..., environment="docker", compaction=True)   # auto-summarize
"""

from rlm.clients.base_lm import BaseLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary
from rlm.environments.docker_repl import DockerREPL


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


def main():
    print("=" * 50)
    print("Docker REPL Example")
    print("=" * 50)

    # Basic execution (no LLM)
    print("\n[1] Basic code execution")
    with DockerREPL() as repl:
        result = repl.execute_code("x = 1 + 2")
        print(f"  x = 1 + 2 → locals: {result.locals}")

        result = repl.execute_code("print(x * 2)")
        print(f"  print(x * 2) → {result.stdout.strip()}")

    # With LLM handler
    print("\n[2] With LLM handler")
    with LMHandler(client=MockLM()) as handler:
        print(f"  Handler at {handler.address}")

        with DockerREPL(lm_handler_address=handler.address) as repl:
            result = repl.execute_code('r = llm_query("Hello!")')
            print(f"  llm_query → stderr: {result.stderr or '(none)'}")

            result = repl.execute_code("print(r)")
            print(f"  Response: {result.stdout.strip()}")

            result = repl.execute_code('rs = llm_query_batched(["Q1", "Q2"])')
            result = repl.execute_code("print(len(rs))")
            print(f"  Batched count: {result.stdout.strip()}")

    # Recursive sub-RLM calls + custom tools
    print("\n[3] Recursive sub-RLM (rlm_query) + custom tools")

    def mock_subcall(instruction, context, model=None):
        # In real use this is RLM._subcall, which spawns a child RLM.
        return RLMChatCompletion(
            root_model=model or "child",
            prompt=context,
            response=f"child-answer({instruction})",
            usage_summary=UsageSummary(model_usage_summaries={}),
            execution_time=0.0,
        )

    with DockerREPL(
        subcall_fn=mock_subcall,
        custom_tools={"triple": "def triple(x):\n    return x * 3", "CONST": 7},
    ) as repl:
        result = repl.execute_code("print(triple(CONST))")
        print(f"  custom tools triple(CONST) → {result.stdout.strip()}")

        result = repl.execute_code('print(rlm_query("solve subtask", context="supporting data"))')
        print(f"  rlm_query → {result.stdout.strip()}")

        result = repl.execute_code(
            'print(rlm_query_batched([("a", "data a"), ("b", "data b"), ("c", "data c")]))'
        )
        print(f"  rlm_query_batched → {result.stdout.strip()}")

    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
