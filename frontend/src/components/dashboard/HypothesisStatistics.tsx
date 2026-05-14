/**
 * Hypothesis Statistics Dashboard
 *
 * Displays hypothesis statistics in organized card groups with progress bar
 */

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  Ban,
  XCircle,
  AlertTriangle,
  CircleFadingPlusIcon,
  Database
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface HypothesisStatisticsProps {
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
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  colorClass: string;
  iconColorClass: string;
}

function StatCard({ icon, label, value, colorClass, iconColorClass }: StatCardProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-fennec-dark-800/50 border border-fennec-dark-700 hover:border-fennec-dark-600 transition-colors">
      <div className={cn("p-2 rounded-md", iconColorClass)}>
        {icon}
      </div>
      <div className="flex-1">
        <div className={cn("text-2xl font-bold", colorClass)}>{value}</div>
        <div className="text-xs text-fennec-dark-500">{label}</div>
      </div>
    </div>
  );
}

export function HypothesisStatistics({ statistics }: HypothesisStatisticsProps) {
  if (!statistics) {
    return null;
  }

  // Calculate completion percentage
  const completionPercentage = statistics.total > 0
    ? Math.round((statistics.completed / statistics.total) * 100)
    : 0;

  return (
    <div className="space-y-4">
      {/* Progress Overview */}
      <Card className="bg-fennec-dark-900/50 border-fennec-dark-700">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-fennec-purple-400" />
              <span className="text-sm font-medium text-white">Overall Progress</span>
            </div>
            <span className="text-sm font-bold text-fennec-purple-400">
              {completionPercentage}%
            </span>
          </div>
          <Progress value={completionPercentage} className="h-2" />
          <div className="mt-2 text-xs text-fennec-dark-500">
            {statistics.completed} of {statistics.total} hypotheses completed
          </div>
        </CardContent>
      </Card>

      {/* Statistics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Status Stats */}
        <StatCard
          icon={<Clock className="h-4 w-4" />}
          label="Pending"
          value={statistics.pending}
          colorClass="text-yellow-400"
          iconColorClass="bg-yellow-500/20 text-yellow-400"
        />

        <StatCard
          icon={<Clock className="h-4 w-4 animate-pulse" />}
          label="In Progress"
          value={statistics.in_progress}
          colorClass="text-blue-400"
          iconColorClass="bg-blue-500/20 text-blue-400"
        />

        <StatCard
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="Completed"
          value={statistics.completed}
          colorClass="text-green-400"
          iconColorClass="bg-green-500/20 text-green-400"
        />

        <StatCard
          icon={<AlertTriangle className="h-4 w-4" />}
          label="Vulnerable"
          value={statistics.vulnerabilities}
          colorClass="text-red-400"
          iconColorClass="bg-red-500/20 text-red-400"
        />

        {/* Issue Stats */}
        <StatCard
          icon={<Ban className="h-4 w-4" />}
          label="Blocked"
          value={statistics.blocked}
          colorClass="text-orange-400"
          iconColorClass="bg-orange-500/20 text-orange-400"
        />

        <StatCard
          icon={<XCircle className="h-4 w-4" />}
          label="Dead End"
          value={statistics.dead_end}
          colorClass="text-gray-400"
          iconColorClass="bg-gray-500/20 text-gray-400"
        />

        {/* Queue Stats */}
        <StatCard
          icon={<CircleFadingPlusIcon className="h-4 w-4" />}
          label="Queue"
          value={statistics.stack_size}
          colorClass="text-purple-400"
          iconColorClass="bg-purple-500/20 text-purple-400"
        />

        <StatCard
          icon={<Database className="h-4 w-4" />}
          label="Outputs"
          value={statistics.outputs_available}
          colorClass="text-cyan-400"
          iconColorClass="bg-cyan-500/20 text-cyan-400"
        />
      </div>
    </div>
  );
}

export default HypothesisStatistics;
