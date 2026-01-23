import { CodeBlock } from "@/components/CodeBlock";
import { Table } from "@/components/Table";

export default function APIPage() {
  return (
    <div className="max-w-4xl">
      {/* Hero Section */}
      <div className="mb-12">
        <h1 className="text-5xl font-bold mb-4 tracking-tight">Using the RLM Client</h1>
        <p className="text-xl text-muted-foreground leading-relaxed">
          The main class for recursive language model completions. Enables LMs to programmatically 
          examine, decompose, and recursively call themselves over their input.
        </p>
      </div>

      {/* Quick Example */}
      <div className="mb-12 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl">
        <h2 className="text-lg font-semibold mb-3 text-foreground">Quick Example</h2>
        <CodeBlock code={`from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
)
result = rlm.completion("Your prompt here")
print(result.response)`} />
      </div>

      {/* Constructor */}
      <div className="mb-16">
        <h2 className="text-3xl font-bold mb-6">Constructor</h2>

        <CodeBlock code={`RLM(
    backend: str = "openai",
    backend_kwargs: dict | None = None,
    environment: str = "local",
    environment_kwargs: dict | None = None,
    depth: int = 0,
    max_depth: int = 1,
    max_iterations: int = 30,
    custom_system_prompt: str | None = None,
    other_backends: list[str] | None = None,
    other_backend_kwargs: list[dict] | None = None,
    logger: RLMLogger | None = None,
    verbose: bool = False,
)`} />

        <div className="mt-8 space-y-10">
          {/* backend */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">backend</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">str</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: "openai"</span>
            </div>
            <p className="text-muted-foreground mb-4">LM provider to use for completions.</p>
            <Table
              headers={["Value", "Provider"]}
              rows={[
                [<code key="1" className="text-sm">"openai"</code>, "OpenAI API"],
                [<code key="2" className="text-sm">"anthropic"</code>, "Anthropic API"],
                [<code key="3" className="text-sm">"vercel"</code>, "Vercel AI Gateway"],
                [<code key="4" className="text-sm">"portkey"</code>, "Portkey AI gateway"],
                [<code key="5" className="text-sm">"openrouter"</code>, "OpenRouter"],
                [<code key="6" className="text-sm">"litellm"</code>, "LiteLLM (multi-provider)"],
                [<code key="7" className="text-sm">"vllm"</code>, "Local vLLM server"],
              ]}
            />
          </div>

          {/* backend_kwargs */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">backend_kwargs</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">dict | None</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: None</span>
            </div>
            <p className="text-muted-foreground mb-4">Provider-specific configuration (API keys, model names, etc.).</p>
            <CodeBlock code={`# OpenAI / Anthropic
backend_kwargs={
    "api_key": "...",
    "model_name": "gpt-5-mini",
}

# Vercel AI Gateway
backend_kwargs={
    "api_key": "...",
    "model_name": "openai/gpt-5.2",  # Format: creator/model-name
}

# vLLM (local)
backend_kwargs={
    "base_url": "http://localhost:8000/v1",
    "model_name": "meta-llama/Llama-3-70b",
}

# Portkey
backend_kwargs={
    "api_key": "...",
    "model_name": "@openai/gpt-5-mini",
}`} />
          </div>

          {/* environment */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">environment</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">str</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: "local"</span>
            </div>
            <p className="text-muted-foreground mb-4">Code execution environment for REPL interactions.</p>
            <Table 
              headers={["Value", "Description"]}
              rows={[
                [<code key="1" className="text-sm">"local"</code>, "Same-process with sandboxed builtins"],
                [<code key="2" className="text-sm">"docker"</code>, "Docker container"],
                [<code key="3" className="text-sm">"modal"</code>, "Modal cloud sandbox"],
              ]}
            />
          </div>

          {/* environment_kwargs */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">environment_kwargs</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">dict | None</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: None</span>
            </div>
            <p className="text-muted-foreground mb-4">Environment-specific configuration.</p>
            <CodeBlock code={`# Docker
environment_kwargs={"image": "python:3.11-slim"}

# Modal
environment_kwargs={
    "app_name": "my-app",
    "timeout": 600,
}

# Local
environment_kwargs={"setup_code": "import numpy as np"}`} />
          </div>

          {/* max_iterations */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">max_iterations</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">int</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: 30</span>
            </div>
            <p className="text-muted-foreground">Maximum REPL iterations before forcing a final answer.</p>
          </div>

          {/* max_depth */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">max_depth</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">int</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: 1</span>
            </div>
            <div className="mb-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
              <p className="text-sm text-amber-800">
                <strong>Note:</strong> This is a TODO. Only <code className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 text-xs font-semibold">max_depth=1</code> is currently supported.
              </p>
            </div>
            <p className="text-muted-foreground">
              Maximum recursion depth. When <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm">depth {">="} max_depth</code>, falls back to regular LM completion.
            </p>
          </div>

          {/* custom_system_prompt */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">custom_system_prompt</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">str | None</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: None</span>
            </div>
            <p className="text-muted-foreground">Override the default RLM system prompt.</p>
          </div>

          {/* other_backends */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">other_backends</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">list[str] | None</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: None</span>
            </div>
            <p className="text-muted-foreground mb-4">Additional backends available for sub-LM calls within the REPL.</p>
            <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    other_backends=["anthropic"],
    other_backend_kwargs=[{"model_name": "claude-sonnet-4-20250514"}],
)`} />
          </div>

          {/* other_backend_kwargs */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">other_backend_kwargs</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">list[dict] | None</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: None</span>
            </div>
            <p className="text-muted-foreground">Configurations for <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm">other_backends</code> (must match order).</p>
          </div>

          {/* logger */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">logger</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">RLMLogger | None</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: None</span>
            </div>
            <p className="text-muted-foreground mb-4">Logger for saving RLM execution trajectories to JSON-lines files.</p>
            <CodeBlock code={`from rlm.logger import RLMLogger

logger = RLMLogger(log_dir="./logs")
rlm = RLM(..., logger=logger)`} />
          </div>

          {/* verbose */}
          <div className="border-l-4 border-blue-500 pl-6">
            <div className="flex items-baseline gap-3 mb-2">
              <code className="text-lg font-semibold text-foreground">verbose</code>
              <span className="text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground font-mono">bool</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-100 text-blue-700 font-mono">default: False</span>
            </div>
            <p className="text-muted-foreground">Enable rich console output showing iterations, code execution, and results.</p>
          </div>
        </div>
      </div>

      {/* completion method */}
      <div className="mb-16">
        <h2 className="text-3xl font-bold mb-6">Methods</h2>

        <div className="border-l-4 border-indigo-500 pl-6 mb-8">
          <div className="flex items-baseline gap-3 mb-4">
            <code className="text-2xl font-semibold text-foreground">completion()</code>
          </div>
          <p className="text-muted-foreground mb-4 text-lg">Main method for RLM completions. Executes the recursive loop and returns the final result.</p>
          
          <p className="text-muted-foreground mb-6 leading-relaxed">
            The method returns an <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">RLMChatCompletion</code> object 
            containing the final response, execution metadata, and usage statistics. This object provides access to the RLM&apos;s output and performance metrics.
          </p>
          
          <CodeBlock code={`result = rlm.completion(
    prompt: str | dict,
    root_prompt: str | None = None,
)`} />

          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4 text-foreground">Arguments</h3>
            <Table 
              headers={["Name", "Type", "Description"]}
              rows={[
                [
                  <code key="1" className="text-sm font-semibold">prompt</code>, 
                  <code key="2" className="text-sm">str | dict</code>, 
                  <span key="5">Input context (becomes <code className="text-xs px-1 py-0.5 rounded bg-muted text-foreground">context</code> variable in REPL)</span>
                ],
                [
                  <code key="3" className="text-sm font-semibold">root_prompt</code>, 
                  <code key="4" className="text-sm">str | None</code>, 
                  "Optional hint visible only to the root LM call"
                ],
              ]}
            />
          </div>

          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4 text-foreground">Returns</h3>
            <p className="text-muted-foreground mb-4"><code className="px-2 py-1 rounded bg-muted text-foreground text-sm font-semibold">RLMChatCompletion</code> object with:</p>
            <Table 
              headers={["Attribute", "Type", "Description"]}
              rows={[
                [<code key="1" className="text-sm font-semibold">response</code>, <code key="2" className="text-sm">str</code>, "Final answer from the RLM"],
                [<code key="3" className="text-sm font-semibold">execution_time</code>, <code key="4" className="text-sm">float</code>, "Total execution time in seconds"],
                [<code key="5" className="text-sm font-semibold">usage_summary</code>, <code key="6" className="text-sm">UsageSummary</code>, "Aggregated token usage across all LM calls"],
                [<code key="7" className="text-sm font-semibold">root_model</code>, <code key="8" className="text-sm">str</code>, "Model name used for root completion"],
              ]}
            />
          </div>
        </div>
      </div>

    </div>
  );
}
