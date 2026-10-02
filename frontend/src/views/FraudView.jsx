import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import { advisorNotes, chatTurns, citations, clientAnswer, memoParagraphs, trustedContact } from "../lib/caseView.js";
import { countdown, fmtAt, fmtClock, fmtDay, holdEndMs, isOpen, money, riskOf } from "../lib/format.js";
import { LockIcon, RiskGauge, SparkIcon, StatusPill, useNow } from "../components/parts.jsx";
import { AlertsPanel, ChatTranscript, ClientHistory, ImpactStrip, SignalGroups } from "../components/caseParts.jsx";
import { LiveDot, usePolling, useToast } from "../components/live.jsx";
import Assistant from "../components/Assistant.jsx";

const ROLE = "fraud";
const DONE = { release: "Hold released. Funds will be sent.", extend: "Hold extended.", escalate: "Escalated to Fraud Investigations." };

export default function FraudView() {
  const [cases, setCases] = useState([]);
  const [selId, setSelId] = useState(null);
  const [c, setCase] = useState(null);
  const [context, setContext] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [releaseOpen, setReleaseOpen] = useState(false);
  const toast = useToast();

  const loadList = useCallback(async () => {
    try {
      const { cases } = await api.listCases(ROLE);
      setCases(cases);
      setSelId((id) => id || cases[0]?.caseId || null);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, []);

  // Queue and open case refresh every few seconds, so client answers and advisor notes appear live.
  usePolling(loadList, [loadList]);
  usePolling(() => selId && api.getCase(ROLE, selId).then(setCase).catch((e) => setError(e.message)), [selId]);
  useEffect(() => {
    setContext(null);
    if (selId) api.getContext(ROLE, selId).then(setContext).catch(() => setContext(null));
  }, [selId]);

  async function decide(action, note = "") {
    setBusy(true);
    setError("");
    try {
      setCase(await api.postDecision(ROLE, c.caseId, action, note));
      toast(DONE[action]);
      await loadList();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
      setReleaseOpen(false);
    }
  }

  const held = cases.filter((x) => isOpen(x.status) || x.status === "ESCALATED").length;

  return (
    <div className="fraud">
      <aside className="queue">
        <div className="queue-head">
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <h4><LiveDot />Case queue</h4>
            <span className="muted" style={{ fontSize: 12 }}>{held} held · {cases.length} open</span>
          </div>
          <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>Held first, then by risk score</div>
        </div>
        {cases.map((q) => {
          const r = riskOf(q.level);
          return (
            <button key={q.caseId} className={`queue-row${q.caseId === selId ? " on" : ""}`} onClick={() => setSelId(q.caseId)}>
              <div className="score-badge" style={{ background: r.bg, color: r.ink, borderTopColor: r.fg }}>
                <b>{q.score ?? "?"}</b>
                <span>{r.label}</span>
              </div>
              <div style={{ minWidth: 0 }}>
                <div className="queue-line">
                  <span style={{ fontWeight: q.caseId === selId ? 800 : 600 }}>{q.clientName}</span>
                  <span className="muted" style={{ fontSize: 11 }}>{fmtClock(q.createdAt)}</span>
                </div>
                <div className="queue-sub">{money(q.amount)} → {q.payeeName}</div>
                <div className="queue-tags"><StatusPill status={q.status} />{q.caseId}</div>
              </div>
            </button>
          );
        })}
      </aside>

      <main className="detail">
        <ImpactStrip cases={cases} />
        {error && <p className="error" style={{ padding: "12px 32px 0" }}>Could not refresh: {error}</p>}
        {!c ? (
          <div className="empty">{cases.length ? "Loading case..." : "No cases yet. Submit a withdrawal from the Client view."}</div>
        ) : (
          <CaseDetail c={c} context={context} busy={busy} onRelease={() => setReleaseOpen(true)} onDecide={decide} />
        )}
      </main>

      {releaseOpen && c && <ReleaseDialog c={c} busy={busy} onCancel={() => setReleaseOpen(false)} onConfirm={(reason) => decide("release", reason)} />}
    </div>
  );
}

function CaseDetail({ c, context, busy, onRelease, onDecide }) {
  const now = useNow();
  const open = isOpen(c.status);
  const end = holdEndMs(c.holdEndsAt);
  const start = Date.parse(c.createdAt);
  const pct = end ? Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100)) : 0;
  const answer = clientAnswer(c);
  const notes = advisorNotes(c);
  const memo = memoParagraphs(c.risk?.memo);
  const cites = citations(c.risk?.memo);
  const audit = [...(c.audit || [])].reverse();
  const txn = c.transaction;

  return (
    <>
      <div className="detail-head">
        <div>
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 6 }}>
            <span className="kicker">Case {c.caseId}</span>
            <StatusPill status={c.status} />
          </div>
          <h2>{c.clientName}</h2>
          <div className="soft" style={{ fontSize: 13, marginTop: 4 }}>Account {c.accountId} · Requested {fmtAt(c.createdAt)} ET</div>
        </div>
        <div className="actions">
          <div className="row">
            <button className="btn btn-secondary" disabled={!(open || c.status === "ESCALATED") || busy} onClick={onRelease}><LockIcon />Release</button>
            <button className="btn btn-secondary" disabled={c.status !== "HELD" || busy} onClick={() => onDecide("extend", "Hold extended for further review")}>Extend hold</button>
            <button className="btn btn-primary" disabled={!open || busy} onClick={() => onDecide("escalate", "Escalated to Fraud Investigations")}>Escalate</button>
          </div>
          <span className="muted" style={{ fontSize: 11 }}>Release is restricted to the Fraud team and requires a logged reason. Escalated cases can be released once investigations clears them</span>
        </div>
      </div>

      <div className="stats">
        <div className="stat">
          <span className="kicker">Risk score</span>
          <RiskGauge score={c.risk?.score} level={c.risk?.level} />
        </div>
        <div className="stat">
          <span className="kicker">Hold ends in</span>
          <div className="big" style={{ fontSize: "clamp(28px, 2.8vw, 44px)", marginTop: 18, whiteSpace: "nowrap" }}>
            {open && end ? countdown(end, now) : "—"}
          </div>
          <div className="soft" style={{ fontSize: 13, marginTop: 10 }}>
            {open && end ? `Ends ${fmtDay(c.holdEndsAt)}, 5:00 PM ET` : c.status === "RELEASED" ? "Hold released" : c.status === "ESCALATED" ? "Escalated, hold stays in place" : "No hold on this transaction"}
          </div>
          <div style={{ marginTop: "auto" }} />
          <div className="bar"><div style={{ width: `${open ? pct.toFixed(1) : 0}%` }} /></div>
          <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>
            {c.status === "EXTENDED" ? "Hold extended 10 business days" : "10 business days: within Rule 2165's 15-day limit for clients 65+; proposed Rule 2166 would allow 10 for any client"}
          </div>
        </div>
        <div className="stat" style={{ gap: 12 }}>
          <span className="kicker">Held transaction</span>
          <div className="big" style={{ fontSize: "clamp(28px, 2.6vw, 36px)" }}>{money(txn.amount)}</div>
          <div className="kv">
            <span>To</span><span style={{ fontWeight: 600 }}>{txn.payee?.name}</span>
            <span>Method</span><span>{txn.channel} · {txn.payee?.type?.replaceAll("_", " ")}</span>
            <span>Requested</span><span>{fmtAt(txn.timestamp)} ET</span>
            {txn.clientNote && <><span>Client note</span><span>“{txn.clientNote}”</span></>}
          </div>
        </div>
      </div>

      <div className="columns">
        <div className="col cell">
          <div className="kicker" style={{ marginBottom: 10 }}>Signals</div>
          <SignalGroups signals={c.risk?.signals} level={c.risk?.level} />
          <div className="memo-head">
            <SparkIcon />
            <span className="kicker">Juno case memo</span>
            <span className="muted" style={{ fontSize: 11, marginLeft: "auto" }}>Drafted {fmtAt(c.createdAt)} ET</span>
          </div>
          <div className="memo">{memo.map((p, i) => <p key={i}>{p}</p>)}</div>
          <div className="chips" style={{ marginTop: 4 }}>
            {cites.map((t) => <span key={t} className="tag tag-outline" style={{ color: "var(--color-accent-700)", borderColor: "var(--color-accent-700)" }}>{t}</span>)}
          </div>
        </div>
        <div className="col">
          <div className="cell">
            <div className="kicker" style={{ marginBottom: 8 }}>Client answer · "Did you request this?"</div>
            <div className="big" style={{ fontSize: 20, color: answer?.denied ? "var(--risk-high-ink)" : "var(--color-text)" }}>{answer ? answer.said : "Awaiting answer"}</div>
            <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
              {answer ? (answer.denied ? "Client denies making this request" : "Client says they made this request") : "Client was asked in the app"}
            </div>
          </div>
          <div className="cell">
            <div className="kicker" style={{ marginBottom: 8 }}>Advisor notes</div>
            {notes.length ? notes.map((n) => (
              <div key={n.responseId} className="note">{n.text}<div className="muted" style={{ fontSize: 11, marginTop: 2 }}>Advisor · {fmtAt(n.at)}</div></div>
            )) : <div className="muted" style={{ fontSize: 14 }}>No notes yet</div>}
          </div>
          {chatTurns(c).length > 0 && (
            <div className="cell">
              <div className="kicker" style={{ marginBottom: 8 }}>Scam-check chat with the client</div>
              <ChatTranscript c={c} />
            </div>
          )}
          <div className="cell">
            <div className="kicker" style={{ marginBottom: 8 }}>Who was alerted</div>
            <AlertsPanel c={c} context={context} />
          </div>
          <div className="cell">
            <div className="kicker" style={{ marginBottom: 8 }}>Trusted contact</div>
            <div style={{ fontSize: 14 }}>{trustedContact(c) || "None on file. Rule 2165 notice cannot be sent."}</div>
          </div>
        </div>
      </div>

      <div className="cell" style={{ borderBottom: "var(--rule)" }}>
        <div className="kicker" style={{ marginBottom: 12 }}>What the firm already knew · contact log and advisor notes</div>
        <ClientHistory context={context} />
      </div>

      <Assistant role="fraud" c={c} />

      <div style={{ padding: "24px 32px 40px", borderTop: "var(--rule)" }}>
        <div className="kicker" style={{ marginBottom: 14 }}>Audit timeline</div>
        {audit.map((a, i) => (
          <div key={i} className="timeline-row">
            <span className="muted">{fmtAt(a.timestamp)}</span>
            <div className="rail"><i style={{ background: a.action === "HELD" || a.action === "ESCALATED" ? "var(--brand-orange)" : a.action === "RELEASED" ? "var(--risk-low)" : a.action === "ASSISTANT_QUESTION" ? "var(--ai)" : "var(--color-text)" }} /><b /></div>
            <div><span style={{ fontWeight: 600 }}>{a.action}</span> <span className="soft">{a.actor}{a.detail ? ` · ${a.detail}` : ""}</span></div>
          </div>
        ))}
      </div>
    </>
  );
}

function ReleaseDialog({ c, busy, onCancel, onConfirm }) {
  const [reason, setReason] = useState("");
  return (
    <div className="dialog-backdrop" style={{ zIndex: 20 }} role="dialog" aria-modal="true">
      <div className="dialog">
        <div className="dialog-title">Release {money(c.transaction.amount)} to {c.transaction.payee?.name}?</div>
        <div className="dialog-body">The funds will be sent and cannot be recalled. Record why the firm no longer believes this is fraud.</div>
        <div className="field">
          <label htmlFor="reason">Reason for release (required)</label>
          <textarea id="reason" className="input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Verified with client by callback on number of record" />
        </div>
        <div className="dialog-actions">
          <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
          <button className="btn btn-primary" disabled={reason.trim().length < 8 || busy} onClick={() => onConfirm(reason.trim())}>Release funds</button>
        </div>
      </div>
    </div>
  );
}
