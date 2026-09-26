'use client';

import { useState, useCallback, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDemoLogs, DemoLogInfo } from '@/hooks/use-demo-logs';
import { FileUploader } from './FileUploader';
import { LogViewer } from './LogViewer';
import { AsciiRLM } from './AsciiGlobe';
import { ThemeToggle } from './ThemeToggle';
import { parseLogFile } from '@/lib/parse-logs';
import { RLMLogFile } from '@/lib/types';
import { cn } from '@/lib/utils';

export function Dashboard() {
  const [logFiles, setLogFiles] = useState<RLMLogFile[]>([]);
  const [selectedLog, setSelectedLog] = useState<RLMLogFile | null>(null);

  // Log files from server that users can load ("Recent Traces" section in UI)
  const { demoLogs, loadingDemos } = useDemoLogs();

  // When a full log file is loaded (upload or demo), parse and register it.
  const handleFileLoaded = useCallback((fileName: string, content: string) => {
    const parsed = parseLogFile(fileName, content);
    setLogFiles(prev => {
      if (prev.some(f => f.fileName === fileName)) {
        return prev.map(f => (f.fileName === fileName ? parsed : f));
      }
      return [...prev, parsed];
    });
    setSelectedLog(parsed);
  }, []);

  const loadDemoLog = useCallback(
    async (fileName: string) => {
      try {
        const response = await fetch(`/logs/${fileName}`);
        if (!response.ok) throw new Error('Failed to load demo log');
        const content = await response.text();
        handleFileLoaded(fileName, content);
      } catch (error) {
        console.error('Error loading demo log:', error);
        alert('Failed to load demo log. Make sure the log files are in the public/logs folder.');
      }
    },
    [handleFileLoaded],
  );

  if (selectedLog) {
    return (
      <LogViewer
        logFile={selectedLog}
        onBack={() => setSelectedLog(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundEffects />

      <div className="relative z-10">
        <DashboardHeader />

        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid lg:grid-cols-2 gap-10">
            
            <div className="space-y-8">
              <UploadSection onFileLoaded={handleFileLoaded} />
              <AsciiSection />
            </div>

            <div className="space-y-8">
              <RecentTracesSection
                demoLogs={demoLogs}
                loading={loadingDemos}
                onSelectDemo={loadDemoLog}
              />
              <LoadedFilesSection
                logFiles={logFiles}
                onSelectLog={setSelectedLog}
              />
            </div>

          </div>
        </main>

        <DashboardFooter />
      </div>
    </div>
  );
}

function BackgroundEffects() {
  return (
    <>
      <div className="absolute inset-0 grid-pattern opacity-30 dark:opacity-15" />
      <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/3 rounded-full blur-3xl" />
    </>
  );
}

function DashboardHeader() {
  return (
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              <span className="text-primary">RLM</span>
              <span className="text-muted-foreground ml-2 font-normal">Visualizer</span>
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Debug recursive language model execution traces
            </p>
          </div>
          <div className="flex items-center gap-4">
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
  );
}

interface UploadSectionProps {
  onFileLoaded: (fileName: string, content: string) => void;
}

function UploadSection({ onFileLoaded }: UploadSectionProps) {
  return (
    <div>
      <h2 className="text-sm font-medium mb-3 flex items-center gap-2 text-muted-foreground">
        <span className="text-primary font-mono">01</span>
        Upload Log File
      </h2>
      <FileUploader onFileLoaded={onFileLoaded} />
    </div>
  );
}

function AsciiSection() {
  return (
    <div className="hidden lg:block">
      <h2 className="text-sm font-medium mb-3 flex items-center gap-2 text-muted-foreground">
        <span className="text-primary font-mono">◈</span>
        RLM Architecture
      </h2>
      <div className="bg-muted/50 border border-border rounded-lg p-4 overflow-x-auto">
        <AsciiRLM />
      </div>
    </div>
  );
}

interface RecentTracesSectionProps {
  demoLogs: DemoLogInfo[];
  loading: boolean;
  onSelectDemo: (fileName: string) => void;
}

function RecentTracesSection({
  demoLogs,
  loading,
  onSelectDemo,
}: RecentTracesSectionProps) {
  return (
    <div>
      <h2 className="text-sm font-medium mb-3 flex items-center gap-2 text-muted-foreground">
        <span className="text-primary font-mono">02</span>
        Recent Traces
        <span className="text-[10px] text-muted-foreground/60 ml-1">(latest 10)</span>
      </h2>

      {loading ? (
        <Card>
          <CardContent className="p-6 text-center">
            <div className="animate-pulse flex items-center justify-center gap-2 text-muted-foreground text-sm">
              Loading traces...
            </div>
          </CardContent>
        </Card>
      ) : demoLogs.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="p-6 text-center text-muted-foreground text-sm">
            No log files found in /public/logs/
          </CardContent>
        </Card>
      ) : (
        <ScrollArea className="h-[320px]">
          <div className="space-y-2 pr-4">ssss
            {demoLogs.map((demo) => (
              <Card
                key={demo.fileName}
                onClick={() => onSelectDemo(demo.fileName)}
                className={cn(
                  'cursor-pointer transition-all hover:scale-[1.01]',
                  'hover:border-primary/50 hover:bg-primary/5',
                )}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-3">
                    <div className="relative flex-shrink-0">
                      <div
                        className={cn(
                          'w-2.5 h-2.5 rounded-full',
                          demo.hasFinalAnswer ? 'bg-primary' : 'bg-muted-foreground/30',
                        )}
                      />
                      {demo.hasFinalAnswer && (
                        <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-primary animate-ping opacity-50" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-xs text-foreground/80">
                          {demo.fileName}
                        </span>
                        <Badge
                          variant="outline"
                          className="text-[9px] px-1.5 py-0 h-4"
                        >
                          {demo.iterations} iter
                        </Badge>
                      </div>
                      {demo.contextPreview && (
                        <p className="text-[11px] font-mono text-muted-foreground truncate">
                          {demo.contextPreview.length > 80
                            ? `${demo.contextPreview.slice(0, 80)}...`
                            : demo.contextPreview}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

interface LoadedFilesSectionProps {
  logFiles: RLMLogFile[];
  onSelectLog: (log: RLMLogFile) => void;
}

function LoadedFilesSection({ logFiles, onSelectLog }: LoadedFilesSectionProps) {
  if (logFiles.length === 0) {
    return null;
  }

  return (
    <div>
      <h2 className="text-sm font-medium mb-3 flex items-center gap-2 text-muted-foreground">
        <span className="text-primary font-mono">03</span>
        Loaded Files
      </h2>
      <ScrollArea className="h-[200px]">
        <div className="space-y-2 pr-4">
          {logFiles.map((log) => (
            <Card
              key={log.fileName}
              className={cn(
                'cursor-pointer transition-all hover:scale-[1.01]',
                'hover:border-primary/50 hover:bg-primary/5',
              )}
              onClick={() => onSelectLog(log)}
            >
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <div className="relative flex-shrink-0">
                    <div
                      className={cn(
                        'w-2.5 h-2.5 rounded-full',
                        log.metadata.finalAnswer
                          ? 'bg-primary'
                          : 'bg-muted-foreground/30',
                      )}
                    />
                    {log.metadata.finalAnswer && (
                      <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-primary animate-ping opacity-50" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs truncate text-foreground/80">
                        {log.fileName}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-[9px] px-1.5 py-0 h-4"
                      >
                        {log.metadata.totalIterations} iter
                      </Badge>
                    </div>
                    <p className="text-[11px] text-muted-foreground truncate">
                      {log.metadata.contextQuestion}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

function DashboardFooter() {
  return (
    <footer className="border-t border-border mt-8">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <p className="text-[10px] text-muted-foreground font-mono">
          RLM Visualizer • Recursive Language Models
        </p>
        <p className="text-[10px] text-muted-foreground font-mono">
          Prompt → [LM ↔ REPL] → Answer
        </p>
      </div>
    </footer>
  );
}
