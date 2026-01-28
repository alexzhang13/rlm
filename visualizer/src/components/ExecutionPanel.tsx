'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CodeBlock } from './CodeBlock';
import { RLMIteration } from '@/lib/types';

interface ExecutionPanelProps {
  iteration: RLMIteration | null;
}

export function ExecutionPanel({ iteration }: ExecutionPanelProps) {
  if (!iteration) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-muted/30 border border-border flex items-center justify-center">
            <span className="text-3xl opacity-50">◇</span>
          </div>
          <p className="text-muted-foreground text-sm">
            Select an iteration to view execution details
          </p>
        </div>
      </div>
    );
  }

  const totalSubCalls = iteration.code_blocks.reduce(
    (acc, block) => acc + (block.result?.rlm_calls?.length || 0), 
    0
  );

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-emerald-500 text-sm">⟨⟩</span>
            </div>
            <div>
              <h2 className="font-semibold text-sm">Code & Sub-LM Calls</h2>
              <p className="text-[11px] text-muted-foreground">
                Iteration {iteration.iteration} • {new Date(iteration.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        {/* Quick stats */}
        <div className="flex gap-2 flex-wrap">
          <Badge variant="outline" className="text-xs">
            {iteration.code_blocks.length} code block{iteration.code_blocks.length !== 1 ? 's' : ''}
          </Badge>
          {totalSubCalls > 0 && (
            <Badge className="bg-fuchsia-500/15 text-fuchsia-600 dark:text-fuchsia-400 border-fuchsia-500/30 text-xs">
              {totalSubCalls} sub-LM call{totalSubCalls !== 1 ? 's' : ''}
            </Badge>
          )}
          {iteration.final_answer && (
            <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs">
              Has Final Answer
            </Badge>
          )}
        </div>
      </div>

      {/* Tabs - Code Execution and Sub-LM Calls only */}
      <Tabs defaultValue="code" className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-shrink-0 px-4 pt-3">
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="code" className="text-xs">
              Code Execution
            </TabsTrigger>
            <TabsTrigger value="sublm" className="text-xs">
              Sub-LM Calls ({totalSubCalls})
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-hidden">
          <TabsContent value="code" className="h-full m-0 data-[state=active]:flex data-[state=active]:flex-col">
            <ScrollArea className="flex-1 h-full">
              <div className="p-4">
                {iteration.code_blocks.length > 0 ? (
                  iteration.code_blocks.map((block, idx) => (
                    <CodeBlock key={idx} block={block} index={idx} />
                  ))
                ) : (
                  <Card className="border-dashed">
                    <CardContent className="p-8 text-center">
                      <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-muted/30 border border-border flex items-center justify-center">
                        <span className="text-xl opacity-50">⟨⟩</span>
                      </div>
                      <p className="text-muted-foreground text-sm">
                        No code was executed in this iteration
                      </p>
                      <p className="text-muted-foreground text-xs mt-1">
                        The model didn&apos;t write any code blocks
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="sublm" className="h-full m-0 data-[state=active]:flex data-[state=active]:flex-col">
            <ScrollArea className="flex-1 h-full">
              <div className="p-4 space-y-4">
                {totalSubCalls > 0 ? (
                  iteration.code_blocks.flatMap((block, blockIdx) =>
                    (block.result?.rlm_calls || []).map((call, callIdx) => (
                      <Card 
                        key={`${blockIdx}-${callIdx}`}
                        className="border-fuchsia-500/30 bg-fuchsia-500/5 dark:border-fuchsia-400/30 dark:bg-fuchsia-400/5"
                      >
                        <CardHeader className="py-3 px-4">
                          <div className="flex items-center justify-between flex-wrap gap-2">
                            <CardTitle className="text-sm flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-fuchsia-500 dark:bg-fuchsia-400" />
                              llm_query() from Block #{blockIdx + 1}
                            </CardTitle>
                            <div className="flex gap-2">
                              <Badge variant="outline" className="text-[10px] font-mono">
                                {call.prompt_tokens} in
                              </Badge>
                              <Badge variant="outline" className="text-[10px] font-mono">
                                {call.completion_tokens} out
                              </Badge>
                              <Badge variant="outline" className="text-[10px] font-mono">
                                {call.execution_time.toFixed(2)}s
                              </Badge>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="px-4 pb-4 space-y-3">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1.5 font-medium uppercase tracking-wider">
                              Prompt
                            </p>
                            <div className="bg-muted/50 rounded-lg p-3 max-h-40 overflow-y-auto border border-border">
                              <pre className="text-xs whitespace-pre-wrap font-mono">
                                {typeof call.prompt === 'string' 
                                  ? call.prompt 
                                  : JSON.stringify(call.prompt, null, 2)}
                              </pre>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1.5 font-medium uppercase tracking-wider">
                              Response
                            </p>
                            <div className="bg-fuchsia-500/10 dark:bg-fuchsia-400/10 rounded-lg p-3 max-h-56 overflow-y-auto border border-fuchsia-500/20 dark:border-fuchsia-400/20">
                              <pre className="text-xs whitespace-pre-wrap font-mono text-fuchsia-700 dark:text-fuchsia-300">
                                {call.response}
                              </pre>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )
                ) : (
                  <Card className="border-dashed">
                    <CardContent className="p-8 text-center">
                      <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-muted/30 border border-border flex items-center justify-center">
                        <span className="text-xl opacity-50">⊘</span>
                      </div>
                      <p className="text-muted-foreground text-sm">
                        No sub-LM calls were made in this iteration
                      </p>
                      <p className="text-muted-foreground text-xs mt-1">
                        Sub-LM calls appear when using llm_query() in the REPL
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
