'use client';

import { PlaygroundForm } from '@/components/PlaygroundForm';
import { PlaygroundResults } from '@/components/PlaygroundResults';
import { useState } from 'react';

interface RunResult {
  success: boolean;
  response: string | null;
  root_model: string | null;
  execution_time: number | null;
  usage_summary: Record<string, any> | null;
  error: string | null;
}

export default function PlaygroundPage() {
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async (config: any) => {
    setLoading(true);
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_PLAYGROUND_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        response: null,
        root_model: null,
        execution_time: null,
        usage_summary: null,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">RLM Playground</h1>
          <p className="text-muted-foreground">
            Run RLM completions interactively. Configure your model, environment, and prompt.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <PlaygroundForm onRun={handleRun} loading={loading} />
          </div>

          <div className="space-y-4">
            <PlaygroundResults result={result} loading={loading} />
          </div>
        </div>
      </div>
    </div>
  );
}

