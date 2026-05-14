/**
 * Reusable Panel Container
 *
 * A consistent wrapper for streaming data panels with title and scrollable content.
 */

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface PanelContainerProps {
  /** Panel title displayed in header */
  title: string;
  /** Optional icon to display before title */
  icon?: ReactNode;
  /** Panel content */
  children: ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Maximum height for scrollable content (e.g., "300px") */
  maxHeight?: string;
  /** Item count badge (optional) */
  count?: number;
  /** Whether the panel is in a loading state */
  loading?: boolean;
  /** Whether content is empty */
  isEmpty?: boolean;
  /** Message to show when empty */
  emptyMessage?: string;
}

export function PanelContainer({
  title,
  icon,
  children,
  className,
  maxHeight = '300px',
  count,
  loading,
  isEmpty,
  emptyMessage = 'No data available',
}: PanelContainerProps) {
  return (
    <div
      className={cn(
        'bg-fennec-dark-800 border border-fennec-dark-700 rounded-lg flex flex-col',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-2 border-b border-fennec-dark-700 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          {icon && <span className="text-fennec-dark-400">{icon}</span>}
          <h3 className="text-sm font-medium text-fennec-dark-300">{title}</h3>
        </div>
        {count !== undefined && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-fennec-dark-700 text-fennec-dark-400">
            {count}
          </span>
        )}
      </div>

      {/* Content */}
      <div
        className="p-3 overflow-y-auto flex-1"
        style={{ maxHeight }}
      >
        {loading ? (
          <div className="flex items-center justify-center h-full text-fennec-dark-500">
            <div className="animate-pulse">Loading...</div>
          </div>
        ) : isEmpty ? (
          <div className="flex items-center justify-center h-full text-fennec-dark-500 text-sm">
            {emptyMessage}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

export default PanelContainer;
