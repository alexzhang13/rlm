import {
  RLMIteration,
  RLMLogFile,
  LogMetadata,
  RLMConfigMetadata,
  extractFinalAnswer,
  CodeBlock,
} from './types';

// Extract the context variable from code block locals
export function extractContextVariable(iterations: RLMIteration[]): string | null {
  for (const iter of iterations) {
    const blocks = iter.code_blocks ?? [];
    for (const block of blocks) {
      const locals = block.result?.locals;
      const preview = resolveContextPreview(locals);
      if (preview) {
        return preview;
      }
    }
  }
  return null;
}

function resolveContextPreview(locals: Record<string, unknown> | undefined): string | null {
  if (!locals) return null;
  const completionContext = locals.completion_context;
  if (typeof completionContext === 'string') {
    return completionContext;
  }
  const contextHistory = locals.context_history;
  if (Array.isArray(contextHistory) && contextHistory.length > 0) {
    const latest = contextHistory[contextHistory.length - 1];
    const preview = formatContextValue(latest);
    if (preview) return preview;
  }

  const sessionContextKey = findLatestSessionContextKey(locals);
  if (sessionContextKey) {
    const preview = formatContextValue(locals[sessionContextKey]);
    if (preview) return preview;
  }

  return null;
}

function findLatestSessionContextKey(locals: Record<string, unknown>) {
  let latestKey: string | null = null;
  let latestIndex = -1;
  for (const key of Object.keys(locals)) {
    if (!key.startsWith('session_context_')) continue;
    const suffix = key.slice('session_context_'.length);
    const index = Number.parseInt(suffix, 10);
    if (Number.isNaN(index)) continue;
    if (index > latestIndex) {
      latestIndex = index;
      latestKey = key;
    }
  }
  return latestKey;
}

function formatContextValue(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (value == null) return null;
  try {
    const serialized = JSON.stringify(value);
    return serialized.length > 0 ? serialized : String(value);
  } catch {
    return String(value);
  }
}

// Default config when metadata is not present (backwards compatibility)
function getDefaultConfig(): RLMConfigMetadata {
  return {
    root_model: null,
    max_depth: null,
    max_iterations: null,
    backend: null,
    backend_kwargs: null,
    environment_type: null,
    environment_kwargs: null,
    other_backends: null,
  };
}

export interface ParsedJSONL {
  iterations: RLMIteration[];
  config: RLMConfigMetadata;
}

export function parseJSONL(content: string): ParsedJSONL {
  const lines = content.trim().split('\n').filter(line => line.trim());
  const iterations: RLMIteration[] = [];
  let config: RLMConfigMetadata = getDefaultConfig();
  
  for (const line of lines) {
    try {
      const parsed = JSON.parse(line);
      
      // Check if this is a metadata entry
      if (parsed.type === 'metadata') {
        config = {
          root_model: parsed.root_model ?? null,
          max_depth: parsed.max_depth ?? null,
          max_iterations: parsed.max_iterations ?? null,
          backend: parsed.backend ?? null,
          backend_kwargs: parsed.backend_kwargs ?? null,
          environment_type: parsed.environment_type ?? null,
          environment_kwargs: parsed.environment_kwargs ?? null,
          other_backends: parsed.other_backends ?? null,
        };
      } else if (parsed.type === 'iteration' || looksLikeIteration(parsed)) {
        iterations.push(parsed as RLMIteration);
      }
    } catch (e) {
      console.error('Failed to parse line:', line, e);
    }
  }
  
  return { iterations, config };
}

function looksLikeIteration(entry: Record<string, unknown>) {
  if (entry == null || typeof entry !== 'object') return false;
  return (
    typeof entry['iteration'] === 'number' &&
    typeof entry['response'] === 'string' &&
    Array.isArray(entry['prompt'])
  );
}

export function extractContextQuestion(iterations: RLMIteration[]): string {
  if (iterations.length === 0) return 'No context found';
  
  const firstIteration = iterations[0];
  const prompt = firstIteration.prompt;
  
  // Look for user message that contains the actual question
  for (const msg of prompt) {
    if (msg.role === 'user' && msg.content) {
      // Try to extract quoted query
      const queryMatch = msg.content.match(/original query: "([^"]+)"/);
      if (queryMatch) {
        return queryMatch[1];
      }
      
      // Check if it contains the actual query pattern
      if (msg.content.includes('answer the prompt')) {
        continue;
      }
      
      // Take first substantial user message
      if (msg.content.length > 50 && msg.content.length < 500) {
        return msg.content.slice(0, 200) + (msg.content.length > 200 ? '...' : '');
      }
    }
  }
  
  // Fallback: look in system prompt for context info
  const systemMsg = prompt.find(m => m.role === 'system');
  if (systemMsg?.content) {
    const contextMatch = systemMsg.content.match(/context variable.*?:(.*?)(?:\n|$)/i);
    if (contextMatch) {
      return contextMatch[1].trim().slice(0, 200);
    }
  }
  
  // Check code block output for actual context
  for (const iter of iterations) {
    const blocks = iter.code_blocks ?? [];
    for (const block of blocks) {
      const preview = resolveContextPreview(block.result?.locals);
      if (preview && preview.length < 500) {
        return preview;
      }
    }
  }
  
  return 'Context available in REPL environment';
}

export function computeMetadata(iterations: RLMIteration[]): LogMetadata {
  let totalCodeBlocks = 0;
  let totalSubLMCalls = 0;
  let totalExecutionTime = 0;
  let hasErrors = false;
  let finalAnswer: string | null = null;
  
  for (const iter of iterations) {
    const blocks: CodeBlock[] = iter.code_blocks ?? [];
    totalCodeBlocks += blocks.length;
    
    // Use iteration_time if available, otherwise sum code block times
    if (iter.iteration_time != null) {
      totalExecutionTime += iter.iteration_time;
    } else {
      for (const block of blocks) {
        if (block.result) {
          totalExecutionTime += block.result.execution_time || 0;
        }
      }
    }
    
    for (const block of blocks) {
      if (block.result) {
        if (block.result.stderr) {
          hasErrors = true;
        }
        if (block.result.rlm_calls) {
          totalSubLMCalls += block.result.rlm_calls.length;
        }
      }
    }
    
    if (iter.final_answer) {
      finalAnswer = extractFinalAnswer(iter.final_answer);
    }
  }
  
  return {
    totalIterations: iterations.length,
    totalCodeBlocks,
    totalSubLMCalls,
    contextQuestion: extractContextQuestion(iterations),
    finalAnswer,
    totalExecutionTime,
    hasErrors,
  };
}

export function parseLogFile(fileName: string, content: string): RLMLogFile {
  const { iterations, config } = parseJSONL(content);
  const metadata = computeMetadata(iterations);
  
  return {
    fileName,
    filePath: fileName,
    iterations,
    metadata,
    config,
  };
}
