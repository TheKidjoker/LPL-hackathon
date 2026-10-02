// Every call the app makes. Shapes are in docs/api.md.
// With no VITE_API_URL set, calls return mock data so the views can be built offline.
import { mockApi } from "./mock/mockApi.js";

export const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
export const USING_MOCK = !API_URL;

async function call(role, method, path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json", "X-Role": role },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error?.message || `Request failed (${res.status})`);
  return data;
}

const liveApi = {
  submitWithdrawal: (role, request) => call(role, "POST", "/withdrawals", request),
  listCases: (role, status) => call(role, "GET", `/cases${status ? `?status=${status}` : ""}`),
  getCase: (role, caseId) => call(role, "GET", `/cases/${caseId}`),
  getContext: (role, caseId) => call(role, "GET", `/cases/${caseId}/context`),
  postResponse: (role, caseId, kind, text) => call(role, "POST", `/cases/${caseId}/responses`, { kind, text }),
  postDecision: (role, caseId, action, note) => call(role, "POST", `/cases/${caseId}/decision`, { action, note }),
  askAssistant: (role, caseId, messages) => call(role, "POST", `/cases/${caseId}/assistant`, { messages }),
  resetDemo: (role) => call(role, "POST", "/demo/reset"),
};

export const api = USING_MOCK ? mockApi : liveApi;
