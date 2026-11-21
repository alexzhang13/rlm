"""Streaming as an optional client capability."""

import warnings
from types import SimpleNamespace

import pytest

from rlm.clients.base_lm import BaseLM
from rlm.clients.openai import OpenAIClient
from rlm.core.lm_handler import LMHandler
from rlm.core.rlm import RLM
from tests.mock_lm import MockLM, StreamingMockLM

RESPONSE = "Here is a plan.\n```repl\nanswer['content'] = 'x'\nanswer['ready'] = True\n```\n"


# ---------------------------------------------------------------- capability


def test_base_lm_does_not_require_streaming():
    """A client written before streaming existed keeps working untouched."""
    lm = MockLM(responses=["hello world"])
    assert lm.supports_streaming is False
    assert list(lm.stream_completion("q")) == ["hello world"]


def test_streaming_client_advertises_capability():
    assert StreamingMockLM().supports_streaming is True
    assert BaseLM.supports_streaming is False


@pytest.mark.parametrize("lm_cls", [MockLM, StreamingMockLM])
def test_deltas_reassemble_to_the_completion(lm_cls):
    """Streaming must not change the response, only how it arrives."""
    streamed = "".join(lm_cls(responses=[RESPONSE]).stream_completion("q"))
    blocking = lm_cls(responses=[RESPONSE]).completion("q")
    assert streamed == blocking == RESPONSE


def test_streaming_mock_yields_multiple_deltas():
    """Guard against the fallback silently standing in for a real stream."""
    deltas = list(StreamingMockLM(responses=[RESPONSE], chunk_size=5).stream_completion("q"))
    assert len(deltas) > 1
    assert all(len(d) <= 5 for d in deltas)


# ------------------------------------------------------------------ handler


def test_handler_streams_and_reports_capability():
    handler = LMHandler(StreamingMockLM(responses=[RESPONSE]))
    assert handler.supports_streaming is True
    assert "".join(handler.stream_completion("q")) == RESPONSE


def test_handler_streaming_falls_back_for_plain_client():
    handler = LMHandler(MockLM(responses=[RESPONSE]))
    assert handler.supports_streaming is False
    assert "".join(handler.stream_completion("q")) == RESPONSE


# --------------------------------------------------------------------- usage


@pytest.mark.parametrize("lm_cls", [MockLM, StreamingMockLM])
def test_usage_is_tracked_through_the_streaming_path(lm_cls):
    lm = lm_cls(responses=[RESPONSE])
    list(lm.stream_completion("q"))
    summary = lm.get_usage_summary()
    assert summary.model_usage_summaries[lm.model_name].total_calls == 1


# ------------------------------------------------------------------ RLM loop


def test_rlm_defaults_to_non_streaming():
    assert RLM(backend_kwargs={"model_name": "m"}).stream is False


def test_on_token_implies_stream():
    assert RLM(backend_kwargs={"model_name": "m"}, on_token=lambda d: None).stream is True


def test_get_response_matches_across_modes():
    """The loop sees an identical response whether or not streaming is on."""
    blocking = RLM(backend_kwargs={"model_name": "m"})
    streaming = RLM(backend_kwargs={"model_name": "m"}, stream=True)

    handler = LMHandler(StreamingMockLM(responses=[RESPONSE]))
    assert blocking._get_response("q", LMHandler(StreamingMockLM(responses=[RESPONSE]))) == (
        streaming._get_response("q", handler)
    )


def test_on_token_receives_every_delta():
    seen = []
    rlm = RLM(backend_kwargs={"model_name": "m"}, on_token=seen.append)
    handler = LMHandler(StreamingMockLM(responses=[RESPONSE], chunk_size=5))

    response = rlm._get_response("q", handler)

    assert len(seen) > 1, "expected incremental deltas"
    assert "".join(seen) == response == RESPONSE


def test_on_token_errors_do_not_break_the_turn():
    def boom(delta):
        raise RuntimeError("callback exploded")

    rlm = RLM(backend_kwargs={"model_name": "m"}, on_token=boom)
    handler = LMHandler(StreamingMockLM(responses=[RESPONSE]))
    assert rlm._get_response("q", handler) == RESPONSE


# ----------------------------------------------------- OpenAI stream parsing


def _text_chunk(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text))], usage=None
    )


def _usage_chunk(prompt_tokens=11, completion_tokens=7):
    """The final choices-empty chunk stream_options={'include_usage'} asks for."""
    return SimpleNamespace(
        choices=[],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model_extra=None,
        ),
    )


def _openai_client_yielding(chunks):
    client = OpenAIClient(api_key="test", model_name="gpt-test")
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)

        class Stream:
            def __iter__(self):
                return iter(chunks)

            def close(self):
                captured["closed"] = True

        return Stream()

    client.client.chat.completions.create = fake_create
    return client, captured


def test_openai_stream_yields_deltas_and_tracks_usage():
    chunks = [_text_chunk("Hel"), _text_chunk("lo"), _text_chunk(None), _usage_chunk()]
    client, captured = _openai_client_yielding(chunks)

    deltas = list(client.stream_completion("q"))

    assert deltas == ["Hel", "lo"], "empty deltas and the usage chunk must not be yielded"
    assert captured["stream"] is True
    assert captured["stream_options"] == {"include_usage": True}
    usage = client.get_last_usage()
    assert (usage.total_input_tokens, usage.total_output_tokens) == (11, 7)


def test_openai_stream_survives_endpoint_without_usage():
    """Some vLLM builds and gateways ignore stream_options: degrade, don't raise."""
    client, _ = _openai_client_yielding([_text_chunk("hi")])

    assert list(client.stream_completion("q")) == ["hi"]

    assert client.model_call_counts["gpt-test"] == 1
    usage = client.get_last_usage()
    assert (usage.total_input_tokens, usage.total_output_tokens) == (0, 0)


def test_sampling_args_cannot_collide_with_stream_kwargs():
    """A stray stream=... in sampling_args would be a duplicate-kwarg TypeError."""
    client, captured = _openai_client_yielding([_text_chunk("hi"), _usage_chunk()])
    client.sampling_args = {"temperature": 0.5, "stream": False, "stream_options": {}}

    assert list(client.stream_completion("q")) == ["hi"]
    assert captured["stream"] is True
    assert captured["temperature"] == 0.5


# ------------------------------------------------------------------ warning


def test_warns_when_streaming_requested_but_unavailable():
    rlm = RLM(backend_kwargs={"model_name": "m"}, stream=True)
    with pytest.warns(RuntimeWarning, match="does not support streaming"):
        rlm._warn_if_streaming_unavailable(MockLM())


def test_warning_fires_only_once_per_rlm():
    rlm = RLM(backend_kwargs={"model_name": "m"}, stream=True)
    with pytest.warns(RuntimeWarning):
        rlm._warn_if_streaming_unavailable(MockLM())
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rlm._warn_if_streaming_unavailable(MockLM())
    assert caught == []


def test_no_warning_when_streaming_is_available():
    rlm = RLM(backend_kwargs={"model_name": "m"}, stream=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rlm._warn_if_streaming_unavailable(StreamingMockLM())
    assert caught == []


def test_no_warning_when_streaming_not_requested():
    rlm = RLM(backend_kwargs={"model_name": "m"})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rlm._warn_if_streaming_unavailable(MockLM())
    assert caught == []


def test_speculation_is_disabled_by_default():
    rlm = RLM(backend_kwargs={"model_name": "m"})
    assert rlm.experimental_spec_ptc is False
    assert rlm.stream is False


def test_openai_closes_partial_stream_and_records_the_attempt():
    client, captured = _openai_client_yielding([_text_chunk("first"), _text_chunk("second")])
    stream = client.stream_completion("q")
    assert next(stream) == "first"
    stream.close()
    assert captured["closed"] is True
    assert client.get_last_usage().total_calls == 1


def test_root_stream_is_closed_when_consumer_interrupts():
    closed = []

    class Client(StreamingMockLM):
        def stream_completion(self, prompt, model=None):
            try:
                yield "one"
                yield "two"
            finally:
                closed.append(True)

    def interrupt(delta):
        raise KeyboardInterrupt

    rlm = RLM(on_token=interrupt)
    with pytest.raises(KeyboardInterrupt):
        rlm._get_response("q", LMHandler(Client()))
    assert closed == [True]


@pytest.mark.parametrize("provider", ["azure_openai", "gemini"])
@pytest.mark.parametrize("finish", [False, True])
def test_provider_stream_closes_and_counts_call(provider, finish):
    from unittest.mock import patch

    class Stream:
        closed = False

        def __iter__(self):
            for text in ("first", "second"):
                if provider == "gemini":
                    yield SimpleNamespace(text=text, usage_metadata=None)
                else:
                    yield _text_chunk(text)

        def close(self):
            self.closed = True

    stream = Stream()
    if provider == "gemini":
        from rlm.clients.gemini import GeminiClient

        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test", model_name="test-model")
        client.client.models.generate_content_stream.return_value = stream
    else:
        from rlm.clients.azure_openai import AzureOpenAIClient

        with (
            patch("rlm.clients.azure_openai.openai.AzureOpenAI"),
            patch("rlm.clients.azure_openai.openai.AsyncAzureOpenAI"),
        ):
            client = AzureOpenAIClient(
                api_key="test", model_name="test-model", azure_endpoint="https://example.test"
            )
        client.client.chat.completions.create.return_value = stream
    deltas = client.stream_completion("q")
    assert next(deltas) == "first"
    if finish:
        assert list(deltas) == ["second"]
    else:
        deltas.close()
    assert stream.closed is True
    assert client.get_last_usage().total_calls == 1
