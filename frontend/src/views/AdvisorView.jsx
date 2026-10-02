import { useState } from "react";
import { api } from "../api.js";
import { advisorNotes, clientAnswer, memoParagraphs } from "../lib/caseView.js";
import { fmtAt, fmtDay, isOpen, money, riskOf } from "../lib/format.js";
import { LevelPill, LockIcon, PhoneIcon, ShieldIcon, SparkIcon, StatusPill } from "../components/parts.jsx";
import { SignalGroups } from "../components/caseParts.jsx";
import { usePolling, useToast } from "../components/live.jsx";
import Assistant from "../components/Assistant.jsx";

const ROLE = "advisor";

export default function AdvisorView() {
  const [cases, setCases] = useState([]);
  const [selId, setSelId] = useState(null);
  const [c, setCase] = useState(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  // Refresh every few seconds so a new hold or the client's answer shows up without reloading.
  usePolling(() =>
    api.listCases(ROLE)
      .then(({ cases }) => {
        setCases(cases);
        setSelId((id) => id || cases.find((x) => isOpen(x.status))?.caseId || cases[0]?.caseId || null);
      })
      .catch((e) => setError(e.message)), []);
  usePolling(() => selId && api.getCase(ROLE, selId).then(setCase).catch((e) => setError(e.message)), [selId]);

  async function saveNote() {
    setSaving(true);
    setError("");
    try {
      setCase(await api.postResponse(ROLE, c.caseId, "note", draft.trim()));
      setDraft("");
      toast("Note saved. The Fraud team can see it now.");
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (!c) return <div className="page muted">{error || (cases.length ? "Loading case..." : "No held withdrawals for your clients.")}</div>;

  const risk = c.risk || {};
  const r = riskOf(risk.level);
  const open = isOpen(c.status);
  const answer = clientAnswer(c);
  const notes = advisorNotes(c);
  const markerLeft = Math.min(99, Math.max(0, risk.score ?? 0));

  return (
    <div className="page">
      {cases.length > 1 && (
        <div className="case-picker">
          {cases.map((x) => (
            <button key={x.caseId} className={`btn ${x.caseId === selId ? "btn-primary" : "btn-secondary"}`} onClick={() => setSelId(x.caseId)}>
              {x.clientName} · {money(x.amount)}
            </button>
          ))}
        </div>
      )}

      <div className="banner">
        <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
          <ShieldIcon size={22} color="var(--brand-orange)" />
          <div>
            <h3>{open ? `${c.clientName} has a held withdrawal` : `${c.clientName}'s withdrawal`}</h3>
            <p>
              {money(c.transaction.amount)} to {c.transaction.payee?.name}
              {open ? ` · on hold until ${fmtDay(c.holdEndsAt)} · score ${risk.score ?? "?"}, ${r.label.toLowerCase()}` : ` · ${c.status.toLowerCase()} by the Fraud team`}
            </p>
          </div>
        </div>
        <button className="btn btn-primary"><PhoneIcon />Call client · number on file</button>
      </div>

      <div className="split">
        <div className="left">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <SparkIcon />
            <span className="kicker">AI risk summary</span>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 20 }}>
            <span className="big" style={{ fontSize: 72, lineHeight: 0.85, letterSpacing: "-0.03em", color: r.fg }}>{risk.score ?? "?"}</span>
            <div style={{ flex: 1, paddingBottom: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <LevelPill level={risk.level} />
                <span className="muted" style={{ fontSize: 12 }}>of 100</span>
              </div>
              <div className="scale">
                <div style={{ background: "var(--risk-low)" }} />
                <div style={{ background: "var(--risk-medium)" }} />
                <div style={{ background: "var(--risk-high)" }} />
                <div className="scale-marker" style={{ left: `${markerLeft}%` }} />
              </div>
              <div className="scale-labels"><span>Low</span><span>Medium</span><span>High</span></div>
            </div>
          </div>
          <div style={{ marginTop: 24 }}><SignalGroups signals={risk.signals} level={risk.level} /></div>
          <div className="divider" />
          <div className="kicker" style={{ marginBottom: 10 }}>AI memo</div>
          <div className="memo" style={{ fontSize: 15, lineHeight: 1.65 }}>
            {memoParagraphs(risk.memo).map((p, i) => <p key={i}>{p}</p>)}
          </div>
          <div className="muted" style={{ fontSize: 11, marginTop: 12 }}>Drafted by Claude · {fmtAt(c.createdAt)} ET · Review before acting</div>
        </div>

        <div className="right">
          <div>
            <div className="kicker" style={{ marginBottom: 10 }}>Client</div>
            <div className="kv" style={{ gridTemplateColumns: "110px minmax(0, 1fr)", rowGap: 6, fontSize: 14 }}>
              <span>Account</span><span>{c.accountId}</span>
              <span>Status</span><span><StatusPill status={c.status} /></span>
              <span>Hold ends</span><span style={{ fontWeight: 600 }}>{open ? fmtDay(c.holdEndsAt) : "—"}</span>
              <span>Client answer</span>
              <span style={{ fontWeight: 600, color: answer?.denied ? "var(--risk-high-ink)" : "var(--color-text)" }}>{answer ? answer.said : "Awaiting answer"}</span>
            </div>
          </div>
          <div>
            <div className="field">
              <label htmlFor="advisor-note">Notes for the Fraud team</label>
              <textarea id="advisor-note" className="input" placeholder={`What you learned from talking with ${c.clientName.split(" ")[0]}`} value={draft} onChange={(e) => setDraft(e.target.value)} />
            </div>
            <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 10 }}>
              <button className="btn btn-secondary" onClick={saveNote} disabled={!draft.trim() || saving}>{saving ? "Saving..." : "Save note"}</button>
              <span className="muted" style={{ fontSize: 12 }}>Visible to the Fraud team</span>
            </div>
            {error && <p className="error">{error}</p>}
            {notes.map((n) => (
              <div key={n.responseId} style={{ fontSize: 13, lineHeight: 1.5, marginTop: 14, paddingTop: 12, borderTop: "var(--hair)" }}>
                {n.text}<div className="muted" style={{ fontSize: 11, marginTop: 2 }}>You · {fmtAt(n.at)}</div>
              </div>
            ))}
          </div>
          <div>
            <button className="btn btn-secondary" disabled><LockIcon />Release hold</button>
            <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>Only the Fraud team can release a hold. Your notes go into their review.</div>
          </div>
        </div>
      </div>
      <div style={{ marginTop: 28, border: "var(--rule)" }}>
        <Assistant role="advisor" c={c} />
      </div>
    </div>
  );
}
