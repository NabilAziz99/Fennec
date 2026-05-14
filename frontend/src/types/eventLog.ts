/**
 * Event Log Types for Debug Monitoring
 *
 * Types for capturing and displaying raw SSE and REST events
 * for debugging and development purposes.
 */

/**
 * Raw event captured from SSE stream or REST API
 */
export interface RawEvent {
  /** Unique identifier for the event */
  id: string;
  /** Timestamp when event was received (ms since epoch) */
  timestamp: number;
  /** Event type name (e.g., 'session_start', 'hypothesis_tree') */
  eventType: string;
  /** Source of the event */
  source: 'sse' | 'rest';
  /** Raw payload data */
  payload: unknown;
  /** Session ID if available */
  sessionId?: string;
  /** Size of payload in bytes (approximate) */
  payloadSize?: number;
}

/**
 * Event statistics - counts by event type
 */
export interface EventStats {
  [eventType: string]: number;
}

/**
 * All known SSE event types from the backend
 */
export type SSEEventType =
  | 'session_start'
  | 'node_update'
  | 'hypothesis_tree'
  | 'current_hypothesis'
  | 'findings_update'
  | 'recon_update'
  | 'task_update'
  | 'task_update_batch'
  | 'step_update'
  | 'step_update_batch'
  | 'message'
  | 'tool_call'
  | 'tool_execution'
  | 'agent_result'
  | 'agent_request'
  | 'subtasks'
  | 'result'
  | 'complete'
  | 'error';

/**
 * All known REST endpoint names
 */
export type RESTEndpoint =
  | 'stats'
  | 'trends'
  | 'severity-distribution'
  | 'tests'
  | 'test-detail'
  | 'hypotheses'
  | 'findings'
  | 'recon'
  | 'executions'
  | 'health';

/**
 * Event log state
 */
export interface EventLogState {
  /** Array of captured events (newest first) */
  events: RawEvent[];
  /** Event counts by type */
  stats: EventStats;
  /** Whether event capture is active */
  isCapturing: boolean;
  /** Maximum number of events to store */
  maxEvents: number;
  /** Total events received (including those evicted) */
  totalReceived: number;
}

/**
 * Event log hook return type
 */
export interface UseEventLogReturn extends EventLogState {
  /** Log a new event */
  logEvent: (eventType: string, payload: unknown, source: 'sse' | 'rest', sessionId?: string) => void;
  /** Clear all events */
  clear: () => void;
  /** Toggle capture on/off */
  toggleCapture: () => void;
  /** Export events to JSON string */
  exportJSON: () => string;
  /** Get events filtered by type */
  getEventsByType: (eventType: string) => RawEvent[];
  /** Get events filtered by source */
  getEventsBySource: (source: 'sse' | 'rest') => RawEvent[];
  /** Reset stats */
  resetStats: () => void;
}

/**
 * Filter options for event log display
 */
export interface EventLogFilter {
  /** Filter by event type (empty = all) */
  eventType?: string;
  /** Filter by source */
  source?: 'sse' | 'rest' | 'all';
  /** Search text in payload */
  searchText?: string;
  /** Filter by session ID */
  sessionId?: string;
}

/**
 * Tool execution record from REST API
 */
export interface ToolExecution {
  id: string;
  session_id: string;
  hypothesis_id?: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  agent: string;
  success: boolean;
  result: string;
  error: string;
  timestamp: string;
}

/**
 * Recon data from REST API
 */
export interface ReconData {
  session_id: string;
  target_url: string;
  recon_completed: boolean;
  summary?: string;
  components?: unknown[];
  vulnerability_candidates?: unknown[];
  key_findings?: string[];
  ip_address?: string;
  ports_open: number[];
  technologies: Array<{
    name: string;
    version?: string;
    type: string;
    confidence: number;
  }>;
  endpoints: Array<{
    path: string;
    method: string;
    parameters: string[];
    auth_required: boolean;
    response_type: string;
    notes: string;
  }>;
  entry_points: Array<{
    location: string;
    type: string;
    input_type: string;
    validation_observed: boolean;
    notes: string;
  }>;
  auth_type?: string;
  login_endpoint?: string;
  registration_available: boolean;
  headers_of_interest: string[];
  cookies_observed: string[];
  default_credentials_found: boolean;
  notes: string[];
}
