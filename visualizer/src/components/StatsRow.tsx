'use client';

import * as React from 'react';

interface StatsRowProps {
  label: string;
  value: string | number;
  valueClassName?: string;
}

export function StatsRow({ label, value, valueClassName }: StatsRowProps) {
  return (
    <div className="flex items-center justify-between">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
        {label}
      </p>
      <p className={`text-xs font-medium ${valueClassName || ''}`}>
        {value}
      </p>
    </div>
  );
}
