import { useParams, Link, useNavigate } from 'react-router-dom';
import { useMemo, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  ExternalLink,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Radio,
  ShieldAlert,
  Activity,
  Search,
  FlaskConical,
  Bug,
} from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import {
  useTestDetail,
  useTestFindings,
  useTestHypotheses,
  useTestRecon,
  useTestToolCalls,
} from '../hooks/useDashboardData';
import { usePentestContext } from '@/contexts/PentestContext';
import {
  ToolCallsPanel,
  HypothesesPanel,
  ReconPanel,
} from '@/components/panels';
import { AssessmentPhasesBar } from '@/components/dashboard/AssessmentPhasesBar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { RichFinding, HypothesisResult, ToolExecutionEvent } from '@/types';
import type { ReconState } from '@/hooks/usePentestStream';

/* ---- Status helpers ---- */

function StatusIcon({ status }: { status: string }) {
  const icons: Record<string, JSX.Element> = {
    completed: <CheckCircle className="h-4 w-4 text-emerald-400" />,
    running: <Clock className="h-4 w-4 text-primary animate-pulse" />,
    pending: <Clock className="h-4 w-4 text-muted-foreground" />,
    failed: <XCircle className="h-4 w-4 text-destructive" />,
    awaiting_review: <ShieldAlert className="h-4 w-4 text-amber-400 animate-pulse" />,
  };
  return icons[status] || icons.pending;
}

const statusVariant: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  completed: 'outline',
  running: 'secondary',
  pending: 'outline',
  failed: 'destructive',
  awaiting_review: 'secondary',
};

function LiveIndicator() {
  return (
    <Badge variant="outline" className="gap-1.5 border-emerald-500/40 text-emerald-400">
      <Radio className="h-3 w-3 animate-pulse" />
      Live
    </Badge>
  );
}

/* ---- Severity badge helper ---- */

const severityColors: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  info: 'bg-fennec-dark-600/20 text-fennec-dark-300 border-fennec-dark-600/30',
};

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <Badge
      variant="outline"
      className={`text-xs ${severityColors[severity] || severityColors.info}`}
    >
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </Badge>
  );
}

/* ---- Phase determination ---- */

type Phase = 'started' | 'authentication' | 'reconnaissance' | 'testing' | 'validation' | 'completed';

function determinePhase(
  status: string | undefined,
  hasRecon: boolean,
  hypothesesCount: number
): Phase {
  if (status === 'completed') return 'completed';
  if (hasRecon && hypothesesCount > 0) return 'testing';
  if (hasRecon) return 'reconnaissance';
  if (status === 'running') return 'authentication';
  return 'started';
}

/* ---- Page ---- */

export default function AssessmentDetailPage() {
  const { testId } = useParams<{ testId: string }>();
  const navigate = useNavigate();
  const toolCallsEndRef = useRef<HTMLDivElement>(null);

  // SSE from context
  const {
    connectionStatus,
    sessionId: streamSessionId,
    testStatus: streamTestStatus,
    hypotheses: streamHypotheses,
    findings: streamFindings,
    recon: streamRecon,
    agentActivity,
    connectToSession,
    tasksByHypothesis,
    stepsByHypothesis,
  } = usePentestContext();

  const isActiveStream = streamSessionId === testId && connectionStatus === 'connected';

  // REST fallback
  const { test, isLoading, error } = useTestDetail(testId || '');
  const isRunning = isActiveStream ? streamTestStatus === 'running' : test?.status === 'running';
  const isActive = isRunning || test?.status === 'awaiting_review';
  const shouldPoll = !isActiveStream && isActive;

  const { findings: restFindings } = useTestFindings(testId || '', shouldPoll);
  const { hypotheses: restHypotheses } = useTestHypotheses(testId || '', shouldPoll);
  const { recon: restRecon } = useTestRecon(testId || '', shouldPoll);
  const { toolCalls: restToolCalls } = useTestToolCalls(testId || '', shouldPoll);

  // Effective job status (SSE takes priority)
  const effectiveStatus = isActiveStream ? (streamTestStatus || test?.status) : test?.status;

  // Findings: SSE primary, REST fallback
  // Only count rows the backend also counts on the global /dashboard/findings
  // page — i.e. completed pentester results with a real verdict. Empty
  // placeholder rows (status='pending', verdict=null) shouldn't be rendered
  // as "Info" findings in the tab, because they cause the inline count to
  // disagree with the sidebar Findings count and confuse the user.
  const findings: RichFinding[] = useMemo(() => {
    const source = isActiveStream && streamFindings.findings.length > 0
      ? streamFindings.findings
      : ((restFindings as unknown as RichFinding[]) || []);
    return source.filter((f) => {
      const v = (f.verdict || '').toString().toLowerCase();
      return v && v !== 'inconclusive';
    });
  }, [isActiveStream, streamFindings.findings, restFindings]);

  // Hypotheses: SSE primary (Record), REST fallback (array -> Record)
  // Only prefer the stream when it has data — otherwise fall through to REST
  // so mid-flight reconnects still show historical hypotheses.
  const hypothesesRecord: Record<string, HypothesisResult> = useMemo(() => {
    if (isActiveStream && Object.keys(streamHypotheses.hypotheses).length > 0) {
      return streamHypotheses.hypotheses;
    }
    // REST returns { id: number, hypothesis_id: string, ... }
    // HypothesisResult expects id: string (UUID). Map hypothesis_id → id.
    return Object.fromEntries((restHypotheses || []).map((h) => {
      const mapped: HypothesisResult = {
        ...h,
        id: (h as unknown as { hypothesis_id?: string }).hypothesis_id || String(h.id),
        status: h.status as HypothesisResult['status'],
        result: null,
        severity: null,
        parent_id: null,
        children_ids: [],
        priority: h.priority ?? 'medium',
        required_agent: h.required_agent ?? 'pentester',
        skills: h.skills ?? [],
        owasp_category: h.owasp_category ?? undefined,
        created_at: h.created_at ?? '',
        started_at: null,
        completed_at: null,
      };
      return [mapped.id, mapped];
    }));
  }, [isActiveStream, streamHypotheses.hypotheses, restHypotheses]);

  const hypothesesArray = Object.values(hypothesesRecord);

  // Recon: SSE primary (ReconState), REST fallback (mapped to ReconState)
  const reconForPanel: ReconState | null = useMemo(() => {
    if (isActiveStream && streamRecon) return streamRecon;
    if (!restRecon) return null;
    return {
      technologies: restRecon.technologies as ReconState['technologies'],
      endpoints: restRecon.endpoints as ReconState['endpoints'],
      entryPoints: restRecon.entry_points as unknown as ReconState['entryPoints'],
      authType: restRecon.auth_type ?? null,
      loginEndpoint: restRecon.login_endpoint ?? null,
      registrationAvailable: restRecon.registration_available,
      summary: restRecon.summary ?? '',
      components: restRecon.components ?? [],
      vulnerabilityCandidates: restRecon.vulnerability_candidates ?? [],
      keyFindings: restRecon.key_findings ?? [],
      ipAddress: restRecon.ip_address ?? null,
      portsOpen: restRecon.ports_open ?? [],
      headersOfInterest: restRecon.headers_of_interest ?? [],
      cookiesObserved: restRecon.cookies_observed ?? [],
      defaultCredentialsFound: restRecon.default_credentials_found ?? false,
      notes: restRecon.notes ?? [],
    };
  }, [isActiveStream, streamRecon, restRecon]);

  // Tool executions: SSE primary, REST fallback
  // Only prefer the stream when it has data — otherwise fall through to REST.
  const toolExecutionsForPanel: ToolExecutionEvent[] = useMemo(() => {
    if (isActiveStream && agentActivity.toolExecutions.length > 0) {
      return agentActivity.toolExecutions;
    }
    return (restToolCalls || []).map((tc) => {
      // Parse tool_input if it arrives as a JSON string from REST
      let parsedInput: Record<string, unknown> = {};
      if (typeof tc.tool_input === 'string') {
        try { parsedInput = JSON.parse(tc.tool_input); } catch { parsedInput = { raw: tc.tool_input }; }
      } else if (tc.tool_input && typeof tc.tool_input === 'object') {
        parsedInput = tc.tool_input as Record<string, unknown>;
      }
      return {
        id: Number(tc.id) || undefined,
        session_id: tc.session_id,
        tool_name: tc.tool_name,
        tool_input: parsedInput,
        agent: tc.agent,
        success: tc.success,
        result: tc.result,
        error: tc.error || null,
        timestamp: tc.timestamp || null,
      };
    });
  }, [isActiveStream, agentActivity.toolExecutions, restToolCalls]);

  // Connect to SSE stream if not already connected
  useEffect(() => {
    if (testId && !isActiveStream && connectionStatus === 'idle') {
      connectToSession(testId);
    }
  }, [testId, isActiveStream, connectionStatus, connectToSession]);

  // Auto-scroll tool calls
  useEffect(() => {
    if (isRunning && toolCallsEndRef.current) {
      toolCallsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [toolExecutionsForPanel.length, isRunning]);

  // Determine current phase
  const currentPhase = determinePhase(
    effectiveStatus,
    reconForPanel !== null,
    hypothesesArray.length
  );

  /* ---- Loading state ---- */
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex flex-col gap-4 p-4 lg:p-6">
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
          <div className="h-24 animate-pulse rounded-xl bg-muted" />
          <div className="h-10 w-96 animate-pulse rounded bg-muted" />
          <div className="h-64 animate-pulse rounded-xl bg-muted" />
        </div>
      </DashboardLayout>
    );
  }

  /* ---- Error / not found ---- */
  if (error || !test) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="mb-4 h-12 w-12 text-destructive" />
          <h2 className="mb-2 text-xl font-semibold">Assessment Not Found</h2>
          <p className="mb-6 text-muted-foreground">
            {error?.message || 'The requested assessment could not be found.'}
          </p>
          <Button asChild>
            <Link to="/dashboard/status">Back to Assessments</Link>
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-4 p-4 md:gap-6">
        {/* Header */}
        <div>
          <Button variant="ghost" size="sm" asChild className="mb-4 -ml-2 text-muted-foreground">
            <Link to="/dashboard/status">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Assessments
            </Link>
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold">{test.title || 'Security Assessment'}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <a
                  href={test.target_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  {test.target_url}
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
                <Badge variant={statusVariant[test.status] ?? 'outline'} className="gap-1.5">
                  <StatusIcon status={test.status} />
                  {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
                </Badge>
                {isActiveStream && <LiveIndicator />}
              </div>
            </div>
            {isRunning && (
              <Button
                variant="outline"
                size="sm"
                className="text-destructive border-destructive/30 hover:bg-destructive/10"
                onClick={async () => {
                  try {
                    const { dashboardApi } = await import('@/services/api');
                    await dashboardApi.cancelJob(testId!);
                    window.location.reload();
                  } catch {
                    // silently ignore
                  }
                }}
              >
                <XCircle className="mr-1.5 h-3.5 w-3.5" />
                Cancel
              </Button>
            )}
          </div>
        </div>

        {/* Phase Bar */}
        <AssessmentPhasesBar currentPhase={currentPhase} hypotheses={hypothesesArray} />

        {/* Tabbed Content */}
        <Tabs defaultValue="activity" className="w-full">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="activity" className="gap-1.5">
              <Activity className="h-3.5 w-3.5" />
              Live Activity
            </TabsTrigger>
            <TabsTrigger value="recon" className="gap-1.5">
              <Search className="h-3.5 w-3.5" />
              Recon Data
            </TabsTrigger>
            <TabsTrigger value="hypotheses" className="gap-1.5">
              <FlaskConical className="h-3.5 w-3.5" />
              Hypotheses
              {hypothesesArray.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-[10px] px-1.5 py-0">
                  {hypothesesArray.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="findings" className="gap-1.5">
              <Bug className="h-3.5 w-3.5" />
              Findings
              {findings.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-[10px] px-1.5 py-0">
                  {findings.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Live Activity Tab */}
          <TabsContent value="activity">
            {toolExecutionsForPanel.length === 0 && agentActivity.toolCalls.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Activity className="mb-3 h-8 w-8 text-muted-foreground/50 animate-pulse" />
                  <p className="text-sm text-muted-foreground">
                    {isRunning
                      ? 'Waiting for agent activity...'
                      : 'No tool call activity recorded for this assessment.'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                <ToolCallsPanel
                  toolExecutions={toolExecutionsForPanel}
                />
                <div ref={toolCallsEndRef} />
              </>
            )}
          </TabsContent>

          {/* Recon Data Tab */}
          <TabsContent value="recon">
            {!reconForPanel ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Search className="mb-3 h-8 w-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    {isRunning
                      ? 'Reconnaissance data will appear here once the recon phase completes.'
                      : 'No reconnaissance data available for this assessment.'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <ReconPanel recon={reconForPanel} isStreaming={isActiveStream} />
            )}
          </TabsContent>

          {/* Hypotheses Tab */}
          <TabsContent value="hypotheses">
            {hypothesesArray.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <FlaskConical className="mb-3 h-8 w-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    {isRunning
                      ? 'Hypotheses will appear here after analysis.'
                      : 'No hypotheses were generated for this assessment.'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <HypothesesPanel
                hypotheses={hypothesesRecord}
                currentHypothesisId={streamHypotheses.currentHypothesisId}
                statistics={streamHypotheses.statistics}
                blockedList={streamHypotheses.blockedList}
                outputsRegistry={streamHypotheses.outputsRegistry}
                pendingOutputs={streamHypotheses.pendingOutputs}
                tasksByHypothesis={tasksByHypothesis}
                stepsByHypothesis={stepsByHypothesis}
                isStreaming={isActiveStream}
              />
            )}
          </TabsContent>

          {/* Findings Tab */}
          <TabsContent value="findings">
            {findings.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Bug className="mb-3 h-8 w-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    {isRunning
                      ? 'Findings will appear here as vulnerabilities are discovered.'
                      : 'No findings were discovered for this assessment.'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader className="py-3">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Findings ({findings.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {findings.map((finding) => {
                    // Short, precise title — prefer OWASP category (always
                    // short), fall back to first line of description_overview
                    // capped at 60 chars. Long descriptions go under the
                    // title as secondary text.
                    const overview = finding.description_overview?.trim() || '';
                    const firstLine = overview.split('\n')[0];
                    const shortFromOverview = firstLine.length > 60
                      ? firstLine.slice(0, 60).trimEnd() + '…'
                      : firstLine;
                    const title = finding.owasp_category
                      || shortFromOverview
                      || `Finding #${finding.id}`;
                    return (
                      <button
                        key={finding.id}
                        type="button"
                        onClick={() =>
                          navigate(`/dashboard/findings?finding_id=${finding.id}`)
                        }
                        className="flex w-full items-start gap-3 rounded-lg border border-border/50 bg-fennec-dark-900 p-3 text-left transition-colors hover:bg-fennec-dark-800 hover:border-border"
                      >
                        <SeverityBadge severity={finding.verdict || 'info'} />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-fennec-dark-200 truncate">
                            {title}
                          </p>
                          {overview && overview !== title && (
                            <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
                              {overview}
                            </p>
                          )}
                          {finding.hypothesis_id && (
                            <p className="mt-1 text-xs font-mono text-fennec-dark-400">
                              Hypothesis: {finding.hypothesis_id}
                            </p>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
