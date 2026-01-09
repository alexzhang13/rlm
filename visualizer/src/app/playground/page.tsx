'use client';

import { ThemeToggle } from '@/components/ThemeToggle';
import { PlaygroundForm } from '@/components/PlaygroundForm';
import { LiveLogViewer } from '@/components/LiveLogViewer';
import { useLiveLog } from '@/hooks/useLiveLog';
import Link from 'next/link';

export default function PlaygroundPage() {
  const { state, startStream, cancel, reset } = useLiveLog();

  const handleRun = async (config: any) => {
    await startStream(config);
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 grid-pattern opacity-30 dark:opacity-15" />
      <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/3 rounded-full blur-3xl" />
      
      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-border">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div>
                <Link href="/">
                  <h1 className="text-3xl font-bold tracking-tight">
                    <span className="text-primary">RLM</span>
                    <span className="text-muted-foreground ml-2 font-normal">Playground</span>
                  </h1>
                </Link>
                <p className="text-sm text-muted-foreground mt-1">
                  Run recursive language model completions interactively
                </p>
              </div>
              <div className="flex items-center gap-4">
                <Link 
                  href="/"
                  className="px-3 py-1.5 rounded-md border border-border bg-muted/30 hover:bg-muted/50 text-[11px] font-mono text-muted-foreground transition-colors flex items-center gap-2"
                >
                  <span className="text-xs">⬉</span> VISUALIZER
                </Link>
                <ThemeToggle />
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                    READY
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="space-y-12">
            <div className="space-y-4">
              <h2 className="text-sm font-medium mb-3 flex items-center gap-2 text-muted-foreground">
                <span className="text-primary font-mono">01</span>
                Configuration
              </h2>
              <PlaygroundForm 
                onRun={handleRun} 
                loading={state.status === 'streaming' || state.status === 'connecting'} 
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
                  <span className="text-primary font-mono">02</span>
                  Live Trace Viewer
                </h2>
                {state.status !== 'idle' && state.status !== 'streaming' && state.status !== 'connecting' && (
                  <button 
                    onClick={reset}
                    className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-primary transition-colors flex items-center gap-2"
                  >
                    <span>↺</span> New Run
                  </button>
                )}
              </div>
              <LiveLogViewer 
                state={state} 
                onCancel={cancel}
              />
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-border mt-8">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <p className="text-[10px] text-muted-foreground font-mono">
              RLM Playground • Recursive Language Models
            </p>
            <p className="text-[10px] text-muted-foreground font-mono">
              [LM ↔ REPL]
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

