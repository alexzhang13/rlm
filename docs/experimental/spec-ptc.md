# Experimental speculative tool calling

On Python 3.12+, install `pip install 'rlms[spec-ptc]'` and opt in:

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "your-streaming-model"},
    experimental_spec_ptc=True,
)
```

The flag defaults to `False`. It enables real model streaming and requires `environment="local"`. Unsupported environments and clients without streaming raise a clear error. Normal RLM usage still supports Python 3.11 and does not import spec-ptc.

The [spec-ptc library](https://github.com/alexzhang13/spec-ptc) executes a discarded shadow of streamed `repl` code. It can start `llm_query`, `llm_query_batched`, `rlm_query`, and `rlm_query_batched` early. Normal execution claims matching results in FIFO order, preserving fresh samples for repeated identical calls. Recursive batches retain their `(instruction, context)` pairs, and children inherit the flag and normal depth limits.

Custom tools and saved Python callables run only during real execution. Recursive calls are speculated only when their child tools contain no callables; otherwise those recursive calls run normally. Use `custom_sub_tools={}` to keep parent custom tools out of children. Generated child code can still perform effects through ordinary Python: speculative recursive tasks must themselves be suitable for early execution. LocalREPL and the library's shadow are not security sandboxes. Subcall callbacks describe actual executions and can therefore fire for speculative children that are later discarded.

Speculation can increase calls and cost when generated code changes or is discarded. All completed speculative work, including unclaimed recursive work, is included in usage accounting. Budget and timeout checks remain at RLM iteration boundaries; they are not a hard cap on already dispatched work. In-flight synchronous calls cannot be forcibly cancelled and are drained before turn teardown. Work still waiting for admission is skipped if it has already been evicted. This can delay cancellation/error cleanup until the underlying client call returns or times out.

The library also limits in-flight string arguments to 120,000 characters by default; this can serialize long-prompt batches. `spec_max_inflight_chars` makes that tradeoff configurable. Recursive concurrency uses `max_concurrent_subcalls`. Plain speculative work defaults to 16 workers, matching the normal LM batch handler. To configure early work or observe reuse:

```python
rlm = RLM(
    ...,
    experimental_spec_ptc=True,
    environment_kwargs={
        "spec_max_inflight_chars": 120000,  # library prefill-pressure budget
        "spec_max_inflight": 16,            # worker pool size
        "spec_max_dispatches_per_turn": 16,  # default 64 dispatches, not an API-call cap
        "speculation_observer": print,      # dispatch/hit/miss/eviction counts per turn
    },
)
```

LocalREPL coordinates its process-wide stdout and working directory across recursive workers, releasing execution ownership while waiting for tools. It does not coordinate arbitrary host threads or other environment types changing the same process globals. This adapter is tested against spec-ptc 0.1.1 on CPython 3.12; the library uses a CPython-specific shadow watchdog. Large contexts also impose shadow-copy and parsing overhead, and opaque/non-copyable values can prevent speculation; normal execution still runs.

## Try the workload comparison

```bash
uv run --python 3.12 --extra spec-ptc python examples/spec_ptc_example.py --repeats 3
```

This runs the actual spec-ptc library, RLM loop, recursive REPLs, and LM socket protocol with deterministic scripted models and controlled generation/tool latency. It compares blocking, streaming-only, and speculative execution on independent, batched, dependent, pure-Python, discarded-code, and recursive workloads. Answers must match across modes. It reports actual model call counts, cache claims, evictions, active iteration time, and end-to-end wall time (which includes setup and teardown). It makes no external API calls; these timings do not predict every real provider or workload.

## Sample results (2026-11-21)

CPython 3.12.7 on macOS, spec-ptc 0.1.1, three repetitions per mode; median seconds. Scripted generation waits 40 ms per line and each simulated tool completion takes 150 ms. All modes returned identical answers. This table compares streaming-only with speculative streaming; the example also runs blocking generation.

| Workload | Active: stream → spec | Wall: stream → spec | Total LM calls: stream → spec |
|---|---:|---:|---:|
| independent | 0.611 → 0.303 | 0.957 → 0.649 | 3 → 3 |
| batched | 0.386 → 0.259 | 0.743 → 0.606 | 5 → 5 |
| large batch | 0.545 → 0.421 | 0.746 → 0.766 | 21 → 21 |
| long context | 0.458 → 1.435 | 0.799 → 1.783 | 9 → 9 |
| dependent | 0.603 → 0.424 | 0.954 → 0.769 | 3 → 3 |
| no tools | 0.182 → 0.192 | 0.504 → 0.504 | 1 → 1 |
| discarded | 0.423 → 0.449 | 0.505 → 0.609 | 2 → 3 |
| recursive | 1.182 → 0.749 | 1.508 → 1.005 | 4 → 4 |

Independent and recursive work overlapped usefully. The 20-call batch reduced active time but increased wall time slightly; setup, teardown, and scheduling matter for small workloads. The discarded-code case made one extra call and took longer. A preliminary four-worker configuration bottlenecked the large batch (0.901 s active); separating the plain-LM worker pool from the recursive limit reduced that to 0.421 s.

The long-context workload sends eight 100,000-character prompts. The default 120,000-character pressure budget effectively serializes them and slows this synthetic workload considerably. With a 1,000,000-character budget, a separate three-repeat run measured 0.453 → 0.323 s active and 0.798 → 0.666 s wall, with the same nine model calls. Higher pressure budgets increase concurrent backend load; choose them for the capacity and latency behavior of your provider.

```bash
uv run --python 3.12 --extra spec-ptc python examples/spec_ptc_example.py \
  --scenario long_context --spec-inflight-chars 1000000 --repeats 3
```

Live smoke-test attempts through the configured OpenAI-compatible endpoint returned HTTP 429. Successful live-provider execution and provider latency improvements remain unverified; the measurements above are controlled simulations.

## Validation

- Full CPython 3.12 suite with spec-ptc 0.1.1, IPython, and Docker: 525 passed, 7 skipped.
- Full CPython 3.11 suite without spec-ptc: 487 passed, 8 skipped.
- Integration coverage includes all four query helpers, model arguments, FIFO multiplicity, dependent calls, multi-block turns, persistence, depth boundaries, custom-tool gating, isolated stdout/relative files, concurrent cells on one REPL, budget accounting (including failed and discarded child work), stream interruption, and eviction of work waiting for character-budget admission.
- Ruff, formatting, pre-commit, and lockfile checks pass.
