import { CheckSquare, Key, Search, Shield, CheckCircle, AlertTriangle } from 'lucide-react';
import type { HypothesisResult } from '@/types';

type Phase = 'started' | 'authentication' | 'reconnaissance' | 'testing' | 'validation' | 'completed';

interface AssessmentPhasesBarProps {
  currentPhase: Phase;
  hypotheses?: HypothesisResult[];
}

const PHASES: { key: Phase; label: string; icon: React.ElementType }[] = [
  { key: 'started', label: 'Assessment Started', icon: CheckSquare },
  { key: 'authentication', label: 'Authentication', icon: Key },
  { key: 'reconnaissance', label: 'Reconnaissance', icon: Search },
  { key: 'testing', label: 'Testing', icon: Shield },
  { key: 'validation', label: 'Validation', icon: CheckCircle },
];

/* ---- OWASP category display names ---- */

const OWASP_DISPLAY_NAMES: Record<string, string> = {
  'A01': 'Broken Access Control',
  'A02': 'Cryptographic Failures',
  'A03': 'Injection',
  'A04': 'Insecure Design',
  'A05': 'Security Misconfiguration',
  'A06': 'Vulnerable Components',
  'A07': 'Authentication',
  'A08': 'Data Integrity Failures',
  'A09': 'Logging & Monitoring',
  'A10': 'SSRF',
};

// Specific vulnerability type display names (used when title contains these)
const VULN_DISPLAY_NAMES: Record<string, string> = {
  'xss': 'Cross-Site Scripting (XSS)',
  'xxe': 'XML External Entity (XXE)',
  'ssrf': 'Server-Side Request Forgery (SSRF)',
  'ssti': 'Server-Side Template Injection (SSTI)',
  'sqli': 'SQL Injection',
  'sql_injection': 'SQL Injection',
  'sql injection': 'SQL Injection',
  'file upload': 'File Upload',
  'file_upload': 'File Upload',
  'business logic': 'Business Logic',
  'path traversal': 'Path Traversal',
  'command injection': 'OS Command Injection',
  'os command': 'OS Command Injection',
  'broken access': 'Broken Access Control',
  'access control': 'Broken Access Control',
  'information disclosure': 'Information Disclosure',
  'security misconfiguration': 'Security Misconfiguration',
  'authentication': 'Authentication',
  'cryptographic': 'Cryptographic Failures',
  'injection': 'Injection',
  'idor': 'Broken Access Control',
};

function getHypothesisDisplayName(h: HypothesisResult): string {
  // If owasp_category is set, use the OWASP display name
  if (h.owasp_category && OWASP_DISPLAY_NAMES[h.owasp_category]) {
    return OWASP_DISPLAY_NAMES[h.owasp_category];
  }

  // Try to extract OWASP code from title like "[A03 Injection]"
  const owaspMatch = h.title.match(/\[?(A\d{2})\b/i);
  if (owaspMatch && OWASP_DISPLAY_NAMES[owaspMatch[1].toUpperCase()]) {
    return OWASP_DISPLAY_NAMES[owaspMatch[1].toUpperCase()];
  }

  // Try to match specific vulnerability types from title
  const titleLower = h.title.toLowerCase();
  for (const [key, name] of Object.entries(VULN_DISPLAY_NAMES)) {
    if (titleLower.includes(key)) {
      return name;
    }
  }

  // Fallback to the hypothesis title (truncated)
  return h.title.length > 30 ? h.title.slice(0, 27) + '...' : h.title;
}

type HypothesisDotStatus = 'tested' | 'testing' | 'pending';

function getHypothesisDotStatus(h: HypothesisResult): HypothesisDotStatus {
  if (h.status === 'completed' || h.status === 'dead_end') return 'tested';
  if (h.status === 'in_progress') return 'testing';
  return 'pending';
}

const hypothesisDotClass: Record<HypothesisDotStatus, string> = {
  tested: 'bg-emerald-500',
  testing: 'bg-amber-500 animate-pulse',
  pending: 'bg-fennec-dark-500',
};

/* ---- Phase helpers ---- */

function getPhaseIndex(phase: Phase): number {
  if (phase === 'completed') return PHASES.length;
  return PHASES.findIndex((p) => p.key === phase);
}

type PhaseStatus = 'complete' | 'active' | 'inactive';

function getPhaseStatus(phaseIdx: number, currentIdx: number): PhaseStatus {
  if (phaseIdx < currentIdx) return 'complete';
  if (phaseIdx === currentIdx) return 'active';
  return 'inactive';
}

function getLineStatus(fromIdx: number, currentIdx: number): PhaseStatus {
  if (fromIdx + 1 < currentIdx) return 'complete';
  if (fromIdx + 1 === currentIdx) return 'active';
  return 'inactive';
}

const statusDotClass: Record<PhaseStatus, string> = {
  complete: 'bg-emerald-500',
  active: 'bg-blue-500 animate-pulse',
  inactive: 'bg-fennec-dark-600',
};

const statusLabelClass: Record<PhaseStatus, string> = {
  complete: 'text-emerald-400',
  active: 'text-blue-400',
  inactive: 'text-fennec-dark-500',
};

const statusLabelText: Record<PhaseStatus, string> = {
  complete: 'Complete',
  active: 'Active',
  inactive: 'Inactive',
};

const lineColorClass: Record<PhaseStatus, string> = {
  complete: 'border-emerald-500/60',
  active: 'border-blue-500/60',
  inactive: 'border-fennec-dark-600/60',
};

const iconContainerClass: Record<PhaseStatus, string> = {
  complete: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  active: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  inactive: 'text-fennec-dark-500 bg-fennec-dark-800 border-fennec-dark-700',
};

/* ---- Expanded Testing Card ---- */

function TestingExpansionCard({ hypotheses }: { hypotheses: HypothesisResult[] }) {
  const total = hypotheses.length;
  const completed = hypotheses.filter(
    (h) => h.status === 'completed' || h.status === 'dead_end'
  ).length;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  // Deduplicate by display name (in case multiple hypotheses map to same category)
  const categoryMap = new Map<string, HypothesisDotStatus>();
  for (const h of hypotheses) {
    const name = getHypothesisDisplayName(h);
    const dotStatus = getHypothesisDotStatus(h);
    const existing = categoryMap.get(name);
    // Keep the most "active" status: testing > pending > tested
    if (!existing || dotStatus === 'testing' || (dotStatus === 'pending' && existing === 'tested')) {
      categoryMap.set(name, dotStatus);
    }
  }

  const categories = Array.from(categoryMap.entries());

  return (
    <div className="absolute top-0 left-0 z-20 rounded-lg border border-amber-500/30 bg-fennec-dark-900 shadow-xl min-w-[340px]">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-fennec-dark-700">
        <AlertTriangle className="h-4 w-4 text-amber-500" />
        <span className="text-sm font-semibold text-fennec-dark-100">Testing</span>
      </div>

      {/* Completion bar */}
      <div className="px-3 pt-2 pb-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-fennec-dark-400 font-medium">Completion</span>
          <span className="text-[10px] text-emerald-400 font-semibold">{pct}%</span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-fennec-dark-700 overflow-hidden">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Category grid */}
      <div className="grid grid-cols-2 gap-1.5 p-3 pt-2">
        {categories.map(([name, dotStatus]) => (
          <div
            key={name}
            className="flex items-center gap-2 rounded border border-fennec-dark-700 bg-fennec-dark-800 px-2.5 py-1.5"
          >
            <div className={`h-2 w-2 rounded-full shrink-0 ${hypothesisDotClass[dotStatus]}`} />
            <span className="text-[11px] text-fennec-dark-200 leading-tight">{name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---- Main Component ---- */

export function AssessmentPhasesBar({ currentPhase, hypotheses = [] }: AssessmentPhasesBarProps) {
  const currentIdx = getPhaseIndex(currentPhase);
  const testingIdx = PHASES.findIndex((p) => p.key === 'testing');
  const showTestingExpansion =
    hypotheses.length > 0 &&
    (currentPhase === 'testing' || currentPhase === 'validation' || currentPhase === 'completed');

  return (
    <div className="overflow-x-auto overflow-y-visible">
      <div className="flex items-center gap-0 min-w-[780px] py-2">
        {PHASES.map((phase, idx) => {
          const status = getPhaseStatus(idx, currentIdx);
          const Icon = phase.icon;
          const isTestingPhase = idx === testingIdx;

          return (
            <div key={phase.key} className="flex items-center">
              {/* Phase Card (with relative position for expansion) */}
              <div className={isTestingPhase ? 'relative' : ''}>
                <div
                  className={`flex flex-col items-center gap-2 rounded-lg border px-4 py-3 w-[152px] shrink-0 ${
                    status === 'active'
                      ? 'border-blue-500/40 bg-blue-500/5'
                      : status === 'complete'
                      ? 'border-emerald-500/20 bg-emerald-500/5'
                      : 'border-fennec-dark-700 bg-fennec-dark-900'
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-md border ${iconContainerClass[status]}`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-medium text-fennec-dark-200 text-center leading-tight">
                    {phase.label}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <div className={`h-2 w-2 rounded-full ${statusDotClass[status]}`} />
                    <span className={`text-[10px] font-medium ${statusLabelClass[status]}`}>
                      {statusLabelText[status]}
                    </span>
                  </div>
                </div>

                {/* Expanded Testing Card */}
                {isTestingPhase && showTestingExpansion && (
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-20">
                    <TestingExpansionCard hypotheses={hypotheses} />
                  </div>
                )}
              </div>

              {/* Connecting line */}
              {idx < PHASES.length - 1 && (
                <div
                  className={`w-8 border-t-2 border-dashed mx-0.5 shrink-0 ${
                    lineColorClass[getLineStatus(idx, currentIdx)]
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default AssessmentPhasesBar;
