/**
 * Event Log Hook
 *
 * Captures and stores raw SSE and REST events for debugging purposes.
 * Provides filtering, export, and statistics functionality.
 */

import { useState, useCallback, useRef } from 'react';
import type {
  RawEvent,
  EventLogState,
  UseEventLogReturn,
} from '../types/eventLog';

const DEFAULT_MAX_EVENTS = 500;

/**
 * Generate a unique event ID
 */
function generateEventId(): string {
  return `evt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Calculate approximate size of payload in bytes
 */
function getPayloadSize(payload: unknown): number {
  try {
    return JSON.stringify(payload).length;
  } catch {
    return 0;
  }
}

/**
 * Hook for capturing and managing event logs
 */
export function useEventLog(maxEvents: number = DEFAULT_MAX_EVENTS): UseEventLogReturn {
  const [state, setState] = useState<EventLogState>({
    events: [],
    stats: {},
    isCapturing: true,
    maxEvents,
    totalReceived: 0,
  });

  // Use ref for event ID counter to avoid re-renders
  const eventCounter = useRef(0);

  /**
   * Log a new event
   */
  const logEvent = useCallback(
    (
      eventType: string,
      payload: unknown,
      source: 'sse' | 'rest',
      sessionId?: string
    ) => {
      setState((prev) => {
        // Skip if not capturing
        if (!prev.isCapturing) {
          return prev;
        }

        eventCounter.current += 1;

        const newEvent: RawEvent = {
          id: generateEventId(),
          timestamp: Date.now(),
          eventType,
          source,
          payload,
          sessionId,
          payloadSize: getPayloadSize(payload),
        };

        // Update stats
        const newStats = { ...prev.stats };
        newStats[eventType] = (newStats[eventType] || 0) + 1;

        // Add event to beginning (newest first), trim if over max
        const newEvents = [newEvent, ...prev.events].slice(0, prev.maxEvents);

        return {
          ...prev,
          events: newEvents,
          stats: newStats,
          totalReceived: prev.totalReceived + 1,
        };
      });
    },
    []
  );

  /**
   * Clear all events
   */
  const clear = useCallback(() => {
    setState((prev) => ({
      ...prev,
      events: [],
      totalReceived: 0,
    }));
  }, []);

  /**
   * Toggle capture on/off
   */
  const toggleCapture = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isCapturing: !prev.isCapturing,
    }));
  }, []);

  /**
   * Export events to JSON string
   */
  const exportJSON = useCallback((): string => {
    const exportData = {
      exportedAt: new Date().toISOString(),
      totalEvents: state.events.length,
      totalReceived: state.totalReceived,
      stats: state.stats,
      events: state.events,
    };
    return JSON.stringify(exportData, null, 2);
  }, [state.events, state.totalReceived, state.stats]);

  /**
   * Get events filtered by type
   */
  const getEventsByType = useCallback(
    (eventType: string): RawEvent[] => {
      return state.events.filter((e) => e.eventType === eventType);
    },
    [state.events]
  );

  /**
   * Get events filtered by source
   */
  const getEventsBySource = useCallback(
    (source: 'sse' | 'rest'): RawEvent[] => {
      return state.events.filter((e) => e.source === source);
    },
    [state.events]
  );

  /**
   * Reset stats only (keep events)
   */
  const resetStats = useCallback(() => {
    setState((prev) => ({
      ...prev,
      stats: {},
    }));
  }, []);

  return {
    ...state,
    logEvent,
    clear,
    toggleCapture,
    exportJSON,
    getEventsByType,
    getEventsBySource,
    resetStats,
  };
}

export default useEventLog;
