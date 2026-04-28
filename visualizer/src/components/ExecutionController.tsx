'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { useRLMMetaStore, TraceNode } from '@/lib/store';
import { Play, Pause, RotateCcw, SkipForward, Settings2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ExecutionControllerProps {
  onSendMessage: (message: string) => Promise<void>;
  onNodeUpdate?: (node: TraceNode) => void;
  status: 'idle' | 'running' | 'ready' | 'error';
}

export function ExecutionController({ 
  onSendMessage, 
  onNodeUpdate,
  status: externalStatus 
}: ExecutionControllerProps) {
  const [localMaxDepth, setLocalMaxDepth] = useState(3);
  const [localUseRLM, setLocalUseRLM] = useState(true);
  const [localStepMode, setLocalStepMode] = useState(false);
  
  const {
    maxDepth,
    useRLM,
    stepMode,
    executionStatus,
    setMaxDepth,
    setUseRLM,
    setStepMode,
    setExecutionStatus,
  } = useRLMMetaStore();

  const eventSourceRef = useRef<EventSource | null>(null);

  const handleSendMessage = useCallback(async (message: string) => {
    setExecutionStatus('running');
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          maxDepth: localMaxDepth,
          useRLM: localUseRLM,
        }),
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

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
              onNodeUpdate?.(event.node);
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }

      setExecutionStatus('ready');
    } catch (error) {
      console.error('Chat error:', error);
      setExecutionStatus('error');
    }
  }, [localMaxDepth, localUseRLM, setExecutionStatus, onNodeUpdate]);

  const handleApplySettings = () => {
    setMaxDepth(localMaxDepth);
    setUseRLM(localUseRLM);
    setStepMode(localStepMode);
  };

  const displayStatus = externalStatus || executionStatus;

  return (
    <div className="border-t border-border p-4 space-y-4">
      {/* Status indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={cn(
            "w-2 h-2 rounded-full",
            displayStatus === 'running' ? "bg-amber-500 animate-pulse" :
            displayStatus === 'ready' ? "bg-emerald-500" :
            displayStatus === 'error' ? "bg-red-500" :
            "bg-muted"
          )} />
          <span className="text-xs font-medium uppercase">
            {displayStatus}
          </span>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2"
          onClick={() => setExecutionStatus('idle')}
        >
          <RotateCcw className="h-3 w-3" />
        </Button>
      </div>

      {/* Controls */}
      <div className="space-y-3">
        {/* RLM Toggle */}
        <div className="flex items-center justify-between">
          <label className="text-xs text-muted-foreground">
            Use RLM Recursion
          </label>
          <Button
            variant={localUseRLM ? "default" : "outline"}
            size="sm"
            className="h-6 text-xs"
            onClick={() => setLocalUseRLM(!localUseRLM)}
          >
            {localUseRLM ? 'ON' : 'OFF'}
          </Button>
        </div>

        {/* Max Depth Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs text-muted-foreground">
              Max Depth
            </label>
            <span className="text-xs font-mono">{localMaxDepth}</span>
          </div>
          <Slider
            value={[localMaxDepth]}
            onValueChange={([v]) => setLocalMaxDepth(v)}
            min={1}
            max={10}
            step={1}
            className="w-full"
          />
        </div>

        {/* Step Mode Toggle */}
        <div className="flex items-center justify-between">
          <label className="text-xs text-muted-foreground flex items-center gap-1">
            <SkipForward className="h-3 w-3" />
            Step Mode
          </label>
          <Button
            variant={localStepMode ? "default" : "outline"}
            size="sm"
            className="h-6 text-xs"
            onClick={() => setLocalStepMode(!localStepMode)}
            disabled={!localUseRLM}
          >
            {localStepMode ? 'ON' : 'OFF'}
          </Button>
        </div>
      </div>

      {/* Apply Button */}
      <Button
        className="w-full"
        size="sm"
        onClick={handleApplySettings}
      >
        <Settings2 className="h-4 w-4 mr-2" />
        Apply Settings
      </Button>

      {/* Status Messages */}
      {displayStatus === 'running' && (
        <div className="text-xs text-muted-foreground text-center">
          Executing...
        </div>
      )}
    </div>
  );
}