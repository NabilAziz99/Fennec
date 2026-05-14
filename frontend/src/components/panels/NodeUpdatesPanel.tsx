/**
 * Node Updates Panel
 *
 * Displays current graph node and agent information.
 */

import { Activity } from 'lucide-react';
import { PanelContainer } from './PanelContainer';

interface NodeUpdatesPanelProps {
  currentNode: string | null;
  currentAgent: string | null;
  isConnected: boolean;
}

// Agent color mapping
const AGENT_COLORS: Record<string, string> = {
  orchestrator: 'text-purple-400',
  pentester: 'text-red-400',
  coder: 'text-blue-400',
  researcher: 'text-green-400',
  devops: 'text-orange-400',
  recon: 'text-cyan-400',
  analyst: 'text-yellow-400',
};

export function NodeUpdatesPanel({
  currentNode,
  currentAgent,
  isConnected,
}: NodeUpdatesPanelProps) {
  const agentColor = currentAgent ? AGENT_COLORS[currentAgent] || 'text-fennec-dark-300' : 'text-fennec-dark-500';

  return (
    <PanelContainer
      title="Node Updates"
      icon={<Activity size={16} />}
      maxHeight="200px"
      isEmpty={!currentNode && !currentAgent}
      emptyMessage="Waiting for node updates..."
    >
      <div className="space-y-3">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-fennec-dark-500">Status</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              isConnected
                ? 'bg-green-500/20 text-green-400'
                : 'bg-fennec-dark-700 text-fennec-dark-400'
            }`}
          >
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Current Node */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-fennec-dark-500">Current Node</span>
          <span className="text-sm font-mono text-fennec-dark-300">
            {currentNode || '—'}
          </span>
        </div>

        {/* Current Agent */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-fennec-dark-500">Active Agent</span>
          <div className="flex items-center gap-2">
            {isConnected && currentAgent && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            )}
            <span className={`text-sm font-mono font-medium ${agentColor}`}>
              {currentAgent || '—'}
            </span>
          </div>
        </div>
      </div>
    </PanelContainer>
  );
}

export default NodeUpdatesPanel;
