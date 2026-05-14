/**
 * Current Hypothesis Alert
 *
 * Prominent display of the currently active hypothesis being tested
 */

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { FlaskConical, Target, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HypothesisResult } from '@/types';

interface CurrentHypothesisAlertProps {
  hypothesis: HypothesisResult;
  isStreaming: boolean;
  onClick?: () => void;
}

export function CurrentHypothesisAlert({
  hypothesis,
  isStreaming,
  onClick,
}: CurrentHypothesisAlertProps) {
  const severityColors: Record<string, string> = {
    critical: 'bg-red-600/20 text-red-400 border-red-600/30',
    high: 'bg-orange-600/20 text-orange-400 border-orange-600/30',
    medium: 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30',
    low: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
    info: 'bg-fennec-dark-600 text-fennec-dark-300 border-fennec-dark-600/30',
  };

  // Calculate time since started
  const getElapsedTime = () => {
    if (!hypothesis.started_at) return null;
    const start = new Date(hypothesis.started_at);
    const now = new Date();
    const diffMs = now.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);

    if (diffMins > 0) {
      return `${diffMins}m ${diffSecs}s`;
    }
    return `${diffSecs}s`;
  };

  const elapsedTime = getElapsedTime();

  return (
    <Alert
      variant="info"
      className={cn(
        "relative overflow-hidden border-2 cursor-pointer transition-all hover:border-fennec-purple-400",
        isStreaming && "animate-pulse-border"
      )}
      onClick={onClick}
    >
      {/* Animated background gradient for active state */}
      {isStreaming && (
        <div className="absolute inset-0 bg-gradient-to-r from-fennec-purple-500/5 via-fennec-purple-400/10 to-fennec-purple-500/5 animate-gradient-x pointer-events-none" />
      )}

      <FlaskConical className="h-5 w-5" />
      <div className="relative">
        <div className="flex items-center gap-2 flex-wrap mb-2">
          <AlertTitle className="text-base flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
            </span>
            Currently Testing
          </AlertTitle>

          <Badge variant="outline" className="ml-auto">
            <Target className="h-3 w-3 mr-1" />
            {hypothesis.required_agent}
          </Badge>

          {hypothesis.severity && (
            <Badge className={cn("border", severityColors[hypothesis.severity])}>
              {hypothesis.severity.toUpperCase()}
            </Badge>
          )}

          {elapsedTime && (
            <Badge variant="outline" className="text-fennec-dark-400">
              <Clock className="h-3 w-3 mr-1" />
              {elapsedTime}
            </Badge>
          )}
        </div>

        <AlertDescription>
          <div className="space-y-2">
            <div className="font-semibold text-white">
              {hypothesis.title}
            </div>
            <div className="text-sm text-fennec-dark-300 line-clamp-2">
              {hypothesis.description}
            </div>

            {/* Skills */}
            {Array.isArray(hypothesis.skills) && hypothesis.skills.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {hypothesis.skills.slice(0, 4).map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 bg-fennec-dark-700/50 text-fennec-dark-400 rounded text-xs"
                  >
                    {skill}
                  </span>
                ))}
                {hypothesis.skills.length > 4 && (
                  <span className="px-2 py-0.5 bg-fennec-dark-700/50 text-fennec-dark-500 rounded text-xs">
                    +{hypothesis.skills.length - 4} more
                  </span>
                )}
              </div>
            )}

            {/* Hypothesis ID */}
            <div className="text-xs text-fennec-dark-600 font-mono">
              ID: {hypothesis.id}
            </div>
          </div>
        </AlertDescription>
      </div>
    </Alert>
  );
}

export default CurrentHypothesisAlert;
