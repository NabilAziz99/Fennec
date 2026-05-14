import { useEffect, useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import { dashboardApi, pentestApi } from '@/services/api';
import type { RichFinding } from '@/types';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Search,
  Shield,
  Bot,
  MessageSquare,
  Sparkles,
  ThumbsUp,
  Copy,
  ChevronDown,
  AlertTriangle,
  FileText,
  Code2,
  Wrench,
} from 'lucide-react';
import { cn, formatRelativeTime, formatDate } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const VALID_VERDICTS = new Set<string>([
  'critical',
  'high',
  'medium',
  'low',
  'info',
]);

type FilterTab = 'open' | 'resolved' | 'archived';

function severityOrder(s: string | null | undefined): number {
  switch (s) {
    case 'critical':
      return 0;
    case 'high':
      return 1;
    case 'medium':
      return 2;
    case 'low':
      return 3;
    case 'info':
      return 4;
    default:
      return 5;
  }
}

function severityBadgeClasses(severity: string | null | undefined): string {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/20 text-red-400 border border-red-500/30';
    case 'high':
      return 'bg-orange-500/20 text-orange-400 border border-orange-500/30';
    case 'medium':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
    case 'low':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/30';
    case 'info':
      return 'bg-gray-500/20 text-gray-400 border border-gray-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border border-gray-500/30';
  }
}

function severityDotColor(severity: string | null | undefined): string {
  switch (severity) {
    case 'critical':
      return 'bg-red-500';
    case 'high':
      return 'bg-orange-500';
    case 'medium':
      return 'bg-yellow-500';
    case 'low':
      return 'bg-blue-500';
    case 'info':
      return 'bg-gray-500';
    default:
      return 'bg-gray-500';
  }
}

// Extended finding type that carries display fields from FindingDetail fallback
interface DisplayFinding extends RichFinding {
  _title?: string;
  _location?: string;
  _parameter?: string;
  _reproduction_steps?: string[];
  _discovered_by?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function FindingsPage() {
  const [searchParams] = useSearchParams();
  const targetId = searchParams.get('target_id');
  // Optional deep-link support: when AssessmentDetailPage navigates here with
  // ?finding_id=<id> we auto-select that finding instead of the first-valid one.
  const findingIdParam = searchParams.get('finding_id');
  const findingIdHint = findingIdParam ? Number(findingIdParam) : null;

  const [findings, setFindings] = useState<DisplayFinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('open');

  // ---- Fetch findings ----
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        // Load basic findings from dashboard API
        const basicFindings = await dashboardApi.getFindings(
          undefined,
          undefined,
          200,
        );

        if (cancelled) return;

        // Map FindingDetail -> DisplayFinding for consistent display
        const mapped: DisplayFinding[] = basicFindings.map((f, idx) => ({
          id: idx,
          job_id: (f as unknown as Record<string, string>).job_id ?? '',
          hypothesis_id: f.hypothesis_id ?? null,
          status: f.status,
          verdict: f.severity as string | null,
          evidence: f.evidence ? [f.evidence] : [],
          suggested_followups: [],
          needs: [],
          error: null,
          description_overview: f.description ?? null,
          description_breakdown: {
            vuln_type: f.vulnerability_type ?? '',
            affected_endpoint: f.location ?? '',
            access_required: 'Unknown',
            exploitability: 'Unknown',
          },
          description_technical: null,
          impact_demonstrated: null,
          impact_attack_scenarios: null,
          impact_business_risk: null,
          evidence_logged: null,
          evidence_payloads: null,
          evidence_observed: f.evidence ?? null,
          remediation_primary: null,
          remediation_implementation: null,
          remediation_hardening: null,
          owasp_category: f.cwe_id ?? null,
          created_at: f.discovered_at,
          _title: f.title,
          _location: f.location,
          _parameter: f.parameter,
          _reproduction_steps: f.reproduction_steps,
          _discovered_by: f.discovered_by,
        }));

        // Also try loading richer data from pentestApi per job
        const jobIds = [
          ...new Set(
            basicFindings
              .map((f) => (f as unknown as Record<string, string>).job_id)
              .filter(Boolean),
          ),
        ];

        let richResults: DisplayFinding[] = [];
        if (jobIds.length > 0) {
          const results = await Promise.allSettled(
            jobIds.map((jid) => pentestApi.getJobFindings(jid, true)),
          );
          for (const r of results) {
            if (r.status === 'fulfilled' && Array.isArray(r.value)) {
              richResults = [...richResults, ...(r.value as DisplayFinding[])];
            }
          }
        }

        if (cancelled) return;

        // Prefer rich findings if available, fall back to mapped basic findings
        const finalFindings = richResults.length > 0 ? richResults : mapped;
        setFindings(finalFindings);

        // If the caller deep-linked with ?finding_id=<id>, prefer that.
        // Otherwise auto-select the first valid finding.
        const deepLinked = findingIdHint != null
          ? finalFindings.find((f) => f.id === findingIdHint)
          : undefined;
        if (deepLinked) {
          setSelectedId(deepLinked.id);
        } else {
          const firstValid = finalFindings.find((f) =>
            VALID_VERDICTS.has(f.verdict ?? ''),
          );
          if (firstValid) {
            setSelectedId(firstValid.id);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load findings',
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [targetId, findingIdHint]);

  // ---- Filtered + sorted list ----
  const filteredFindings = useMemo(() => {
    let list = findings.filter((f) => VALID_VERDICTS.has(f.verdict ?? ''));

    // target_id filter
    if (targetId) {
      list = list.filter(
        (f) =>
          f.job_id === targetId ||
          (f._location ?? '').toLowerCase().includes(targetId.toLowerCase()),
      );
    }

    // search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((f) => {
        const title = f._title ?? f.description_overview ?? '';
        return (
          title.toLowerCase().includes(q) ||
          (f.verdict ?? '').includes(q) ||
          (f.owasp_category ?? '').toLowerCase().includes(q)
        );
      });
    }

    // Sort by severity
    list.sort((a, b) => severityOrder(a.verdict) - severityOrder(b.verdict));

    return list;
  }, [findings, searchQuery, targetId]);

  const selected = useMemo(
    () => filteredFindings.find((f) => f.id === selectedId) ?? null,
    [filteredFindings, selectedId],
  );

  // Helper to get display title
  function getTitle(f: DisplayFinding): string {
    return f._title ?? f.description_overview?.slice(0, 80) ?? `Finding #${f.id}`;
  }

  // ---- Render ----
  return (
    <DashboardLayout>
      {loading ? (
        <div className="flex h-full min-h-[60vh] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-fennec-purple-500 border-t-transparent" />
            <span className="text-sm text-fennec-dark-400">
              Loading findings...
            </span>
          </div>
        </div>
      ) : error ? (
        <div className="flex h-full min-h-[60vh] items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-center">
            <AlertTriangle className="h-8 w-8 text-fennec-red-400" />
            <p className="text-sm text-fennec-dark-300">{error}</p>
            <Button
              size="sm"
              variant="outline"
              className="border-fennec-dark-600 text-fennec-dark-300"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        </div>
      ) : filteredFindings.length === 0 && findings.length === 0 ? (
        <div className="flex h-full min-h-[60vh] items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-center max-w-sm">
            <Shield className="h-12 w-12 text-fennec-dark-600" />
            <h3 className="text-lg font-medium text-fennec-dark-300">
              No findings yet
            </h3>
            <p className="text-sm text-fennec-dark-500">
              Run a penetration test to discover vulnerabilities. Findings will
              appear here once tests complete.
            </p>
          </div>
        </div>
      ) : (
        /* ====== Three-panel layout ====== */
        <div className="flex h-[calc(100vh-var(--header-height))] text-white overflow-hidden">
          {/* ============================================================ */}
          {/* LEFT SIDEBAR                                                  */}
          {/* ============================================================ */}
          <aside className="w-[300px] min-w-[300px] border-r border-fennec-dark-700 flex flex-col bg-fennec-dark-950/50">
            {/* Filter tabs */}
            <div className="px-3 pt-3 pb-2 border-b border-fennec-dark-700">
              <div className="flex gap-1 rounded-lg bg-fennec-dark-800 p-1">
                {(['open', 'resolved', 'archived'] as FilterTab[]).map(
                  (tab) => (
                    <button
                      key={tab}
                      onClick={() => setFilterTab(tab)}
                      className={cn(
                        'flex-1 rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-colors',
                        filterTab === tab
                          ? 'bg-fennec-purple-600/20 text-fennec-purple-400'
                          : 'text-fennec-dark-400 hover:text-fennec-dark-200',
                      )}
                    >
                      {tab}
                    </button>
                  ),
                )}
              </div>
            </div>

            {/* Search */}
            <div className="px-3 py-2 border-b border-fennec-dark-700">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-fennec-dark-500" />
                <input
                  type="text"
                  placeholder="Search findings..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-md bg-fennec-dark-800 border border-fennec-dark-600 py-1.5 pl-8 pr-3 text-sm text-white placeholder-fennec-dark-500 focus:outline-none focus:border-fennec-purple-500 transition-colors"
                />
              </div>
            </div>

            {/* Findings list */}
            <div className="flex-1 overflow-y-auto">
              {filteredFindings.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                  <Search className="h-8 w-8 text-fennec-dark-600 mb-2" />
                  <p className="text-sm text-fennec-dark-500">
                    No findings match your search
                  </p>
                </div>
              ) : (
                filteredFindings.map((f) => {
                  const isSelected = f.id === selectedId;
                  const title = getTitle(f);
                  return (
                    <button
                      key={f.id}
                      onClick={() => setSelectedId(f.id)}
                      className={cn(
                        'w-full text-left px-3 py-3 border-b border-fennec-dark-800 transition-colors',
                        isSelected
                          ? 'bg-fennec-dark-800 ring-1 ring-fennec-purple-500/50'
                          : 'hover:bg-fennec-dark-800/50',
                      )}
                    >
                      <div className="flex items-start gap-2">
                        <span
                          className={cn(
                            'mt-1.5 h-2 w-2 rounded-full shrink-0',
                            severityDotColor(f.verdict),
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-fennec-dark-100 truncate">
                            {title}
                          </p>
                          <div className="mt-1 flex items-center gap-2 text-xs text-fennec-dark-500">
                            <span
                              className={cn(
                                'inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase',
                                severityBadgeClasses(f.verdict),
                              )}
                            >
                              {f.verdict}
                            </span>
                            <span className="text-fennec-purple-400">
                              Red Team
                            </span>
                            <span className="ml-auto whitespace-nowrap">
                              {formatRelativeTime(f.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>

            {/* Count */}
            <div className="px-3 py-2 border-t border-fennec-dark-700 text-xs text-fennec-dark-500">
              {filteredFindings.length} finding
              {filteredFindings.length !== 1 ? 's' : ''}
            </div>
          </aside>

          {/* ============================================================ */}
          {/* CENTER PANEL                                                  */}
          {/* ============================================================ */}
          <main className="flex-1 flex flex-col overflow-hidden">
            {selected ? (
              <>
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-fennec-dark-700">
                  <h2 className="text-lg font-semibold text-white truncate pr-4">
                    {getTitle(selected)}
                  </h2>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-fennec-dark-600 text-fennec-dark-300 hover:text-white hover:border-fennec-purple-500"
                    >
                      <Wrench className="h-3.5 w-3.5 mr-1" />
                      Patch
                    </Button>
                    <Button
                      size="sm"
                      className="bg-fennec-purple-600 hover:bg-fennec-purple-700 text-white"
                    >
                      Resolve
                    </Button>
                  </div>
                </div>

                {/* Tab content */}
                <Tabs
                  defaultValue="description"
                  className="flex-1 flex flex-col overflow-hidden"
                >
                  <div className="px-6 pt-4 border-b border-fennec-dark-700">
                    <TabsList className="bg-fennec-dark-800">
                      <TabsTrigger value="description" className="gap-1.5">
                        <FileText className="h-3.5 w-3.5" />
                        Description
                      </TabsTrigger>
                      <TabsTrigger value="impact" className="gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Impact
                      </TabsTrigger>
                      <TabsTrigger value="evidence" className="gap-1.5">
                        <Code2 className="h-3.5 w-3.5" />
                        Evidence
                      </TabsTrigger>
                      <TabsTrigger value="remediation" className="gap-1.5">
                        <Wrench className="h-3.5 w-3.5" />
                        Remediation
                      </TabsTrigger>
                    </TabsList>
                  </div>

                  <div className="flex-1 overflow-y-auto px-6 py-5">
                    {/* ---- Description Tab ---- */}
                    <TabsContent value="description" className="mt-0 space-y-6">
                      {selected.description_overview && (
                        <div>
                          <p className="text-sm text-fennec-dark-200 leading-relaxed whitespace-pre-line">
                            {selected.description_overview}
                          </p>
                        </div>
                      )}

                      {selected.description_breakdown && (
                        <div className="rounded-lg border border-fennec-dark-700 bg-fennec-dark-800/50 p-4">
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-3">
                            Breakdown
                          </h4>
                          <ul className="space-y-2 text-sm">
                            {selected.description_breakdown.vuln_type && (
                              <li className="flex gap-2">
                                <span className="text-fennec-dark-500 shrink-0 w-36">
                                  Vuln Type:
                                </span>
                                <span className="text-fennec-dark-200">
                                  {selected.description_breakdown.vuln_type}
                                </span>
                              </li>
                            )}
                            {selected.description_breakdown
                              .affected_endpoint && (
                              <li className="flex gap-2">
                                <span className="text-fennec-dark-500 shrink-0 w-36">
                                  Affected Endpoint:
                                </span>
                                <span className="text-fennec-dark-200 font-mono text-xs">
                                  {
                                    selected.description_breakdown
                                      .affected_endpoint
                                  }
                                </span>
                              </li>
                            )}
                            {selected.description_breakdown.access_required &&
                              selected.description_breakdown.access_required !==
                                'Unknown' && (
                                <li className="flex gap-2">
                                  <span className="text-fennec-dark-500 shrink-0 w-36">
                                    Access Required:
                                  </span>
                                  <span className="text-fennec-dark-200">
                                    {
                                      selected.description_breakdown
                                        .access_required
                                    }
                                  </span>
                                </li>
                              )}
                            {selected.description_breakdown.exploitability &&
                              selected.description_breakdown.exploitability !==
                                'Unknown' && (
                                <li className="flex gap-2">
                                  <span className="text-fennec-dark-500 shrink-0 w-36">
                                    Exploitability:
                                  </span>
                                  <span className="text-fennec-dark-200">
                                    {
                                      selected.description_breakdown
                                        .exploitability
                                    }
                                  </span>
                                </li>
                              )}
                          </ul>
                        </div>
                      )}

                      {selected.description_technical && (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Technical Details
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.description_technical}
                          </p>
                        </div>
                      )}

                      {selected._reproduction_steps &&
                        selected._reproduction_steps.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                              Reproduction Steps
                            </h4>
                            <ol className="list-decimal list-inside space-y-1 text-sm text-fennec-dark-300">
                              {selected._reproduction_steps.map(
                                (step, i) => (
                                  <li key={i}>{step}</li>
                                ),
                              )}
                            </ol>
                          </div>
                        )}
                    </TabsContent>

                    {/* ---- Impact Tab ---- */}
                    <TabsContent value="impact" className="mt-0 space-y-6">
                      {selected.impact_demonstrated ? (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Demonstrated Impact
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.impact_demonstrated}
                          </p>
                        </div>
                      ) : (
                        <p className="text-sm text-fennec-dark-500 italic">
                          No impact analysis available for this finding.
                        </p>
                      )}

                      {selected.impact_attack_scenarios && (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Attack Scenarios
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.impact_attack_scenarios}
                          </p>
                        </div>
                      )}

                      {selected.impact_business_risk && (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Business Risk
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.impact_business_risk}
                          </p>
                        </div>
                      )}
                    </TabsContent>

                    {/* ---- Evidence Tab ---- */}
                    <TabsContent value="evidence" className="mt-0 space-y-6">
                      {selected.evidence_logged &&
                      selected.evidence_logged.length > 0 ? (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-3">
                            Logged Evidence
                          </h4>
                          <div className="space-y-4">
                            {selected.evidence_logged.map((entry, i) => (
                              <div
                                key={i}
                                className="space-y-2 rounded-lg border border-fennec-dark-700 p-3"
                              >
                                <div>
                                  <span className="text-xs font-medium text-fennec-dark-400 uppercase tracking-wider">
                                    Request
                                  </span>
                                  <pre className="mt-1 rounded-md bg-fennec-dark-900 p-3 text-xs text-fennec-dark-200 overflow-x-auto font-mono">
                                    {entry.request}
                                  </pre>
                                </div>
                                <div>
                                  <span className="text-xs font-medium text-fennec-dark-400 uppercase tracking-wider">
                                    Response
                                  </span>
                                  <pre className="mt-1 rounded-md bg-fennec-dark-900 p-3 text-xs text-fennec-dark-200 overflow-x-auto font-mono">
                                    {entry.response}
                                  </pre>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : selected.evidence.length > 0 ? (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-3">
                            Evidence
                          </h4>
                          {selected.evidence.map((e, i) => (
                            <pre
                              key={i}
                              className="mb-2 rounded-md bg-fennec-dark-900 p-3 text-xs text-fennec-dark-200 overflow-x-auto font-mono"
                            >
                              {e}
                            </pre>
                          ))}
                        </div>
                      ) : null}

                      {selected.evidence_payloads &&
                        selected.evidence_payloads.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                              Payloads Used
                            </h4>
                            <pre className="rounded-md bg-fennec-dark-900 p-3 text-xs text-fennec-dark-200 overflow-x-auto font-mono">
                              {selected.evidence_payloads.join('\n')}
                            </pre>
                          </div>
                        )}

                      {selected.evidence_observed && (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Observed Behavior
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.evidence_observed}
                          </p>
                        </div>
                      )}

                      {!selected.evidence_logged?.length &&
                        !selected.evidence.length &&
                        !selected.evidence_payloads?.length &&
                        !selected.evidence_observed && (
                          <p className="text-sm text-fennec-dark-500 italic">
                            No evidence data available for this finding.
                          </p>
                        )}
                    </TabsContent>

                    {/* ---- Remediation Tab ---- */}
                    <TabsContent
                      value="remediation"
                      className="mt-0 space-y-6"
                    >
                      {selected.remediation_primary ? (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Primary Mitigation
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.remediation_primary}
                          </p>
                        </div>
                      ) : (
                        <p className="text-sm text-fennec-dark-500 italic">
                          No remediation guidance available for this finding.
                        </p>
                      )}

                      {selected.remediation_implementation && (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Implementation Pattern
                          </h4>
                          <pre className="rounded-md bg-fennec-dark-900 p-3 text-xs text-fennec-dark-200 overflow-x-auto font-mono">
                            {selected.remediation_implementation}
                          </pre>
                        </div>
                      )}

                      {selected.remediation_hardening && (
                        <div>
                          <h4 className="text-sm font-semibold text-fennec-dark-200 mb-2">
                            Additional Hardening
                          </h4>
                          <p className="text-sm text-fennec-dark-300 leading-relaxed whitespace-pre-line">
                            {selected.remediation_hardening}
                          </p>
                        </div>
                      )}
                    </TabsContent>
                  </div>
                </Tabs>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <p className="text-sm text-fennec-dark-500">
                  Select a finding to view details
                </p>
              </div>
            )}
          </main>

          {/* ============================================================ */}
          {/* RIGHT SIDEBAR                                                 */}
          {/* ============================================================ */}
          {selected && (
            <aside className="w-[260px] min-w-[260px] border-l border-fennec-dark-700 flex flex-col overflow-y-auto bg-fennec-dark-950/50">
              {/* Details section */}
              <div className="px-4 py-4 border-b border-fennec-dark-700">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-fennec-dark-500 mb-3">
                  Details
                </h3>

                {/* Severity + score + tags */}
                <div className="flex items-center gap-2 mb-4">
                  <span
                    className={cn(
                      'inline-flex items-center rounded px-2 py-0.5 text-xs font-bold uppercase',
                      severityBadgeClasses(selected.verdict),
                    )}
                  >
                    {selected.verdict}
                  </span>
                  <span className="text-sm font-semibold text-fennec-dark-200">
                    8.8
                  </span>
                  <Badge
                    variant="outline"
                    className="text-[10px] text-fennec-dark-400 border-fennec-dark-600"
                  >
                    3 tags
                  </Badge>
                </div>

                {/* Metadata rows */}
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-fennec-dark-500">Type</span>
                    <span className="text-fennec-purple-400 font-medium">
                      Red Team
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fennec-dark-500">OWASP</span>
                    <span className="text-fennec-dark-200 font-mono text-xs">
                      {selected.owasp_category ?? 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fennec-dark-500">Cred</span>
                    <span className="text-fennec-dark-400 text-xs">None</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fennec-dark-500">Date</span>
                    <span className="text-fennec-dark-200 text-xs">
                      {formatDate(selected.created_at)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fennec-dark-500">Assigned</span>
                    <span className="text-fennec-dark-400 text-xs italic">
                      Unassigned
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions section */}
              <div className="px-4 py-4 border-b border-fennec-dark-700">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-fennec-dark-500 mb-3">
                  Actions
                </h3>
                <div className="space-y-2">
                  <button className="w-full flex items-center gap-2 rounded-md bg-fennec-dark-800 px-3 py-2 text-sm text-fennec-dark-300 hover:bg-fennec-dark-700 transition-colors">
                    <Bot className="h-4 w-4 text-fennec-purple-400" />
                    Agent
                  </button>
                  <button className="w-full flex items-center gap-2 rounded-md bg-fennec-dark-800 px-3 py-2 text-sm text-fennec-dark-300 hover:bg-fennec-dark-700 transition-colors">
                    <Sparkles className="h-4 w-4 text-fennec-yellow-400" />
                    AI Summary
                  </button>
                  <button className="w-full flex items-center gap-2 rounded-md bg-fennec-dark-800 px-3 py-2 text-sm text-fennec-dark-300 hover:bg-fennec-dark-700 transition-colors">
                    <ThumbsUp className="h-4 w-4 text-fennec-green-400" />
                    Feedback
                  </button>
                </div>
              </div>

              {/* Finding ID */}
              <div className="px-4 py-3 border-b border-fennec-dark-700">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-fennec-dark-500 font-mono truncate mr-2">
                    ID: {String(selected.id).slice(0, 12)}
                    {String(selected.id).length > 12 ? '...' : ''}
                  </span>
                  <button
                    className="text-fennec-dark-500 hover:text-fennec-dark-300 transition-colors"
                    onClick={() =>
                      navigator.clipboard.writeText(String(selected.id))
                    }
                    title="Copy ID"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {/* Comments */}
              <div className="px-4 py-3">
                <button className="flex w-full items-center justify-between text-sm text-fennec-dark-400 hover:text-fennec-dark-200 transition-colors">
                  <span className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Comments
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </button>
                <div className="mt-2 text-xs text-fennec-dark-500 italic">
                  No comments yet
                </div>
              </div>
            </aside>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}
