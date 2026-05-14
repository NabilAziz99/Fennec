/**
 * Event Statistics Panel
 *
 * Displays event counts grouped by type with visual badges.
 */

import type { EventStats } from '@/types/eventLog';

interface EventStatsPanelProps {
  stats: EventStats;
  totalReceived: number;
  isCapturing: boolean;
}

// Color coding for different event types
const EVENT_COLORS: Record<string, string> = {
  // Session lifecycle (green)
  session_start: 'bg-green-500/20 text-green-400 border-green-500/30',
  complete: 'bg-green-500/20 text-green-400 border-green-500/30',

  // Errors (red)
  error: 'bg-red-500/20 text-red-400 border-red-500/30',

  // Hypothesis/Testing (purple)
  hypothesis_tree: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  current_hypothesis: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  task_update: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  task_update_batch: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  step_update: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  step_update_batch: 'bg-purple-500/20 text-purple-400 border-purple-500/30',

  // Findings (orange)
  findings_update: 'bg-orange-500/20 text-orange-400 border-orange-500/30',

  // Recon (blue)
  recon_update: 'bg-blue-500/20 text-blue-400 border-blue-500/30',

  // Agent activity (cyan)
  node_update: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  message: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  tool_call: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  tool_execution: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  agent_result: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  agent_request: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',

  // Results (yellow)
  result: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  subtasks: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
};

const DEFAULT_COLOR = 'bg-gray-500/20 text-gray-400 border-gray-500/30';

export function EventStatsPanel({ stats, totalReceived, isCapturing }: EventStatsPanelProps) {
  const sortedEvents = Object.entries(stats).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-fennec-dark-800 border border-fennec-dark-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-fennec-dark-300">Event Statistics</h3>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-fennec-dark-400">
            Total: <span className="text-white font-mono">{totalReceived}</span>
          </span>
          <span
            className={`px-2 py-0.5 rounded-full ${
              isCapturing
                ? 'bg-green-500/20 text-green-400'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}
          >
            {isCapturing ? 'Capturing' : 'Paused'}
          </span>
        </div>
      </div>

      {sortedEvents.length === 0 ? (
        <p className="text-fennec-dark-500 text-sm">No events captured yet</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {sortedEvents.map(([eventType, count]) => (
            <span
              key={eventType}
              className={`inline-flex items-center gap-1.5 px-2 py-1 rounded border text-xs font-mono ${
                EVENT_COLORS[eventType] || DEFAULT_COLOR
              }`}
            >
              <span className="truncate max-w-[120px]">{eventType}</span>
              <span className="font-bold">{count}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default EventStatsPanel;
