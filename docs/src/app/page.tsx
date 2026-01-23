import { CodeBlock } from "@/components/CodeBlock";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/Tabs";
import { Button } from "@/components/Button";
import Link from "next/link";

export default function Home() {
  return (
    <div>
      {/* WIP Warning */}
      <div className="mb-8 p-4 bg-amber-50 border-2 border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <strong>⚠️ Work in Progress:</strong> These documentation are highly WIP and subject to large changes. 
          It is helpful for minimally getting started, but will be updated as we go.
        </p>
      </div>

      {/* Hero Section */}
      <div className="mb-16">
        <h1 className="text-4xl md:text-5xl font-bold mb-8 tracking-tight text-foreground">
          Recursive Language Models
        </h1>
        
        <div className="flex flex-wrap gap-4 mb-12">
          <Button href="https://arxiv.org/abs/2512.24601" variant="default" external>
            Paper
          </Button>
          <Button href="https://github.com/alexzhang13/rlm" variant="outline" external>
            GitHub
          </Button>
        </div>
        
        <div className="max-w-4xl">
          <p className="text-xl text-muted-foreground mb-6 leading-relaxed">
            <strong className="text-foreground">Recursive Language Models (RLMs)</strong> are a task-agnostic inference paradigm for 
            language models to handle near-infinite length contexts by enabling the LM to{" "}
            <em className="text-foreground/90">programmatically</em> examine, decompose, and recursively call itself over its input.
          </p>

          <p className="text-lg text-muted-foreground leading-relaxed">
            RLMs replace the canonical <code className="px-1.5 py-0.5 rounded bg-muted text-foreground font-semibold text-base">llm.completion(prompt, model)</code> call with a{" "}
            <code className="px-1.5 py-0.5 rounded bg-muted text-foreground font-semibold text-base">rlm.completion(prompt, model)</code> call. RLMs offload the context as a variable in a 
            REPL environment that the LM can interact with and launch sub-LM calls inside of.
          </p>
        </div>
      </div>

      <div className="my-12">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl p-8 shadow-lg">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground">Installation</h2>
              <p className="text-sm text-muted-foreground">We use uv, but any virtual environment works.</p>
            </div>
          </div>
          
          <p className="text-muted-foreground mb-6 leading-relaxed">
            We use <code className="px-2 py-1 rounded-md bg-white border border-blue-200 text-foreground font-semibold">uv</code> for developing RLM. Install it first:
          </p>
          
          <CodeBlock language="bash" code={`# Install uv (first time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
uv init && uv venv --python 3.12
source .venv/bin/activate

# Install RLM in editable mode
uv pip install -e .

# For Modal sandbox support
uv pip install -e . --extra modal`} />
        </div>
        
        <p className="text-muted-foreground mt-6 leading-relaxed">
          Once installed, you can import and use RLM in your Python code. See the{" "}
          <Link href="/api" className="text-primary hover:underline font-medium">Using the RLM Client</Link>{" "}
          section for detailed API documentation and examples.
        </p>
      </div>

      <div className="my-16">
        <h2 className="text-3xl font-bold mb-4">Quick Start</h2>
        <p className="text-muted-foreground mb-6 leading-relaxed">
          These examples show how to initialize RLM with different LM providers. The RLM will automatically 
          execute Python code in a REPL environment to solve the task. For more details on configuration options, 
          see the <Link href="/api" className="text-primary hover:underline font-medium">Using the RLM Client</Link>{" "}
          documentation.
        </p>
      
      <Tabs defaultValue="openai">
        <TabsList>
          <TabsTrigger value="openai">OpenAI</TabsTrigger>
          <TabsTrigger value="anthropic">Anthropic</TabsTrigger>
          <TabsTrigger value="vercel">Vercel AI Gateway</TabsTrigger>
          <TabsTrigger value="portkey">Portkey</TabsTrigger>
        </TabsList>
        <TabsContent value="openai">
          <CodeBlock code={`import os
from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-5-mini",
    },
    verbose=False,  # print to logs
)

result = rlm.completion("Calculate 2^(2^(2^2)) using Python.")
print(result.response)`} />
        </TabsContent>
        <TabsContent value="anthropic">
          <CodeBlock code={`import os
from rlm import RLM

rlm = RLM(
    backend="anthropic",
    backend_kwargs={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model_name": "claude-sonnet-4-20250514",
    },
    verbose=False,  # print to logs
)

result = rlm.completion("Calculate 2^(2^(2^2)) using Python.")
print(result.response)`} />
        </TabsContent>
        <TabsContent value="vercel">
          <CodeBlock code={`import os
from rlm import RLM

rlm = RLM(
    backend="vercel",
    backend_kwargs={
        "api_key": os.getenv("AI_GATEWAY_API_KEY"),
        "model_name": "openai/gpt-5.2",  # Format: creator/model-name
    },
    verbose=False,  # print to logs
)

result = rlm.completion("Calculate 2^(2^(2^2)) using Python.")
print(result.response)`} />
        </TabsContent>
        <TabsContent value="portkey">
          <CodeBlock code={`import os
from rlm import RLM

rlm = RLM(
    backend="portkey",
    backend_kwargs={
        "api_key": os.getenv("PORTKEY_API_KEY"),
        "model_name": "@openai/gpt-5-mini",
    },
    verbose=False,  # print to logs
)

result = rlm.completion("Calculate 2^(2^(2^2)) using Python.")
print(result.response)`} />
        </TabsContent>
      </Tabs>
      </div>

      <div className="my-16">
        <h2 className="text-3xl font-bold mb-4">REPL Environments</h2>
        <p className="text-lg text-muted-foreground mb-8 leading-relaxed max-w-3xl">
          RLMs execute LM-generated Python code in a sandboxed REPL environment. We support two types 
          of environments: <strong className="text-foreground">non-isolated</strong> and <strong className="text-foreground">isolated</strong>.
        </p>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <h3 className="font-semibold text-foreground">Non-isolated environments</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              Run code on the same machine as the RLM process:
            </p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1.5 ml-2">
              <li><code className="px-1.5 py-0.5 rounded bg-white/80 text-foreground font-semibold">local</code> (default) — Same-process execution with sandboxed builtins. Fast but shares memory with host.</li>
              <li><code className="px-1.5 py-0.5 rounded bg-white/80 text-foreground font-semibold">docker</code> — Containerized execution in Docker. Better isolation, reproducible environments.</li>
            </ul>
          </div>

          <div className="bg-gradient-to-br from-emerald-50 to-teal-50/50 rounded-xl p-6 border border-emerald-200 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              <h3 className="font-semibold text-foreground">Isolated environments</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              Run code on completely separate machines, guaranteeing full isolation:
            </p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1.5 ml-2">
              <li><code className="px-1.5 py-0.5 rounded bg-white/80 text-foreground font-semibold">modal</code> — Cloud sandboxes via <a href="https://modal.com" className="text-primary hover:underline font-medium">Modal</a>. Production-ready, fully isolated from host.</li>
            </ul>
          </div>
        </div>

      <Tabs defaultValue="local">
        <TabsList>
          <TabsTrigger value="local">Local (Default)</TabsTrigger>
          <TabsTrigger value="docker">
            Docker
            <img 
              src="https://github.com/docker.png" 
              alt="Docker" 
              height="16" 
              className="ml-2 inline-block"
              style={{ height: '16px', verticalAlign: 'middle' }}
            />
          </TabsTrigger>
          <TabsTrigger value="modal">
            Modal
            <img 
              src="https://github.com/modal-labs.png" 
              alt="Modal" 
              height="16" 
              className="ml-2 inline-block"
              style={{ height: '16px', verticalAlign: 'middle' }}
            />
          </TabsTrigger>
        </TabsList>
        <TabsContent value="local">
          <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    environment="local",
)`} />
        </TabsContent>
        <TabsContent value="docker">
          <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    environment="docker",
    environment_kwargs={
        "image": "python:3.11-slim",
    },
)`} />
        </TabsContent>
        <TabsContent value="modal">
          <CodeBlock code={`rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    environment="modal",
    environment_kwargs={
        "app_name": "my-rlm-app",
        "timeout": 600,
    },
)`} />
        </TabsContent>
      </Tabs>

        <p className="text-muted-foreground mt-6">
          See <Link href="/environments" className="text-primary hover:underline">Environments</Link> for 
          details on each environment&apos;s architecture and configuration.
        </p>
      </div>

      <div className="my-16">
        <h2 className="text-3xl font-bold mb-6">Core Components</h2>
        
        <p className="text-muted-foreground mb-6 leading-relaxed text-lg max-w-4xl">
          RLMs indirectly handle contexts by storing them in a persistent REPL environment, where an LM can view and 
          run code inside of. It also has the ability to sub-query (R)LMs (i.e. with <code className="px-1.5 py-0.5 rounded bg-muted text-foreground text-sm font-semibold">llm_query</code> calls) 
          and produce a final answer based on this). This design generally requires the following components:
        </p>

        <div className="bg-gradient-to-br from-purple-50 to-pink-50/30 rounded-xl p-8 border border-purple-200/50 shadow-sm mb-6">
          <ol className="list-decimal list-inside text-muted-foreground space-y-3 text-lg max-w-2xl">
            <li>Set up a REPL environment, where state is persisted across code execution turns.</li>
            <li>Put the prompt (or context) into a programmatic variable.</li>
            <li>Allow the model to write code that peeks into and decomposes the variable, and observes any side effects.</li>
            <li>Encourage the model, in its code, to recurse over shorter, programmatically constructed prompts.</li>
          </ol>
        </div>

        <div className="bg-gradient-to-br from-slate-50 to-blue-50 border-2 border-slate-200 rounded-xl p-6">
          <img 
            src="/rlm/teaser.png" 
            alt="RLM Core Components Architecture" 
            className="rounded-lg shadow-sm w-full h-auto"
          />
        </div>
      </div>

      <div className="my-16">
        <h2 className="text-3xl font-bold mb-6">Citation</h2>
        <div className="bg-gradient-to-br from-amber-50 to-orange-50/30 rounded-xl p-6 border border-amber-200/50 shadow-sm">
          <pre className="text-sm font-mono leading-relaxed text-foreground">{`@misc{zhang2025recursivelanguagemodels,
      title={Recursive Language Models}, 
      author={Alex L. Zhang and Tim Kraska and Omar Khattab},
      year={2025},
      eprint={2512.24601},
      archivePrefix={arXiv},
}`}</pre>
        </div>
      </div>
    </div>
  );
}

