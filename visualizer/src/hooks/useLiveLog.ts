import { useState, useCallback, useRef } from 'react';
import { LiveLogState, RLMIteration, RLMConfigMetadata } from '@/lib/types';

export function useLiveLog() {
  const [state, setState] = useState<LiveLogState>({
    status: 'idle',
    config: null,
    iterations: [],
    error: null,
    finalResult: null,
  });
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (config: any) => {
    setState({
      status: 'connecting',
      config: null,
      iterations: [],
      error: null,
      finalResult: null,
    });

    abortControllerRef.current = new AbortController();
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_PLAYGROUND_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/run/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      
      if (!response.body) throw new Error('No response body');

      setState(s => ({ ...s, status: 'streaming' }));

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        let eventData = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7);
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6);
          } else if (line === '' && eventData) {
            const parsed = JSON.parse(eventData);
            
            if (eventType === 'metadata') {
              setState(s => ({ 
                ...s, 
                config: {
                  root_model: parsed.root_model ?? null,
                  max_depth: parsed.max_depth ?? null,
                  max_iterations: parsed.max_iterations ?? null,
                  backend: parsed.backend ?? null,
                  backend_kwargs: parsed.backend_kwargs ?? null,
                  environment_type: parsed.environment_type ?? null,
                  environment_kwargs: parsed.environment_kwargs ?? null,
                  other_backends: parsed.other_backends ?? null,
                }
              }));
            } else if (eventType === 'iteration') {
              setState(s => ({ 
                ...s, 
                iterations: [...s.iterations, parsed as RLMIteration] 
              }));
            } else if (eventType === 'complete') {
              setState(s => ({ 
                ...s, 
                status: 'complete',
                finalResult: parsed,
              }));
            } else if (eventType === 'error') {
              setState(s => ({ 
                ...s, 
                status: 'error',
                error: parsed.error,
              }));
            }
            
            eventType = '';
            eventData = '';
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setState(s => ({ ...s, status: 'cancelled' }));
      } else {
        setState(s => ({ 
          ...s, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
      }
    }
  }, []);

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      config: null,
      iterations: [],
      error: null,
      finalResult: null,
    });
  }, []);

  return { state, startStream, cancel, reset };
}
