/**
 * Hook for fetching reconnaissance data from REST API
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi } from '../services/api';
import type { ReconData } from '../types/eventLog';

export interface UseReconDataOptions {
  /** Whether to poll for updates */
  poll?: boolean;
  /** Polling interval in ms (default: 5000) */
  pollInterval?: number;
  /** Whether to fetch immediately on mount */
  fetchOnMount?: boolean;
}

export interface UseReconDataReturn {
  /** Recon data if available */
  data: ReconData | null;
  /** Loading state */
  isLoading: boolean;
  /** Error if any */
  error: Error | null;
  /** Refetch the data */
  refetch: () => Promise<void>;
  /** Last fetch timestamp */
  lastFetched: number | null;
}

export function useReconData(
  sessionId: string | undefined,
  options: UseReconDataOptions = {}
): UseReconDataReturn {
  const { poll = false, pollInterval = 5000, fetchOnMount = true } = options;

  const [data, setData] = useState<ReconData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastFetched, setLastFetched] = useState<number | null>(null);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    if (!sessionId) {
      setData(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await dashboardApi.getReconData(sessionId);
      setData(result);
      setLastFetched(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch recon data'));
      // Don't clear existing data on error (stale data might be useful)
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Initial fetch
  useEffect(() => {
    if (fetchOnMount && sessionId) {
      fetchData();
    }
  }, [fetchOnMount, sessionId, fetchData]);

  // Polling
  useEffect(() => {
    if (poll && sessionId) {
      pollIntervalRef.current = setInterval(fetchData, pollInterval);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [poll, sessionId, pollInterval, fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
    lastFetched,
  };
}

export default useReconData;
