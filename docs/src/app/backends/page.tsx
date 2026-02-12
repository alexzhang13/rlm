import { CodeBlock } from "@/components/CodeBlock";

export default function BackendsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Backends</h1>
      
      <p className="text-muted-foreground mb-6">
        <p>
          RLMs natively support a wide range of language model providers, including <code>OpenAI</code>, <code>Anthropic</code>, <code>Azure Anthropic (Foundry)</code>, <code>Azure OpenAI</code>, <code>Portkey</code>, <code>OpenRouter</code>, and <code>LiteLLM</code>. Additional providers can be supported with minimal effort. The <code>backend_kwargs</code> are named arguments passed directly to the backend client.
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

      <h2 className="text-2xl font-semibold mb-4">Azure Anthropic (Foundry)</h2>
      <p className="text-muted-foreground mb-4">
        For Anthropic models hosted on{" "}
        <a href="https://ai.azure.com/" className="text-primary underline font-medium" target="_blank" rel="noopener noreferrer">Azure AI Foundry</a>.
        Uses the same <code>ANTHROPIC_FOUNDRY_*</code> environment variable convention as{" "}
        <a href="https://docs.anthropic.com/en/docs/claude-code" className="text-primary underline font-medium" target="_blank" rel="noopener noreferrer">Claude Code</a>,
        so if you already have those env vars set, this backend picks them up automatically.
      </p>
      <CodeBlock language="bash" code={`# Set Foundry credentials (same vars Claude Code uses)
export ANTHROPIC_FOUNDRY_API_KEY="your-key"
export ANTHROPIC_FOUNDRY_RESOURCE="ml-platform-openai-stg-useast-2"
# Or use a project-scoped endpoint instead of RESOURCE:
# export ANTHROPIC_FOUNDRY_BASE_URL="https://res.services.ai.azure.com/api/projects/my-proj"`} />
      <CodeBlock code={`rlm = RLM(
    backend="azure_anthropic",
    backend_kwargs={
        "model_name": "claude-opus-4-6",
        # Credentials read from ANTHROPIC_FOUNDRY_* env vars.
        # Or pass explicitly:
        # "resource": "ml-platform-openai-stg-useast-2",
        # "api_key": "...",
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

      <h2 className="text-2xl font-semibold mb-4">Multiple Backends (Experimental)</h2>
      <p className="text-muted-foreground mb-4">
        <strong>Experimental:</strong> This feature allows you to specify <em>ordered</em> lists of backends and model kwargs, so that RLMs can sub-call different language models from within execution code. 
        The order of <code>other_backends</code> and <code>other_backend_kwargs</code> must match: e.g., the 0th element of <code>other_backends</code> is used with the 0th dict in <code>other_backend_kwargs</code>.
        <br />
        <br />
        <span className="font-medium">
          This functionality is for advanced use and is currently experimental.
        </span>
        It will become more useful as RLMs get the ability to orchestrate and delegate between different LMs within a workflow.
      </p>
      <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    other_backends=["anthropic", "openai"],  # ORDER MATTERS!
    other_backend_kwargs=[
        {"model_name": "claude-sonnet-4-20250514"},
        {"model_name": "gpt-4o-mini"},
    ],  # ORDER MATCHES other_backends
)`} />
      <p className="text-muted-foreground mt-4">Inside REPL (future releases):</p>
      <CodeBlock code={`llm_query("prompt")  # Uses default (gpt-5-mini)
llm_query("prompt", model="claude-sonnet-4-20250514")  # Uses Claude 
llm_query("prompt", model="gpt-4o-mini")  # Uses GPT-4o-mini`} />
    </div>
  );
}

