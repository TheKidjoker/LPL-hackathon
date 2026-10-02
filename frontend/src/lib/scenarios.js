// Kaylin's demo scenarios (data/), so the client view submits exactly what the eval scores.
import accounts from "../../../data/accounts.json";
import scenarios from "../../../data/scenarios.json";

// The scenarios were written for a request at this time. Payees added shortly before it
// are re-dated relative to now, so payee_added_recently fires on any demo day.
const WRITTEN_FOR = Date.parse("2026-10-02T14:05:00Z");
const DAY = 24 * 3600e3;

const byId = Object.fromEntries(accounts.map((a) => [a.accountId, a]));

export const SCENARIOS = scenarios.map((s) => ({
  id: s.scenarioId,
  accountId: s.accountId,
  clientName: byId[s.accountId]?.clientName || s.accountId,
  balance: byId[s.accountId]?.balance,
  hasAdvisor: !!byId[s.accountId]?.advisor,
  story: s.story,
  expectedLevel: s.expectedLevel,
  request: s.request,
}));

export function freshRequest(scenario, overrides = {}) {
  const req = structuredClone(scenario.request);
  const added = Date.parse(req.payee?.addedAt || "");
  if (added && WRITTEN_FOR - added >= 0 && WRITTEN_FOR - added < DAY) {
    req.payee.addedAt = new Date(Date.now() - (WRITTEN_FOR - added)).toISOString().replace(/\.\d+Z$/, "Z");
  }
  return { ...req, ...overrides, payee: { ...req.payee, ...(overrides.payee || {}) } };
}
