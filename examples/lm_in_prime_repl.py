"""
Example: Using llm_query() from within a Prime Intellect Sandbox.

This demonstrates the LM Handler + PrimeREPL integration where code
running in a cloud sandbox can query the LLM via the HTTP broker pattern.
"""

import os

from dotenv import load_dotenv

from rlm.clients.portkey import PortkeyClient
from rlm.core.lm_handler import LMHandler
from rlm.environments.prime_repl import PrimeREPL

load_dotenv()

setup_code = """
secret = "1424424"
"""

context_payload = """
This is a test context. It should print out, revealing the magic number to be 4.
"""

code = """
response = llm_query("What is 2 + 2? Reply with just the number.")
print(response)
print(type(response))
print(context)
print("Secret from setup code: ", secret)
"""


def main():
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        print("Error: PORTKEY_API_KEY not set")
        return
    print(f"PORTKEY_API_KEY: {api_key[:8]}...")

    client = PortkeyClient(api_key=api_key, model_name="@openai/gpt-5-nano")
    print("Created Portkey client with model: @openai/gpt-5-nano")

    # Start LM Handler
    with LMHandler(client=client) as handler:
        print(f"LM Handler started at {handler.address}")

        # Create Prime REPL with handler connection
        print("\nCreating Prime sandbox...")
        with PrimeREPL(
            name="rlm-lm-demo",
            docker_image="python:3.11-slim",
            timeout_minutes=30,
            lm_handler_address=handler.address,
            context_payload=context_payload,
            setup_code=setup_code,
        ) as repl:
            print(f"PrimeREPL created, sandbox ID: {repl.sandbox_id}")
            print(f"Broker URL: {repl.broker_url}\n")

            # Run code that uses llm_query
            print(f"Executing: {code}")

            result = repl.execute_code(code)

            print(f"stdout: {result.stdout!r}")
            print(f"stderr: {result.stderr!r}")
            print(f"response variable: {result.locals.get('response')!r}")
            print(f"locals: {result.locals!r}")
            print(f"execution time: {result.execution_time:.3f}s")
            print(f"rlm_calls made: {len(result.rlm_calls)}")


if __name__ == "__main__":
    main()
