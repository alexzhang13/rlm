'use client';

import { Button } from '@/components/ui/button';

interface KeyValuePair {
  key: string;
  value: string;
}

interface KeyValueEditorProps {
  pairs: KeyValuePair[];
  onChange: (pairs: KeyValuePair[]) => void;
  disabled?: boolean;
  keyPlaceholder?: string;
  valuePlaceholder?: string;
}

export function KeyValueEditor({
  pairs,
  onChange,
  disabled = false,
  keyPlaceholder = 'key',
  valuePlaceholder = 'value',
}: KeyValueEditorProps) {
  const updatePair = (index: number, field: 'key' | 'value', newValue: string) => {
    const newPairs = [...pairs];
    newPairs[index] = { ...newPairs[index], [field]: newValue };
    onChange(newPairs);
  };

  const addPair = () => {
    onChange([...pairs, { key: '', value: '' }]);
  };

  const removePair = (index: number) => {
    onChange(pairs.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-2">
      {pairs.map((pair, index) => (
        <div key={index} className="flex gap-2 items-center">
          <input
            type="text"
            value={pair.key}
            onChange={(e) => updatePair(index, 'key', e.target.value)}
            placeholder={keyPlaceholder}
            className="flex-1 px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={disabled}
          />
          <input
            type="text"
            value={pair.value}
            onChange={(e) => updatePair(index, 'value', e.target.value)}
            placeholder={valuePlaceholder}
            className="flex-1 px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={disabled}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => removePair(index)}
            disabled={disabled}
            className="shrink-0"
          >
            Remove
          </Button>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={addPair}
        disabled={disabled}
        className="w-full"
      >
        + Add Key-Value Pair
      </Button>
    </div>
  );
}

