"""
Example usage of Modal REPL with code execution and LLM queries.

Run with: python -m examples.modal_repl_example
"""

from rlm.clients.base_lm import BaseLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import ModelUsageSummary, UsageSummary
from rlm.environments.modal_repl import ModalREPL


class MockLM(BaseLM):
    """Simple mock LM that echoes prompts."""

    def __init__(self):
        super().__init__(model_name="mock-model")

    def completion(self, prompt, model=None, **kwargs):
        return f"Mock response to: {prompt[:50]}"

    async def acompletion(self, prompt, model=None, **kwargs):
        return self.completion(prompt)

    def get_usage_summary(self):
        return UsageSummary(
            model_usage_summaries={
                "mock-model": ModelUsageSummary(
                    total_calls=1, total_input_tokens=10, total_output_tokens=10
                )
            }
        )

    def get_last_usage(self):
        return self.get_usage_summary()


def main():
    print("=" * 60)
    print("Modal REPL Example")
    print("=" * 60)

    # Example 1: Basic code execution
    print("\n[1] Basic code execution (no LLM handler)")
    print("-" * 40)

    with ModalREPL(app_name="rlm-example") as repl:
        result = repl.execute_code("x = 1 + 2")
        print("Executed: x = 1 + 2")
        print(f"Locals: {result.locals}")

        result = repl.execute_code("print(x * 2)")
        print("Executed: print(x * 2)")
        print(f"Stdout: {result.stdout.strip()}")

        result = repl.execute_code("answer = 42")
        result = repl.execute_code('print(FINAL_VAR("answer"))')
        print(f"FINAL_VAR('answer'): {result.stdout.strip()}")

    # Example 2: With LLM handler
    print("\n[2] Code execution with LLM handler")
    print("-" * 40)

    mock_client = MockLM()

    with LMHandler(client=mock_client) as handler:
        print(f"LM Handler started at {handler.address}")

        with ModalREPL(
            app_name="rlm-example-handler",
            lm_handler_address=handler.address,
        ) as repl:
            # Single LLM query
            result = repl.execute_code('response = llm_query("What is 2+2?")')
            print("Executed: response = llm_query('What is 2+2?')")
            print(f"Stderr: {result.stderr or '(none)'}")

            result = repl.execute_code("print(response)")
            print(f"Response: {result.stdout.strip()}")

            # Batched LLM query
            result = repl.execute_code(
                'responses = llm_query_batched(["Question 1", "Question 2", "Question 3"])'
            )
            print("\nExecuted: responses = llm_query_batched([...])")

            result = repl.execute_code("print(f'Got {len(responses)} responses')")
            print(f"Result: {result.stdout.strip()}")

            result = repl.execute_code("print(responses[0])")
            print(f"First response: {result.stdout.strip()}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
