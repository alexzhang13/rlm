# CS2640 Final Project — Cache-Informed Prompting for RLMs

Fork of [alexzhang13/rlm](https://github.com/alexzhang13/rlm) for the
COMPSCI 2640 (Modern Computer Storage Systems) final project.

**Research question.** Does injecting cache-eviction theory (LRU, S3-FIFO,
SIEVE, cost-benefit reasoning) into the RLM root system prompt improve
accuracy and/or cost on RLM's own benchmarks?

## Fork ground rules

- The upstream `rlm/` package is touched minimally — only for needed backend
  additions (e.g., `rlm/clients/agent_sdk.py`). All experiment code lives
  under `experiments/`.
- Results, prompt variants, and analysis live in `experiments/`, `results/`,
  `report/`, `slides/`.
- Branch: `cs2640-cache-informed` (off `upstream/main` at commit 95bff82).

## Auth

All sonnet calls go through `claude_agent_sdk` + `CLAUDE_CODE_OAUTH_TOKEN`
(Max subscription billing; no raw Anthropic API key needed). Export the token
before any run:

```bash
export CLAUDE_CODE_OAUTH_TOKEN='sk-ant-oat01-...'
```

The Agent SDK injects a ~16K Claude Code default preamble into each call.
This is constant across all arms (A0–A6 + 3 baselines), so relative
comparisons are valid; absolute costs are inflated vs raw-API and will be
footnoted in Table 1.

## Backend

- `backend="agent_sdk"` (new) — `rlm/clients/agent_sdk.py`
- Wraps `claude_agent_sdk.query()` on a dedicated background event loop so
  RLM's sync `completion()` path works.
- `max_turns=5` per completion (Agent SDK counts tool-probe cycles as extra
  turns even with `allowed_tools=[]`).
- Usage tracking records both primary Sonnet and the SDK's background Haiku
  orchestrator separately. Table 1 reports Sonnet-only cost.

## Phases

See `plans/cs2640-plan.md` for the full 9-phase plan.

- **Phase 0** (done): fork + Agent SDK backend + smoke test
- **Phase 1**: (largely obviated by Agent SDK auto-caching — see notes)
- **Phase 2**: 5 benchmark adapters (OOLONG, OOLONG-Pairs, BrowseComp+, LongBench-v2 CodeQA, S-NIAH)
- **Phase 3**: 3 non-RLM baselines (direct, summary agent, CodeAct+BM25)
- **Phase 4**: 5 prompt arms (A0 vanilla, A1 LRU, A3 S3-FIFO, A4 SIEVE, A6 theory)
- **Phase 5**: experiment runner
- **Phase 6**: pilot (n=3 per bench, 120 queries, ~$108)
- **Phase 7**: full run (N=10/10/8/10/4 per bench, 336 queries, ~$300)
- **Phase 8**: quantitative + behavioral analysis
- **Phase 9**: writeup + slides + course-repo PR

## Smoke test

```bash
export CLAUDE_CODE_OAUTH_TOKEN='sk-ant-oat01-...'
uv run python experiments/smoke_test.py
```

Expected result on pass: finds the injected `SECRET_NUMBER=...` in a
40K-character haystack via recursive sub-calls. Typical cost ≈ $0.90.
