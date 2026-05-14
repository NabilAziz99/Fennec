/**
 * Hypothesis Card (Simplified)
 *
 * Compact card showing key hypothesis information at a glance.
 * Click to open full detail dialog.
 */

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { HypothesisResult, Task, StepRecord } from '@/types';
import {
  Target,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ChevronRight,
} from 'lucide-react';

interface HypothesisCardProps {
  hypothesis: HypothesisResult;
  tasks: Task[];
  steps: StepRecord[];
  isActive: boolean;
  isStreaming: boolean;
  onClick?: () => void;
}

export function HypothesisCard({
  hypothesis,
  tasks,
  steps,
  isActive,
  onClick,
}: HypothesisCardProps) {
  if (!hypothesis || typeof hypothesis !== 'object') {
    return null;
  }
  const statusColors: Record<string, string> = {
    pending: 'border-fennec-dark-600 bg-fennec-dark-900/30',
    in_progress: 'border-fennec-purple-500 shadow-fennec-purple-500/20 shadow-lg bg-fennec-purple-900/10',
    completed: 'border-fennec-green-600 bg-fennec-green-900/10',
    blocked: 'border-fennec-orange-500 bg-fennec-orange-900/10',
    dead_end: 'border-fennec-dark-500 bg-fennec-dark-900/20',
  };

  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Clock className="h-5 w-5 text-fennec-dark-400" />,
    in_progress: <Clock className="h-5 w-5 text-fennec-purple-400 animate-pulse" />,
    completed: <CheckCircle2 className="h-5 w-5 text-fennec-green-400" />,
    blocked: <AlertTriangle className="h-5 w-5 text-fennec-orange-400" />,
    dead_end: <AlertTriangle className="h-5 w-5 text-fennec-dark-500" />,
  };

  const severityColors: Record<string, string> = {
    critical: 'bg-red-600/20 text-red-400 border-red-600/30',
    high: 'bg-orange-600/20 text-orange-400 border-orange-600/30',
    medium: 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30',
    low: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
    info: 'bg-fennec-dark-600 text-fennec-dark-300 border-fennec-dark-600/30',
  };

  // Calculate progress
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const totalTasks = tasks.length;
  const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Count findings
  const findingsCount = hypothesis.findings?.length || 0;

  return (
    <div
      className={cn(
        'rounded-lg border-2 transition-all cursor-pointer hover:scale-[1.02] hover:shadow-xl group',
        statusColors[hypothesis.status] || statusColors.pending,
        isActive && 'ring-2 ring-fennec-purple-400/50',
        // Add left border color based on hypothesis.color
        hypothesis.color && `border-l-4`,
      )}
      style={{
        borderLeftColor: hypothesis.color || undefined,
      }}
      onClick={onClick}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {/* Status Icon */}
            {statusIcons[hypothesis.status] || statusIcons.pending}

            {/* Title & ID */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-white truncate group-hover:text-fennec-purple-400 transition-colors">
                {hypothesis.title}
              </h3>
              <p className="text-xs text-fennec-dark-500 mt-0.5 font-mono">
                {String(hypothesis.id).slice(0, 8)}
              </p>
            </div>
          </div>

          {/* Badges */}
          <div className="flex flex-col gap-1 flex-shrink-0">
            {hypothesis.severity && (
              <Badge className={cn("text-xs border", severityColors[hypothesis.severity])}>
                {hypothesis.severity.toUpperCase()}
              </Badge>
            )}
            <Badge variant="outline" className="text-xs text-fennec-dark-400 border-fennec-dark-600">
              <Target className="h-3 w-3 mr-1" />
              {hypothesis.required_agent}
            </Badge>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-fennec-dark-300 line-clamp-2 mb-3">
          {hypothesis.description}
        </p>

        {/* Skills (max 3) */}
        {Array.isArray(hypothesis.skills) && hypothesis.skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {hypothesis.skills.slice(0, 3).map((skill, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 bg-fennec-dark-700/50 text-fennec-dark-400 rounded text-xs"
              >
                {skill}
              </span>
            ))}
            {hypothesis.skills.length > 3 && (
              <span className="px-2 py-0.5 bg-fennec-dark-700/50 text-fennec-dark-500 rounded text-xs">
                +{hypothesis.skills.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Key Metrics */}
        <div className="flex items-center gap-4 text-xs text-fennec-dark-500">
          {/* Tasks Progress */}
          {totalTasks > 0 && (
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>
                {completedTasks}/{totalTasks} tasks
              </span>
              <span className="text-fennec-dark-600">({progressPercent}%)</span>
            </div>
          )}

          {/* Findings */}
          {findingsCount > 0 && (
            <div className="flex items-center gap-1.5 text-red-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>{findingsCount} finding{findingsCount !== 1 && 's'}</span>
            </div>
          )}

          {/* Actions Count */}
          {steps.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span>{steps.length} action{steps.length !== 1 && 's'}</span>
            </div>
          )}
        </div>

        {/* Blocked Indicator */}
        {hypothesis.blocked_by && (
          <div className="mt-3 px-2 py-1.5 bg-fennec-orange-600/10 border border-fennec-orange-600/30 rounded text-xs text-fennec-orange-400">
            ⏸ Waiting for: {hypothesis.waiting_for || hypothesis.blocked_by}
          </div>
        )}
      </div>

      {/* Footer - Click to View Details */}
      <div className="px-4 py-2 bg-fennec-dark-800/30 border-t border-fennec-dark-700 flex items-center justify-between text-xs text-fennec-dark-500 group-hover:text-fennec-purple-400 transition-colors">
        <span>Click to view full details</span>
        <ChevronRight className="h-4 w-4" />
      </div>
    </div>
  );
}

export default HypothesisCard;
