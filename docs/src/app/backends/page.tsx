import { CodeBlock } from "@/components/CodeBlock";

export default function BackendsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Backends</h1>
      
      <p className="text-muted-foreground mb-6">
        <p>
          RLMs natively support a wide range of language model providers, including <code>OpenAI</code>, <code>Anthropic</code>, <code>Portkey</code>, <code>OpenRouter</code>, and <code>LiteLLM</code>. Additional providers can be supported with minimal effort. The <code>backend_kwargs</code> are named arguments passed directly to the backend client.
        </p>
      </p>

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">OpenAI</h2>
      <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={
        "api_key": os.getenv("OPENAI_API_KEY"),  # or set OPENAI_API_KEY env
        "model_name": "gpt-5-mini",
        "base_url": "https://api.openai.com/v1",  # optional
    },
)`} />

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">Anthropic</h2>
      <CodeBlock code={`rlm = RLM(
    backend="anthropic",
    backend_kwargs={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model_name": "claude-sonnet-4-20250514",
    },
)`} />

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">Portkey</h2>
      <p className="text-muted-foreground mb-4">
        <a href="https://portkey.ai/docs/api-reference/sdk/python" className="text-primary underline font-medium" target="_blank" rel="noopener noreferrer">Portkey</a> is a client for routing to hundreds of different open and closed frontier models.
      </p>
      <CodeBlock code={`rlm = RLM(
    backend="portkey",
    backend_kwargs={
        "api_key": os.getenv("PORTKEY_API_KEY"),
        "model_name": "@openai/gpt-5-mini",  # Portkey format: @provider/model
    },
)`} />

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">OpenRouter</h2>
      <p className="text-muted-foreground mb-4">
        <a href="https://openrouter.ai/docs" className="text-primary underline font-medium" target="_blank" rel="noopener noreferrer">OpenRouter</a> is a multi-provider gateway for accessing a wide range of models from different providers through one API.
      </p>
      <CodeBlock code={`rlm = RLM(
    backend="openrouter",
    backend_kwargs={
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model_name": "openai/gpt-5-mini",  # Format: provider/model
    },
)`} />

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">LiteLLM</h2>
      <p className="text-muted-foreground mb-4">
        <a href="https://docs.litellm.ai/docs/" className="text-primary underline font-medium" target="_blank" rel="noopener noreferrer">LiteLLM</a> is a universal interface for 100+ model providers, with support for local models and custom endpoints.
      </p>
      <CodeBlock code={`rlm = RLM(
    backend="litellm",
    backend_kwargs={
        "model_name": "gpt-5-mini",
    },
)
# Set provider API keys in environment`} />

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">vLLM (Local)</h2>
      <p className="text-muted-foreground mb-4">Local model serving.</p>
      <CodeBlock language="bash" code={`# Start vLLM server
python -m vllm.entrypoints.openai.api_server \\
    --model meta-llama/Llama-3-70b \\
    --port 8000`} />
      <CodeBlock code={`rlm = RLM(
    backend="vllm",
    backend_kwargs={
        "base_url": "http://localhost:8000/v1",  # Required
        "model_name": "meta-llama/Llama-3-70b",
    },
)`} />

      <hr className="my-8 border-border" />

      <h2 className="text-2xl font-semibold mb-4">Depth-Specific Backends</h2>
      <p className="text-muted-foreground mb-4">
        Provide an ordered list of backends and model kwargs, one per recursion depth.
        The order of <code>other_backends</code> and <code>other_backend_kwargs</code> must match: the 0th
        entry is used at depth 1, the 1st entry at depth 2, and so on. Missing depths fall back to the
        root backend.
        <br />
        <br />
        This is an advanced feature for controlling cost/quality across recursive calls.
      </p>
      <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    recursive_max_depth=3,
    other_backends=["anthropic", "openai", "openai"],  # depth 1..3
    other_backend_kwargs=[
        {"model_name": "claude-sonnet-4-20250514"},
        {"model_name": "gpt-4o-mini"},
        {"model_name": "gpt-4o-nano"},
    ],  # ORDER MATCHES other_backends
)`} />
    </div>
  );
}
