'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { KeyValueEditor } from './KeyValueEditor';
import { cn } from '@/lib/utils';

interface PlaygroundFormProps {
  onRun: (config: any) => void;
  loading: boolean;
}

interface KeyValuePair {
  key: string;
  value: string;
}

export function PlaygroundForm({ onRun, loading }: PlaygroundFormProps) {
  const [backend, setBackend] = useState<string>('openai');
  const [backendKwargs, setBackendKwargs] = useState<KeyValuePair[]>([
    { key: 'model_name', value: 'openai/gpt-4.1-mini' },
  ]);
  const [environment, setEnvironment] = useState<string>('local');
  const [environmentKwargs, setEnvironmentKwargs] = useState<KeyValuePair[]>([]);
  const [prompt, setPrompt] = useState<string>('Print me the first 10 Fibonacci numbers.');
  const [rootPrompt, setRootPrompt] = useState<string>('');
  const [maxIterations, setMaxIterations] = useState<number>(30);
  const [maxDepth, setMaxDepth] = useState<number>(1);
  const [customSystemPrompt, setCustomSystemPrompt] = useState<string>('');
  const [otherBackends, setOtherBackends] = useState<string[]>([]);
  const [otherBackendKwargs, setOtherBackendKwargs] = useState<KeyValuePair[][]>([]);
  const [verbose, setVerbose] = useState<boolean>(false);

  // Convert key-value pairs to object
  const pairsToObject = (pairs: KeyValuePair[]): Record<string, any> => {
    const obj: Record<string, any> = {};
    pairs.forEach(({ key, value }) => {
      if (key.trim()) {
        // Try to parse as number or boolean, otherwise keep as string
        let parsedValue: any = value;
        if (value === 'true') parsedValue = true;
        else if (value === 'false') parsedValue = false;
        else if (value === 'null' || value === '') parsedValue = null;
        else if (!isNaN(Number(value)) && value.trim() !== '') {
          parsedValue = Number(value);
        }
        obj[key.trim()] = parsedValue;
      }
    });
    return obj;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const config: any = {
      prompt,
      root_prompt: rootPrompt || undefined,
      backend,
      backend_kwargs: pairsToObject(backendKwargs),
      environment,
      environment_kwargs: pairsToObject(environmentKwargs),
      max_iterations: maxIterations,
      max_depth: maxDepth,
      verbose: verbose,
      enable_logging: true,
    };

    if (customSystemPrompt.trim()) {
      config.custom_system_prompt = customSystemPrompt;
    }

    if (otherBackends.length > 0) {
      config.other_backends = otherBackends;
      if (otherBackendKwargs.length > 0) {
        config.other_backend_kwargs = otherBackendKwargs.map(pairsToObject);
      }
    }

    onRun(config);
  };

  const addOtherBackend = () => {
    setOtherBackends([...otherBackends, 'openai']);
    setOtherBackendKwargs([...otherBackendKwargs, []]);
  };

  const removeOtherBackend = (index: number) => {
    setOtherBackends(otherBackends.filter((_, i) => i !== index));
    setOtherBackendKwargs(otherBackendKwargs.filter((_, i) => i !== index));
  };

  const updateOtherBackend = (index: number, backend: string) => {
    const newBackends = [...otherBackends];
    newBackends[index] = backend;
    setOtherBackends(newBackends);
  };

  return (
    <Card className="border-border bg-card/50 backdrop-blur-sm">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
            <div className="space-y-6">
              {/* Backend Selection */}
              <div className="space-y-2">
                <label htmlFor="backend" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">
                  Backend
                </label>
                <select
                  id="backend"
                  value={backend}
                  onChange={(e) => setBackend(e.target.value)}
                  className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                  disabled={loading}
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="portkey">Portkey</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="vllm">vLLM</option>
                  <option value="litellm">LiteLLM</option>
                </select>
              </div>

              {/* Backend Kwargs */}
              <div className="space-y-2">
                <label className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">Backend Kwargs</label>
                <p className="text-[10px] text-muted-foreground/60 font-mono italic">
                  Key-value pairs for backend configuration (e.g., model_name, api_key)
                </p>
                <div className="rounded-md border border-border bg-muted/10 p-2">
                  <KeyValueEditor
                    pairs={backendKwargs}
                    onChange={setBackendKwargs}
                    disabled={loading}
                    keyPlaceholder="e.g., model_name"
                    valuePlaceholder="e.g., gpt-5-nano"
                  />
                </div>
              </div>

              {/* Environment */}
              <div className="space-y-2">
                <label htmlFor="environment" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">
                  Environment
                </label>
                <select
                  id="environment"
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                  disabled={loading}
                >
                  <option value="local">Local</option>
                  <option value="modal">Modal</option>
                  <option value="prime">Prime</option>
                </select>
              </div>

              {/* Environment Kwargs */}
              <div className="space-y-2">
                <label className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">Environment Kwargs</label>
                <div className="rounded-md border border-border bg-muted/10 p-2">
                  <KeyValueEditor
                    pairs={environmentKwargs}
                    onChange={setEnvironmentKwargs}
                    disabled={loading}
                  />
                </div>
              </div>

              {/* Custom System Prompt */}
              <div className="space-y-2">
                <label htmlFor="customSystemPrompt" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">
                  Custom System Prompt (optional)
                </label>
                <textarea
                  id="customSystemPrompt"
                  value={customSystemPrompt}
                  onChange={(e) => setCustomSystemPrompt(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary resize-y"
                  placeholder="Override the default RLM system prompt..."
                  disabled={loading}
                />
              </div>
            </div>

            <div className="space-y-6">
              {/* Prompt */}
              <div className="space-y-2">
                <label htmlFor="prompt" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                  <span className="text-primary">▶</span> Prompt
                </label>
                <textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={5}
                  className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary resize-y leading-relaxed"
                  placeholder="Enter your prompt here..."
                  disabled={loading}
                  required
                />
              </div>

              {/* Root Prompt */}
              <div className="space-y-2">
                <label htmlFor="rootPrompt" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">
                  Root Prompt (optional hint)
                </label>
                <input
                  id="rootPrompt"
                  type="text"
                  value={rootPrompt}
                  onChange={(e) => setRootPrompt(e.target.value)}
                  className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="e.g. Solve the following math problem..."
                  disabled={loading}
                />
              </div>

              {/* Max Iterations & Depth */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="maxIterations" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">
                    Max Iterations
                  </label>
                  <input
                    id="maxIterations"
                    type="number"
                    value={maxIterations}
                    onChange={(e) => setMaxIterations(parseInt(e.target.value) || 30)}
                    min={1}
                    max={100}
                    className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="maxDepth" className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider">
                    Max Depth
                  </label>
                  <select
                    id="maxDepth"
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-muted/30 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                    disabled={loading}
                  >
                    <option value={0}>0 (None)</option>
                    <option value={1}>1 (Recursive)</option>
                  </select>
                </div>
              </div>

              {/* Toggles */}
              <div className="flex flex-wrap gap-6 pt-2">
                <div className="flex items-center space-x-2">
                  <input
                    id="verbose"
                    type="checkbox"
                    checked={verbose}
                    onChange={(e) => setVerbose(e.target.checked)}
                    className="w-4 h-4 rounded border-border bg-muted accent-primary"
                    disabled={loading}
                  />
                  <label htmlFor="verbose" className="text-[11px] font-mono font-medium text-muted-foreground">
                    VERBOSE_MODE
                  </label>
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className={cn(
                  "w-full font-mono text-xs tracking-widest uppercase py-6",
                  "transition-all active:scale-[0.98]"
                )}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-background animate-pulse" />
                    EXECUTING...
                  </span>
                ) : 'Run RLM Trace'}
              </Button>
            </div>
          </div>
        </form>

      </CardContent>
    </Card>
  );
}
