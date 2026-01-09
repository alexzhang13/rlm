'use client';

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  variant?: 'cyan' | 'magenta' | 'yellow' | 'green' | 'red';
  subtext?: string;
  compact?: boolean;
}

const variantStyles = {
  cyan: 'border-sky-500/30 bg-sky-500/5 dark:border-sky-400/30 dark:bg-sky-400/5',
  magenta: 'border-fuchsia-500/30 bg-fuchsia-500/5 dark:border-fuchsia-400/30 dark:bg-fuchsia-400/5',
  yellow: 'border-amber-500/30 bg-amber-500/5 dark:border-amber-400/30 dark:bg-amber-400/5',
  green: 'border-emerald-500/30 bg-emerald-500/5 dark:border-emerald-400/30 dark:bg-emerald-400/5',
  red: 'border-red-500/30 bg-red-500/5 dark:border-red-400/30 dark:bg-red-400/5',
};

const textStyles = {
  cyan: 'text-sky-600 dark:text-sky-400',
  magenta: 'text-fuchsia-600 dark:text-fuchsia-400',
  yellow: 'text-amber-600 dark:text-amber-400',
  green: 'text-emerald-600 dark:text-emerald-400',
  red: 'text-red-600 dark:text-red-400',
};

export function StatsCard({ label, value, icon, variant = 'cyan', subtext, compact = false }: StatsCardProps) {
  if (compact) {
    return (
      <div className={cn(
        'flex flex-col items-center justify-center px-3 py-1.5 rounded-md border min-w-[70px]',
        variantStyles[variant],
        textStyles[variant]
      )}>
        <span className="text-[9px] font-mono uppercase opacity-70 leading-none mb-0.5 whitespace-nowrap">{label}</span>
        <span className="text-xs font-mono font-bold leading-none">{value}</span>
      </div>
    );
  }
  return (
    <Card className={cn(
      'border transition-all duration-300 hover:scale-[1.02]',
      variantStyles[variant]
    )}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className={cn('text-2xl', textStyles[variant])}>
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {label}
            </p>
            <p className={cn('text-2xl font-bold tracking-tight', textStyles[variant])}>
              {value}
            </p>
            {subtext && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate">
                {subtext}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
