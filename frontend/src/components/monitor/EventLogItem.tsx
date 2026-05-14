/**
 * Event Log Item
 *
 * Displays a single event with expandable JSON payload.
 */

import { useState } from 'react';
import { ChevronRight, ChevronDown, Copy, Check } from 'lucide-react';
import type { RawEvent } from '@/types/eventLog';

interface EventLogItemProps {
  event: RawEvent;
  index: number;
}

// Format timestamp as HH:MM:SS.mmm
function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');
  const ms = date.getMilliseconds().toString().padStart(3, '0');
  return `${hours}:${minutes}:${seconds}.${ms}`;
}

// Format payload size
function formatSize(bytes: number | undefined): string {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
}

// Get color class for source badge
function getSourceColor(source: 'sse' | 'rest'): string {
  return source === 'sse'
    ? 'bg-purple-500/20 text-purple-400'
    : 'bg-blue-500/20 text-blue-400';
}

// Get color class for event type
function getEventTypeColor(eventType: string): string {
  if (eventType === 'error') return 'text-red-400';
  if (eventType === 'complete' || eventType === 'session_start') return 'text-green-400';
  if (eventType.includes('hypothesis') || eventType.includes('task') || eventType.includes('step'))
    return 'text-purple-400';
  if (eventType.includes('finding')) return 'text-orange-400';
  if (eventType === 'recon_update') return 'text-blue-400';
  return 'text-cyan-400';
}

export function EventLogItem({ event, index }: EventLogItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(JSON.stringify(event.payload, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const payloadString = JSON.stringify(event.payload, null, 2);
  const isLargePayload = payloadString.length > 500;

  return (
    <div className="border-b border-fennec-dark-700 last:border-b-0">
      {/* Header row */}
      <div
        className="flex items-center gap-3 px-3 py-2 hover:bg-fennec-dark-800/50 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Expand/collapse icon */}
        <button className="text-fennec-dark-500 hover:text-fennec-dark-300">
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>

        {/* Index */}
        <span className="text-fennec-dark-500 text-xs font-mono w-8">#{index + 1}</span>

        {/* Timestamp */}
        <span className="text-fennec-dark-400 text-xs font-mono w-24">
          {formatTime(event.timestamp)}
        </span>

        {/* Event type */}
        <span className={`text-sm font-mono flex-1 ${getEventTypeColor(event.eventType)}`}>
          {event.eventType}
        </span>

        {/* Source badge */}
        <span
          className={`text-xs px-1.5 py-0.5 rounded uppercase font-medium ${getSourceColor(
            event.source
          )}`}
        >
          {event.source}
        </span>

        {/* Payload size */}
        {event.payloadSize && (
          <span className="text-fennec-dark-500 text-xs font-mono w-16 text-right">
            {formatSize(event.payloadSize)}
          </span>
        )}

        {/* Copy button */}
        <button
          onClick={handleCopy}
          className="text-fennec-dark-500 hover:text-fennec-dark-300 p-1"
          title="Copy payload"
        >
          {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
        </button>
      </div>

      {/* Expanded payload */}
      {isExpanded && (
        <div className="px-3 pb-3">
          <pre
            className={`bg-fennec-dark-900 rounded p-3 text-xs font-mono overflow-x-auto ${
              isLargePayload ? 'max-h-96 overflow-y-auto' : ''
            }`}
          >
            <code className="text-fennec-dark-300">{payloadString}</code>
          </pre>
        </div>
      )}
    </div>
  );
}

export default EventLogItem;
