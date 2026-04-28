'use client';

import * as React from "react";
import { cn } from "@/lib/utils";

interface SliderProps {
  className?: string;
  value: number[];
  onValueChange: (value: number[]) => void;
  min?: number;
  max?: number;
  step?: number;
}

export function Slider({ className, value, onValueChange, min = 0, max = 100, step = 1 }: SliderProps) {
  const percentage = ((value[0] - min) / (max - min)) * 100;

  return (
    <div className={cn("relative w-full", className)}>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="absolute h-full bg-primary transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={(e) => onValueChange([Number(e.target.value)])}
        className="absolute inset-0 h-2 w-full cursor-pointer opacity-0"
      />
    </div>
  );
}