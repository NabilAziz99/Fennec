import type {
  DashboardStats,
  VulnerabilityTrend,
  SeverityDistribution,
  TestActivity,
  HypothesisResult,
  FindingDetail,
  StartTestRequest,
  JobResponse,
  ReviewResponse,
  ReviewSubmitRequest,
  Target,
  Credential,
  RichFinding,
} from '../types';
import type { ReconData, ToolExecution } from '../types/eventLog';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

// Generic fetch wrapper with error handling
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  } catch {
    // Network error (no backend, offline, CORS) — throw a silent error
    // that callers can catch without console noise
    throw new Error('__network_unavailable__');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = error.detail;
    const message = typeof detail === 'string' ? detail : (detail?.message || detail?.error || JSON.stringify(detail) || `HTTP ${response.status}`);
    throw new Error(message);
  }

  return response.json();
}

// Dashboard API
export const dashboardApi = {
  getStats: () => fetchApi<DashboardStats>('/dashboard/stats'),

  getTrends: (days = 30) =>
    fetchApi<VulnerabilityTrend[]>(`/dashboard/trends?days=${days}`),

  getSeverityDistribution: () =>
    fetchApi<SeverityDistribution>('/dashboard/severity-distribution'),

  getTests: (limit = 20, offset = 0) =>
    fetchApi<TestActivity[]>(`/dashboard/tests?limit=${limit}&offset=${offset}`),

  getTestDetail: (sessionId: string) =>
    fetchApi<TestActivity>(`/dashboard/tests/${sessionId}`),

  getHypotheses: (sessionId?: string, _limit = 50) => {
    if (sessionId) {
      return fetchApi<HypothesisResult[]>(`/jobs/${sessionId}/hypotheses`);
    }
    const params = new URLSearchParams();
    params.append('limit', _limit.toString());
    return fetchApi<HypothesisResult[]>(`/dashboard/hypotheses?${params}`);
  },

  getFindings: (sessionId?: string, severity?: string, _limit = 50) => {
    if (sessionId) {
      return fetchApi<FindingDetail[]>(
        `/jobs/${sessionId}/pentester_results?exclude_safe=true`
      );
    }
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    params.append('limit', _limit.toString());
    return fetchApi<FindingDetail[]>(`/dashboard/findings?${params}`);
  },

  getReconData: (sessionId: string) =>
    fetchApi<ReconData>(`/jobs/${sessionId}/recon_result`),

  getToolExecutions: (sessionId: string, _limit = 100, _offset = 0) =>
    fetchApi<ToolExecution[]>(`/jobs/${sessionId}/tool_calls`),

  cancelJob: (jobId: string) =>
    fetchApi<JobResponse>(`/jobs/${jobId}/cancel`, { method: 'POST' }),
};

// Pentest API
export const pentestApi = {
  startTest: (request: StartTestRequest): Promise<JobResponse> =>
    fetchApi<JobResponse>('/jobs', {
      method: 'POST',
      body: JSON.stringify({
        name: request.name ?? `Assessment – ${request.target_url}`,
        target_url: request.target_url,
        mode: request.mode ?? 'black_box',
        htli: request.htli ?? false,
        target_id: request.target_id,
        credential_id: request.credential_id,
        method: request.method ?? 'balanced',
        frequency: request.frequency ?? undefined,
      }),
    }),

  /** SSE stream — connects to /jobs/{id}/stream */
  streamSession: (sessionId: string): EventSource => {
    const url = `${API_BASE}/jobs/${sessionId}/stream`;
    return new EventSource(url);
  },

  getSession: (sessionId: string) =>
    fetchApi<{ session_id: string; status: string; target_url: string }>(
      `/sessions/${sessionId}`
    ),

  getJobFindings: (jobId: string, excludeSafe = true) =>
    fetchApi<RichFinding[]>(
      `/jobs/${jobId}/pentester_results?exclude_safe=${excludeSafe}`
    ),

  deleteSession: (sessionId: string) =>
    fetchApi<{ status: string; message: string }>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    }),
};

// Target API
export const targetApi = {
  list: () => fetchApi<Target[]>('/targets'),
  create: (data: { domain: string; name: string }) =>
    fetchApi<Target>('/targets', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: string) => fetchApi<Target>(`/targets/${id}`),
  update: (id: string, data: { name?: string; domain?: string }) =>
    fetchApi<Target>(`/targets/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) =>
    fetchApi<void>(`/targets/${id}`, { method: 'DELETE' }),
  verify: (id: string) =>
    fetchApi<{ verified: boolean; message: string }>(`/targets/${id}/verify`, { method: 'POST' }),
};

// Credential API
export const credentialApi = {
  list: (targetId?: string) =>
    fetchApi<Credential[]>(`/credentials${targetId ? `?target_id=${targetId}` : ''}`),
  create: (data: {
    target_id: string;
    name: string;
    username: string;
    password: string;
    auth_type: string;
  }) => fetchApi<Credential>('/credentials', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: { name?: string; username?: string; password?: string; auth_type?: string }) =>
    fetchApi<Credential>(`/credentials/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) =>
    fetchApi<void>(`/credentials/${id}`, { method: 'DELETE' }),
};

// SSE Event Stream Helper
export function createSSEStream(
  response: Response,
  onEvent: (event: string, data: unknown) => void,
  onError?: (error: Error) => void
) {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    onError?.(new Error('No response body'));
    return;
  }

  let buffer = '';
  let currentEvent = '';
  let currentData = '';

  const processChunk = (chunk: string) => {
    buffer += chunk;
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.trim() === '' || line.startsWith(':')) {
        if (currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            console.log(`[SSE] Received event: ${currentEvent}`, data);
            onEvent(currentEvent, data);
          } catch (e) {
            console.warn(`[SSE] Failed to parse event data for ${currentEvent}:`, e);
            onEvent(currentEvent, currentData);
          }
          currentEvent = '';
          currentData = '';
        }
        continue;
      }

      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        const dataLine = line.slice(6);
        currentData = currentData ? currentData + '\n' + dataLine : dataLine;
      }
    }
  };

  const read = async () => {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          if (currentEvent && currentData) {
            try {
              const data = JSON.parse(currentData);
              console.log(`[SSE] Received event (end): ${currentEvent}`, data);
              onEvent(currentEvent, data);
            } catch {
              onEvent(currentEvent, currentData);
            }
          }
          break;
        }
        processChunk(decoder.decode(value, { stream: true }));
      }
    } catch (error) {
      console.error('[SSE] Stream error:', error);
      onError?.(error as Error);
    }
  };

  read();

  return () => reader.cancel();
}

// Review API (HTLI)
export const reviewApi = {
  getPendingReview: (jobId: string) =>
    fetchApi<ReviewResponse>(`/jobs/${jobId}/reviews/pending`),

  submitReview: (jobId: string, payload: ReviewSubmitRequest) =>
    fetchApi<ReviewResponse>(`/jobs/${jobId}/reviews/submit`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getReviews: (jobId: string) =>
    fetchApi<ReviewResponse[]>(`/jobs/${jobId}/reviews`),
};

// Health check
export const healthCheck = () => fetch(`${API_BASE}/health`).then((r) => r.json());
