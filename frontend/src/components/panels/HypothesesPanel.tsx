/**
 * Hypotheses Panel (Redesigned)
 *
 * Enhanced layout with filtering, sorting, and better organization
 */

import { useState, useMemo } from 'react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/Collapsible';
import { ChevronDown} from 'lucide-react';
import { FlaskConical, AlertTriangle } from 'lucide-react';
import { PanelContainer } from './PanelContainer';
import { HypothesisCard } from '@/components/dashboard/HypothesisCard';
import { HypothesisStatistics } from '@/components/dashboard/HypothesisStatistics';
import { CurrentHypothesisAlert } from '@/components/dashboard/CurrentHypothesisAlert';
import { HypothesisFilters, FilterView, SortOption } from '@/components/dashboard/HypothesisFilters';
import { HypothesisDetailDialog } from '@/components/dashboard/HypothesisDetailDialog';
import type { HypothesisResult, Task, StepRecord, BlockedHypothesis } from '@/types';
import {Badge} from "@/components/ui/badge.tsx";

interface HypothesesPanelProps {
  hypotheses: Record<string, HypothesisResult>;
  currentHypothesisId: string | null;
  statistics: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    blocked: number;
    dead_end: number;
    vulnerabilities: number;
    stack_size: number;
    blocked_count: number;
    outputs_available: number;
  } | null;
  blockedList: BlockedHypothesis[];
  outputsRegistry: Record<string, string>;
  pendingOutputs: Record<string, string>;
  tasksByHypothesis: Record<string, Task[]>;
  stepsByHypothesis: Record<string, StepRecord[]>;
  isStreaming: boolean;
}

export function HypothesesPanel({
  hypotheses,
  currentHypothesisId,
  statistics,
  blockedList,
  outputsRegistry,
  pendingOutputs,
  tasksByHypothesis,
  stepsByHypothesis,
  isStreaming,
}: HypothesesPanelProps) {
  // UI State
  const [activeView, setActiveView] = useState<FilterView>('all');
  const [sortBy, setSortBy] = useState<SortOption>('priority');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHypothesis, setSelectedHypothesis] = useState<string | null>(null);

  const hypothesesArray = Object.values(hypotheses);
  const hasHypotheses = hypothesesArray.length > 0;
  const currentHypothesis = currentHypothesisId ? hypotheses[currentHypothesisId] : null;

  // Calculate filter counts
  const filterCounts = useMemo(() => {
    return {
      all: hypothesesArray.length,
      active: hypothesesArray.filter(h => h.status === 'in_progress' || h.status === 'pending').length,
      completed: hypothesesArray.filter(h => h.status === 'completed').length,
      blocked: hypothesesArray.filter(h => h.status === 'blocked').length,
      vulnerable: hypothesesArray.filter(h => h.result === 'vulnerable').length,
    };
  }, [hypothesesArray]);

  // Filter hypotheses based on active view
  const filteredHypotheses = useMemo(() => {
    let filtered = hypothesesArray;

    // Apply view filter
    switch (activeView) {
      case 'active':
        filtered = filtered.filter(h => h.status === 'in_progress' || h.status === 'pending');
        break;
      case 'completed':
        filtered = filtered.filter(h => h.status === 'completed');
        break;
      case 'blocked':
        filtered = filtered.filter(h => h.status === 'blocked');
        break;
      case 'vulnerable':
        filtered = filtered.filter(h => h.result === 'vulnerable');
        break;
      // 'all' - no filter
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        h =>
          h.title.toLowerCase().includes(query) ||
          (h.description?.toLowerCase().includes(query) ?? false) ||
          String(h.id).toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [hypothesesArray, activeView, searchQuery]);

  // Sort hypotheses
  const sortedHypotheses = useMemo(() => {
    const sorted = [...filteredHypotheses];

    switch (sortBy) {
      case 'priority':
        return sorted.sort((a, b) => Number(b.priority) - Number(a.priority));
      case 'status':
        const statusOrder = ['in_progress', 'pending', 'blocked', 'completed', 'dead_end'];
        return sorted.sort((a, b) => statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status));
      case 'recent':
        return sorted.sort((a, b) => {
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          return dateB - dateA;
        });
      case 'severity':
        const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4, null: 5 };
        return sorted.sort((a, b) => {
          const severityA = severityOrder[a.severity || 'null'] ?? 5;
          const severityB = severityOrder[b.severity || 'null'] ?? 5;
          return severityA - severityB;
        });
      default:
        return sorted;
    }
  }, [filteredHypotheses, sortBy]);

  // Handle hypothesis selection for detail dialog
  const handleCardClick = (hypothesisId: string) => {
    setSelectedHypothesis(hypothesisId);
  };

  const selectedHypothesisData = selectedHypothesis ? hypotheses[selectedHypothesis] : null;

  return (
    <>
      <PanelContainer
        title="Hypotheses"
        icon={<FlaskConical size={16} />}
        count={hypothesesArray.length}
        maxHeight="none"
        isEmpty={!hasHypotheses}
        emptyMessage="No hypotheses generated yet"
        className="flex-1"
      >
        <div className="space-y-4">
          {/* Statistics */}
          {statistics && <HypothesisStatistics statistics={statistics} />}

          {/* Current Hypothesis Alert */}
          {currentHypothesis && (
            <CurrentHypothesisAlert
              hypothesis={currentHypothesis}
              isStreaming={isStreaming && currentHypothesis.id === currentHypothesisId}
              onClick={() => handleCardClick(currentHypothesis.id)}
            />
          )}

          {/* Blocked Hypotheses Warning */}
          {blockedList.length > 0 && (
            <div className="p-3 bg-orange-500/10 border border-orange-500/30 rounded">
              <div className="flex items-center gap-2 text-sm text-orange-400">
                <AlertTriangle size={16} />
                <span className="font-medium">{blockedList.length} blocked hypothesis</span>
              </div>
              <div className="mt-2 space-y-1">
                {blockedList.slice(0, 3).map((blocked) => (
                  <div key={blocked.hypothesis_id} className="text-xs text-fennec-dark-400">
                    <span className="font-mono">{blocked.hypothesis_id.slice(0, 8)}</span>
                    {blocked.waiting_for && (
                      <span className="text-fennec-dark-500"> → waiting for: {blocked.waiting_for}</span>
                    )}
                  </div>
                ))}
                {blockedList.length > 3 && (
                  <div className="text-xs text-fennec-dark-500">
                    ...and {blockedList.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Outputs Registry */}
          {Object.keys(outputsRegistry).length > 0 && (
            <div>
              <div className="text-xs text-fennec-dark-500 mb-2">Available Outputs:</div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(outputsRegistry).map(([key, value]) => (
                  <span
                    key={key}
                    className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded"
                    title={value}
                  >
                    {key}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Pending Outputs - Collapsible */}
          {Object.keys(pendingOutputs).length > 0 && (
              <Collapsible defaultOpen={Object.keys(pendingOutputs).length <= 5}>
                <div className="rounded-lg border border-fennec-dark-700 bg-fennec-dark-800/30">
                  <CollapsibleTrigger className="flex w-full items-center justify-between p-3 hover:bg-fennec-dark-800/50 transition-colors">
                    <div className="flex items-center gap-2">
                      <div className="text-xs font-medium text-fennec-dark-300">
                        Pending Outputs
                      </div>
                      <Badge variant="outline" className="bg-orange-500/20 text-orange-400 border-orange-500/30">
                        {Object.keys(pendingOutputs).length}
                      </Badge>
                    </div>
                    <ChevronDown className="h-4 w-4 text-fennec-dark-500 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div className="px-3 pb-3 pt-1">
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(pendingOutputs).map(([key, value]) => (
                            <span
                                key={key}
                                className="text-xs px-2 py-1 bg-orange-500/20 text-orange-400 rounded border border-orange-500/30 hover:bg-orange-500/30 transition-colors cursor-default"
                                title={value}
                            >
                {key}
              </span>
                        ))}
                      </div>
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
          )}

          {/* Filters */}
          {hasHypotheses && (
            <HypothesisFilters
              activeView={activeView}
              onViewChange={setActiveView}
              sortBy={sortBy}
              onSortChange={setSortBy}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              counts={filterCounts}
            />
          )}

          {/* Hypotheses Grid */}
          {sortedHypotheses.length === 0 && hasHypotheses ? (
            <div className="text-center py-8 text-fennec-dark-500">
              No hypotheses match your filters
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {sortedHypotheses.map((hypothesis) => (
                <HypothesisCard
                  key={hypothesis.id}
                  hypothesis={hypothesis}
                  tasks={tasksByHypothesis[hypothesis.id] || []}
                  steps={stepsByHypothesis[hypothesis.id] || []}
                  isActive={hypothesis.id === currentHypothesisId}
                  isStreaming={isStreaming && hypothesis.id === currentHypothesisId}
                  onClick={() => handleCardClick(hypothesis.id)}
                />
              ))}
            </div>
          )}
        </div>
      </PanelContainer>

      {/* Detail Dialog */}
      <HypothesisDetailDialog
        hypothesis={selectedHypothesisData}
        tasks={selectedHypothesisData ? (tasksByHypothesis[selectedHypothesisData.id] || []) : []}
        steps={selectedHypothesisData ? (stepsByHypothesis[selectedHypothesisData.id] || []) : []}
        isOpen={selectedHypothesis !== null}
        onClose={() => setSelectedHypothesis(null)}
        isActive={selectedHypothesis === currentHypothesisId}
      />
    </>
  );
}

export default HypothesesPanel;
