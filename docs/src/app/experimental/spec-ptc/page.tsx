import { CodeBlock } from "@/components/CodeBlock";
import { Table } from "@/components/Table";

export default function SpecPTCPage() {
  return (
    <div className="max-w-4xl space-y-12">
      <header>
        <h1 className="text-4xl font-bold mb-4">Experimental speculative tool calling</h1>
        <p className="text-lg text-muted-foreground">
          Start LM and recursive RLM calls while the model is still generating code, using{" "}
          <a href="https://github.com/alexzhang13/spec-ptc" className="text-primary hover:underline">
            spec-ptc
          </a>.
        </p>
      </header>

      <section>
        <h2 className="text-2xl font-bold mb-4">Enable speculation</h2>
        <p>
          Requires Python 3.12+, LocalREPL, and a streaming-capable model client.
          The feature is experimental and disabled by default.
        </p>
        <CodeBlock language="bash" code={`pip install 'rlms[spec-ptc]'`} />
        <CodeBlock code={`from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    environment="local",
    experimental_spec_ptc=True,
)
result = rlm.completion("Your context", root_prompt="Your instruction")
print(result.response)`} />
        <p className="text-muted-foreground">
          Enabling the flag also enables streaming. Unsupported clients or environments raise an
          error. Standard RLM usage still supports Python 3.11 without installing spec-ptc.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">How calls execute</h2>
        <p>
          A temporary trial copy of generated REPL code starts eligible calls early. Normal execution
          reuses matching results in call order; repeated identical calls still receive separate samples.
          All four helpers are supported: <code>llm_query</code>, <code>llm_query_batched</code>,{" "}
          <code>rlm_query</code>, and <code>rlm_query_batched</code>.
        </p>
        <CodeBlock code={`result = rlm_query("Summarize this document", context=document)
results = rlm_query_batched([
    ("Summarize this document", document_a),
    ("Extract the key dates", document_b),
])`} />
        <p className="text-muted-foreground">
          Recursive children inherit the flag and run in their own REPL. Batch results preserve input
          order. Normal depth limits apply: at the limit, the instruction and context are included
          in a plain LM call.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Configure early work</h2>
        <p>
          Pass these options through <code>environment_kwargs</code>. Recursive concurrency uses
          the RLM argument <code>max_concurrent_subcalls</code>.
        </p>
        <Table
          headers={["Option", "Default", "Purpose"]}
          rows={[
            ["spec_max_inflight", "16", "Tool worker threads."],
            ["spec_max_inflight_chars", "120000", "Limit on in-flight string arguments."],
            ["spec_max_dispatches_per_turn", "64", "Tool invocations started early per turn; not an API-call cap for batches."],
            ["speculation_observer", "None", "Callback receiving dispatch, claim_hit, claim_miss, and evict counts per turn."],
          ]}
        />
        <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    experimental_spec_ptc=True,
    max_concurrent_subcalls=4,
    environment_kwargs={
        "spec_max_inflight_chars": 120000,
        "spec_max_dispatches_per_turn": 16,
        "speculation_observer": print,
    },
)`} />
        <p className="text-muted-foreground">
          The character limit can serialize long-input batches. Increasing it allows more concurrent
          backend load. Observer counts describe tools started early, results reused, calls without a
          reusable result, and discarded work.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Limitations</h2>
        <ul className="list-disc pl-6 space-y-3 text-muted-foreground">
          <li>
            Discarded code can add calls and cost. Completed speculative work, including unused or
            failed recursive work, counts toward usage. Budget and timeout checks occur between
            iterations and do not cap already dispatched work.
          </li>
          <li>
            Running synchronous calls cannot be forcibly cancelled. Cleanup waits for them to finish
            or time out; discarded work that has not started is skipped.
          </li>
          <li>
            Custom tools and saved Python callables run only during normal execution. Recursive calls
            whose child tools contain callables also run normally. Use <code>custom_sub_tools={"{}"}</code>{" "}
            to keep parent tools out of children. Generated child Python can still have effects:
            speculative recursive tasks must be suitable for early execution. Subcall callbacks can
            fire for children whose results are later discarded.
          </li>
          <li>
            LocalREPL and trial execution are not security sandboxes. LocalREPL coordinates stdout
            and working directories across its workers, but cannot coordinate arbitrary host threads
            or other environment types changing the same process globals.
          </li>
          <li>
            The library uses a CPython-specific watchdog. Large contexts add copying and parsing
            overhead, and values that cannot be copied may prevent speculation. Normal execution
            still runs.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Compare workloads</h2>
        <p>
          From the repository checkout, compare blocking, streaming-only, and speculative execution
          with scripted models. The example reports model call counts, result reuse, discarded work,
          and elapsed time. It makes no external API calls; simulated timings do not predict provider
          performance.
        </p>
        <CodeBlock language="bash" code={`uv run --python 3.12 --extra spec-ptc python examples/spec_ptc_example.py --repeats 3`} />
      </section>
    </div>
  );
}
