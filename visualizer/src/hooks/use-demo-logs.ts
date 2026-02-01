import { useCallback, useEffect, useState } from 'react';

import { extractContextVariable, parseLogFile } from '@/lib/parse-logs';

// Lightweight summary of a log file for the "Recent Traces" list
export interface DemoLogInfo {
  fileName: string;
  contextPreview: string | null;
  hasFinalAnswer: boolean;
  iterations: number;
}

interface UseDemoLogsResult {
  demoLogs: DemoLogInfo[];
  loadingDemos: boolean;
  refetch: () => Promise<void>;
}

// Encapsulates fetching + parsing of demo log previews from the backend
export function useDemoLogs(): UseDemoLogsResult {
  const [demoLogs, setDemoLogs] = useState<DemoLogInfo[]>([]);
  const [loadingDemos, setLoadingDemos] = useState(true);

  const loadDemoPreviews = useCallback(async () => {
    setLoadingDemos(true);

    try {
      // 1) Ask API for the list of available log files
      const listResponse = await fetch('/api/logs');
      if (!listResponse.ok) {
        throw new Error('Failed to fetch log list');
      }

      const { files } = await listResponse.json() as { files: string[] };

      const previews: DemoLogInfo[] = [];

      // 2) For each file, fetch the JSONL content and build a small preview object
      for (const fileName of files) {
        try {
          const response = await fetch(`/logs/${fileName}`);
          if (!response.ok) continue;

          const content = await response.text();
          const parsed = parseLogFile(fileName, content);
          const contextVar = extractContextVariable(parsed.iterations);

          previews.push({
            fileName,
            contextPreview: contextVar,
            hasFinalAnswer: !!parsed.metadata.finalAnswer,
            iterations: parsed.metadata.totalIterations,
          });
        } catch (error) {
          // If one file fails, log it and keep going with the rest
          // eslint-disable-next-line no-console
          console.error('Failed to load demo preview:', fileName, error);
        }
      }

      setDemoLogs(previews);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to load demo logs:', error);
    } finally {
      setLoadingDemos(false);
    }
  }, []);

  // Load once on mount so Dashboard just consumes the data.
  useEffect(() => {
    void loadDemoPreviews();
  }, [loadDemoPreviews]);

  return {
    demoLogs,
    loadingDemos,
    refetch: loadDemoPreviews,
  };
}

