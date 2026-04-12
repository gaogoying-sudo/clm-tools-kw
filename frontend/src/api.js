const BASE = '/api';

const ADMIN_TOKEN_STORAGE_KEY = 'clm_admin_token';

export function setAdminToken(token) {
  if (token == null || String(token).trim() === '') {
    localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    return;
  }
  localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, String(token));
}

export function getAdminToken() {
  try {
    return localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

async function request(path, options = {}) {
  const token = getAdminToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'X-Admin-Token': token } : {}),
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Sessions
  syncToday: () => request('/sessions/sync-today', { method: 'POST' }),
  devResetToday: () => request('/sessions/dev/reset-today', { method: 'POST' }),
  getTodaySessions: () => request('/sessions/today/list'),
  getSession: (id, rootEventType) => request(`/sessions/${id}${rootEventType ? `?root_event_type=${rootEventType}` : ''}`),
  pushSession: (id) => request(`/sessions/${id}/push`, { method: 'POST' }),

  // Answers
  submitAnswers: (sessionId, data) =>
    request(`/answers/${sessionId}/submit`, { method: 'POST', body: JSON.stringify(data) }),

  // Admin
  getDashboard: (date) => request(`/admin/dashboard${date ? `?target_date=${date}` : ''}`),
  getEngineers: (date) => request(`/admin/engineers${date ? `?target_date=${date}` : ''}`),
  getSessionAnswers: (id) => request(`/admin/sessions/${id}/answers`),
  getCandidates: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/admin/candidates${qs ? `?${qs}` : ''}`);
  },
  updateCandidate: (id, data) =>
    request(`/admin/candidates/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Questions management
  getQuestions: () => request('/admin/questions'),
  createQuestion: (data) =>
    request('/admin/questions', { method: 'POST', body: JSON.stringify(data) }),
  updateQuestion: (id, data) =>
    request(`/admin/questions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteQuestion: (id) =>
    request(`/admin/questions/${id}`, { method: 'DELETE' }),

  // History
  getHistory: (startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const qs = params.toString();
    return request(`/admin/history${qs ? `?${qs}` : ''}`);
  },

  // Export
  exportUrl: (startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    return `${BASE}/admin/export?${params.toString()}`;
  },

  // QA Records
  getQARecords: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/admin/qa-records${qs ? `?${qs}` : ''}`);
  },

  // Search (with cache)
  searchData: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/admin/search${qs ? `?${qs}` : ''}`);
  },
};
