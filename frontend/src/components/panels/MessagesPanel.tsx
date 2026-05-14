/**
 * Messages Panel
 *
 * Displays LLM messages from agents.
 */

import { useState } from 'react';
import { MessageSquare, ChevronDown, ChevronRight } from 'lucide-react';
import { PanelContainer } from './PanelContainer';

interface Message {
  type: string;
  content: string;
  timestamp: number;
}

interface MessagesPanelProps {
  messages: Message[];
}

// Format timestamp
function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// Message type colors
const TYPE_COLORS: Record<string, string> = {
  AIMessage: 'bg-purple-500/20 text-purple-400',
  HumanMessage: 'bg-blue-500/20 text-blue-400',
  SystemMessage: 'bg-gray-500/20 text-gray-400',
  ToolMessage: 'bg-green-500/20 text-green-400',
};

// Truncate content for display
function truncateContent(content: string, maxLength: number = 200): string {
  if (content.length <= maxLength) return content;
  return content.slice(0, maxLength) + '...';
}

function MessageItem({ message }: { message: Message }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLong = message.content.length > 200;

  return (
    <div className="p-2 bg-fennec-dark-900 rounded border border-fennec-dark-700">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-1.5 py-0.5 rounded ${
              TYPE_COLORS[message.type] || 'bg-fennec-dark-700 text-fennec-dark-400'
            }`}
          >
            {message.type}
          </span>
          <span className="text-xs text-fennec-dark-500">
            {formatTime(message.timestamp)}
          </span>
        </div>
        {isLong && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-fennec-dark-500 hover:text-fennec-dark-300"
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        )}
      </div>
      <div className="text-sm text-fennec-dark-300 whitespace-pre-wrap break-words">
        {isExpanded ? message.content : truncateContent(message.content)}
      </div>
    </div>
  );
}

export function MessagesPanel({ messages }: MessagesPanelProps) {
  // Show newest first
  const reversedMessages = [...messages].reverse();

  return (
    <PanelContainer
      title="Messages"
      icon={<MessageSquare size={16} />}
      count={messages.length}
      maxHeight="300px"
      isEmpty={messages.length === 0}
      emptyMessage="No messages yet"
    >
      <div className="space-y-2">
        {reversedMessages.map((message, index) => (
          <MessageItem key={index} message={message} />
        ))}
      </div>
    </PanelContainer>
  );
}

export default MessagesPanel;
