'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface RunResult {
  success: boolean;
  response: string | null;
  root_model: string | null;
  execution_time: number | null;
  usage_summary: Record<string, any> | null;
  error: string | null;
}

interface PlaygroundResultsProps {
  result: RunResult | null;
  loading: boolean;
}

export function PlaygroundResults({ result, loading }: PlaygroundResultsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="space-y-2 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="text-sm text-muted-foreground">Running RLM completion...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-muted-foreground">
              Submit a query to see results here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result.success) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <h3 className="font-semibold text-destructive mb-2">Error</h3>
            <p className="text-sm text-destructive">{result.error || 'Unknown error occurred'}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Results</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Success Badge */}
        <div className="flex items-center gap-2">
          <Badge variant="default" className="bg-green-600">
            Success
          </Badge>
          {result.root_model && (
            <Badge variant="outline">
              {result.root_model}
            </Badge>
          )}
          {result.execution_time !== null && (
            <Badge variant="outline">
              {result.execution_time.toFixed(2)}s
            </Badge>
          )}
        </div>

        {/* Response */}
        <div className="space-y-2">
          <h3 className="font-semibold text-sm">Response</h3>
          <ScrollArea className="h-[300px] w-full rounded-md border border-input p-4">
            <pre className="text-sm font-mono whitespace-pre-wrap break-words">
              {result.response || 'No response'}
            </pre>
          </ScrollArea>
        </div>

        {/* Usage Summary */}
        {result.usage_summary && (
          <div className="space-y-2">
            <h3 className="font-semibold text-sm">Usage Summary</h3>
            <div className="rounded-md border border-input p-4 space-y-2">
              {result.usage_summary.model_usage_summaries ? (
                Object.entries(result.usage_summary.model_usage_summaries).map(
                  ([model, usage]: [string, any]) => (
                    <div key={model} className="space-y-1">
                      <div className="font-medium text-sm">{model}</div>
                      <div className="text-xs text-muted-foreground space-y-0.5 ml-4">
                        <div>Calls: {usage.total_calls || 0}</div>
                        <div>Input tokens: {usage.total_input_tokens || 0}</div>
                        <div>Output tokens: {usage.total_output_tokens || 0}</div>
                        <div>
                          Total tokens:{' '}
                          {(usage.total_input_tokens || 0) + (usage.total_output_tokens || 0)}
                        </div>
                      </div>
                    </div>
                  )
                )
              ) : (
                <p className="text-sm text-muted-foreground">No usage data available</p>
              )}
            </div>
          </div>
        )}

        {/* Execution Time */}
        {result.execution_time !== null && (
          <div className="text-xs text-muted-foreground">
            Execution time: {result.execution_time.toFixed(3)} seconds
          </div>
        )}
      </CardContent>
    </Card>
  );
}

