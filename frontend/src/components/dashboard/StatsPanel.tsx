import { cn } from '@/lib/utils';
import type { HypothesesState } from '@/hooks/usePentestStream';

interface StatsPanelProps {
  statistics: HypothesesState['statistics'];
  outputsRegistry: Record<string, string>;
  pendingOutputs: Record<string, string>;
  blockedCount: number;
  isStreaming?: boolean;
}

export function StatsPanel({
  statistics,
  outputsRegistry,
  pendingOutputs,
  blockedCount,
  isStreaming = false,
}: StatsPanelProps) {
  if (!statistics) return null;

  const stats = [
    { label: 'Total', value: statistics.total, color: 'text-white', bg: 'bg-fennec-dark-700' },
    { label: 'Pending', value: statistics.pending, color: 'text-fennec-dark-400', bg: 'bg-fennec-dark-800' },
    { label: 'In Progress', value: statistics.in_progress, color: 'text-fennec-purple-400', bg: 'bg-fennec-purple-600/10' },
    { label: 'Completed', value: statistics.completed, color: 'text-fennec-green-400', bg: 'bg-fennec-green-600/10' },
    { label: 'Blocked', value: statistics.blocked, color: 'text-fennec-orange-400', bg: 'bg-fennec-orange-600/10' },
    { label: 'Dead End', value: statistics.dead_end, color: 'text-fennec-dark-500', bg: 'bg-fennec-dark-800' },
    { label: 'Vulns', value: statistics.vulnerabilities, color: 'text-fennec-red-400', bg: 'bg-fennec-red-600/10' },
    { label: 'Queue', value: statistics.stack_size, color: 'text-fennec-dark-400', bg: 'bg-fennec-dark-800' },
  ];

  return (
    <div className="bg-fennec-dark-900/80 border border-fennec-dark-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Hypothesis Progress</h3>
        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-fennec-green-400">
            <span className="w-2 h-2 bg-fennec-green-400 rounded-full animate-pulse" />
            Live
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mb-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className={cn('text-center p-2 rounded-lg', stat.bg)}
          >
            <p className={cn('text-2xl font-bold', stat.color)}>{stat.value}</p>
            <p className="text-xs text-fennec-dark-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Outputs Section */}
      {(Object.keys(outputsRegistry).length > 0 || Object.keys(pendingOutputs).length > 0) && (
        <div className="border-t border-fennec-dark-700 pt-4 mt-4">
          <div className="flex flex-wrap gap-6">
            {Object.keys(outputsRegistry).length > 0 && (
              <div className="flex-1 min-w-[200px]">
                <p className="text-xs text-fennec-green-400 mb-2 font-medium">
                  Available Data ({Object.keys(outputsRegistry).length})
                </p>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(outputsRegistry).map(([key, value]) => (
                    <span
                      key={key}
                      className="px-2 py-1 bg-fennec-green-600/20 text-fennec-green-300 rounded text-xs"
                      title={value}
                    >
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {Object.keys(pendingOutputs).length > 0 && (
              <div className="flex-1 min-w-[200px]">
                <p className="text-xs text-fennec-orange-400 mb-2 font-medium">
                  Pending ({Object.keys(pendingOutputs).length})
                </p>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(pendingOutputs).map(([key, value]) => (
                    <span
                      key={key}
                      className="px-2 py-1 bg-fennec-orange-600/20 text-fennec-orange-300 rounded text-xs animate-pulse"
                      title={value}
                    >
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Blocked Count Warning */}
      {blockedCount > 0 && (
        <div className="mt-4 p-2 bg-fennec-orange-600/10 border border-fennec-orange-600/30 rounded-lg">
          <div className="flex items-center gap-2 text-xs text-fennec-orange-400">
            <span>⚠</span>
            <span>{blockedCount} hypothesis{blockedCount > 1 ? 'es' : ''} blocked waiting for data</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default StatsPanel;
