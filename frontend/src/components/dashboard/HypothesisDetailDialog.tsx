/**
 * Hypothesis Detail Dialog
 *
 * Full-screen dialog showing comprehensive hypothesis information
 */

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import type { HypothesisResult, Task, StepRecord } from '@/types';
import {
  FlaskConical,
  Target,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Database,
  XCircle,
  Loader2,
} from 'lucide-react';

interface HypothesisDetailDialogProps {
  hypothesis: HypothesisResult | null;
  tasks: Task[];
  steps: StepRecord[];
  isOpen: boolean;
  onClose: () => void;
  isActive: boolean;
}

export function HypothesisDetailDialog({
                                         hypothesis,
                                         tasks,
                                         steps,
                                         isOpen,
                                         onClose,
                                         isActive,
                                       }: HypothesisDetailDialogProps) {
  if (!hypothesis) return null;

  const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    pending: {
      color: 'text-fennec-dark-400 bg-fennec-dark-700/30 border-fennec-dark-600',
      icon: <Loader2 className="h-3 w-3 mr-1" />,
      label: 'PENDING',
    },
    in_progress: {
      color: 'text-fennec-purple-400 bg-fennec-purple-600/20 border-fennec-purple-500/30',
      icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" />,
      label: 'IN PROGRESS',
    },
    completed: {
      color: 'text-fennec-green-400 bg-fennec-green-600/20 border-fennec-green-500/30',
      icon: <CheckCircle2 className="h-3 w-3 mr-1" />,
      label: 'COMPLETED',
    },
    blocked: {
      color: 'text-fennec-orange-400 bg-fennec-orange-600/20 border-fennec-orange-500/30',
      icon: <AlertTriangle className="h-3 w-3 mr-1" />,
      label: 'BLOCKED',
    },
    dead_end: {
      color: 'text-fennec-dark-500 bg-fennec-dark-800 border-fennec-dark-600',
      icon: <XCircle className="h-3 w-3 mr-1" />,
      label: 'DEAD END',
    },
  };

  const severityColors: Record<string, string> = {
    critical: 'bg-red-600/20 text-red-400 border-red-600/30',
    high: 'bg-orange-600/20 text-orange-400 border-orange-600/30',
    medium: 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30',
    low: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
    info: 'bg-fennec-dark-600 text-fennec-dark-300 border-fennec-dark-600/30',
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Not started';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const currentStatus = statusConfig[hypothesis.status];

  return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto bg-fennec-light-900 border-fennec-light-700">
          <DialogHeader>
            <div className="flex items-start justify-between gap-4 pb-4">
              <div className="flex-1 space-y-3">
                <DialogTitle className="text-2xl text-white flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-fennec-purple-600/20 border border-fennec-purple-500/30">
                    <FlaskConical className="h-5 w-5 text-fennec-purple-400" />
                  </div>
                  {hypothesis.title}
                </DialogTitle>
                <DialogDescription className="text-fennec-dark-300 text-base leading-relaxed">
                  {hypothesis.description}
                </DialogDescription>
              </div>
              <div className="flex flex-col gap-2 items-end">
                <Badge className={cn("border px-3 py-1", currentStatus.color)}>
                  {currentStatus.icon}
                  {currentStatus.label}
                </Badge>
                {hypothesis.severity && (
                    <Badge className={cn("border px-3 py-1", severityColors[hypothesis.severity])}>
                      {hypothesis.severity.toUpperCase()}
                    </Badge>
                )}
                {isActive && (
                    <Badge variant="outline" className="border-blue-500/40 text-blue-400 px-3 py-1">
                  <span className="relative flex h-2 w-2 mr-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                  </span>
                      ACTIVE
                    </Badge>
                )}
              </div>
            </div>
          </DialogHeader>

          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList className="grid w-full grid-cols-5 bg-fennec-dark-800/50">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="tasks">
                Tasks {tasks.length > 0 && <span className="ml-1 text-xs">({tasks.length})</span>}
              </TabsTrigger>
              <TabsTrigger value="actions">
                Actions {steps.length > 0 && <span className="ml-1 text-xs">({steps.length})</span>}
              </TabsTrigger>
              <TabsTrigger value="findings">
                Findings {hypothesis.findings && <span className="ml-1 text-xs">({hypothesis.findings.length})</span>}
              </TabsTrigger>
              <TabsTrigger value="data">Data I/O</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6 mt-6">
              {/* Blocking Info - Show at top if blocked */}
              {hypothesis.blocked_by && (
                  <div className="p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                    <div className="flex items-center gap-2 text-orange-400 font-medium mb-2">
                      <AlertTriangle className="h-5 w-5" />
                      This hypothesis is blocked
                    </div>
                    <div className="text-fennec-dark-300 text-sm">
                      Waiting for: <span className="font-medium text-white">{hypothesis.waiting_for || hypothesis.blocked_by}</span>
                    </div>
                  </div>
              )}

              {/* Key Metadata Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-fennec-dark-800/30 border border-fennec-dark-700">
                  <div className="text-xs text-fennec-dark-500 mb-1">Priority Score</div>
                  <div className="text-2xl font-bold text-white">{Number(hypothesis.priority).toFixed(2)}</div>
                </div>
                <div className="p-4 rounded-lg bg-fennec-dark-800/30 border border-fennec-dark-700">
                  <div className="text-xs text-fennec-dark-500 mb-1">Required Agent</div>
                  <Badge variant="outline" className="text-fennec-purple-400 border-fennec-purple-500/30 mt-1">
                    <Target className="h-3 w-3 mr-1" />
                    {hypothesis.required_agent}
                  </Badge>
                </div>
                <div className="p-4 rounded-lg bg-fennec-dark-800/30 border border-fennec-dark-700">
                  <div className="text-xs text-fennec-dark-500 mb-1">Result</div>
                  <div className="text-sm font-medium text-white mt-1">{hypothesis.result || 'Pending evaluation'}</div>
                </div>
                <div className="p-4 rounded-lg bg-fennec-dark-800/30 border border-fennec-dark-700">
                  <div className="text-xs text-fennec-dark-500 mb-1">Hypothesis ID</div>
                  <div className="text-xs font-mono text-fennec-dark-300 mt-1 truncate">{hypothesis.id}</div>
                </div>
              </div>

              <Separator className="bg-fennec-dark-700" />

              {/* Timeline */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-base font-semibold text-white">
                  <Calendar className="h-5 w-5 text-fennec-purple-400" />
                  Timeline
                </div>
                <div className="space-y-3 pl-7">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-fennec-dark-400">Created</span>
                    <span className="text-sm text-white font-medium">{formatDate(hypothesis.created_at)}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-fennec-dark-400">Started</span>
                    <span className="text-sm text-white font-medium">{formatDate(hypothesis.started_at)}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-fennec-dark-400">Completed</span>
                    <span className="text-sm text-white font-medium">{formatDate(hypothesis.completed_at)}</span>
                  </div>
                </div>
              </div>

              {/* Skills */}
              {Array.isArray(hypothesis.skills) && hypothesis.skills.length > 0 && (
                  <><Separator className="bg-fennec-dark-700" />
                    <div className="space-y-3">
                      <div className="text-base font-semibold text-white">Required Skills</div>
                      <div className="flex flex-wrap gap-2">
                        {hypothesis.skills.map((skill, idx) => (
                            <Badge
                                key={idx}
                                variant="outline"
                                className="bg-fennec-dark-700/50 text-fennec-dark-300 border-fennec-dark-600 px-3 py-1"
                            >
                              {skill}
                            </Badge>
                        ))}
                      </div>
                    </div>
                  </>
              )}
            </TabsContent>

            {/* Tasks Tab */}
            <TabsContent value="tasks" className="space-y-3 mt-6">
              {tasks.length === 0 ? (
                  <div className="text-center py-12 text-fennec-dark-500">
                    <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No tasks assigned yet</p>
                  </div>
              ) : (
                  <div className="space-y-3">
                    {tasks.map((task) => (
                        <div
                            key={task.id}
                            className="p-4 rounded-lg bg-fennec-dark-800/30 border border-fennec-dark-700 hover:bg-fennec-dark-800/50 transition-colors"
                        >
                          <div className="flex items-start gap-4">
                            <div className="mt-1">
                              {task.status === 'completed' && (
                                  <CheckCircle2 className="h-5 w-5 text-fennec-green-400" />
                              )}
                              {task.status === 'in_progress' && (
                                  <Loader2 className="h-5 w-5 text-fennec-purple-400 animate-spin" />
                              )}
                              {task.status === 'pending' && (
                                  <div className="h-5 w-5 rounded-full border-2 border-fennec-dark-600" />
                              )}
                            </div>
                            <div className="flex-1 space-y-2">
                              <div className={cn(
                                  "font-medium text-base",
                                  task.status === 'completed' && 'text-fennec-dark-400 line-through',
                                  task.status === 'in_progress' && 'text-white',
                                  task.status === 'pending' && 'text-fennec-dark-300'
                              )}>
                                {task.status === 'in_progress' && task.activeForm
                                    ? task.activeForm
                                    : task.subject}
                              </div>
                              {task.description && (
                                  <div className="text-sm text-fennec-dark-400 leading-relaxed">
                                    {task.description}
                                  </div>
                              )}
                              {task.owner && (
                                  <div className="flex items-center gap-2 text-xs text-fennec-dark-500">
                                    <Target className="h-3 w-3" />
                                    {task.owner}
                                  </div>
                              )}
                            </div>
                          </div>
                        </div>
                    ))}
                  </div>
              )}
            </TabsContent>

            {/* Actions Tab */}
            <TabsContent value="actions" className="space-y-3 mt-6">
              {steps.length === 0 ? (
                  <div className="text-center py-12 text-fennec-dark-500">
                    <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No actions recorded yet</p>
                  </div>
              ) : (
                  <div className="space-y-3">
                    {steps.map((step, idx) => (
                        <div
                            key={idx}
                            className="p-4 rounded-lg bg-fennec-dark-800/30 border border-fennec-dark-700"
                        >
                          <div className="flex items-start gap-4">
                            <div className={cn(
                                'w-3 h-3 rounded-full mt-1.5 flex-shrink-0',
                                step.success ? 'bg-fennec-green-400' : 'bg-fennec-red-400'
                            )} />
                            <div className="flex-1 space-y-2">
                              <div className="font-medium text-white text-base">{step.action}</div>
                              <div className="text-sm text-fennec-dark-400">
                                Agent: <span className="text-fennec-purple-400 font-medium">{step.agent}</span>
                              </div>
                              {step.input_summary && (
                                  <div className="text-sm text-fennec-dark-400">
                                    <span className="text-fennec-dark-500">Input:</span> {step.input_summary}
                                  </div>
                              )}
                              {step.output_summary && (
                                  <div className="text-sm text-fennec-dark-400">
                                    <span className="text-fennec-dark-500">Output:</span> {step.output_summary}
                                  </div>
                              )}
                              {step.timestamp && (
                                  <div className="text-xs text-fennec-dark-600">
                                    {new Date(step.timestamp).toLocaleString()}
                                  </div>
                              )}
                            </div>
                          </div>
                        </div>
                    ))}
                  </div>
              )}
            </TabsContent>

            {/* Findings Tab */}
            <TabsContent value="findings" className="space-y-3 mt-6">
              {!Array.isArray(hypothesis.findings) || hypothesis.findings.length === 0 ? (
                  <div className="text-center py-12 text-fennec-dark-500">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No findings discovered</p>
                  </div>
              ) : (
                  <div className="space-y-3">
                    {hypothesis.findings.map((finding, idx) => (
                        <div
                            key={idx}
                            className="flex items-start gap-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/15 transition-colors"
                        >
                          <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-fennec-dark-200 leading-relaxed">{finding}</span>
                        </div>
                    ))}
                  </div>
              )}
            </TabsContent>

            {/* Data I/O Tab */}
            <TabsContent value="data" className="space-y-6 mt-6">
              {Array.isArray(hypothesis.expected_outputs) && hypothesis.expected_outputs.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-base font-semibold text-orange-400">
                      <Database className="h-5 w-5" />
                      Expected Outputs
                    </div>
                    <ul className="space-y-2 pl-7">
                      {hypothesis.expected_outputs.map((output, idx) => (
                          <li key={idx} className="text-sm text-fennec-dark-300 leading-relaxed">
                            • {output}
                          </li>
                      ))}
                    </ul>
                  </div>
              )}

              {Array.isArray(hypothesis.actual_outputs) && hypothesis.actual_outputs.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-base font-semibold text-green-400">
                      <CheckCircle2 className="h-5 w-5" />
                      Produced Outputs
                    </div>
                    <ul className="space-y-2 pl-7">
                      {hypothesis.actual_outputs.map((output, idx) => (
                          <li key={idx} className="text-sm text-fennec-dark-300 leading-relaxed">
                            • {output}
                          </li>
                      ))}
                    </ul>
                  </div>
              )}

              {(!Array.isArray(hypothesis.expected_outputs) || hypothesis.expected_outputs.length === 0) &&
                  (!Array.isArray(hypothesis.actual_outputs) || hypothesis.actual_outputs.length === 0) && (
                      <div className="text-center py-12 text-fennec-dark-500">
                        <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p>No data I/O information available</p>
                      </div>
                  )}
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
  );
}

export default HypothesisDetailDialog;
