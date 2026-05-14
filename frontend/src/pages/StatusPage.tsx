import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  RefreshCw,
  ChevronRight,
  Activity,
  Clock,
  History,
  Loader2,
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { dashboardApi } from '@/services/api';
import { AssessmentPhasesBar } from '@/components/dashboard/AssessmentPhasesBar';
import { useTestRecon, useTestHypotheses } from '@/hooks/useDashboardData';
import type { TestActivity } from '@/types';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '--';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function truncate(str: string, len: number): string {
  if (!str) return '--';
  return str.length > len ? str.slice(0, len) + '...' : str;
}

type Phase = 'started' | 'authentication' | 'reconnaissance' | 'testing' | 'validation' | 'completed';

function LiveWorkflowArea({ firstRunningTest }: { firstRunningTest: TestActivity | null }) {
  const testId = firstRunningTest?.id ?? '';
  const isRunning = firstRunningTest?.status === 'running';

  const { recon } = useTestRecon(testId, isRunning);
  const { hypotheses } = useTestHypotheses(testId, isRunning);

  if (!firstRunningTest) {
    return (
      <div className="rounded-lg border border-dashed border-border/60 bg-muted/30 p-8 text-center">
        <Activity className="mx-auto h-8 w-8 text-muted-foreground/50 mb-3" />
        <p className="text-sm text-muted-foreground">
          Start an assessment to see its workflow in real time.
        </p>
      </div>
    );
  }

  let phase: Phase = 'started';
  if (firstRunningTest.status === 'completed') {
    phase = 'completed';
  } else if (recon && hypotheses.length > 0) {
    phase = 'testing';
  } else if (recon) {
    phase = 'reconnaissance';
  } else if (firstRunningTest.status === 'running') {
    phase = 'authentication';
  }

  return (
    <div className="rounded-lg border border-border/50 bg-card p-4">
      <p className="text-xs text-muted-foreground mb-2">
        Live workflow for: <span className="font-medium text-fennec-dark-200">{firstRunningTest.title || truncate(firstRunningTest.target_url, 40)}</span>
      </p>
      <AssessmentPhasesBar currentPhase={phase} hypotheses={hypotheses} />
    </div>
  );
}

export default function StatusPage() {
  const navigate = useNavigate();
  const [tests, setTests] = useState<TestActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchTests = useCallback(async () => {
    try {
      const data = await dashboardApi.getTests(50);
      setTests(data);
    } catch {
      // Silently handle — no backend or network error
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTests();
  }, [fetchTests]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchTests();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const runningTests = tests.filter((t) => t.status === 'running');
  const completedTests = tests.filter(
    (t) => t.status === 'completed' || t.status === 'failed'
  );

  return (
    <DashboardLayout onRefresh={handleRefresh} isRefreshing={isRefreshing}>
      <div className="flex flex-col gap-6 p-4 lg:p-6">
        {/* Page Title */}
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Assessments</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor and manage your security assessments
          </p>
        </div>

        {/* Live Workflow Area */}
        <LiveWorkflowArea firstRunningTest={runningTests[0] ?? null} />

        {/* Active Assessments */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-500" />
              <h2 className="text-lg font-medium">Active Assessments</h2>
              {runningTests.length > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {runningTests.length}
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw
                className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`}
              />
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : runningTests.length === 0 ? (
            <div className="rounded-lg border border-border/50 bg-muted/20 p-6 text-center">
              <p className="text-sm text-muted-foreground">
                No active assessments.
              </p>
            </div>
          ) : (
            <div className="rounded-lg border border-border/50">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Status</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Credential Used</TableHead>
                    <TableHead>Initiated By</TableHead>
                    <TableHead>Started at</TableHead>
                    <TableHead className="w-[80px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runningTests.map((test) => (
                    <TableRow
                      key={test.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/dashboard/status/${test.id}`)}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="h-2.5 w-2.5 rounded-full bg-blue-500 animate-pulse" />
                          <span className="text-xs text-blue-400">Running</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {test.id.slice(0, 8)}...
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm">
                        {test.title || truncate(test.target_url, 35)}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/20">
                          {test.method
                            ? test.method.charAt(0).toUpperCase() + test.method.slice(1)
                            : 'Balanced'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {test.credential_id ? truncate(test.credential_id, 15) : '--'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {test.initiated_by || 'User'}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatDate(test.started_at)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              await dashboardApi.cancelJob(test.id);
                              fetchTests();
                            } catch {
                              // silently ignore
                            }
                          }}
                        >
                          Cancel
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </section>

        {/* Scheduled Assessments */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-lg font-medium">Scheduled Assessments</h2>
          </div>
          <div className="rounded-lg border border-border/50 bg-muted/20 p-6 text-center">
            <p className="text-sm text-muted-foreground">
              No scheduled assessments.
            </p>
          </div>
        </section>

        {/* Historical Assessments */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <History className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-lg font-medium">Historical Assessments</h2>
            {completedTests.length > 0 && (
              <Badge variant="secondary" className="text-xs">
                {completedTests.length}
              </Badge>
            )}
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : completedTests.length === 0 ? (
            <div className="rounded-lg border border-border/50 bg-muted/20 p-6 text-center">
              <p className="text-sm text-muted-foreground">
                No historical assessments yet.
              </p>
            </div>
          ) : (
            <div className="rounded-lg border border-border/50">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Status</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Credential Used</TableHead>
                    <TableHead>Initiated By</TableHead>
                    <TableHead>Started at</TableHead>
                    <TableHead>Completed at</TableHead>
                    <TableHead className="w-[40px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {completedTests.map((test) => (
                    <TableRow
                      key={test.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/dashboard/status/${test.id}`)}
                    >
                      <TableCell>
                        <div
                          className={`h-2.5 w-2.5 rounded-full ${
                            test.status === 'completed'
                              ? 'bg-emerald-500'
                              : 'bg-red-500'
                          }`}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {test.id.slice(0, 8)}...
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm">
                        {truncate(test.target_url, 35)}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/20">
                          {test.method
                            ? test.method.charAt(0).toUpperCase() + test.method.slice(1)
                            : 'Balanced'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {test.credential_id ? truncate(test.credential_id, 15) : '--'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {test.initiated_by || 'User'}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatDate(test.started_at)}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatDate(test.completed_at)}
                      </TableCell>
                      <TableCell>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}
