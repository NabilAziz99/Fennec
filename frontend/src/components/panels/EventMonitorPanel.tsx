import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Radio, Trash2, ChevronDown, ChevronRight } from 'lucide-react';

interface EventLog {
  id: number;
  timestamp: string;
  eventType: string;
  payload: unknown;
  sessionId?: string;
}

interface RawEvent {
  eventType: string;
  payload: unknown;
  sessionId?: string;
}

interface EventMonitorPanelProps {
  /** Latest raw event pushed from parent */
  lastEvent?: RawEvent | null;
  /** Maximum number of events to keep */
  maxEvents?: number;
}

export function EventMonitorPanel({ lastEvent, maxEvents = 100 }: EventMonitorPanelProps) {
  const [events, setEvents] = useState<EventLog[]>([]);
  const [expandedEvents, setExpandedEvents] = useState<Set<number>>(new Set());
  const [isPaused, setIsPaused] = useState(false);

  const eventIdCounter = useRef(0);
  const lastProcessedKey = useRef<string | null>(null);

  const addEvent = (eventType: string, payload: unknown, sessionId?: string) => {
    if (isPaused) return;

    const newEvent: EventLog = {
      id: eventIdCounter.current++,
      timestamp: new Date().toLocaleTimeString(),
      eventType,
      payload,
      sessionId,
    };

    setEvents((prev) => {
      const updated = [newEvent, ...prev];
      return updated.slice(0, maxEvents);
    });
  };

  // When parent pushes a new event, add it
  useEffect(() => {
    if (!lastEvent) return;

    // Prevent duplicates if parent re-renders with same object
    const key = `${lastEvent.eventType}:${JSON.stringify(lastEvent.payload)}:${lastEvent.sessionId ?? ''}`;
    if (lastProcessedKey.current === key) return;
    lastProcessedKey.current = key;

    addEvent(lastEvent.eventType, lastEvent.payload, lastEvent.sessionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastEvent]);

  const toggleExpand = (id: number) => {
    setExpandedEvents((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      return newSet;
    });
  };

  const clearEvents = () => {
    setEvents([]);
    setExpandedEvents(new Set());
  };

  const getEventColor = (eventType: string): string => {
    const colorMap: Record<string, string> = {
      session_start: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
      reconnected: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
      node_update: 'bg-purple-500/20 text-purple-400 border-purple-500/40',
      hypothesis_tree: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
      current_hypothesis: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
      findings_update: 'bg-red-500/20 text-red-400 border-red-500/40',
      recon_update: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',
      message: 'bg-gray-500/20 text-gray-400 border-gray-500/40',
      tool_call: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
      tool_execution: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
      agent_result: 'bg-pink-500/20 text-pink-400 border-pink-500/40',
      agent_request: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40',
      task_update: 'bg-teal-500/20 text-teal-400 border-teal-500/40',
      step_update: 'bg-teal-500/20 text-teal-400 border-teal-500/40',
      complete: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
      error: 'bg-red-500/20 text-red-400 border-red-500/40',
    };
    return colorMap[eventType] || 'bg-gray-500/20 text-gray-400 border-gray-500/40';
  };

  const formatPayload = (payload: unknown): string => {
    try {
      return JSON.stringify(payload, null, 2);
    } catch {
      return String(payload);
    }
  };

  return (
      <Card className="h-full">
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Radio className="h-4 w-4 animate-pulse text-emerald-400" />
              Event Monitor ({events.length})
            </CardTitle>

            <div className="flex gap-2">
              <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPaused((p) => !p)}
                  className="h-7 text-xs"
              >
                {isPaused ? 'Resume' : 'Pause'}
              </Button>

              <Button variant="outline" size="sm" onClick={clearEvents} className="h-7 text-xs">
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="max-h-96 overflow-y-auto">
          {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">No events received yet...</p>
          ) : (
              <div className="space-y-2">
                {events.map((event) => {
                  const isExpanded = expandedEvents.has(event.id);
                  return (
                      <div
                          key={event.id}
                          className="rounded-lg border border-border/50 bg-card/50 p-2 text-xs"
                      >
                        <div
                            className="flex cursor-pointer items-center justify-between"
                            onClick={() => toggleExpand(event.id)}
                        >
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                                <ChevronDown className="h-3 w-3" />
                            ) : (
                                <ChevronRight className="h-3 w-3" />
                            )}
                            <span className="text-muted-foreground">{event.timestamp}</span>
                            <Badge variant="outline" className={getEventColor(event.eventType)}>
                              {event.eventType}
                            </Badge>
                          </div>
                        </div>

                        {isExpanded && (
                            <pre className="mt-2 max-h-64 overflow-auto rounded bg-muted/50 p-2 text-xs">
                      {formatPayload(event.payload)}
                    </pre>
                        )}
                      </div>
                  );
                })}
              </div>
          )}
        </CardContent>
      </Card>
  );
}
