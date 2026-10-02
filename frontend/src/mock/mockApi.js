// Same functions as the live API, backed by in-memory cases in the docs/api.md shape.
// Role filtering mirrors backend/common/views.py.
import { sampleCase } from "./sampleCase.js";
import accounts from "../../../data/accounts.json";
import { SCENARIOS } from "../lib/scenarios.js";

const ACCOUNTS = Object.fromEntries(accounts.map((a) => [a.accountId, a]));

const otherCases = [
  {
    caseId: "case-0002", accountId: "acc-1002", clientName: "Robert Okafor", createdAt: "2026-10-02T14:32:00Z", status: "HELD",
    transaction: { transactionId: "txn-9002", accountId: "acc-1002", timestamp: "2026-10-02T14:32:00Z", type: "withdrawal", amount: 42500,
      payee: { payeeId: "pay-778", name: "Harbor Title Escrow", type: "bank", addedAt: "2026-10-02T13:10:00Z" }, channel: "web", clientNote: "Closing on the house" },
    risk: { score: 74, level: "high", memo: "Robert Okafor, 71, is wiring $42,500 for a home closing. The wire instructions were changed by an email this morning, and the receiving bank differs from the one used for his deposit last month. This matches a business email compromise aimed at real estate closings.\n\nRecommended: confirm the instructions by phone with the title company using a number from the closing documents, not the email. A Rule 2165 hold is in place.",
      signals: [{ name: "new_payee", detail: "Wire instructions changed by email today" }, { name: "senior_client", detail: "Client is 71" }], doNotNotify: [] },
    holdEndsAt: "2026-10-16", notified: ["client", "adv-02", "fraud-team"], decision: null,
    responses: [{ responseId: "resp-r1", role: "advisor", kind: "note", text: "Robert says the title officer emailed new instructions. I asked him not to reply to that thread.", at: "2026-10-02T15:20:00Z" }],
    audit: [{ timestamp: "2026-10-02T14:32:07Z", actor: "system", action: "HELD", detail: "Risk score 74" }, { timestamp: "2026-10-02T15:20:00Z", actor: "advisor", action: "NOTE", detail: "Advisor note added" }],
  },
  {
    caseId: "case-0003", accountId: "acc-1003", clientName: "Dana Whitcombe", createdAt: "2026-10-01T19:40:00Z", status: "HELD",
    transaction: { transactionId: "txn-9003", accountId: "acc-1003", timestamp: "2026-10-01T19:40:00Z", type: "withdrawal", amount: 65000,
      payee: { payeeId: "pay-779", name: "Apex Bullion Co.", type: "individual", addedAt: "2026-09-10T00:00:00Z" }, channel: "web", clientNote: "" },
    risk: { score: 61, level: "medium", memo: "Dana Whitcombe, 66, is sending $65,000 to a precious-metals dealer registered three weeks ago. No impostor indicators, but the dealer is unverified.\n\nRecommended: confirm the dealer's registration before release.",
      signals: [{ name: "large_vs_history", detail: "38% of the balance, first metals purchase" }, { name: "senior_client", detail: "Client is 66" }], doNotNotify: [] },
    holdEndsAt: "2026-10-15", notified: ["client", "adv-01", "fraud-team"], decision: null, responses: [],
    audit: [{ timestamp: "2026-10-01T19:40:05Z", actor: "system", action: "HELD", detail: "Risk score 61" }],
  },
  {
    caseId: "case-0004", accountId: "acc-1004", clientName: "Lena Park", createdAt: "2026-10-01T16:02:00Z", status: "RELEASED",
    transaction: { transactionId: "txn-9004", accountId: "acc-1004", timestamp: "2026-10-01T16:02:00Z", type: "withdrawal", amount: 8400,
      payee: { payeeId: "pay-780", name: "Northline Property Mgmt", type: "bank", addedAt: "2025-08-01T00:00:00Z" }, channel: "web", clientNote: "Rent" },
    risk: { score: 12, level: "low", memo: "Recurring rent payment to an established payee. No action needed.", signals: [], doNotNotify: [] },
    holdEndsAt: null, notified: [], decision: null, responses: [],
    audit: [{ timestamp: "2026-10-01T16:02:03Z", actor: "system", action: "RELEASED", detail: "Risk score 12" }],
  },
];

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

const fresh = () => [structuredClone(sampleCase), ...structuredClone(otherCases)];
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
    return { accountId: a?.accountId, clientName: a?.clientName, clientAge: a?.clientAge, accountOpened: a?.accountOpened, advisor, contacts };
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
