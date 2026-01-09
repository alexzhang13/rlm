'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { StatsCard } from './StatsCard';
import { TrajectoryPanel } from './TrajectoryPanel';
import { ExecutionPanel } from './ExecutionPanel';
import { IterationTimeline } from './IterationTimeline';
import { LiveLogState } from '@/lib/types';
import { computeMetadata } from '@/lib/parse-logs';
import { cn } from '@/lib/utils';

interface LiveLogViewerProps {
  state: LiveLogState;
  onCancel: () => void;
}

export function LiveLogViewer({ state, onCancel }: LiveLogViewerProps) {
  const [selectedIteration, setSelectedIteration] = useState(0);
  const { status, config, iterations, error, finalResult } = state;

  // Auto-select latest iteration as they come in
  useEffect(() => {
    if (status === 'streaming' && iterations.length > 0) {
      setSelectedIteration(iterations.length - 1);
    }
  }, [iterations.length, status]);

  // Compute live metadata
  const metadata = computeMetadata(iterations);

  if (status === 'idle') {
    return (
      <Card className="border-border bg-card/50 backdrop-blur-sm border-dashed">
        <CardContent className="pt-12 pb-12">
          <div className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <div className="text-5xl opacity-20 font-mono text-primary animate-pulse">◈</div>
              <p className="text-sm text-muted-foreground font-mono tracking-widest uppercase">
                Awaiting execution parameters...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col overflow-y-auto overflow-x-auto border border-border rounded-lg bg-background relative">
      {/* Streaming Overlay for connection phase */}
      {status === 'connecting' && (
        <div className="absolute inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className="relative mx-auto w-12 h-12">
              <div className="absolute inset-0 animate-spin rounded-full border-t-2 border-primary"></div>
              <div className="absolute inset-0 animate-ping rounded-full border border-primary/20"></div>
            </div>
            <p className="text-xs font-mono text-primary animate-pulse tracking-widest">ESTABLISHING STREAM...</p>
          </div>
        </div>
      )}

      {/* Top Bar */}
      <header className="border-b border-border bg-card/50 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-2 h-2 rounded-full",
              status === 'streaming' ? "bg-primary animate-pulse" : 
              status === 'complete' ? "bg-emerald-500" :
              status === 'error' ? "bg-destructive" : "bg-muted-foreground"
            )} />
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest">
              {status}
            </span>
            <div className="h-4 w-px bg-border mx-1" />
            <span className="text-[10px] text-muted-foreground font-mono truncate max-w-[200px]">
              {config?.root_model ?? 'Initializing...'}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            {status === 'streaming' && (
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={onCancel}
                className="h-7 px-3 text-[10px] font-mono tracking-tighter"
              >
                STOP_EXECUTION
              </Button>
            )}
            {error && (
              <Badge variant="destructive" className="text-[9px] uppercase font-mono px-1.5 py-0">
                Error
              </Badge>
            )}
          </div>
        </div>
      </header>

      {/* Stats Row */}
      <div className="border-b border-border bg-muted/20 px-4 py-3">
        <div className="flex gap-3 overflow-x-auto no-scrollbar">
          <StatsCard label="Iter" value={iterations.length} icon="◎" variant="cyan" compact />
          <StatsCard label="Code" value={metadata.totalCodeBlocks} icon="⟨⟩" variant="green" compact />
          <StatsCard label="SubLM" value={metadata.totalSubLMCalls} icon="◇" variant="magenta" compact />
          <StatsCard label="Time" value={`${(finalResult?.execution_time || metadata.totalExecutionTime).toFixed(1)}s`} icon="⏱" variant="yellow" compact />
        </div>
      </div>

      {/* Iteration Timeline */}
      <IterationTimeline
        iterations={iterations}
        selectedIteration={selectedIteration}
        onSelectIteration={setSelectedIteration}
      />

      {/* Main Content */}
      <div className="flex-1 min-h-0">
        {iterations.length > 0 ? (
          <ResizablePanelGroup orientation="horizontal">
            <ResizablePanel defaultSize={50} minSize={20}>
              <TrajectoryPanel
                iterations={iterations}
                selectedIteration={selectedIteration}
                onSelectIteration={setSelectedIteration}
              />
            </ResizablePanel>
            <ResizableHandle withHandle className="bg-border" />
            <ResizablePanel defaultSize={50} minSize={20}>
              <ExecutionPanel
                iteration={iterations[selectedIteration] || null}
              />
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground text-[11px] font-mono italic">
            Waiting for first iteration...
          </div>
        )}
      </div>

      {/* Final Result / Error Banner */}
      {(status === 'complete' || status === 'error' || status === 'cancelled') && (
        <div className={cn(
          "border-t p-3 text-xs font-mono",
          status === 'complete' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" :
          status === 'error' ? "bg-destructive/10 border-destructive/20 text-destructive" :
          "bg-muted/10 border-border text-muted-foreground"
        )}>
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 truncate">
              {status === 'complete' ? (
                <span className="flex items-center gap-2">
                  <span className="font-bold">DONE:</span> {finalResult?.response?.slice(0, 100)}...
                </span>
              ) : status === 'error' ? (
                <span className="flex items-center gap-2">
                  <span className="font-bold">ERROR:</span> {error}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <span className="font-bold">CANCELLED</span> by user
                </span>
              )}
            </div>
            {finalResult?.usage_summary && (
              <div className="text-[10px] opacity-70 shrink-0">
                METRICS_SAVED
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
