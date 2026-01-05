'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface PlaygroundFormProps {
  onRun: (config: any) => void;
  loading: boolean;
}

export function PlaygroundForm({ onRun, loading }: PlaygroundFormProps) {
  const [backend, setBackend] = useState<string>('openai');
  const [modelName, setModelName] = useState<string>('gpt-5-nano');
  const [apiKey, setApiKey] = useState<string>('');
  const [environment, setEnvironment] = useState<string>('local');
  const [prompt, setPrompt] = useState<string>('Print me the first 100 powers of two, each on a newline.');
  const [rootPrompt, setRootPrompt] = useState<string>('');
  const [maxIterations, setMaxIterations] = useState<number>(30);
  const [maxDepth, setMaxDepth] = useState<number>(1);
  const [enableLogging, setEnableLogging] = useState<boolean>(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const config: any = {
      prompt,
      root_prompt: rootPrompt || undefined,
      backend,
      backend_kwargs: {
        model_name: modelName,
        ...(apiKey && { api_key: apiKey }),
      },
      environment,
      environment_kwargs: {},
      max_iterations: maxIterations,
      max_depth: maxDepth,
      enable_logging: enableLogging,
    };

    onRun(config);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Backend Selection */}
          <div className="space-y-2">
            <label htmlFor="backend" className="text-sm font-medium">
              Backend
            </label>
            <select
              id="backend"
              value={backend}
              onChange={(e) => setBackend(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
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

          {/* Model Name */}
          <div className="space-y-2">
            <label htmlFor="modelName" className="text-sm font-medium">
              Model Name
            </label>
            <input
              id="modelName"
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="gpt-5-nano"
              disabled={loading}
              required
            />
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <label htmlFor="apiKey" className="text-sm font-medium">
              API Key (optional, uses env var if empty)
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Leave empty to use OPENAI_API_KEY env var"
              disabled={loading}
            />
          </div>

          {/* Environment */}
          <div className="space-y-2">
            <label htmlFor="environment" className="text-sm font-medium">
              Environment
            </label>
            <select
              id="environment"
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={loading}
            >
              <option value="local">Local</option>
              <option value="modal">Modal</option>
              <option value="prime">Prime</option>
            </select>
          </div>

          {/* Prompt */}
          <div className="space-y-2">
            <label htmlFor="prompt" className="text-sm font-medium">
              Prompt
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring resize-y"
              placeholder="Enter your prompt here..."
              disabled={loading}
              required
            />
          </div>

          {/* Root Prompt */}
          <div className="space-y-2">
            <label htmlFor="rootPrompt" className="text-sm font-medium">
              Root Prompt (optional)
            </label>
            <input
              id="rootPrompt"
              type="text"
              value={rootPrompt}
              onChange={(e) => setRootPrompt(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Optional hint shown to the root LM"
              disabled={loading}
            />
          </div>

          {/* Max Iterations */}
          <div className="space-y-2">
            <label htmlFor="maxIterations" className="text-sm font-medium">
              Max Iterations
            </label>
            <input
              id="maxIterations"
              type="number"
              value={maxIterations}
              onChange={(e) => setMaxIterations(parseInt(e.target.value) || 30)}
              min={1}
              max={100}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={loading}
            />
          </div>

          {/* Max Depth */}
          <div className="space-y-2">
            <label htmlFor="maxDepth" className="text-sm font-medium">
              Max Depth
            </label>
            <select
              id="maxDepth"
              value={maxDepth}
              onChange={(e) => setMaxDepth(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={loading}
            >
              <option value={0}>0 (No recursion)</option>
              <option value={1}>1 (One level of recursion)</option>
            </select>
          </div>

          {/* Enable Logging */}
          <div className="flex items-center space-x-2">
            <input
              id="enableLogging"
              type="checkbox"
              checked={enableLogging}
              onChange={(e) => setEnableLogging(e.target.checked)}
              className="w-4 h-4 rounded border-input"
              disabled={loading}
            />
            <label htmlFor="enableLogging" className="text-sm font-medium">
              Enable Logging (save to logs/)
            </label>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={loading}
            className="w-full"
          >
            {loading ? 'Running...' : 'Run RLM'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

