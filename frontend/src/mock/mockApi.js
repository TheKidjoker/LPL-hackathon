// Same functions as the live API, backed by one in-memory case.
// Role filtering mirrors backend/common/views.py.
import { sampleCase } from "./sampleCase.js";

let current = structuredClone(sampleCase);
const delay = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");

function forRole(c, role) {
  if (role === "fraud") return structuredClone(c);
  const base = {
    caseId: c.caseId, status: c.status, createdAt: c.createdAt,
    transaction: c.transaction, holdEndsAt: c.holdEndsAt, decision: c.decision,
  };
  if (role === "advisor") {
    const { doNotNotify, ...risk } = c.risk;
    return structuredClone({ ...base, clientName: c.clientName, accountId: c.accountId, notified: c.notified, risk, responses: c.responses });
  }
  return structuredClone({ ...base, responses: c.responses.filter((r) => r.role === "client") });
}

function summary(c) {
  return {
    caseId: c.caseId, clientName: c.clientName, amount: c.transaction.amount, payeeName: c.transaction.payee.name,
    status: c.status, score: c.risk.score, level: c.risk.level, createdAt: c.createdAt, holdEndsAt: c.holdEndsAt,
  };
}

export const mockApi = {
  async submitWithdrawal(role, request) {
    await delay(1500); // the real call takes about 7 seconds
    current = structuredClone(sampleCase);
    current.transaction = { ...current.transaction, ...request, payee: { ...current.transaction.payee, ...request.payee } };
    return forRole(current, role);
  },
  async listCases(role, status) {
    await delay(200);
    return { cases: [current].filter((c) => !status || c.status === status).map(summary) };
  },
  async getCase(role) {
    await delay(200);
    return forRole(current, role);
  },
  async postResponse(role, caseId, kind, text) {
    await delay(300);
    const response = { responseId: `resp-${current.responses.length + 1}`, role, kind, text, at: now() };
    if (kind === "chat") Object.assign(response, { chatReply: "Did someone contact you first and ask you to move this money?", done: false });
    current.responses.push(response);
    return forRole(current, role);
  },
  async postDecision(role, caseId, action, note) {
    await delay(300);
    if (role !== "fraud") throw new Error("Only the fraud team can decide.");
    current.status = { release: "RELEASED", extend: "EXTENDED", escalate: "ESCALATED" }[action];
    current.decision = { action, by: role, at: now(), note };
    if (action === "release") current.holdEndsAt = null;
    current.audit.push({ timestamp: now(), actor: role, action: current.status, detail: note });
    return forRole(current, role);
  },
  async resetDemo() {
    current = structuredClone(sampleCase);
    return { ok: true, accountsLoaded: 0 };
  },
};
