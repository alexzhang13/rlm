"""Basic tests for OpenAIClient."""

import os

from dotenv import load_dotenv

from rlm.clients.openai import OpenAIClient

load_dotenv()


def test_openai_completion_with_kwargs():
    """Test that kwargs are passed through to OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    model_name = "openai/gpt-5.2"

    if not api_key:
        print("Skipping test: OPENAI_API_KEY not set")
        return

    client = OpenAIClient(api_key=api_key, model_name=model_name, base_url=base_url)
    prompt = "What is the capital of France?"

    try:
        # Test with kwargs
        sample_kwargs = {"reasoning_effort": "high", "extra_body": {"usage": {"include": True}}}
        result = client.completion(prompt, **sample_kwargs)
        print(f"OpenAI response with {sample_kwargs=}:\n{result}")
        assert result is not None
        assert len(result) > 0
    except Exception as e:
        print(f"OpenAIClient error: {e}")
        raise


def test_openai_completion_without_kwargs():
    """Test that completion works without kwargs."""
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    model_name = "openai/gpt-4.1-mini"

    if not api_key:
        print("Skipping test: OPENAI_API_KEY not set")
        return

    client = OpenAIClient(api_key=api_key, model_name=model_name, base_url=base_url)
    prompt = "What is the capital of France?"

    try:
        # Test without kwargs
        result = client.completion(prompt)
        print(f"OpenAI response without kwargs:\n{result}")
        assert result is not None
        assert len(result) > 0
    except Exception as e:
        print(f"OpenAIClient error: {e}")
        raise


if __name__ == "__main__":
    test_openai_completion_with_kwargs()
    test_openai_completion_without_kwargs()
