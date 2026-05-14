import {Collapsible, CollapsibleContent, CollapsibleTrigger} from '@/components/ui/Collapsible';
import { cn } from '@/lib/utils';
import type { RichFinding } from '@/types';
import {ChevronDown} from "lucide-react";

interface FindingsPanelProps {
  findings: RichFinding[];
  summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}

const severityOrder = ['critical', 'high', 'medium', 'low', 'info'] as const;
type Severity = typeof severityOrder[number];

const severityColors: Record<Severity, { bg: string; text: string; border: string; badgeBg: string }> = {
  critical: {
    bg: 'bg-red-600/20',
    text: 'text-red-400',
    border: 'border-red-600/30',
    badgeBg: 'bg-red-600/30',
  },
  high: {
    bg: 'bg-orange-600/20',
    text: 'text-orange-400',
    border: 'border-orange-600/30',
    badgeBg: 'bg-orange-600/30',
  },
  medium: {
    bg: 'bg-yellow-600/20',
    text: 'text-yellow-400',
    border: 'border-yellow-600/30',
    badgeBg: 'bg-yellow-600/30',
  },
  low: {
    bg: 'bg-blue-600/20',
    text: 'text-blue-400',
    border: 'border-blue-600/30',
    badgeBg: 'bg-blue-600/30',
  },
  info: {
    bg: 'bg-fennec-dark-600/50',
    text: 'text-fennec-dark-300',
    border: 'border-fennec-dark-600',
    badgeBg: 'bg-fennec-dark-600',
  },
};

export function FindingsPanel({ findings, summary }: FindingsPanelProps) {
  const groupedFindings = severityOrder.reduce((acc, severity) => {
    acc[severity] = findings.filter(f => f.verdict === severity);
    return acc;
  }, {} as Record<Severity, RichFinding[]>);

  return (
    <div className="bg-fennec-dark-900/80 border border-fennec-dark-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-white mb-4">Findings Summary</h3>

      {/* Summary badges */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {severityOrder.map((sev) => (
          summary[sev] > 0 && (
            <span
              key={sev}
              className={cn(
                'px-3 py-1.5 rounded-full text-xs font-medium',
                severityColors[sev].badgeBg,
                severityColors[sev].text
              )}
            >
              {summary[sev]} {sev.toUpperCase()}
            </span>
          )
        ))}
        {summary.total === 0 && (
          <span className="text-fennec-dark-500 text-sm italic">No findings yet</span>
        )}
      </div>

      {/* Findings by severity */}
      {findings.length > 0 && (
        <div className="space-y-2">
          {severityOrder.map((severity) => (
              groupedFindings[severity]?.length > 0 && (
                  <Collapsible
                      key={severity}
                      defaultOpen={severity === 'critical' || severity === 'high'}
                      className={cn('border rounded-lg', severityColors[severity].border)}
                  >
                    <CollapsibleTrigger className={cn(
                        'flex w-full items-center justify-between p-3 rounded-t-lg hover:opacity-80 transition-opacity',
                        severityColors[severity].bg,
                        severityColors[severity].text
                    )}>
                      <div className="flex items-center gap-2">
          <span className="font-medium text-sm">
            {severity.toUpperCase()}
          </span>
                        <span className={cn(
                            'text-xs px-2 py-0.5 rounded-full',
                            severityColors[severity].badgeBg
                        )}>
            {groupedFindings[severity].length}
          </span>
                      </div>
                      <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
                    </CollapsibleTrigger>
                    <CollapsibleContent className="px-3 pb-3">
                      <div className="space-y-2 mt-2">
                        {groupedFindings[severity].map((finding) => (
                            <FindingCard key={finding.id} finding={finding} severity={severity} />
                        ))}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
              )
          ))}
        </div>
      )}
    </div>
  );
}

interface FindingCardProps {
  finding: RichFinding;
  severity: Severity;
}

function FindingCard({ finding, severity }: FindingCardProps) {
  const colors = severityColors[severity];
  const title = finding.description_overview || finding.owasp_category || `Finding #${finding.id}`;
  const vulnType = finding.description_breakdown?.vuln_type;
  const location = finding.description_breakdown?.affected_endpoint;

  return (
    <div className={cn('p-3 rounded-lg', colors.bg)}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className={cn('font-medium', colors.text)}>{title}</div>
          <div className="text-xs text-fennec-dark-400 mt-1 space-x-2">
            {vulnType && <span>{vulnType}</span>}
            {vulnType && location && <span>•</span>}
            {location && <span>{location}</span>}
          </div>
        </div>
        <span className={cn(
          'text-xs px-2 py-0.5 rounded flex-shrink-0',
          finding.status === 'completed' && 'bg-fennec-green-600/20 text-fennec-green-400',
          finding.status === 'error' && 'bg-fennec-red-600/20 text-fennec-red-400',
        )}>
          {finding.status}
        </span>
      </div>

      {finding.description_technical && (
        <p className="text-xs text-fennec-dark-400 mt-2 line-clamp-2">
          {finding.description_technical}
        </p>
      )}

      {finding.evidence && finding.evidence.length > 0 && (
        <div className="mt-2 p-2 bg-fennec-dark-900/50 rounded text-xs font-mono text-fennec-dark-400 overflow-x-auto">
          <code className="whitespace-pre-wrap break-all">{finding.evidence[0]}</code>
        </div>
      )}

      {finding.owasp_category && (
        <div className="mt-2 text-xs text-fennec-dark-500">
          OWASP: {finding.owasp_category}
        </div>
      )}

      {finding.created_at && (
        <div className="mt-2 flex items-center gap-2 text-xs text-fennec-dark-600">
          <span>{new Date(finding.created_at).toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}

export default FindingsPanel;
