// Same functions as the live API, backed by in-memory cases in the docs/api.md shape.
// Role filtering mirrors backend/common/views.py.
import { sampleCase } from "./sampleCase.js";
import accounts from "../../../data/accounts.json";
import seedCases from "../../../data/cases.json";
import seedAudit from "../../../data/audit.json";
import { SCENARIOS } from "../lib/scenarios.js";

const ACCOUNTS = Object.fromEntries(accounts.map((a) => [a.accountId, a]));


const CHAT_SCRIPT = [
  "Were you told to keep this secret, even from family or your bank?",
  "Is anyone asking you to hurry, or still on the phone with you now?",
  "This matches a common scam. Your money is safe and the transfer stays paused. Real bank or brokerage staff will never ask you to move money to protect it. A fraud specialist can talk it through with you now.",
];

function scenarioCase(request) {
  const a = ACCOUNTS[request.accountId] || {};
  const scenario = SCENARIOS.find((s) => s.accountId === request.accountId);
  const high = scenario?.expectedLevel === "high";
  const score = high ? 90 : 18;
  const insiders = request.accountId === "acc-1005" ? ["jo-05"] : [];
  return {
    accountId: request.accountId, clientName: a.clientName || request.accountId, status: high ? "HELD" : "RELEASED",
    transaction: { transactionId: `txn-${Date.now()}`, accountId: request.accountId, type: "withdrawal", payee: {} },
    risk: {
      score, level: high ? "high" : "low", doNotNotify: insiders,
      memo: high ? `${a.clientName} asked to send ${money(request.amount)} to ${request.payee.name}, a new payee. ${scenario?.story || ""} Recommend a temporary hold under FINRA Rule 2165 and proposed Rule 2166 while the client is reached on the number of record.` : `Consistent with ${a.clientName}'s normal activity. No action needed.`,
      signals: high ? [{ name: "new_payee", detail: `${request.payee.name} has never been paid from this account` }, { name: "senior_client", detail: `Client is ${a.clientAge}` }] : [],
    },
    holdEndsAt: high ? "2026-10-16" : null,
    notified: high ? ["client", "fraud-team", ...(a.advisor ? [a.advisor.contactId] : []), ...(a.emergencyContact ? [a.emergencyContact.contactId] : []), ...(a.jointOwners || []).map((j) => j.contactId).filter((id) => !insiders.includes(id))] : [],
    responses: [], decision: null, audit: [],
  };
}

const money = (n) => n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

// The same pre-seeded cases the live demo reset loads (data/cases.json), with their audit rows.
const seeded = () =>
  seedCases.map((c) => ({ ...structuredClone(c), audit: seedAudit.filter((a) => a.caseId === c.caseId).map(({ caseId, ...row }) => row) }));
const fresh = () => [structuredClone(sampleCase), ...seeded()];
let cases = fresh();

const delay = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");
const find = (id) => {
  const c = cases.find((x) => x.caseId === id);
  if (!c) throw new Error("Case not found.");
  return c;
};

function forRole(c, role) {
  if (role === "fraud") return structuredClone(c);
  const base = { caseId: c.caseId, status: c.status, createdAt: c.createdAt, transaction: c.transaction, holdEndsAt: c.holdEndsAt, decision: c.decision };
  if (role === "advisor") {
    const { doNotNotify, ...risk } = c.risk;
    return structuredClone({ ...base, clientName: c.clientName, accountId: c.accountId, notified: c.notified, risk, responses: c.responses });
  }
  return structuredClone({ ...base, responses: c.responses.filter((r) => r.role === "client") });
}

const summary = (c) => ({
  caseId: c.caseId, clientName: c.clientName, amount: c.transaction.amount, payeeName: c.transaction.payee.name,
  status: c.status, score: c.risk.score, level: c.risk.level, createdAt: c.createdAt, holdEndsAt: c.holdEndsAt,
});

const rank = (s) => (s === "HELD" || s === "EXTENDED" || s === "ESCALATED" ? 0 : 1);

export const mockApi = {
  async submitWithdrawal(role, request) {
    await delay(4000); // the real call takes about 10 seconds
    const c = request.accountId === "acc-1001" ? structuredClone(sampleCase) : scenarioCase(request);
    c.caseId = `case-${Math.random().toString(16).slice(2, 10)}`;
    c.createdAt = now();
    c.transaction = { ...c.transaction, ...request, timestamp: now(), payee: { ...c.transaction.payee, ...request.payee } };
    c.audit = [{ timestamp: now(), actor: "system", action: c.status, detail: `Risk score ${c.risk.score}` }];
    cases = [c, ...cases];
    return forRole(c, role);
  },
  async getContext(role, caseId) {
    await delay(150);
    const a = ACCOUNTS[find(caseId).accountId];
    const advisor = a?.advisor || null;
    if (role === "client") return { advisor };
    const contacts = [
      ...(advisor ? [{ ...advisor, relationship: "advisor", kind: "advisor" }] : []),
      ...(a?.emergencyContact ? [{ ...a.emergencyContact, kind: "emergency" }] : []),
      ...(a?.jointOwners || []).map((j) => ({ ...j, kind: "joint_owner" })),
    ];
    return { accountId: a?.accountId, clientName: a?.clientName, clientAge: a?.clientAge, accountOpened: a?.accountOpened, advisor, contacts, contactLog: a?.contactLog || [], advisorNotes: a?.advisorNotes || [] };
  },
  async askAssistant(role, caseId, messages) {
    await delay(2200);
    const c = find(caseId);
    const q = messages[messages.length - 1].text.toLowerCase();
    const signals = (c.risk.signals || []).map((s) => s.detail).slice(0, 4).join("; ");
    let reply;
    if (/ask|call|question/.test(q)) {
      reply = `Call ${c.clientName.split(" ")[0]} on the number on file, not any number she gives you. Ask:
1. Did anyone contact you first about moving this money?
2. Were you told to keep it secret from family or from us?
3. Is anyone on the phone with you right now?
If any answer is yes, reassure her the money is safe and add a note for the Fraud team.`;
    } else if (/verify|release|check/.test(q)) {
      reply = `Before any release: confirm the request by callback on the number of record, confirm the payee independently, and get a trusted contact on file (Rule 2165 notice). Right now the evidence points the other way: ${signals}.`;
    } else if (/summar|notes|evidence/.test(q)) {
      reply = `${c.clientName}: ${money(c.transaction.amount)} to ${c.transaction.payee.name}, score ${c.risk.score} (${c.risk.level}). Evidence: ${signals}. Status ${c.status}${c.holdEndsAt ? `, hold until ${c.holdEndsAt}` : ""}.`;
    } else {
      reply = `It was held because the score was ${c.risk.score} (${c.risk.level}), above the 70 hold threshold. The main reasons: ${signals}. This is mock data; the live assistant answers from the real case.`;
    }
    return { reply, suggestions: role === "fraud" ? ["What should I verify before releasing?", "Summarize the evidence for my notes", "Who was alerted?"] : ["What should I ask the client on the call?", "Explain the risk in plain English"] };
  },
  async listCases(role, status) {
    await delay(200);
    const list = cases.filter((c) => !status || c.status === status);
    list.sort((a, b) => rank(a.status) - rank(b.status) || (b.risk.score ?? 0) - (a.risk.score ?? 0));
    return { cases: list.map(summary) };
  },
  async getCase(role, caseId) {
    await delay(200);
    return forRole(find(caseId), role);
  },
  async postResponse(role, caseId, kind, text) {
    const c = find(caseId);
    const response = { responseId: `resp-${Date.now()}`, role, kind, text, at: now() };
    if (kind === "chat") {
      await delay(1500);
      const n = c.responses.filter((r) => r.kind === "chat").length;
      Object.assign(response, { chatReply: CHAT_SCRIPT[Math.min(n, CHAT_SCRIPT.length - 1)], done: n >= CHAT_SCRIPT.length - 1 });
    } else {
      await delay(300);
    }
    c.responses.push(response);
    c.audit.push({ timestamp: now(), actor: role, action: kind.toUpperCase(), detail: text });
    return forRole(c, role);
  },
  async postDecision(role, caseId, action, note) {
    await delay(300);
    if (role !== "fraud") throw new Error("Only the fraud team can decide.");
    const c = find(caseId);
    c.status = { release: "RELEASED", extend: "EXTENDED", escalate: "ESCALATED" }[action];
    c.decision = { action, by: role, at: now(), note };
    if (action === "release") c.holdEndsAt = null;
    if (action === "extend") c.holdEndsAt = "2026-11-06";
    c.audit.push({ timestamp: now(), actor: role, action: c.status, detail: note });
    return forRole(c, role);
  },
  async resetDemo() {
    cases = fresh();
    return { ok: true, accountsLoaded: 4 };
  },
};
