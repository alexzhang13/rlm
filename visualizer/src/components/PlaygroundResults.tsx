'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface RunResult {
  success: boolean;
  response: string | null;
  root_model: string | null;
  execution_time: number | null;
  usage_summary: Record<string, any> | null;
  verbose_output: string | null;
  error: string | null;
}

interface PlaygroundResultsProps {
  result: RunResult | null;
  loading: boolean;
}

export function PlaygroundResults({ result, loading }: PlaygroundResultsProps) {
  if (loading) {
    return (
      <Card className="border-border bg-card/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <div className="space-y-4 text-center">
              <div className="relative mx-auto w-10 h-10">
                <div className="absolute inset-0 animate-spin rounded-full border-b-2 border-primary"></div>
                <div className="absolute inset-0 animate-ping rounded-full border border-primary/20"></div>
              </div>
              <p className="text-sm font-mono text-muted-foreground animate-pulse">EXECUTING RLM TRACE...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card className="border-border bg-card/50 backdrop-blur-sm border-dashed">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <div className="text-center space-y-2">
              <div className="text-4xl opacity-20 font-mono text-primary">◈</div>
              <p className="text-sm text-muted-foreground font-mono">
                Awaiting execution parameters...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result.success) {
    return (
      <Card className="border-destructive/50 bg-destructive/5 backdrop-blur-sm">
        <CardContent className="pt-6 space-y-4">
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <h3 className="font-mono font-semibold text-destructive mb-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-destructive animate-pulse" />
              EXECUTION_ERROR
            </h3>
            <pre className="text-xs font-mono text-destructive whitespace-pre-wrap">
              {result.error || 'Unknown error occurred'}
            </pre>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border bg-card/50 backdrop-blur-sm">
      <CardContent className="pt-6 space-y-6">
        {/* Status Badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-primary/10 border border-primary/20">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] font-mono text-primary font-bold">SUCCESS</span>
            </div>
            {result.root_model && (
              <Badge variant="outline" className="font-mono text-[10px]">
                {result.root_model}
              </Badge>
            )}
          </div>
          {result.execution_time !== null && (
            <div className="text-[10px] font-mono text-muted-foreground">
              TIME: {result.execution_time.toFixed(3)}s
            </div>
          )}
        </div>

        {/* Response */}
        <div className="space-y-3">
          <h3 className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
            <span className="text-primary">▶</span> Final Answer
          </h3>
          <div className="rounded-lg border border-border bg-muted/30 overflow-hidden">
            <ScrollArea className="h-[300px] w-full p-4">
              <pre className="text-sm font-mono whitespace-pre-wrap break-words leading-relaxed">
                {result.response || 'No response'}
              </pre>
            </ScrollArea>
          </div>
        </div>

        {/* Usage Summary */}
        {result.usage_summary && (
          <div className="space-y-3">
            <h3 className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <span className="text-primary">Σ</span> Usage Metrics
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {result.usage_summary.model_usage_summaries ? (
                Object.entries(result.usage_summary.model_usage_summaries).map(
                  ([model, usage]: [string, any]) => (
                    <div key={model} className="p-3 rounded-md border border-border bg-muted/20 flex flex-wrap items-center justify-between gap-4">
                      <div className="font-mono text-xs font-medium">{model}</div>
                      <div className="flex items-center gap-4">
                        <div className="text-center">
                          <div className="text-[10px] text-muted-foreground font-mono uppercase">Calls</div>
                          <div className="text-xs font-mono">{usage.total_calls || 0}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-[10px] text-muted-foreground font-mono uppercase">Tokens</div>
                          <div className="text-xs font-mono">
                            {(usage.total_input_tokens || 0) + (usage.total_output_tokens || 0)}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                )
              ) : (
                <p className="text-[10px] font-mono text-muted-foreground italic">No metrics available</p>
              )}
            </div>
          </div>
        )}

        {/* Verbose Output */}
        {result.verbose_output && (
          <div className="space-y-3">
            <h3 className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <span className="text-primary">◈</span> Trace Logs
            </h3>
            <div className="rounded-lg border border-border bg-black/40 overflow-hidden">
              <ScrollArea className="h-[400px] w-full p-4">
                <pre className="text-[11px] font-mono text-primary/80 whitespace-pre-wrap break-words leading-tight">
                  {result.verbose_output}
                </pre>
              </ScrollArea>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

