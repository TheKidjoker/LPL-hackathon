// Derives what the screens show from a Case in the docs/api.md shape.

export const memoParagraphs = (memo) =>
  (memo || "").split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);

export function citations(memo) {
  const text = memo || "";
  const cites = [];
  if (/2165/.test(text)) cites.push("FINRA Rule 2165");
  if (/2166/.test(text)) cites.push("Proposed Rule 2166");
  if (/4512/.test(text)) cites.push("Rule 4512 · trusted contact");
  return cites;
}

const last = (list) => list[list.length - 1];

export function clientAnswer(c) {
  const r = last((c.responses || []).filter((x) => x.role === "client" && (x.kind === "confirm" || x.kind === "deny")));
  if (!r) return null;
  return { said: r.kind === "deny" ? "No, I did not" : "Yes, it was me", denied: r.kind === "deny", at: r.at };
}

export const advisorNotes = (c) => (c.responses || []).filter((x) => x.role === "advisor" && x.kind === "note");

export function trustedContact(c) {
  const r = last((c.responses || []).filter((x) => x.kind === "emergency_contact"));
  return r ? r.text : null;
}

export const chatTurns = (c) => (c.responses || []).filter((x) => x.kind === "chat");
