import { create } from 'zustand';
import { RLMIteration, RLMConfigMetadata } from '@/lib/types';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  traceId?: string;
}

export interface TraceNode {
  id: string;
  parentId: string | null;
  depth: number;
  prompt: string;
  response: string;
  timestamp: number;
}

export interface TraceTree {
  executionId: string;
  nodes: TraceNode[];
  rootPrompt: string;
  finalAnswer: string | null;
  status: 'running' | 'completed' | 'error';
  config: {
    maxDepth: number;
    model: string;
  };
}

export type ExecutionStatus = 'idle' | 'running' | 'ready' | 'error';

interface RLMMetaStore {
  chatMessages: ChatMessage[];
  currentExecutionId: string | null;
  selectedMessageId: string | null;
  ollamaConnected: boolean;
  ollamaModels: string[];
  selectedModel: string;
  executionStatus: ExecutionStatus;
  maxDepth: number;
  useRLM: boolean;
  stepMode: boolean;
  
  chatHistory: ChatMessage[][];
  
  traceNodes: TraceNode[];
  liveExecutionId: string | null;
  selectedTraceNodeId: string | null;
  
  addChatMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setSelectedMessage: (id: string | null) => void;
  setExecutionId: (id: string | null) => void;
  addMessageToHistory: () => void;
  loadMessageFromHistory: (index: number) => void;
  
  setOllamaStatus: (connected: boolean, models: string[]) => void;
  setSelectedModel: (model: string) => void;
  setExecutionStatus: (status: ExecutionStatus) => void;
  setMaxDepth: (depth: number) => void;
  setUseRLM: (use: boolean) => void;
  setStepMode: (enabled: boolean) => void;
  
  addTraceNode: (node: TraceNode) => void;
  setLiveExecutionId: (id: string | null) => void;
  selectTraceNode: (id: string | null) => void;
  clearTraceNodes: () => void;
  
  clearChat: () => void;
}

export const useRLMMetaStore = create<RLMMetaStore>((set, get) => ({
  chatMessages: [],
  currentExecutionId: null,
  selectedMessageId: null,
  ollamaConnected: false,
  ollamaModels: [],
  selectedModel: '',
  executionStatus: 'idle',
  maxDepth: 3,
  useRLM: true,
  stepMode: false,
  chatHistory: [],
  
  traceNodes: [],
  liveExecutionId: null,
  selectedTraceNodeId: null,
  
  addChatMessage: (message) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      timestamp: Date.now(),
    };
    set((state) => ({
      chatMessages: [...state.chatMessages, newMessage],
      selectedMessageId: newMessage.id,
    }));
    get().addMessageToHistory();
  },
  
  setSelectedMessage: (id) => {
    set({ selectedMessageId: id });
    if (id) {
      const msg = get().chatMessages.find(m => m.id === id);
      if (msg?.traceId) {
        set({ currentExecutionId: msg.traceId });
      }
    }
  },
  
  setExecutionId: (id) => {
    set({ currentExecutionId: id });
  },
  
  addMessageToHistory: () => {
    const current = get().chatMessages;
    if (current.length > 0) {
      set((state) => ({
        chatHistory: [...state.chatHistory, [...current]],
      }));
    }
  },
  
  loadMessageFromHistory: (index) => {
    const history = get().chatHistory;
    if (index >= 0 && index < history.length) {
      set({
        chatMessages: [...history[index]],
        selectedMessageId: history[index][history[index].length - 1]?.id || null,
      });
    }
  },
  
  setOllamaStatus: (connected, models) => {
    set({
      ollamaConnected: connected,
      ollamaModels: models,
      selectedModel: models.length > 0 ? models[0] : '',
    });
  },
  
  setSelectedModel: (model) => {
    set({ selectedModel: model });
  },
  
  setExecutionStatus: (status) => {
    set({ executionStatus: status });
  },
  
  setMaxDepth: (depth) => {
    set({ maxDepth: depth });
  },
  
  setUseRLM: (use) => {
    set({ useRLM: use });
  },
  
  setStepMode: (enabled) => {
    set({ stepMode: enabled });
  },
  
  addTraceNode: (node) => {
    set((state) => ({
      traceNodes: [...state.traceNodes, node],
      selectedTraceNodeId: node.id,
    }));
  },
  
  setLiveExecutionId: (id) => {
    set({ liveExecutionId: id });
  },
  
  selectTraceNode: (id) => {
    set({ selectedTraceNodeId: id });
  },
  
  clearTraceNodes: () => {
    set({
      traceNodes: [],
      liveExecutionId: null,
      selectedTraceNodeId: null,
    });
  },
  
  clearChat: () => {
    set((state) => ({
      chatMessages: [],
      currentExecutionId: null,
      selectedMessageId: null,
      chatHistory: state.chatHistory,
    }));
    get().clearTraceNodes();
  },
}));