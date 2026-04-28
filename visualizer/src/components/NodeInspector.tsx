'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRLMMetaStore } from '@/lib/store';

export function NodeInspector() {
  const { traceNodes, selectedTraceNodeId, selectTraceNode } = useRLMMetaStore();
  const selectedNode = traceNodes.find(n => n.id === selectedTraceNodeId);

  const getDepthColor = (depth: number) => {
    const colors = [
      'bg-emerald-500',
      'bg-cyan-500', 
      'bg-amber-500',
      'bg-rose-500',
      'bg-violet-500',
    ];
    return colors[depth % colors.length];
  };

  return (
    <div className="flex flex-col h-full">
      {/* Node List */}
      <div className="border-b border-border">
        <div className="px-4 py-2">
          <h3 className="text-xs font-medium uppercase text-muted-foreground">
            Trace Nodes ({traceNodes.length})
          </h3>
        </div>
        <ScrollArea className="h-[150px] px-4 pb-3">
          <div className="space-y-1">
            {traceNodes.length === 0 ? (
              <span className="text-xs text-muted-foreground">No nodes yet</span>
            ) : (
              traceNodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => selectTraceNode(node.id)}
                  className={`w-full text-left px-2 py-1.5 rounded text-xs font-mono transition-colors ${
                    selectedTraceNodeId === node.id 
                      ? 'bg-primary/20 text-primary' 
                      : 'hover:bg-muted'
                  }`}
                >
                  <span className={`inline-block w-2 h-2 rounded-full ${getDepthColor(node.depth)} mr-2`} />
                  depth={node.depth}
                  <span className="text-muted-foreground ml-2">
                    {node.prompt.slice(0, 30)}...
                  </span>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Node Details */}
      <div className="flex-1 overflow-hidden">
        {selectedNode ? (
          <ScrollArea className="h-full">
            <div className="p-4 space-y-4">
              <div className="flex items-center gap-2">
                <Badge className={getDepthColor(selectedNode.depth)}>
                  Depth {selectedNode.depth}
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  {new Date(selectedNode.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <div>
                <p className="text-xs text-muted-foreground mb-1.5 font-medium uppercase">
                  Prompt
                </p>
                <div className="bg-muted/50 rounded-lg p-3 border border-border max-h-40 overflow-y-auto">
                  <pre className="text-xs whitespace-pre-wrap font-mono">
                    {selectedNode.prompt}
                  </pre>
                </div>
              </div>

              <div>
                <p className="text-xs text-muted-foreground mb-1.5 font-medium uppercase">
                  Response
                </p>
                <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/20 max-h-60 overflow-y-auto">
                  <pre className="text-xs whitespace-pre-wrap font-mono text-emerald-700 dark:text-emerald-300">
                    {selectedNode.response || 'Pending...'}
                  </pre>
                </div>
              </div>
            </div>
          </ScrollArea>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-xs text-muted-foreground">
              Select a node to view details
            </p>
          </div>
        )}
      </div>
    </div>
  );
}