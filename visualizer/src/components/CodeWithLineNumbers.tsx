'use client';

import { SyntaxHighlight } from './SyntaxHighlight';

interface CodeWithLineNumbersProps {
  code: string;
  language?: 'python' | 'text';
  startLine?: number;
}

export function CodeWithLineNumbers({ 
  code, 
  language = 'python',
  startLine = 1 
}: CodeWithLineNumbersProps) {
  const lines = code.split('\n');
  const lineNumberWidth = Math.max(2, String(lines.length + startLine - 1).length);
  
  return (
    <div className="flex">
      {/* Line numbers */}
      <div className="flex-shrink-0 border-r border-border/30 select-none">
        {lines.map((_, idx) => (
          <div 
            key={idx} 
            className="text-right text-muted-foreground/50 text-xs leading-relaxed"
            style={{ width: `${lineNumberWidth}ch` }}
          >
            {idx + startLine}
          </div>
        ))}
      </div>
      
      {/* Code */}
      <div className="flex-shrink-0 pl-4">
        <SyntaxHighlight code={code} language={language} />
      </div>
    </div>
  );
}

