'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRLMMetaStore, ChatMessage } from '@/lib/store';
import { Send, User, Bot, Trash2, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  onSendMessage: (message: string) => Promise<void>;
  disabled?: boolean;
}

export function ChatPanel({ onSendMessage, disabled }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const {
    chatMessages,
    executionStatus,
    addChatMessage,
    clearChat,
    loadMessageFromHistory,
  } = useRLMMetaStore();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleSend = async () => {
    if (!input.trim() || sending || disabled) return;
    
    const userMessage = input.trim();
    setInput('');
    setSending(true);
    
    addChatMessage({ role: 'user', content: userMessage });
    
    try {
      await onSendMessage(userMessage);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="p-4 space-y-4 min-h-full">
          {chatMessages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-muted/30 border border-border flex items-center justify-center">
                  <Bot className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground text-sm">
                  Start a conversation
                </p>
                <p className="text-muted-foreground text-xs mt-1">
                  Send a message to begin RLM execution
                </p>
              </div>
            </div>
          ) : (
            chatMessages.map((msg) => (
              <ChatMessageItem key={msg.id} message={msg} />
            ))
          )}
        </div>
      </ScrollArea>
      
      {/* Input Area */}
      <div className="border-t border-border p-4 space-y-3">
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={clearChat}
            className="h-8 px-2"
            title="Clear chat"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'Processing...' : 'Type your message...'}
            disabled={disabled || sending}
            className="flex-1 min-h-[60px] max-h-[120px] resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
          />
          <Button
            onClick={handleSend}
            disabled={disabled || sending || !input.trim()}
            className="h-auto px-4"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        
        {sending && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Processing...
          </div>
        )}
      </div>
    </div>
  );
}

interface ChatMessageItemProps {
  message: ChatMessage;
}

function ChatMessageItem({ message }: ChatMessageItemProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn(
      'flex gap-3',
      isUser ? 'flex-row-reverse' : 'flex-row'
    )}>
      <div className={cn(
        'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center',
        isUser 
          ? 'bg-primary/10 border border-primary/30' 
          : 'bg-muted/50 border border-border'
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-primary" />
        ) : (
          <Bot className="h-4 w-4 text-muted-foreground" />
        )}
      </div>
      
      <div className={cn(
        'flex-1 max-w-[80%] rounded-lg p-3',
        isUser 
          ? 'bg-primary/5 border border-primary/20' 
          : 'bg-muted/30 border border-border'
      )}>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <p className={cn(
          'text-[10px] mt-2',
          isUser ? 'text-right' : 'text-muted-foreground'
        )}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}