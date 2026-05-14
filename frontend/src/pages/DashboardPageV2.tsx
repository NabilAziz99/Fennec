import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ChevronRight } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import VulnerabilityTrendsChart from '../components/dashboard/VulnerabilityTrendsChart';
import { useDashboardData } from '../hooks/useDashboardData';
import { targetApi } from '../services/api';
import type { Target } from '../types';

const TIME_RANGES = [
    { label: '7d', days: 7 },
    { label: '14d', days: 14 },
    { label: '30d', days: 30 },
    { label: '90d', days: 90 },
];

export default function DashboardPage() {
    const { data, isLoading, error, refetch } = useDashboardData();
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [activeRange, setActiveRange] = useState(2); // default 30d
    const [targets, setTargets] = useState<Target[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        targetApi.list().then(setTargets).catch(() => {});
    }, []);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        await refetch();
        setTimeout(() => setIsRefreshing(false), 500);
    };

    const stats = data?.stats;
    const totalFindings = stats
        ? stats.critical_count + stats.high_count + stats.medium_count + stats.low_count + stats.info_count
        : 0;

    // Composite score (simple weighted average, 0-10 scale)
    const compositeScore = stats
        ? Math.max(0, 10 - (
            (stats.critical_count * 2 + stats.high_count * 1.5 + stats.medium_count * 1 + stats.low_count * 0.3) / Math.max(1, totalFindings) * 3
        )).toFixed(1)
        : '—';

    const severityLabel = stats && stats.critical_count > 0 ? 'Critical' :
        stats && stats.high_count > 0 ? 'High' :
        stats && stats.medium_count > 0 ? 'Medium' : 'Low';

    const severityColor = severityLabel === 'Critical' ? 'text-red-400' :
        severityLabel === 'High' ? 'text-orange-400' :
        severityLabel === 'Medium' ? 'text-yellow-400' : 'text-green-400';

    return (
        <DashboardLayout onRefresh={handleRefresh} isRefreshing={isRefreshing}>
            <div className="flex flex-col gap-6 py-6 px-6">
                {/* Welcome header */}
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold text-white">
                        Welcome back, Aziz Taleb
                    </h1>
                </div>

                {/* Error banner */}
                {error && (
                    <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4">
                        <AlertCircle className="h-5 w-5 text-destructive" />
                        <p className="text-sm text-destructive flex-1">{error.message}</p>
                        <button onClick={handleRefresh} className="text-sm font-medium text-destructive hover:underline">Retry</button>
                    </div>
                )}

                {/* Score + stats row */}
                <div className="flex items-center gap-6 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                        <span className="text-3xl font-bold text-white">{compositeScore}</span>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${severityColor} bg-white/5`}>
                            /10 {severityLabel}
                        </span>
                    </div>
                    <div className="h-6 w-px bg-border" />
                    <span className="font-medium text-white">{totalFindings}</span>
                    <span>findings</span>
                    <span className="text-xs">— 0% ↗</span>
                    <div className="h-6 w-px bg-border" />
                    <div className="flex items-center gap-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
                        <span>{stats?.critical_count ?? 0}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-orange-500" />
                        <span>{stats?.high_count ?? 0}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-yellow-500" />
                        <span>{stats?.medium_count ?? 0}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-blue-500" />
                        <span>{stats?.low_count ?? 0}</span>
                    </div>
                    <div className="h-6 w-px bg-border" />
                    <span>🎯 {targets.length} targets</span>
                    <span>📋 {stats?.total_tests ?? 0} assessments</span>
                </div>

                {/* Findings Trend chart with time range tabs */}
                <div className="rounded-xl border border-border bg-card p-5">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h2 className="text-sm font-semibold text-white tracking-wider uppercase">Findings Trend</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">{totalFindings} open findings</p>
                        </div>
                        <div className="flex items-center gap-1 bg-muted/30 rounded-lg p-0.5">
                            {TIME_RANGES.map((r, i) => (
                                <button
                                    key={r.label}
                                    onClick={() => setActiveRange(i)}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                                        activeRange === i
                                            ? 'bg-white/10 text-white'
                                            : 'text-muted-foreground hover:text-white'
                                    }`}
                                >
                                    {r.label}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="flex items-center gap-4 mb-3 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                            <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
                            Critical {stats?.critical_count ?? 0}
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="inline-block w-2 h-2 rounded-full bg-orange-500" />
                            High {stats?.high_count ?? 0}
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="inline-block w-2 h-2 rounded-full bg-yellow-500" />
                            Medium {stats?.medium_count ?? 0}
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="inline-block w-2 h-2 rounded-full bg-blue-500" />
                            Low {stats?.low_count ?? 0}
                        </div>
                    </div>
                    <VulnerabilityTrendsChart
                        data={data?.trends || []}
                        isLoading={isLoading}
                    />
                </div>

                {/* Bottom row: Target Security + right column */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Target Security */}
                    <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-sm font-semibold text-white tracking-wider uppercase">Target Security</h2>
                            <button
                                onClick={() => navigate('/dashboard/targets')}
                                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-white transition-colors"
                            >
                                View All Targets <ChevronRight className="h-3 w-3" />
                            </button>
                        </div>

                        {targets.length === 0 && !isLoading ? (
                            <p className="text-sm text-muted-foreground py-8 text-center">No targets configured yet.</p>
                        ) : (
                            <div className="space-y-3">
                                {targets.map(target => {
                                    const tc = target.severity_counts || {};
                                    const targetTotal = (tc.critical || 0) + (tc.high || 0) + (tc.medium || 0) + (tc.low || 0) + (tc.info || 0);
                                    const targetScore = targetTotal > 0
                                        ? Math.max(0, 10 - ((tc.critical || 0) * 2 + (tc.high || 0) * 1.5 + (tc.medium || 0) * 1 + (tc.low || 0) * 0.3) / Math.max(1, targetTotal) * 3).toFixed(1)
                                        : '—';

                                    return (
                                        <div
                                            key={target.id}
                                            onClick={() => navigate(`/dashboard/findings?target_id=${target.id}`)}
                                            className="flex items-center justify-between p-4 rounded-lg border border-border/50 hover:border-border cursor-pointer transition-colors group"
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center text-xs font-bold text-muted-foreground">
                                                    {target.name.charAt(0).toUpperCase()}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-medium text-white group-hover:text-purple-300 transition-colors">
                                                        {target.name}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground">{target.domain}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-6">
                                                <div className="text-right">
                                                    <p className="text-xs text-muted-foreground">MindFort Composite Score</p>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <div className="w-24 h-1.5 bg-muted/30 rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full bg-gradient-to-r from-red-500 via-orange-500 to-green-500 rounded-full"
                                                                style={{ width: `${Math.min(100, (parseFloat(targetScore === '—' ? '0' : targetScore) / 10) * 100)}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-sm font-semibold text-white">{targetScore}/10</span>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                    <span className="text-red-400">{tc.critical || 0} critical</span>
                                                    <span className="text-orange-400">{tc.high || 0} high</span>
                                                    <span>+{(tc.medium || 0) + (tc.low || 0) + (tc.info || 0)} other</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Right column: Time to Fix + Unresolved by Age */}
                    <div className="space-y-6">
                        <div className="rounded-xl border border-border bg-card p-5">
                            <h3 className="text-sm font-semibold text-white tracking-wider uppercase mb-3">Time to Fix</h3>
                            <p className="text-sm text-muted-foreground">No remediation data yet.</p>
                        </div>
                        <div className="rounded-xl border border-border bg-card p-5">
                            <h3 className="text-sm font-semibold text-white tracking-wider uppercase mb-3">Unresolved Findings by Age</h3>
                            <p className="text-sm text-muted-foreground mb-3">{totalFindings} open findings</p>
                            <table className="w-full text-xs text-muted-foreground">
                                <thead>
                                    <tr className="border-b border-border/50">
                                        <th className="text-left py-2 font-medium">Age</th>
                                        <th className="text-center py-2 font-medium"><span className="inline-block w-2 h-2 rounded-full bg-red-500" /> Crit</th>
                                        <th className="text-center py-2 font-medium"><span className="inline-block w-2 h-2 rounded-full bg-orange-500" /> High</th>
                                        <th className="text-center py-2 font-medium"><span className="inline-block w-2 h-2 rounded-full bg-yellow-500" /> Med</th>
                                        <th className="text-center py-2 font-medium"><span className="inline-block w-2 h-2 rounded-full bg-green-500" /> Low</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="border-b border-border/30">
                                        <td className="py-2">&gt; 30 days</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                    </tr>
                                    <tr className="border-b border-border/30">
                                        <td className="py-2">&gt; 60 days</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                    </tr>
                                    <tr>
                                        <td className="py-2">&gt; 90 days</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                        <td className="text-center">—</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
