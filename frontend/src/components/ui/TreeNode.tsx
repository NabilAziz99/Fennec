import { useState, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface TreeNodeProps {
  label: ReactNode;
  children?: ReactNode;
  icon?: ReactNode;
  statusIndicator?: ReactNode;
  isLast?: boolean;
  defaultExpanded?: boolean;
  depth?: number;
}

export function TreeNode({
  label,
  children,
  icon,
  statusIndicator,
  isLast = false,
  defaultExpanded = false,
  depth = 0,
}: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const hasChildren = !!children;

  return (
    <div className="relative">
      {/* Vertical tree line */}
      {depth > 0 && !isLast && (
        <div className="absolute left-2 top-6 bottom-0 w-px bg-fennec-dark-700" />
      )}

      {/* Horizontal connector */}
      {depth > 0 && (
        <div className="absolute left-2 top-3 w-3 h-px bg-fennec-dark-700" />
      )}

      <div className={cn('flex items-start gap-2', depth > 0 && 'ml-5')}>
        {/* Expand/collapse button or status indicator */}
        {hasChildren ? (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-0.5 p-0.5 text-fennec-dark-400 hover:text-white transition-colors"
          >
            <motion.span
              animate={{ rotate: isExpanded ? 90 : 0 }}
              transition={{ duration: 0.15 }}
              className="block text-xs"
            >
              ▶
            </motion.span>
          </button>
        ) : (
          <span className="w-4 mt-0.5 flex items-center justify-center">
            {statusIndicator || <span className="text-fennec-dark-500">•</span>}
          </span>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {icon}
            <span className="text-sm">{label}</span>
          </div>

          {/* Children */}
          <AnimatePresence initial={false}>
            {hasChildren && isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: 'easeInOut' }}
                className="mt-2 overflow-hidden"
              >
                {children}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default TreeNode;
