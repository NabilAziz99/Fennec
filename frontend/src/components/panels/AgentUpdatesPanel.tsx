/**
 * Agent Updates Panel
 *
 * Displays agent results and inter-agent requests.
 */

import { Bot, ArrowRight } from 'lucide-react';
import { PanelContainer } from './PanelContainer';
import type { AgentResultEvent, AgentRequestEvent } from '@/types';

interface AgentUpdatesPanelProps {
  agentResults: AgentResultEvent[];
  agentRequests: AgentRequestEvent[];
}

// Status color mapping
const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-500/20 text-green-400',
  needs_info: 'bg-yellow-500/20 text-yellow-400',
  dead_end: 'bg-red-500/20 text-red-400',
};

// Result color mapping
const RESULT_COLORS: Record<string, string> = {
  vulnerable: 'text-red-400',
  safe: 'text-green-400',
  inconclusive: 'text-yellow-400',
};

export function AgentUpdatesPanel({
  agentResults,
  agentRequests,
}: AgentUpdatesPanelProps) {
  const totalCount = agentResults.length + agentRequests.length;

  // Merge and sort by time (newest first) - we don't have timestamps, so show as-is
  // Results first, then requests
  const hasData = totalCount > 0;

  return (
    <PanelContainer
      title="Agent Updates"
      icon={<Bot size={16} />}
      count={totalCount}
      maxHeight="300px"
      isEmpty={!hasData}
      emptyMessage="No agent updates yet"
    >
      <div className="space-y-2">
        {/* Agent Results */}
        {agentResults.slice().reverse().map((result, index) => (
          <div
            key={`result-${index}`}
            className="p-2 bg-fennec-dark-900 rounded border border-fennec-dark-700"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-fennec-dark-500">Agent Result</span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded ${
                  STATUS_COLORS[result.status] || 'bg-fennec-dark-700 text-fennec-dark-400'
                }`}
              >
                {result.status}
              </span>
            </div>

            {result.hypothesis_id && (
              <div className="text-xs text-fennec-dark-400 mb-1">
                Hypothesis: <span className="font-mono">{result.hypothesis_id.slice(0, 8)}</span>
              </div>
            )}

            {result.result && (
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-fennec-dark-500">Result:</span>
                <span className={`text-sm font-medium ${RESULT_COLORS[result.result] || 'text-fennec-dark-300'}`}>
                  {result.result}
                </span>
              </div>
            )}

            {result.severity && (
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-fennec-dark-500">Severity:</span>
                <span className="text-sm">{result.severity}</span>
              </div>
            )}

            {Array.isArray(result.findings) && result.findings.length > 0 && (
              <div className="mt-1">
                <span className="text-xs text-fennec-dark-500">Findings: </span>
                <span className="text-xs text-fennec-dark-300">{result.findings.length}</span>
              </div>
            )}

            {Array.isArray(result.outputs) && result.outputs.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {result.outputs.map((output, i) => (
                  <span key={i} className="text-xs px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded">
                    {output}
                  </span>
                ))}
              </div>
            )}

            {Array.isArray(result.needs) && result.needs.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {result.needs.map((need, i) => (
                  <span key={i} className="text-xs px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded">
                    needs: {need}
                  </span>
                ))}
              </div>
            )}

            {result.error && (
              <div className="mt-1 text-xs text-red-400">
                Error: {result.error}
              </div>
            )}
          </div>
        ))}

        {/* Agent Requests */}
        {agentRequests.slice().reverse().map((request, index) => (
          <div
            key={`request-${index}`}
            className="p-2 bg-fennec-dark-900 rounded border border-fennec-dark-700"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-fennec-dark-500">Agent Request</span>
              <div className="flex items-center gap-1 text-xs">
                <span className="text-purple-400">{request.from_agent}</span>
                <ArrowRight size={12} className="text-fennec-dark-500" />
                <span className="text-blue-400">{request.to_agent}</span>
              </div>
            </div>

            <div className="text-sm text-fennec-dark-300 mb-1">
              {request.task}
            </div>

            {request.context && (
              <div className="text-xs text-fennec-dark-500 truncate">
                Context: {typeof request.context === 'string' ? request.context : JSON.stringify(request.context)}
              </div>
            )}
          </div>
        ))}
      </div>
    </PanelContainer>
  );
}

export default AgentUpdatesPanel;
