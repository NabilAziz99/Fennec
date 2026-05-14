// Dashboard Statistics
export interface DashboardStats {
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  risk_mitigation_value: number;
  issues_fixed: number;
  total_tests: number;
  running_tests: number;
  total_agents: number;
  active_agents: number;
}

// Vulnerability Trend Data Point
export interface VulnerabilityTrend {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

// Severity Distribution
export interface SeverityDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

// Test Activity
export interface TestActivity {
  id: string;
  title: string;
  status: 'completed' | 'running' | 'pending' | 'failed' | 'awaiting_review';
  target_url: string;
  issues: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  duration: string;
  started_at: string;
  completed_at: string | null;
  hypothesis_count: number;
  findings_count: number;
  method?: string;
  credential_id?: string | null;
  initiated_by?: string;
}

// Hypothesis Result
// export interface HypothesisResult {
//   id: string;
//   title: string;
//   description: string;
//   status: 'completed' | 'running' | 'pending' | 'failed';
//   result: 'vulnerable' | 'safe' | 'inconclusive' | null;
//   severity: 'critical' | 'high' | 'medium' | 'low' | 'info' | null;
//   findings: string[];
//   steps: StepRecord[];
//   parent_id: string | null;
//   children_ids: string[];
//   required_agent: string;
//   started_at: string | null;
//   completed_at: string | null;
// }
export interface HypothesisResult {
    id: string;
    title: string;
    description?: string;
    status: 'pending' | 'in_progress' | 'completed' | 'blocked' | 'dead_end';
    result: 'vulnerable' | 'safe' | 'inconclusive' | null;
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info' | null;
    priority: number | string;
    parent_id: string | null;
    children_ids: string[];
    required_agent: string;
    skills?: string[];
    owasp_category?: string;
    findings?: string[];
    steps?: StepRecord[];
    tasks?: { tasks: Record<string, Task>; _counter: number };
    blocked_by?: string | null;
    waiting_for?: string | null;
    expected_outputs?: string[];
    actual_outputs?: string[];
    created_at: string;
    started_at: string | null;
    completed_at: string | null;
    color?: string;
}



// Step Record
export interface StepRecord {
  agent: string;
  action: string;
  input_summary: string;
  output_summary: string;
  success: boolean;
  timestamp: string;
}

// Target
export interface Target {
  id: string;
  user_id: string;
  domain: string;
  name: string;
  verified: boolean;
  verification_token: string | null;
  severity_counts: Record<string, number>;
  last_scanned: string | null;
  created_at: string;
  updated_at: string | null;
}

// Credential (password never exposed)
export interface Credential {
  id: string;
  target_id: string;
  name: string;
  username: string;
  auth_type: string;
  created_at: string;
}

// Finding Detail
export interface FindingDetail {
  id: string;
  job_id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  status: 'confirmed' | 'potential' | 'false_positive' | 'needs_verification';
  location: string;
  parameter: string;
  evidence: string;
  reproduction_steps: string[];
  vulnerability_type: string;
  cwe_id: string | null;
  hypothesis_id: string | null;
  discovered_at: string;
  discovered_by: string;
}

// Rich finding with MindFort-style tabs (extends FindingDetail for pentester results)
export interface RichFinding {
  id: number;
  job_id: string;
  hypothesis_id: string | null;
  status: string;
  verdict: string | null;
  evidence: string[];
  suggested_followups: string[];
  needs: string[];
  error: string | null;
  // Rich finding fields
  description_overview?: string | null;
  description_breakdown?: {
    vuln_type: string;
    affected_endpoint: string;
    access_required: string;
    exploitability: string;
  } | null;
  description_technical?: string | null;
  impact_demonstrated?: string | null;
  impact_attack_scenarios?: string | null;
  impact_business_risk?: string | null;
  evidence_logged?: Array<{ request: string; response: string }> | null;
  evidence_payloads?: string[] | null;
  evidence_observed?: string | null;
  remediation_primary?: string | null;
  remediation_implementation?: string | null;
  remediation_hardening?: string | null;
  owasp_category?: string | null;
  created_at: string;
}

// SSE Event Types
export type SSEEventType =
  | 'session_start'
  | 'node_update'
  | 'message'
  | 'tool_call'
  | 'tool_execution'
  | 'subtasks'
  | 'result'
  | 'complete'
  | 'error'
  | 'hypothesis_tree'
  | 'hypothesis_update'
  | 'current_hypothesis'
  | 'findings_update'
  | 'recon_update'
  | 'task_update'
  | 'step_update'
  | 'agent_result'
  | 'agent_request';

export interface SSEEvent {
  type: SSEEventType;
  data: unknown;
}

// API Response Types
export interface StartTestRequest {
  target_url: string;
  name?: string;
  description?: string;
  mode?: 'black_box' | 'white_box';
  htli?: boolean;
  target_id?: string;
  credential_id?: string;
  method?: 'turbo' | 'balanced' | 'deep';
  frequency?: 'daily' | 'weekly' | 'monthly' | null;
}

export interface JobResponse {
  id: string;
  user_id: string;
  name: string;
  status: string;
  target_url: string;
  mode: string;
  timeout_seconds: number;
  description: string | null;
  htli: boolean;
  target_id: string | null;
  credential_id: string | null;
  method: string;
  frequency: string | null;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface StartTestResponse {
  session_id: string;
  status: string;
  message: string;
}


// Blocked hypothesis info
export interface BlockedHypothesis {
    hypothesis_id: string;
    waiting_for: string;
    blocked_at: string;
}

// Hypothesis tree event payload
export interface HypothesisTreeEvent {
    session_id: string;
    hypotheses: Record<string, HypothesisResult>;
    dfs_stack: string[];
    blocked_list: BlockedHypothesis[];
    outputs_registry: Record<string, string>;
    pending_outputs: Record<string, string>;
    current_hypothesis_id: string | null;
    statistics: {
        total: number;
        pending: number;
        in_progress: number;
        completed: number;
        blocked: number;
        dead_end: number;
        vulnerabilities: number;
        stack_size: number;
        blocked_count: number;
        outputs_available: number;
    };
}

// Current hypothesis event payload
export interface CurrentHypothesisEvent {
    session_id: string;
    hypothesis_id: string;
    hypothesis: HypothesisResult | null;
}

// Findings update event payload
export interface FindingsUpdateEvent {
    session_id: string;
    findings: RichFinding[];
    correlations: Correlation[];
    summary: {
        total: number;
        critical: number;
        high: number;
        medium: number;
        low: number;
        info: number;
    };
}

// Correlation type
export interface Correlation {
    id: string;
    title: string;
    description: string;
    finding_ids: string[];
    attack_chain: string;
    escalation_potential: string;
    new_recon_targets: string[];
    new_hypotheses: unknown[];
    confidence: number;
    created_at: string;
}

// Recon update event payload
export interface ReconUpdateEvent {
    session_id: string;
    recon_completed: boolean;
    target_url: string;
    technologies: Technology[];
    endpoints: Endpoint[];
    entry_points: EntryPoint[];
    auth_type: string | null;
    login_endpoint: string | null;
    registration_available: boolean;
}

export interface Technology {
    name: string;
    version: string | null;
    type: string;
    confidence: number;
}

export interface Endpoint {
    path: string;
    method: string;
    parameters: string[];
    auth_required: boolean;
    response_type: string;
    notes: string;
}

export interface EntryPoint {
    location: string;
    type: string;
    input_type: string;
    validation_observed: string;
    notes: string;
}

// Severity type
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

// Status type
export type TestStatus = 'completed' | 'running' | 'pending' | 'failed' | 'queued' | 'awaiting_review';

// Task (matches backend src/state/task.py)
export interface Task {
  id: string;
  subject: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  activeForm: string;
  owner: string;
  metadata: Record<string, unknown>;
  blocks: string[];
  blockedBy: string[];
}

// Task update event payload
export interface TaskUpdateEvent {
  session_id: string;
  hypothesis_id: string;
  tasks: Task[];
  counter: number;
}

// Step update event payload
export interface StepUpdateEvent {
  session_id: string;
  hypothesis_id: string;
  step: StepRecord;
  all_steps: StepRecord[];
}

// Agent result event payload (pentester/coder results before analyst processes)
export interface AgentResultEvent {
  session_id: string;
  hypothesis_id: string | null;
  status: 'completed' | 'needs_info' | 'dead_end';
  result: 'vulnerable' | 'safe' | 'inconclusive' | null;
  severity: Severity | null;
  findings: string[];
  outputs: string[];
  needs: string[];
  error: string | null;
  new_hypotheses: NewHypothesis[];
}

// New hypothesis from agent result
export interface NewHypothesis {
  title: string;
  description: string;
  required_agent: string;
  skills: string[];
  priority: number;
  expected_outputs: string[];
}

// Agent request event payload (cross-agent communication)
export interface AgentRequestEvent {
  session_id: string;
  from_agent: string;
  to_agent: string;
  task: string;
  context: string;
}

// Tool execution event payload (detailed tool results)
export interface ToolExecutionEvent {
  id?: number;
  session_id: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  agent: string;
  success: boolean;
  result: string;
  error: string | null;
  timestamp: string | null;
}

// Extended Recon update event payload (with additional fields)
export interface ReconUpdateEventExtended extends ReconUpdateEvent {
  ip_address: string | null;
  ports_open: number[];
  headers_of_interest: Record<string, string>;
  cookies_observed: string[];
  default_credentials_found: Array<{
    username: string;
    password: string;
    location: string;
  }>;
  notes: string[];
}

// --- Hypothesis Review (HTLI) types ---

export interface HypothesisEditItem {
  hypothesis_id: string;
  action: 'approve' | 'reject';
  title?: string;
  description?: string;
  priority?: number;
}

export interface NewHypothesisItem {
  title: string;
  description?: string;
  priority?: number;
  skills?: string[];
  required_agent?: string;
}

export interface ReviewSubmitRequest {
  edits: HypothesisEditItem[];
  new_hypotheses: NewHypothesisItem[];
  guidance_notes: string;
}

export interface ReviewResponse {
  id: number;
  job_id: string;
  status: 'pending' | 'approved' | 'auto_approved';
  hypotheses_snapshot: Record<string, unknown>[];
  user_edits: Record<string, unknown> | null;
  timeout_seconds: number;
  review_cycle: number;
  created_at: string;
  reviewed_at: string | null;
  seconds_remaining: number | null;
}
