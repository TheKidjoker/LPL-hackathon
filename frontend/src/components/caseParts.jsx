import { chatTurns } from "../lib/caseView.js";
import { fmtAt, money, riskOf, signalLabel } from "../lib/format.js";
import { SparkIcon } from "./parts.jsx";

// Signals computed by our rules (ai/fraud_ai/signals.py). Anything else came from Claude
// or the scam-check chat, and gets its own group so the AI's reasoning is visible.
const RULE_SIGNALS = new Set(["new_payee", "payee_added_recently", "full_liquidation", "senior_client", "first_crypto", "unusual_timing", "large_vs_history"]);

export function SignalGroups({ signals, level }) {
  const r = riskOf(level);
  const all = signals || [];
  const rules = all.filter((s) => RULE_SIGNALS.has(s.name));
  const claude = all.filter((s) => !RULE_SIGNALS.has(s.name));
  const chip = (s, ai) => (
    <span key={s.name} className={`chip${ai ? " ai-chip" : ""}`} style={ai ? undefined : { background: r.bg, color: r.ink }}>
      <i style={ai ? undefined : { background: r.fg }} />
      <span><b style={{ fontWeight: 600 }}>{signalLabel(s)}</b> · {s.detail}</span>
    </span>
  );
  return (
    <div>
      <div className="signal-group">
        <div className="kicker">Rule checks · {rules.length}</div>
        <div className="chips">{rules.length ? rules.map((s) => chip(s, false)) : <span className="muted" style={{ fontSize: 13 }}>No rules fired</span>}</div>
      </div>
      {claude.length > 0 && (
        <div className="signal-group">
          <div className="kicker"><SparkIcon size={12} />Juno found · {claude.length}</div>
          <div className="chips">{claude.map((s) => chip(s, true))}</div>
        </div>
      )}
    </div>
  );
}

// Who was alerted, and who was deliberately left out because Claude thinks they may be involved.
export function AlertsPanel({ c, context }) {
  const contacts = Object.fromEntries((context?.contacts || []).map((x) => [x.contactId, x]));
  const label = (id) => {
    if (id === "client") return `${c.clientName} (client)`;
    if (id === "fraud-team") return "Fraud team";
    const x = contacts[id];
    return x ? `${x.name} (${x.relationship || x.kind})` : id;
  };
  const skipped = c.risk?.doNotNotify || [];
  const notified = c.notified || [];
  if (!notified.length && !skipped.length) return <div className="muted" style={{ fontSize: 14 }}>No alerts sent</div>;
  return (
    <div className="alert-list">
      {notified.map((id) => (
        <div key={id} className="alert-row"><span className="dot" style={{ background: "var(--risk-low)" }} />{label(id)}<span className="muted" style={{ fontSize: 12 }}>alerted in the app</span></div>
      ))}
      {skipped.map((id) => (
        <div key={id} className="alert-row skipped"><span className="dot" style={{ background: "var(--risk-high)" }} />{label(id)}<span style={{ fontSize: 12 }}>not alerted: may be involved</span></div>
      ))}
    </div>
  );
}

export function ChatTranscript({ c }) {
  const turns = chatTurns(c);
  if (!turns.length) return null;
  return (
    <div className="transcript">
      <div className="q">Did someone contact you first?</div>
      {turns.map((t) => (
        <div key={t.responseId}>
          <div className="a"><b>Client:</b> {t.text}</div>
          {t.chatReply && <div className="q" style={{ marginTop: 4 }}>{t.chatReply}</div>}
        </div>
      ))}
    </div>
  );
}

// Totals across the queue, plus the measured results from scripts/measure_scenarios.py.
export function ImpactStrip({ cases }) {
  const held = cases.filter((x) => x.status !== "RELEASED");
  const released = cases.filter((x) => x.status === "RELEASED");
  const dollars = held.reduce((sum, x) => sum + (x.amount || 0), 0);
  return (
    <div className="impact">
      <div><b>{money(dollars)}</b><span>Protected on hold</span></div>
      <div><b>{held.length}</b><span>Withdrawals held</span></div>
      <div><b>{released.length}</b><span>Released automatically</span></div>
      <div className="tested">Live tests, 3 runs × 6 scenarios: 9/9 scams held · 0 false positives · 10.9s average · ~3¢ per case</div>
    </div>
  );
}

export const fmtResponseAt = (r) => fmtAt(r.at);

const PARTY = {
  client: { label: "Client", color: "var(--color-neutral-600)" },
  third_party: { label: "Someone else", color: "var(--brand-orange)" },
  advisor: { label: "Advisor", color: "var(--risk-low)" },
};
const CHANNEL = { phone: "Phone", email: "Email", branch: "Branch", web_chat: "Web chat", web: "Web", juno: "Asked Juno in the app" };
const JUNO_VERDICT = { likely_scam: ["Juno: likely scam", "var(--risk-high)"], suspicious: ["Juno: suspicious", "var(--risk-medium)"], looks_safe: ["Juno: looks safe", "var(--risk-low)"] };

// What the firm already knew before this withdrawal: the contact log and the advisor's CRM notes.
// Contacts from someone other than the client are highlighted, since scams often run through them.
export function ClientHistory({ context }) {
  if (!context) return <div className="muted" style={{ fontSize: 14 }}>Loading history...</div>;
  const contacts = [...(context.contactLog || [])].sort((a, b) => b.at.localeCompare(a.at));
  const notes = [...(context.advisorNotes || [])].sort((a, b) => b.at.localeCompare(a.at));
  if (!contacts.length && !notes.length) return <div className="muted" style={{ fontSize: 14 }}>No recent contacts or notes on file</div>;
  return (
    <div className="history">
      {contacts.map((c, i) => {
        const p = PARTY[c.party] || PARTY.client;
        return (
          <div key={`c${i}`} className={`history-row${c.party === "third_party" ? " flagged" : ""}`}>
            <span className="history-dot" style={{ background: p.color }} />
            <div>
              <div className="history-meta">{fmtAt(c.at)} ET · {CHANNEL[c.channel] || c.channel} · <b>{c.who}</b>{c.party === "third_party" && <span className="history-tag">{p.label}</span>}{JUNO_VERDICT[c.verdict] && <span className="history-tag" style={{ background: JUNO_VERDICT[c.verdict][1] }}>{JUNO_VERDICT[c.verdict][0]}</span>}</div>
              <div>{c.summary}</div>
            </div>
          </div>
        );
      })}
      {notes.map((n, i) => (
        <div key={`n${i}`} className="history-row">
          <span className="history-dot" style={{ background: "var(--risk-low)" }} />
          <div>
            <div className="history-meta">{fmtAt(n.at)} ET · Advisor CRM note · <b>{n.by}</b></div>
            <div>{n.text}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
