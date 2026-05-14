import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi } from '../services/api';
import type {
  DashboardStats,
  VulnerabilityTrend,
  SeverityDistribution,
  TestActivity,
  HypothesisResult,
  FindingDetail,
} from '../types';
import type { ReconData, ToolExecution } from '../types/eventLog';

interface DashboardData {
  stats: DashboardStats;
  trends: VulnerabilityTrend[];
  distribution: SeverityDistribution;
  tests: TestActivity[];
}

interface UseDashboardDataReturn {
  data: DashboardData | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

// Default empty data
const defaultStats: DashboardStats = {
  total_vulnerabilities: 0,
  critical_count: 0,
  high_count: 0,
  medium_count: 0,
  low_count: 0,
  info_count: 0,
  risk_mitigation_value: 0,
  issues_fixed: 0,
  total_tests: 0,
  running_tests: 0,
  total_agents: 5,
  active_agents: 0,
};

const defaultDistribution: SeverityDistribution = {
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
  info: 0,
};

export function useDashboardData(
  refreshInterval: number = 30000
): UseDashboardDataReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      // Fetch all dashboard data in parallel
      const [stats, trends, distribution, tests] = await Promise.all([
        dashboardApi.getStats().catch(() => defaultStats),
        dashboardApi.getTrends(30).catch(() => []),
        dashboardApi.getSeverityDistribution().catch(() => defaultDistribution),
        dashboardApi.getTests(10).catch(() => []),
      ]);

      setData({
        stats,
        trends,
        distribution,
        tests,
      });
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      setError(err instanceof Error ? err : new Error('Failed to fetch data'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Set up refresh interval
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, refreshInterval]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  };
}

// Hook for fetching tests only
export function useTests(limit: number = 20) {
  const [tests, setTests] = useState<TestActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchTests = useCallback(async () => {
    try {
      const data = await dashboardApi.getTests(limit);
      setTests(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      setError(err instanceof Error ? err : new Error('Failed to fetch tests'));
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchTests();
  }, [fetchTests]);

  return {
    tests,
    isLoading,
    error,
    refetch: fetchTests,
  };
}

// Hook for fetching a single test detail with auto-polling while running
export function useTestDetail(testId: string) {
  const [test, setTest] = useState<TestActivity | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchTest = useCallback(async () => {
    if (!testId) return;

    try {
      const data = await dashboardApi.getTestDetail(testId);
      setTest(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      if (err instanceof Error && err.message.includes('404')) return;
      setError(err instanceof Error ? err : new Error('Failed to fetch test'));
    } finally {
      setIsLoading(false);
    }
  }, [testId]);

  // Initial fetch
  useEffect(() => {
    fetchTest();
  }, [fetchTest]);

  // Poll every 3s while the test is still running
  useEffect(() => {
    if (test?.status === 'running' || test?.status === 'awaiting_review') {
      intervalRef.current = setInterval(fetchTest, 10000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [test?.status, fetchTest]);

  return {
    test,
    isLoading,
    error,
    refetch: fetchTest,
  };
}

// Hook for fetching hypotheses for a test session, polls while running
export function useTestHypotheses(testId: string, isRunning: boolean) {
  const [hypotheses, setHypotheses] = useState<HypothesisResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchHypotheses = useCallback(async () => {
    if (!testId) return;
    try {
      const data = await dashboardApi.getHypotheses(testId);
      setHypotheses(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      setError(err instanceof Error ? err : new Error('Failed to fetch hypotheses'));
    } finally {
      setIsLoading(false);
    }
  }, [testId]);

  useEffect(() => {
    fetchHypotheses();
  }, [fetchHypotheses]);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(fetchHypotheses, 10000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, fetchHypotheses]);

  return { hypotheses, isLoading, error, refetch: fetchHypotheses };
}

// Hook for fetching findings for a test session, polls while running
export function useTestFindings(testId: string, isRunning: boolean) {
  const [findings, setFindings] = useState<FindingDetail[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchFindings = useCallback(async () => {
    if (!testId) return;
    try {
      const data = await dashboardApi.getFindings(testId);
      setFindings(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      setError(err instanceof Error ? err : new Error('Failed to fetch findings'));
    } finally {
      setIsLoading(false);
    }
  }, [testId]);

  useEffect(() => {
    fetchFindings();
  }, [fetchFindings]);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(fetchFindings, 10000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, fetchFindings]);

  return { findings, isLoading, error, refetch: fetchFindings };
}

// Hook for fetching recon data for a test session, polls while running
export function useTestRecon(testId: string, isRunning: boolean) {
  const [recon, setRecon] = useState<ReconData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchRecon = useCallback(async () => {
    if (!testId) return;
    try {
      const data = await dashboardApi.getReconData(testId);
      setRecon(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      // Silently ignore 404 — recon data doesn't exist until the recon agent stores it
      if (err instanceof Error && err.message.includes('404')) return;
      setError(err instanceof Error ? err : new Error('Failed to fetch recon data'));
    } finally {
      setIsLoading(false);
    }
  }, [testId]);

  useEffect(() => {
    fetchRecon();
  }, [fetchRecon]);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(fetchRecon, 10000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, fetchRecon]);

  return { recon, isLoading, error, refetch: fetchRecon };
}

// Hook for fetching tool executions for a test session, polls while running
export function useTestToolCalls(testId: string, isRunning: boolean) {
  const [toolCalls, setToolCalls] = useState<ToolExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchToolCalls = useCallback(async () => {
    if (!testId) return;
    try {
      const data = await dashboardApi.getToolExecutions(testId);
      setToolCalls(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.message === '__network_unavailable__') return;
      setError(err instanceof Error ? err : new Error('Failed to fetch tool calls'));
    } finally {
      setIsLoading(false);
    }
  }, [testId]);

  useEffect(() => {
    fetchToolCalls();
  }, [fetchToolCalls]);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(fetchToolCalls, 10000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, fetchToolCalls]);

  return { toolCalls, isLoading, error, refetch: fetchToolCalls };
}
