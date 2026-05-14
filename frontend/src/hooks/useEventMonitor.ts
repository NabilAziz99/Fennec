import { useEffect, useState, useRef } from 'react';
import { usePentestContext } from '@/contexts/PentestContext';

interface EventLog {
  id: number;
  timestamp: string;
  eventType: string;
  payload: unknown;
  sessionId?: string;
}

export function useEventMonitor(maxEvents: number = 100) {
  const [events, setEvents] = useState<EventLog[]>([]);
  const eventIdCounter = useRef(0);
  const { agentActivity, hypotheses, findings, recon } = usePentestContext();

  // Monitor agentActivity changes
  useEffect(() => {
    if (agentActivity.messages.length > 0) {
      const lastMessage = agentActivity.messages[agentActivity.messages.length - 1];
      addEvent('message', lastMessage);
    }
  }, [agentActivity.messages.length]);

  useEffect(() => {
    if (agentActivity.toolCalls.length > 0) {
      const lastToolCall = agentActivity.toolCalls[agentActivity.toolCalls.length - 1];
      addEvent('tool_call', lastToolCall);
    }
  }, [agentActivity.toolCalls.length]);

  useEffect(() => {
    if (agentActivity.currentNode) {
      addEvent('node_update', { node: agentActivity.currentNode, agent: agentActivity.currentAgent });
    }
  }, [agentActivity.currentNode, agentActivity.currentAgent]);

  // Monitor hypotheses changes
  useEffect(() => {
    if (Object.keys(hypotheses.hypotheses).length > 0) {
      addEvent('hypothesis_tree', {
        count: Object.keys(hypotheses.hypotheses).length,
        statistics: hypotheses.statistics,
      });
    }
  }, [hypotheses.hypotheses, hypotheses.statistics]);

  // Monitor findings changes
  useEffect(() => {
    if (findings.findings.length > 0) {
      addEvent('findings_update', { count: findings.findings.length, summary: findings.summary });
    }
  }, [findings.findings.length]);

  // Monitor recon changes
  useEffect(() => {
    if (recon) {
      addEvent('recon_update', { summary: recon.summary });
    }
  }, [recon]);

  const addEvent = (eventType: string, payload: unknown, sessionId?: string) => {
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

  const clearEvents = () => {
    setEvents([]);
  };

  return { events, clearEvents };
}
