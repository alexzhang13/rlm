import { Table } from "@/components/Table";
import { CodeBlock } from "@/components/CodeBlock";
import Link from "next/link";

export default function EnvironmentsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">REPL Environments</h1>
      
      <p className="text-xl text-muted-foreground mb-6 leading-relaxed">
        REPL environments are sandboxed Python execution contexts where the LM can write and execute code 
        to analyze the input context. These environments provide the LM with programmatic access to 
        computation, data processing, and the ability to make sub-LM calls.
      </p>

      <p className="text-muted-foreground mb-8 leading-relaxed">
        When you call <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">rlm.completion(prompt)</code>, 
        your prompt becomes the <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">context</code> variable 
        in a Python REPL. The LM can then write Python code to examine this context, decompose complex tasks, 
        and recursively call itself via <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">llm_query()</code> 
        to handle sub-problems.
      </p>

      <div className="my-12">
        <h2 className="text-2xl font-bold mb-4">Isolation Levels</h2>
        
        <p className="text-muted-foreground mb-6 leading-relaxed">
          RLM supports two types of environments based on their isolation level:
        </p>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-xl p-6 border border-slate-200 shadow-sm">
            <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              Non-Isolated Environments
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Run code on the same machine as the RLM process (or in a container on the same host).
            </p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1.5 ml-2">
              <li><strong className="text-foreground">Faster execution</strong> — No network overhead</li>
              <li><strong className="text-foreground">Shared resources</strong> — Access to host filesystem, network, and memory</li>
              <li><strong className="text-foreground">Lower security</strong> — Code runs with host process privileges</li>
              <li><strong className="text-foreground">Use cases:</strong> Development, testing, trusted code</li>
            </ul>
          </div>

          <div className="bg-gradient-to-br from-emerald-50 to-teal-50/50 rounded-xl p-6 border border-emerald-200 shadow-sm">
            <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              Isolated Environments
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Run code on completely separate machines (cloud VMs), guaranteeing full isolation.
            </p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1.5 ml-2">
              <li><strong className="text-foreground">Full isolation</strong> — No access to host resources</li>
              <li><strong className="text-foreground">Higher security</strong> — Code cannot affect host system</li>
              <li><strong className="text-foreground">Network overhead</strong> — Communication via HTTP tunnels</li>
              <li><strong className="text-foreground">Use cases:</strong> Production, untrusted code, sensitive data</li>
            </ul>
          </div>
        </div>

        <p className="text-muted-foreground leading-relaxed">
          <strong className="text-foreground">Why this matters:</strong> The isolation level determines the security 
          and trust model of your RLM application. Non-isolated environments are faster and simpler, but code execution 
          shares the host&apos;s resources and privileges. Isolated environments provide complete separation, making them 
          essential for production deployments or when executing untrusted LM-generated code.
        </p>
      </div>

      <div className="my-12">
        <h2 className="text-2xl font-bold mb-4">Available Environments</h2>
        <Table 
          headers={["Environment", "Isolation", "Best For"]}
          rows={[
            [<Link key="1" href="/environments/local" className="text-primary hover:underline"><code>local</code></Link>, "Non-isolated", "Development"],
            [<Link key="2" href="/environments/docker" className="text-primary hover:underline"><code>docker</code></Link>, "Non-isolated", "CI/CD, reproducibility"],
            [<Link key="3" href="/environments/modal" className="text-primary hover:underline"><code>modal</code></Link>, "Isolated", "Production"],
          ]}
        />
      </div>

      <div className="my-12">
        <h2 className="text-2xl font-bold mb-4">REPL Globals</h2>
        
        <p className="text-muted-foreground mb-6 leading-relaxed">
          These variables and functions are available inside code executed in the REPL environment:
        </p>

        <div className="bg-gradient-to-br from-slate-50 to-blue-50 border-2 border-slate-200 rounded-xl p-6 mb-6">
          <Table 
            headers={["Name", "Description"]}
            rows={[
              [
                <code key="1" className="text-sm font-semibold">context</code>, 
                "Your input prompt, available as a variable in the REPL"
              ],
              [
                <code key="2" className="text-sm font-semibold">llm_query(prompt, model=None)</code>, 
                "Query a sub-LM from within the REPL. Returns the completion string."
              ],
              [
                <code key="3" className="text-sm font-semibold">llm_query_batched(prompts, model=None)</code>, 
                "Concurrent sub-LM queries. Returns a list of completion strings."
              ],
              [
                <code key="4" className="text-sm font-semibold">FINAL_VAR(var_name)</code>, 
                "Mark a variable as the final answer to return from the RLM"
              ],
              [
                <code key="5" className="text-sm font-semibold">custom_tools</code>, 
                "Any custom functions or data you provide via the custom_tools parameter"
              ],
            ]}
          />
        </div>

        <CodeBlock code={`# Example usage in REPL
context = "Your input here"

# Query a sub-LM
result = llm_query("Summarize the context", model="gpt-5-mini")

# Use a custom tool (if provided)
data = fetch_data(context["url"])  # Custom function

# Process the result
summary = process(result)

# Return final answer
FINAL_VAR(summary)`} />
      </div>

      <div className="my-12">
        <h2 className="text-2xl font-bold mb-4">Custom Tools</h2>
        
        <p className="text-muted-foreground mb-6 leading-relaxed">
          You can provide custom functions and data that the RLM can use in its REPL environment 
          via the <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">custom_tools</code> parameter:
        </p>

        <CodeBlock code={`from rlm import RLM

def fetch_weather(city: str) -> str:
    """Fetch weather data for a city."""
    return f"Weather in {city}: Sunny, 72°F"

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    custom_tools={
        # Plain format (no description)
        "fetch_weather": fetch_weather,
        
        # Dict format with description (recommended)
        "calculate_tip": {"tool": lambda x: x * 0.2, "description": "Calculate 20% tip for a bill amount"},
        "API_KEY": {"tool": "your-key", "description": "API key for external services"},
    },
)

# The model can now call fetch_weather() in its REPL code`} />

        <p className="text-muted-foreground mt-6 leading-relaxed">
          <strong className="text-foreground">Tool descriptions:</strong> Use the dict format 
          <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">{`{"tool": value, "description": "..."}`}</code> to 
          provide descriptions that help the model understand what each tool does. Descriptions are automatically 
          included in the system prompt.
        </p>

        <p className="text-muted-foreground mt-4 leading-relaxed">
          <strong className="text-foreground">Sub-agent tools:</strong> By default, sub-agents (code using 
          <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">llm_query()</code>) 
          inherit the same custom tools. Use <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">custom_sub_tools</code> to 
          provide different tools for sub-agents, or pass an empty dict to disable tools for sub-agents.
        </p>
      </div>

      <div className="my-12">
        <h2 className="text-2xl font-bold mb-4">Architecture</h2>

      <h3 className="text-lg font-medium mt-6 mb-2">Non-Isolated (local, docker)</h3>
      <p className="text-muted-foreground mb-4">Direct TCP socket communication:</p>
      <pre className="text-sm">{`┌────────────┐   Socket   ┌────────────┐
│ Environment│◄──────────►│ LM Handler │
│ llm_query()│            │            │
└────────────┘            └────────────┘`}</pre>

      <h3 className="text-lg font-medium mt-6 mb-2">Isolated (modal)</h3>
      <p className="text-muted-foreground mb-4">HTTP broker pattern for cloud sandboxes:</p>
      <pre className="text-sm">{`┌─────────────────────────────────────┐
│ Host                                │
│  ┌──────────┐       ┌────────────┐ │
│  │ ModalREPL│◄─────►│ LM Handler │ │
│  │ (polls)  │Socket └────────────┘ │
│  └────┬─────┘                      │
│       │ HTTP                       │
└───────┼────────────────────────────┘
        ▼
┌───────────────────────────────────────┐
│ Modal Sandbox                         │
│  ┌────────────┐     ┌──────────────┐ │
│  │   Broker   │◄───►│ Code Exec    │ │
│  │  (Flask)   │     │ llm_query()  │ │
│  └────────────┘     └──────────────┘ │
└───────────────────────────────────────┘`}</pre>

      <p className="text-muted-foreground mt-4">
        The broker queues <code>llm_query()</code> requests, host polls for pending requests, 
        forwards them to the LM Handler, and posts responses back.
      </p>
      </div>
    </div>
  );
}

