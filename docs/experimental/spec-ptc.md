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

The [spec-ptc library](https://github.com/alexzhang13/spec-ptc) runs a temporary trial copy of `repl` code while the model generates it. It can start `llm_query`, `llm_query_batched`, `rlm_query`, and `rlm_query_batched` early. Normal execution reuses matching results in call order; repeated identical calls still receive separate samples. Recursive batches retain their `(instruction, context)` pairs, and children inherit the flag and normal depth limits.

Custom tools and saved Python callables run only during real execution. Recursive calls are speculated only when their child tools contain no callables; otherwise those recursive calls run normally. Use `custom_sub_tools={}` to keep parent custom tools out of children. Generated child code can still perform effects through ordinary Python: speculative recursive tasks must themselves be suitable for early execution. LocalREPL and the library's shadow are not security sandboxes. Subcall callbacks describe actual executions and can therefore fire for speculative children that are later discarded.

Speculation can increase calls and cost when generated code changes or is discarded. All completed speculative work, including unclaimed recursive work, is included in usage accounting. Budget and timeout checks remain at RLM iteration boundaries; they are not a hard cap on already dispatched work. In-flight synchronous calls cannot be forcibly cancelled and are drained before turn teardown. Work still waiting for admission is skipped if it has already been evicted. This can delay cancellation/error cleanup until the underlying client call returns or times out.

The library also limits in-flight string arguments to 120,000 characters by default; this can serialize long-prompt batches. `spec_max_inflight_chars` makes that tradeoff configurable. Recursive concurrency uses `max_concurrent_subcalls`. Plain speculative work defaults to 16 workers, matching the normal LM batch handler. The dispatch limit counts tool invocations, not individual API calls inside a batch. To configure early work or observe reuse:

```python
rlm = RLM(
    ...,
    experimental_spec_ptc=True,
    environment_kwargs={
        "spec_max_inflight_chars": 120000,  # input characters across running tools
        "spec_max_inflight": 16,            # tool worker threads
        "spec_max_dispatches_per_turn": 16,  # tools started early; default 64
        "speculation_observer": print,      # started/reused/missed/discarded counts
    },
)
```

LocalREPL coordinates its process-wide stdout and working directory across recursive workers, releasing execution ownership while waiting for tools. It does not coordinate arbitrary host threads or other environment types changing the same process globals. The library uses a CPython-specific watchdog to stop trial execution. Large contexts also impose shadow-copy and parsing overhead, and opaque/non-copyable values can prevent speculation; normal execution still runs.

## Try the workload comparison

```bash
uv run --python 3.12 --extra spec-ptc python examples/spec_ptc_example.py --repeats 3
```

This runs the actual spec-ptc library, RLM loop, recursive REPLs, and LM socket protocol with deterministic scripted models and controlled generation/tool latency. It compares blocking, streaming-only, and speculative execution on independent, batched, dependent, pure-Python, discarded-code, and recursive workloads. Answers must match across modes. It reports actual model call counts, cache claims, evictions, active iteration time, and end-to-end wall time (which includes setup and teardown). It makes no external API calls; these timings do not predict every real provider or workload.

For long-input batches, increase the input-character limit only if your provider can handle the extra concurrent load:

```bash
uv run --python 3.12 --extra spec-ptc python examples/spec_ptc_example.py \
  --scenario long_context --spec-inflight-chars 1000000 --repeats 3
```
