
---

<h1 align="center" style="font-size:2.8em">
<span>Recursive Language Models (<span style="color:orange">RLM</span>s) — Delta-Labs Fork</span>
</h1>

<p align="center" style="font-size:1.3em">
  <a href="https://arxiv.org/abs/2512.24601">Paper</a> •
  <a href="https://alexzhang13.github.io/rlm/">Upstream Docs</a> •
  <a href="https://github.com/alexzhang13/rlm">Upstream Repo</a>
</p>

<p align="center">
  <a href="https://github.com/Delta-Labs-AG/rlm/actions/workflows/style.yml">
    <img src="https://github.com/Delta-Labs-AG/rlm/actions/workflows/style.yml/badge.svg" alt="Style" />
  </a>
  <a href="https://github.com/Delta-Labs-AG/rlm/actions/workflows/test.yml">
    <img src="https://github.com/Delta-Labs-AG/rlm/actions/workflows/test.yml/badge.svg" alt="Test" />
  </a>
  <a href="https://github.com/Delta-Labs-AG/rlm/releases">
    <img src="https://img.shields.io/github/v/release/Delta-Labs-AG/rlm?label=release" alt="Release" />
  </a>
</p>

## What is this?

This is [Delta-Labs'](https://github.com/Delta-Labs-AG) maintained fork of [alexzhang13/rlm](https://github.com/alexzhang13/rlm) with production hardening for our [rlm-service](https://github.com/Delta-Labs-AG/rlm-service). All changes are backward-compatible with the upstream API.

## Installation

Pin to a release tag:
```bash
pip install "rlms @ git+https://github.com/Delta-Labs-AG/rlm.git@v0.1.0-delta.1"
```

Or track `main`:
```bash
pip install "rlms @ git+https://github.com/Delta-Labs-AG/rlm.git@main"
```

In `requirements.txt`:
```
rlms @ git+https://github.com/Delta-Labs-AG/rlm.git@v0.1.0-delta.1
```

## Changes from upstream

### Thread-safe REPL environment
The upstream `LocalREPL` calls `os.chdir()` which is process-global and unsafe when multiple REPL instances run concurrently in threads. This fork replaces `_temp_cwd()` with a no-op and uses stable per-instance directories under `/tmp/rlm_repl_envs/`. Also adds multimodal prompt support to `llm_query` and `llm_query_batched`.

### Resilient OpenAI client
Adds [tenacity](https://github.com/jd/tenacity) retry with exponential jitter for `RateLimitError` and `APITimeoutError`, httpx timeout of 600s, `max_retries=3` on the OpenAI client, and `reasoning_effort` parameter support.

### Per-prompt batch error handling
Uses `asyncio.gather(*tasks, return_exceptions=True)` so a single failed prompt in a batch returns an error string instead of killing the entire batch.

### Minimal system prompt
`rlm.utils.rlm_system_prompt.RLM_SYSTEM_PROMPT_MINIMAL` — a concise prompt focused on `FINAL_VAR`-only returns and JSON schema compliance, used via `custom_system_prompt` for structured output use cases.

### response_format plumbing
Threads OpenAI structured outputs (`response_format`) through the entire stack: `llm_query()` → socket protocol → `LMHandler` → OpenAI client. Supports both single and per-prompt batched formats.

## Quick start

```python
from rlm import RLM
from rlm.utils.rlm_system_prompt import RLM_SYSTEM_PROMPT_MINIMAL

rlm = RLM(
    backend="openai",
    backend_kwargs={
        "model_name": "gpt-4.1-mini",
        "reasoning_effort": "medium",  # Delta-Labs addition
    },
    custom_system_prompt=RLM_SYSTEM_PROMPT_MINIMAL,
    verbose=True,
)

print(rlm.completion("Summarize the key themes in the context.").response)
```

### Using response_format (structured output)

In REPL setup code passed to the RLM:
```python
result = llm_query(prompt, response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "my_output",
        "strict": True,
        "schema": { ... }
    }
})
```

## Releases

Releases are created automatically on push to `main` via the [Release Delta](.github/workflows/release-delta.yml) workflow. Tags follow `v{version}-delta.{n}` (e.g. `v0.1.0-delta.1`).

## Development

```bash
uv venv --python 3.12
uv pip install -e .
uv pip install pytest pytest-asyncio pytest-cov ruff
```

```bash
ruff check .                 # lint
ruff format --check .        # format check
pytest tests/ -v             # test
```

## Upstream sync

```bash
git remote add upstream https://github.com/alexzhang13/rlm.git
git fetch upstream
git merge upstream/main      # resolve conflicts as needed
```

## License

MIT — see upstream [LICENSE](https://github.com/alexzhang13/rlm/blob/main/LICENSE).
