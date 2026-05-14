/**
 * Hook for fetching tool execution history from REST API
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi } from '../services/api';
import type { ToolExecution } from '../types/eventLog';

export interface UseToolExecutionsOptions {
  /** Number of records per page (default: 100) */
  limit?: number;
  /** Initial offset (default: 0) */
  initialOffset?: number;
  /** Whether to poll for updates */
  poll?: boolean;
  /** Polling interval in ms (default: 5000) */
  pollInterval?: number;
  /** Whether to fetch immediately on mount */
  fetchOnMount?: boolean;
}

export interface UseToolExecutionsReturn {
  /** Tool execution records */
  data: ToolExecution[];
  /** Loading state */
  isLoading: boolean;
  /** Error if any */
  error: Error | null;
  /** Refetch the data */
  refetch: () => Promise<void>;
  /** Load more records (pagination) */
  loadMore: () => Promise<void>;
  /** Whether there might be more records */
  hasMore: boolean;
  /** Current offset */
  offset: number;
  /** Total count of loaded records */
  totalLoaded: number;
  /** Last fetch timestamp */
  lastFetched: number | null;
}

export function useToolExecutions(
  sessionId: string | undefined,
  options: UseToolExecutionsOptions = {}
): UseToolExecutionsReturn {
  const {
    limit = 100,
    initialOffset = 0,
    poll = false,
    pollInterval = 5000,
    fetchOnMount = true,
  } = options;

  const [data, setData] = useState<ToolExecution[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [offset, setOffset] = useState(initialOffset);
  const [hasMore, setHasMore] = useState(true);
  const [lastFetched, setLastFetched] = useState<number | null>(null);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(
    async (append = false) => {
      if (!sessionId) {
        setData([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      const currentOffset = append ? offset : 0;

      try {
        const result = await dashboardApi.getToolExecutions(
          sessionId,
          limit,
          currentOffset
        );

        if (append) {
          setData((prev) => [...prev, ...result]);
        } else {
          setData(result);
        }

        // If we got fewer results than limit, there's no more data
        setHasMore(result.length === limit);
        setLastFetched(Date.now());

        if (append) {
          setOffset((prev) => prev + result.length);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error('Failed to fetch tool executions')
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, limit, offset]
  );

  const refetch = useCallback(async () => {
    setOffset(0);
    await fetchData(false);
  }, [fetchData]);

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading) return;
    await fetchData(true);
  }, [hasMore, isLoading, fetchData]);

  // Initial fetch
  useEffect(() => {
    if (fetchOnMount && sessionId) {
      fetchData(false);
    }
  }, [fetchOnMount, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Polling (only refetches first page)
  useEffect(() => {
    if (poll && sessionId) {
      pollIntervalRef.current = setInterval(() => {
        fetchData(false);
      }, pollInterval);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [poll, sessionId, pollInterval]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    data,
    isLoading,
    error,
    refetch,
    loadMore,
    hasMore,
    offset,
    totalLoaded: data.length,
    lastFetched,
  };
}

export default useToolExecutions;
