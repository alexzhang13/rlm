'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { FileUploader } from './FileUploader';
import { LogViewer } from './LogViewer';
import { AsciiRLM } from './AsciiGlobe';
import { ThemeToggle } from './ThemeToggle';
import { ChatPanel } from './ChatPanel';
import { ExecutionController } from './ExecutionController';
import { NodeInspector } from './NodeInspector';
import { parseLogFile, extractContextVariable } from '@/lib/parse-logs';
import { RLMLogFile } from '@/lib/types';
import { useRLMMetaStore, TraceNode } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Bot, RefreshCw, Play, Square, Settings2 } from 'lucide-react';

interface DemoLogInfo {
  fileName: string;
  contextPreview: string | null;
  hasFinalAnswer: boolean;
  iterations: number;
}

export function Dashboard() {
  const [logFiles, setLogFiles] = useState<RLMLogFile[]>([]);
  const [selectedLog, setSelectedLog] = useState<RLMLogFile | null>(null);
  const [demoLogs, setDemoLogs] = useState<DemoLogInfo[]>([]);
  const [loadingDemos, setLoadingDemos] = useState(true);
  const [showChatPanel, setShowChatPanel] = useState(true);
  
  const {
    ollamaConnected,
    ollamaModels,
    selectedModel,
    executionStatus,
    maxDepth,
    useRLM,
    setOllamaStatus,
    setSelectedModel,
    setExecutionStatus,
    addChatMessage,
    addTraceNode,
    traceNodes,
    clearTraceNodes,
  } = useRLMMetaStore();

  const checkOllamaStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/ollama/status');
      const data = await response.json();
      const models = data.models || [];
      setOllamaStatus(data.connected, models);
    } catch {
      setOllamaStatus(false, []);
    }
  }, [setOllamaStatus]);

  useEffect(() => {
    checkOllamaStatus();
    loadDemoPreviews();
  }, []);

  async function loadDemoPreviews() {
    try {
      const listResponse = await fetch('/api/logs');
      if (!listResponse.ok) throw new Error('Failed to fetch log list');
      const { files } = await listResponse.json();
      
      const previews: DemoLogInfo[] = [];
      for (const fileName of files.slice(0, 10)) {
        try {
          const response = await fetch(`/logs/${fileName}`);
          if (!response.ok) continue;
          const content = await response.text();
          const parsed = parseLogFile(fileName, content);
          const contextVar = extractContextVariable(parsed.iterations);
          
          previews.push({
            fileName,
            contextPreview: contextVar,
            hasFinalAnswer: !!parsed.metadata.finalAnswer,
            iterations: parsed.metadata.totalIterations,
          });
        } catch (e) {
          console.error('Failed to load demo preview:', fileName, e);
        }
      }
      setDemoLogs(previews);
    } catch (e) {
      console.error('Failed to load demo logs:', e);
    } finally {
      setLoadingDemos(false);
    }
  }

  const handleFileLoaded = useCallback((fileName: string, content: string) => {
    const parsed = parseLogFile(fileName, content);
    setLogFiles(prev => {
      if (prev.some(f => f.fileName === fileName)) {
        return prev.map(f => f.fileName === fileName ? parsed : f);
      }
      return [...prev, parsed];
    });
    setSelectedLog(parsed);
  }, []);

  const loadDemoLog = useCallback(async (fileName: string) => {
    try {
      const response = await fetch(`/logs/${fileName}`);
      if (!response.ok) throw new Error('Failed to load demo log');
      const content = await response.text();
      handleFileLoaded(fileName, content);
    } catch (error) {
      console.error('Error loading demo log:', error);
      alert('Failed to load demo log. Make sure the log files are in the public/logs folder.');
    }
  }, [handleFileLoaded]);

  const handleSendMessage = useCallback(async (message: string) => {
    clearTraceNodes();
    setExecutionStatus('running');
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          model: selectedModel,
          maxDepth,
          useRLM,
        }),
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';
      let finalAnswer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          
          const data = line.slice(6);
          if (data === '[DONE]') continue;

          try {
            const event = JSON.parse(data);
            
            if (event.type === 'status') {
              if (event.status === 'completed') {
                setExecutionStatus('ready');
              } else if (event.status === 'error') {
                setExecutionStatus('error');
              }
            } else if (event.type === 'node' && event.node) {
              addTraceNode(event.node);
            } else if (event.type === 'final' && event.finalAnswer) {
              finalAnswer = event.finalAnswer;
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }

      if (finalAnswer) {
        addChatMessage({ role: 'assistant', content: finalAnswer });
      } else if (traceNodes.length > 0) {
        const lastNode = traceNodes[traceNodes.length - 1];
        addChatMessage({ role: 'assistant', content: lastNode.response || 'No response' });
      }
      
      setExecutionStatus('ready');
    } catch (error) {
      console.error('Chat error:', error);
      setExecutionStatus('error');
      addChatMessage({ role: 'assistant', content: 'Error: ' + (error instanceof Error ? error.message : 'Unknown error') });
    }
  }, [selectedModel, maxDepth, useRLM, setExecutionStatus, addChatMessage, addTraceNode, clearTraceNodes, traceNodes]);

  const handleNodeUpdate = useCallback((node: TraceNode) => {
    addTraceNode(node);
  }, [addTraceNode]);

  if (selectedLog) {
    return <LogViewer logFile={selectedLog} onBack={() => setSelectedLog(null)} />;
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-background">
      {/* Top Bar */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                <span className="text-primary">RLM</span>
                <span className="text-muted-foreground ml-2 font-normal">Visualizer</span>
              </h1>
              <p className="text-xs text-muted-foreground">
                Debug recursive language model execution traces
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* Ollama Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted/50 border border-border">
                <Bot className={cn(
                  "h-4 w-4",
                  ollamaConnected ? "text-emerald-500" : "text-muted-foreground"
                )} />
                <span className="text-xs text-muted-foreground">
                  {ollamaConnected ? (
                    ollamaModels.length > 0 ? (
                      <select
                        className="bg-background border border-border rounded px-2 py-1 text-xs cursor-pointer hover:border-primary/50"
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                      >
                        {ollamaModels.map((model) => (
                          <option key={model} value={model}>{model}</option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-emerald-500">Ollama Ready (no models)</span>
                    )
                  ) : (
                    <span className="text-destructive">Ollama Offline</span>
                  )}
                </span>
                <Button variant="ghost" size="sm" className="h-6 px-2" onClick={checkOllamaStatus}>
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
              
              {/* Execution Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted/50 border border-border">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  executionStatus === 'running' ? "bg-amber-500 animate-pulse" :
                  executionStatus === 'ready' ? "bg-emerald-500" :
                  executionStatus === 'error' ? "bg-red-500" :
                  "bg-muted"
                )} />
                <span className="text-xs font-medium uppercase">{executionStatus}</span>
              </div>
              
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 min-h-0">
        <ResizablePanelGroup orientation="horizontal">
          {/* Left Panel - Chat & History */}
          <ResizablePanel defaultSize={25} minSize={20} maxSize={40}>
            <div className="h-full border-r border-border flex flex-col">
              {/* Chat History */}
              <div className="flex-shrink-0 border-b border-border p-4">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-sm font-medium flex items-center gap-2">
                    <Bot className="h-4 w-4" />
                    Chat
                  </h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowChatPanel(!showChatPanel)}
                  >
                    {showChatPanel ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                </div>
                {showChatPanel && (
                  <div className="h-[calc(100vh-300px)] min-h-[300px]">
                    <ChatPanel onSendMessage={handleSendMessage} disabled={executionStatus === 'running'} />
                  </div>
                )}
              </div>
              
              {/* Demo Logs */}
              <div className="flex-1 border-t border-border overflow-hidden">
                <div className="p-4">
                  <h3 className="text-xs font-medium uppercase text-muted-foreground mb-3">
                    Saved Traces
                  </h3>
                  <ScrollArea className="h-[calc(100vh-450px)]">
                    <div className="space-y-2">
                      {loadingDemos ? (
                        <p className="text-xs text-muted-foreground">Loading...</p>
                      ) : demoLogs.length === 0 ? (
                        <p className="text-xs text-muted-foreground">No traces found</p>
                      ) : (
                        demoLogs.map((demo) => (
                          <Card
                            key={demo.fileName}
                            onClick={() => loadDemoLog(demo.fileName)}
                            className="cursor-pointer hover:border-primary/50"
                          >
                            <CardContent className="p-3">
                              <div className="flex items-center gap-3">
                                <div className={cn(
                                  'w-2.5 h-2.5 rounded-full',
                                  demo.hasFinalAnswer ? 'bg-primary' : 'bg-muted-foreground/30'
                                )} />
                                <div className="flex-1 min-w-0">
                                  <span className="font-mono text-xs truncate block">
                                    {demo.fileName}
                                  </span>
                                  <span className="text-[10px] text-muted-foreground">
                                    {demo.iterations} iterations
                                  </span>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="bg-border hover:bg-primary/30 transition-colors" />

          {/* Center - RLM Visualization (placeholder for live execution) */}
          <ResizablePanel defaultSize={50} minSize={30} maxSize={70}>
            <div className="h-full border-r border-border flex flex-col">
              <div className="flex-shrink-0 border-b border-border p-4">
                <h2 className="text-sm font-medium">RLM Execution Tree</h2>
              </div>
              <div className="flex-1 overflow-auto p-4">
                {traceNodes.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-muted/30 border border-border flex items-center justify-center">
                        <AsciiRLM />
                      </div>
                      <p className="text-muted-foreground text-sm">
                        No execution in progress
                      </p>
                      <p className="text-muted-foreground text-xs mt-1">
                        Send a message to start RLM execution
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {traceNodes.map((node) => (
                      <Card key={node.id} className="border-l-4">
                        <CardContent className="p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">depth={node.depth}</Badge>
                            <span className="text-xs text-muted-foreground font-mono">
                              {new Date(node.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="text-xs font-mono">
                            <div className="mb-2">
                              <span className="text-muted-foreground">Prompt: </span>
                              {node.prompt.slice(0, 100)}...
                            </div>
                            <div>
                              <span className="text-muted-foreground">Response: </span>
                              {node.response?.slice(0, 100) || '...'}...
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="bg-border hover:bg-primary/30 transition-colors" />

          {/* Right Panel - Node Inspector & Controls */}
          <ResizablePanel defaultSize={25} minSize={20} maxSize={40}>
            <div className="h-full flex flex-col">
              {/* Controls */}
              <div className="flex-shrink-0 border-b border-border">
                <ExecutionController 
                  onSendMessage={handleSendMessage} 
                  onNodeUpdate={handleNodeUpdate}
                  status={executionStatus}
                />
              </div>
              
              {/* Node Inspector */}
              <div className="flex-1 overflow-hidden">
                <NodeInspector />
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  );
}