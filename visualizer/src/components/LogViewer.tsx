'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { StatsCard } from './StatsCard';
import { TrajectoryPanel } from './TrajectoryPanel';
import { ExecutionPanel } from './ExecutionPanel';
import { IterationTimeline } from './IterationTimeline';
import { ThemeToggle } from './ThemeToggle';
import { RLMLogFile } from '@/lib/types';

interface LogViewerProps {
  logFile: RLMLogFile;
  onBack: () => void;
}

export function LogViewer({ logFile, onBack }: LogViewerProps) {
  const [selectedIteration, setSelectedIteration] = useState(0);
  const { iterations, metadata, config } = logFile;

  const goToPrevious = useCallback(() => {
    setSelectedIteration(prev => Math.max(0, prev - 1));
  }, []);

  const goToNext = useCallback(() => {
    setSelectedIteration(prev => Math.min(iterations.length - 1, prev + 1));
  }, [iterations.length]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' || e.key === 'j') {
        goToPrevious();
      } else if (e.key === 'ArrowRight' || e.key === 'k') {
        goToNext();
      } else if (e.key === 'Escape') {
        onBack();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToPrevious, goToNext, onBack]);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-background">
      <LogViewerHeader
        fileName={logFile.fileName}
        config={config}
        metadata={metadata}
        onBack={onBack}
      />

      <div className="flex-1 flex overflow-hidden bg-background">
        
        <div className="w-[30%] max-w-xs flex-shrink-0">
          <LogViewerSummary metadata={metadata} />
        </div>

        <div className="flex-1 flex flex-col overflow-hidden bg-background">  
          <IterationTimeline
            iterations={iterations}
            selectedIteration={selectedIteration}
            onSelectIteration={setSelectedIteration}
          />
          <LogViewerMainContent
            iterations={iterations}
            selectedIteration={selectedIteration}
            onSelectIteration={setSelectedIteration}
          />
        </div>

      </div>
      
      <LogViewerFooter />
    </div>
  );
}

interface LogViewerHeaderProps {
  fileName: string;
  config: RLMLogFile['config'];
  metadata: RLMLogFile['metadata'];
  onBack: () => void;
}

function LogViewerHeader({
  fileName,
  config,
  metadata,
  onBack,
}: LogViewerHeaderProps) {
  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-sm">
      <div className="px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="text-muted-foreground hover:text-foreground"
            >
              ← Back
            </Button>
            <div className="h-5 w-px bg-border" />
            <div>
              <h1 className="font-semibold flex items-center gap-2 text-sm">
                <span className="text-primary">◈</span>
                {fileName}
              </h1>
              <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                {config.root_model ?? 'Unknown model'} •{' '}
                {config.backend ?? 'Unknown backend'} •{' '}
                {config.environment_type ?? 'Unknown env'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {metadata.hasErrors && (
              <Badge variant="destructive" className="text-xs">
                Has Errors
              </Badge>
            )}
            {metadata.finalAnswer && (
              <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white text-xs">
                Completed
              </Badge>
            )}
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}

interface LogViewerSummaryProps {
  metadata: RLMLogFile['metadata'];
}

function LogViewerSummary({ metadata }: LogViewerSummaryProps) {
  return (
    <div className="h-full border-r border-border bg-muted/30 px-6 py-4 overflow-y-auto">
      <div className="flex flex-col gap-6">
        <Card className="bg-gradient-to-r from-primary/5 to-accent/5 border-primary/20">
          <CardContent className="p-4">
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1">
                  Context / Question
                </p>
                <p className="text-sm font-medium">
                  {metadata.contextQuestion}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1">
                  Final Answer
                </p>
                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                  {metadata.finalAnswer || 'Not yet completed'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-wrap gap-2">
          <StatsCard
            label="Iterations"
            value={metadata.totalIterations}
            icon="◎"
            variant="cyan"
          />
          <StatsCard
            label="Code"
            value={metadata.totalCodeBlocks}
            icon="⟨⟩"
            variant="green"
          />
          <StatsCard
            label="Sub-LM"
            value={metadata.totalSubLMCalls}
            icon="◇"
            variant="magenta"
          />
          <StatsCard
            label="Exec"
            value={`${metadata.totalExecutionTime.toFixed(2)}s`}
            icon="⏱"
            variant="yellow"
          />
        </div>
      </div>
    </div>
  );
}

interface LogViewerMainContentProps {
  iterations: RLMLogFile['iterations'];
  selectedIteration: number;
  onSelectIteration: (index: number) => void;
}

function LogViewerMainContent({
  iterations,
  selectedIteration,
  onSelectIteration,
}: LogViewerMainContentProps) {
  return (
    <div className="flex-1 min-h-0">
      <ResizablePanelGroup orientation="horizontal" className="h-full">
      
      <ResizablePanel defaultSize={50} minSize={20} maxSize={80}>
        <div className="h-full border-r border-border">
          <TrajectoryPanel
            iterations={iterations}
            selectedIteration={selectedIteration}
            onSelectIteration={onSelectIteration}
          />
        </div>
      </ResizablePanel>

      <ResizableHandle
        withHandle
        className="bg-border hover:bg-primary/30 transition-colors"
      />

      <ResizablePanel defaultSize={50} minSize={20} maxSize={80}>
        <ExecutionPanel
          iteration={iterations[selectedIteration] || null}
        />
      </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

function LogViewerFooter() {
  return (
    <div className="border-t border-border bg-muted/30 px-6 py-1.5">
      <div className="flex items-center justify-center gap-6 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <kbd className="px-1 py-0.5 bg-muted rounded text-[9px]">←</kbd>
          <kbd className="px-1 py-0.5 bg-muted rounded text-[9px]">→</kbd>
          Navigate
        </span>
        <span className="flex items-center gap-1">
          <kbd className="px-1 py-0.5 bg-muted rounded text-[9px]">Esc</kbd>
          Back
        </span>
      </div>
    </div>
  );
}
