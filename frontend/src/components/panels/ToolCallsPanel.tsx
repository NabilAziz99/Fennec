/**
 * Tool Calls Panel
 *
 * Displays tool invocations and their execution results.
 */

import { Wrench, ChevronDown, Check, X, ListTodo } from 'lucide-react';
// import { JSONTree } from 'react-json-tree';
import { PanelContainer } from './PanelContainer';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/Collapsible';
import { cn } from '@/lib/utils';
import type { ToolExecutionEvent } from '@/types';
// import JsonView from "@uiw/react-json-view";

interface ToolCallsPanelProps {
  toolExecutions: ToolExecutionEvent[];
}

// Format timestamp
function formatTime(timestamp: number | string | null): string {
  if (!timestamp) return '';
  const date = typeof timestamp === 'string' ? new Date(timestamp) : new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

interface TodoItem {
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
}

function WriteTodosItem({ exec }: { exec: ToolExecutionEvent }) {
  // todos may arrive as a JSON string (double-serialized by OpenRouter) or a proper array
  let rawTodos = exec.tool_input?.todos;
  if (typeof rawTodos === 'string') {
    try { rawTodos = JSON.parse(rawTodos); } catch { rawTodos = []; }
  }
  const todos: TodoItem[] = Array.isArray(rawTodos) ? rawTodos : [];

  return (
    <div className="bg-fennec-dark-900 rounded border border-fennec-dark-700 w-full p-2 space-y-1">
      <div className="flex items-center gap-2 mb-2">
        <ListTodo size={14} className="text-fennec-dark-400 shrink-0" />
        <span className="text-xs font-medium text-fennec-dark-300">Task List</span>
        {exec.agent && (
          <span className="text-xs text-fennec-dark-500 ml-auto">{exec.agent}</span>
        )}
        {exec.timestamp && (
          <span className="text-xs text-fennec-dark-500">{formatTime(exec.timestamp)}</span>
        )}
      </div>
      {todos.map((todo, i) => (
        <div key={i} className="flex items-start gap-2 py-0.5">
          {todo.status === 'completed' ? (
            <Check size={13} className="text-green-400 shrink-0 mt-0.5" />
          ) : todo.status === 'in_progress' ? (
            <span className="w-3 h-3 rounded-full border-2 border-yellow-400 shrink-0 mt-0.5 animate-pulse" />
          ) : (
            <span className="w-3 h-3 rounded-full border border-fennec-dark-500 shrink-0 mt-0.5" />
          )}
          <span className={cn(
            "text-xs",
            todo.status === 'completed' ? "line-through text-fennec-dark-500" :
            todo.status === 'in_progress' ? "text-yellow-300" :
            "text-fennec-dark-300"
          )}>
            {todo.content}
          </span>
        </div>
      ))}
    </div>
  );
}

/** Parse a raw result string into a structured value for display.
 *
 * Priority:
 * 1. Valid JSON object/array  → return parsed value (rendered as pretty JSON)
 * 2. JSON-encoded string      → return the decoded string (already has real \n chars)
 * 3. Raw string               → unescape common sequences (\n \t \r) so <pre> renders them
 */
function parseResult(result: string): object | string {
    // 0: Extract content from Python ToolMessage repr (content='...' name='terminal' ...)
    const contentMatch = result.match(/^content='([\s\S]*?)'\s+name='/);
    if (contentMatch) {
        result = contentMatch[1]
            .replace(/\\n/g, '\n')
            .replace(/\\t/g, '\t')
            .replace(/\\r/g, '\r')
            .replace(/\\'/g, "'");
    }

    // 1 & 2: Try JSON parse — handles both objects and JSON-encoded strings
    try {
        const parsed = JSON.parse(result);
        if (typeof parsed === 'object' && parsed !== null) return parsed;
        if (typeof parsed === 'string') return parsed; // already has real newlines
    } catch {
        // not valid JSON — fall through
    }

    // 3: Unescape common C-style escape sequences in raw strings
    return result
        .replace(/\\n/g, '\n')
        .replace(/\\t/g, '\t')
        .replace(/\\r/g, '\r');
}

function ToolExecutionItem({ exec }: { exec: ToolExecutionEvent }) {
    const resultData = exec.result ? parseResult(exec.result) : null;
    const command = exec.tool_input?.command as string | undefined;
    const message = exec.tool_input?.message as string | undefined;

    return (
        <Collapsible className="bg-fennec-dark-900 rounded border border-fennec-dark-700 w-full">
            <CollapsibleTrigger className="flex items-start justify-between w-full p-2 hover:bg-fennec-dark-800/50 transition-colors rounded group ">
                <div className="flex flex-col gap-1 min-w-0 flex-1 text-start ">
                    <div className="flex items-center gap-2">
                        <span className={cn(
                            "text-xs px-1.5 py-0.5 rounded font-medium shrink-0",
                            exec.success === true ? "bg-green-500/20 text-green-400"
                              : exec.success === false ? "bg-red-500/20 text-red-400"
                              : "bg-yellow-500/20 text-yellow-400"
                        )}>
                            EXEC
                        </span>
                        <span className="text-sm font-mono text-fennec-dark-300 truncate">{exec.tool_name}</span>
                        {exec.success === true ? (
                            <Check size={14} className="text-green-400 shrink-0" />
                        ) : exec.success === false ? (
                            <X size={14} className="text-red-400 shrink-0" />
                        ) : null}
                    </div>
                    {message && (
                        <span className="text-xs text-fennec-dark-400 truncate pl-1 pt-5">{message}</span>
                    )}
                    {command && (
                        <code className="text-xs text-fennec-orange-400 bg-fennec-dark-950 px-1.5 py-0.5 rounded truncate block">
                            {command}
                        </code>
                    )}
                </div>
                <div className="flex items-center gap-2 shrink-0 pl-2 pt-0.5">
                    {exec.agent && (
                        <span className="text-xs text-fennec-dark-500">{exec.agent}</span>
                    )}
                    {exec.timestamp && (
                        <span className="text-xs text-fennec-dark-500">{formatTime(exec.timestamp)}</span>
                    )}
                    <ChevronDown className="h-4 w-4 text-fennec-dark-500 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="px-2 pb-2 overflow-hidden ">
                {exec.error ? (
                    <div className="text-xs text-red-400 mt-1 bg-red-500/10 p-2 rounded border border-red-500/20 w-full">
                        {exec.error}
                    </div>
                ) : resultData && typeof resultData === 'object' ? (
                    <pre className="mt-2 max-h-64 overflow-auto rounded bg-muted/50 p-2 text-xs">
                        {JSON.stringify(resultData, null, 2)}
                    </pre>
                ) : (
                    <pre className="text-xs text-fennec-dark-400 overflow-x-auto bg-fennec-dark-950 p-3 rounded mt-1 w-full">
                        {resultData as string ?? exec.result}
                    </pre>
                )}
            </CollapsibleContent>
        </Collapsible>
    );
}


export function ToolCallsPanel({ toolExecutions }: ToolCallsPanelProps) {
  const reversedExecutions = [...toolExecutions].reverse();

  return (
      <PanelContainer
          title="Tool Calls & Executions"
          icon={<Wrench size={16} />}
          count={toolExecutions.length}
          maxHeight="300px"
          isEmpty={toolExecutions.length === 0}
          emptyMessage="No tool calls yet"
      >
        <div className="space-y-2">
          {reversedExecutions.map((exec) =>
              exec.tool_name === 'write_todos'
                  ? <WriteTodosItem key={exec.id ?? `exec-${exec.timestamp}`} exec={exec} />
                  : <ToolExecutionItem key={exec.id ?? `exec-${exec.timestamp}`} exec={exec} />
          )}
        </div>
      </PanelContainer>
  );
}

export default ToolCallsPanel;
