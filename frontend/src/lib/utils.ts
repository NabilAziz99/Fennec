import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Severity, TestStatus, SeverityDistribution } from '../types';

// Tailwind class merger
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format number with K/M suffix
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

// Format currency
export function formatCurrency(amount: number): string {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`;
  }
  return `$${amount}`;
}

// Format date
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

// Format relative time
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return formatDate(dateString);
}

// Get severity color
export function getSeverityColor(severity: Severity): string {
  const colors: Record<Severity, string> = {
    critical: 'text-fennec-red-400',
    high: 'text-fennec-orange-400',
    medium: 'text-fennec-yellow-400',
    low: 'text-fennec-blue-400',
    info: 'text-fennec-dark-300',
  };
  return colors[severity] || colors.info;
}

// Get severity background color
export function getSeverityBgColor(severity: Severity): string {
  const colors: Record<Severity, string> = {
    critical: 'bg-fennec-red-600/20',
    high: 'bg-fennec-orange-600/20',
    medium: 'bg-fennec-yellow-600/20',
    low: 'bg-fennec-blue-600/20',
    info: 'bg-fennec-dark-600/20',
  };
  return colors[severity] || colors.info;
}

// Get severity badge class
export function getSeverityBadgeClass(severity: Severity): string {
  const classes: Record<Severity, string> = {
    critical: 'severity-critical',
    high: 'severity-high',
    medium: 'severity-medium',
    low: 'severity-low',
    info: 'severity-info',
  };
  return classes[severity] || classes.info;
}

// Get status color
export function getStatusColor(status: TestStatus): string {
  const colors: Record<TestStatus, string> = {
    completed: 'text-fennec-green-400',
    running: 'text-fennec-purple-400',
    pending: 'text-fennec-dark-400',
    failed: 'text-fennec-red-400',
    queued: 'text-fennec-dark-400',
    awaiting_review: 'text-amber-400',
  };
  return colors[status] || colors.pending;
}

// Get status badge class
export function getStatusBadgeClass(status: TestStatus): string {
  const classes: Record<TestStatus, string> = {
    completed: 'status-completed',
    running: 'status-running',
    pending: 'status-pending',
    failed: 'status-failed',
    queued: 'status-pending',
    awaiting_review: 'status-running',
  };
  return classes[status] || classes.pending;
}

// Hypothesis status type
export type HypothesisStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'dead_end';

// Get hypothesis status badge class
export function getHypothesisStatusBadgeClass(status: HypothesisStatus): string {
  const classes: Record<HypothesisStatus, string> = {
    pending: 'bg-fennec-dark-600/40 text-fennec-dark-300',
    in_progress: 'bg-fennec-purple-600/20 text-fennec-purple-400',
    completed: 'bg-fennec-green-600/20 text-fennec-green-400',
    blocked: 'bg-fennec-orange-600/20 text-fennec-orange-400',
    dead_end: 'bg-fennec-dark-700 text-fennec-dark-400',
  };
  return classes[status] || classes.pending;
}

// Chart colors
export const CHART_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#6b7280',
  safe: '#22c55e',
};

// Pie chart data formatter
export function formatPieChartData(distribution: SeverityDistribution) {
  const entries: [string, number][] = [
    ['critical', distribution.critical],
    ['high', distribution.high],
    ['medium', distribution.medium],
    ['low', distribution.low],
    ['info', distribution.info],
  ];

  return entries
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
      fill: CHART_COLORS[name as keyof typeof CHART_COLORS] || CHART_COLORS.info,
    }));
}

// Validate URL
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Generate random ID
export function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}
