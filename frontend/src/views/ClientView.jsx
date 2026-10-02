import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { chatTurns, clientAnswer, trustedContact } from "../lib/caseView.js";
import { fmtDay, isOpen, money } from "../lib/format.js";
import { PhoneIcon, ShieldIcon } from "../components/parts.jsx";

const ROLE = "client";

const DEMO_REQUEST = {
  accountId: "acc-1001",
  amount: 180000,
  payee: { name: "CoinVault Exchange", type: "crypto_exchange", addedAt: "2026-10-02T12:01:00Z" },
  channel: "web",
  clientNote: "Moving funds to a safe account as instructed by bank security.",
};

const REVIEW_STEPS = ["Verifying the payee", "Checking recent account activity", "Comparing with your usual patterns"];

const WARNING_SIGNS = [
  "Someone called saying they are from your bank or our firm's security team",
  "You were told your account was hacked and your money must be moved to keep it safe",
  "You were asked to buy crypto, gold or gift cards",
  "You were told to keep this secret, even from family or your advisor",
  "You feel pressure to act today, or someone is still on the phone with you",
];

export default function ClientView({ caseId, onCase }) {
  const [tab, setTab] = useState("withdraw");
  const [c, setCase] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (caseId) api.getCase(ROLE, caseId).then(setCase).catch((e) => setError(e.message));
  }, [caseId]);

  const update = (next) => {
    setCase(next);
    onCase(next.caseId);
  };

  return (
    <div className="page" style={{ maxWidth: 1200, paddingTop: 28, paddingBottom: 56 }}>
      <div className="tabs">
        <button className={tab === "withdraw" ? "on" : ""} onClick={() => setTab("withdraw")}>Withdraw funds</button>
        <button className={tab === "chat" ? "on" : ""} onClick={() => setTab("chat")}>Scam check · client with no advisor</button>
      </div>
      {error && <p className="error">{error}</p>}
      {tab === "withdraw" ? (
        <div className="client">
          <div className="main">
            {c ? <Outcome c={c} onUpdate={update} setError={setError} /> : <WithdrawForm onDone={update} setError={setError} />}
          </div>
          <SidePanel />
        </div>
      ) : (
        <ScamCheck c={c} onUpdate={update} goWithdraw={() => setTab("withdraw")} setError={setError} />
      )}
    </div>
  );
}

function WithdrawForm({ onDone, setError }) {
  const [form, setForm] = useState({ amount: money(DEMO_REQUEST.amount, true), payee: DEMO_REQUEST.payee.name, note: DEMO_REQUEST.clientNote });
  const [stepIdx, setStepIdx] = useState(-1);

  async function submit() {
    setError("");
    setStepIdx(0);
    // Real scoring takes about 10 seconds; walk the steps while it runs.
    const timers = [1, 2].map((i) => setTimeout(() => setStepIdx(i), i * 3000));
    try {
      const amount = Number(String(form.amount).replace(/[^0-9.]/g, ""));
      const result = await api.submitWithdrawal(ROLE, {
        ...DEMO_REQUEST,
        amount,
        // The demo payee was "added" two hours before submit, so payee_added_recently fires on any day.
        payee: { ...DEMO_REQUEST.payee, name: form.payee, addedAt: new Date(Date.now() - 2 * 3600e3).toISOString().replace(/\.\d+Z$/, "Z") },
        clientNote: form.note,
      });
      setStepIdx(3);
      setTimeout(() => onDone(result), 400);
    } catch (e) {
      setError(e.message);
      setStepIdx(-1);
    } finally {
      timers.forEach(clearTimeout);
    }
  }

  if (stepIdx >= 0) {
    return (
      <>
        <h2>Reviewing your request…</h2>
        <p className="soft">This usually takes a few seconds. Please keep this page open.</p>
        <div style={{ height: 4, background: "var(--color-neutral-300)", margin: "28px 0 8px", maxWidth: 520 }}>
          <div style={{ height: 4, background: "var(--color-text)", width: `${Math.round(((stepIdx + 1) / 4) * 100)}%`, transition: "width 0.6s" }} />
        </div>
        <div style={{ maxWidth: 520, borderTop: "var(--rule)", marginTop: 20 }}>
          {REVIEW_STEPS.map((t, i) => (
            <div key={t} className="review-step" style={{ color: i <= stepIdx ? "var(--color-text)" : "var(--color-neutral-500)" }}>
              <span style={{ background: i < stepIdx ? "var(--color-text)" : "transparent" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-bg)" strokeWidth="3" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
              </span>
              {t}
            </div>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <h2>Withdraw funds</h2>
      <p className="soft">From Brokerage {DEMO_REQUEST.accountId} · Available {money(DEMO_REQUEST.amount, true)}</p>
      <div className="form">
        <div className="field">
          <label htmlFor="amount">Amount</label>
          <input id="amount" className="input" style={{ fontSize: 22, fontWeight: 800, minHeight: 52 }} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="payee">Payee</label>
          <input id="payee" className="input" value={form.payee} onChange={(e) => setForm({ ...form, payee: e.target.value })} />
          <div style={{ display: "flex", gap: 8, marginTop: 6, alignItems: "center" }}>
            <span className="tag tag-neutral">New payee</span>
            <span className="muted" style={{ fontSize: 12 }}>Added today</span>
          </div>
        </div>
        <div className="field">
          <label htmlFor="note">Note (optional)</label>
          <textarea id="note" className="input" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        </div>
        <div className="soft" style={{ fontSize: 13 }}>Wire transfer · usually arrives in 1 business day</div>
        <div>
          <button className="btn btn-primary" style={{ minWidth: 220, justifyContent: "flex-start", padding: "12px 16px", fontSize: 15 }} onClick={submit}>
            Submit withdrawal
          </button>
        </div>
      </div>
    </>
  );
}

function Outcome({ c, onUpdate, setError }) {
  const [contact, setContact] = useState({ name: "", phone: "" });
  const [busy, setBusy] = useState(false);
  const answer = clientAnswer(c);
  const savedContact = trustedContact(c);
  const held = isOpen(c.status) || c.status === "ESCALATED";
  const txn = c.transaction;

  async function respond(kind, text) {
    setBusy(true);
    setError("");
    try {
      onUpdate(await api.postResponse(ROLE, c.caseId, kind, text));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!held) {
    return (
      <>
        <h2>Your withdrawal is on its way</h2>
        <p className="soft" style={{ fontSize: 16 }}>{money(txn.amount, true)} to {txn.payee?.name}. Wire transfers usually arrive in 1 business day.</p>
      </>
    );
  }

  return (
    <>
      <div className="kicker" style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12, fontSize: 12 }}>
        <ShieldIcon check />Your money is safe in your account
      </div>
      <h1 style={{ maxWidth: "16ch", fontSize: 44 }}>We paused this withdrawal to protect you</h1>
      <p className="soft" style={{ fontSize: 16, lineHeight: 1.6, maxWidth: "58ch", marginTop: 12 }}>
        Nothing has left your account. We hold large transfers to new payees when they look like patterns we see in scams, so you have time to check with someone you trust.
      </p>
      <div className="facts">
        <div><div className="muted" style={{ fontSize: 12 }}>Amount</div><div className="big" style={{ fontSize: 26 }}>{money(txn.amount, true)}</div></div>
        <div><div className="muted" style={{ fontSize: 12 }}>To</div><div className="big" style={{ fontSize: 20, marginTop: 4 }}>{txn.payee?.name}</div></div>
        <div><div className="muted" style={{ fontSize: 12 }}>On hold until</div><div className="big" style={{ fontSize: 20, marginTop: 4 }}>{fmtDay(c.holdEndsAt) || "Under review"}</div></div>
      </div>

      <h3>Did you request this?</h3>
      {!answer ? (
        <div style={{ display: "flex", gap: 12, marginTop: 14, flexWrap: "wrap" }}>
          <button className="btn btn-secondary" disabled={busy} style={{ minWidth: 200, justifyContent: "flex-start", padding: "14px 16px", fontSize: 15 }} onClick={() => respond("confirm", "Yes, I requested this.")}>Yes, it was me</button>
          <button className="btn btn-secondary" disabled={busy} style={{ minWidth: 200, justifyContent: "flex-start", padding: "14px 16px", fontSize: 15 }} onClick={() => respond("deny", "No, I did not request this.")}>No, I did not</button>
        </div>
      ) : answer.denied ? (
        <div className="callout">
          <b>Thank you. You did the right thing.</b>
          <p>This withdrawal will not be sent. Our Fraud team will call you within the hour on the number we have on file. If someone is on the phone with you now, it is safe to hang up.</p>
        </div>
      ) : (
        <div className="callout">
          <b>Thanks for confirming.</b>
          <p>The hold stays in place until {fmtDay(c.holdEndsAt)} while we review it with you. Your advisor will call to talk it through. You can still cancel at any time.</p>
        </div>
      )}

      <div className="divider" style={{ margin: "36px 0 20px" }} />
      <h6 style={{ marginBottom: 6 }}>Common signs of a scam</h6>
      <div style={{ maxWidth: 620 }}>
        {WARNING_SIGNS.map((t, i) => (
          <div key={t} className="warn-row"><b>{String(i + 1).padStart(2, "0")}</b><span>{t}</span></div>
        ))}
      </div>

      <div className="divider" style={{ margin: "36px 0 20px" }} />
      <h4>Add an emergency contact</h4>
      <p className="soft" style={{ fontSize: 14, maxWidth: "58ch" }}>Someone we can call if we are worried about your account. They cannot see your balance or move money.</p>
      {savedContact ? (
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 12, fontSize: 15 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--risk-low-ink)" strokeWidth="2.5" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
          <span><b>{savedContact}</b> added as your emergency contact</span>
        </div>
      ) : (
        <div className="contact-form">
          <div className="field">
            <label htmlFor="cname">Name and relationship</label>
            <input id="cname" className="input" placeholder="Susan Ellis, daughter" value={contact.name} onChange={(e) => setContact({ ...contact, name: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="cphone">Phone</label>
            <input id="cphone" className="input" placeholder="(555) 555-0100" value={contact.phone} onChange={(e) => setContact({ ...contact, phone: e.target.value })} />
          </div>
          <button
            className="btn btn-primary"
            style={{ minHeight: 36 }}
            disabled={busy || !contact.name.trim() || contact.phone.replace(/\D/g, "").length < 7}
            onClick={() => respond("emergency_contact", `${contact.name.trim()} · ${contact.phone.trim()}`)}
          >
            Add contact
          </button>
        </div>
      )}
    </>
  );
}

function SidePanel() {
  return (
    <aside>
      <div>
        <div className="kicker" style={{ marginBottom: 8 }}>Your advisor</div>
        <div className="big" style={{ fontSize: 18 }}>Call the number on your statement</div>
        <div className="soft" style={{ fontSize: 14, marginTop: 4 }}>Mon–Fri, 8–6 ET</div>
      </div>
      <div style={{ height: 2, background: "var(--color-divider)" }} />
      <div style={{ fontSize: 14, lineHeight: 1.6 }}><b>We will never ask you to move money to keep it safe.</b> Not by phone, text or email. If someone does, it is a scam.</div>
      <div style={{ height: 2, background: "var(--color-divider)" }} />
      <div className="soft" style={{ fontSize: 13, lineHeight: 1.6 }}>Holds follow FINRA Rule 2165, which lets firms pause disbursements for clients 65 and older when they suspect financial exploitation.</div>
    </aside>
  );
}

const FIRST_REPLIES = ["Yes, someone called me", "Yes, by text or email", "No, this was my idea"];
const LATER_REPLIES = ["Yes", "No", "I'm not sure"];

function ScamCheck({ c, onUpdate, goWithdraw, setError }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef(null);
  const turns = c ? chatTurns(c) : [];
  const done = turns.length > 0 && turns[turns.length - 1].done;

  useEffect(() => {
    logRef.current?.lastElementChild?.scrollIntoView({ block: "nearest" });
  }, [turns.length]);

  if (!c) {
    return (
      <div className="empty" style={{ paddingLeft: 0 }}>
        <p>The scam check runs on a held withdrawal.</p>
        <button className="btn btn-primary" onClick={goWithdraw}>Start a withdrawal</button>
      </div>
    );
  }

  async function send(answer) {
    if (!answer.trim()) return;
    setBusy(true);
    setError("");
    try {
      onUpdate(await api.postResponse(ROLE, c.caseId, "chat", answer.trim()));
      setText("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const txn = c.transaction;
  return (
    <div className="chat">
      <aside>
        <span className="kicker">Transfer waiting for a check</span>
        <div className="big" style={{ fontSize: 34 }}>{money(txn.amount, true)}</div>
        <div className="kv" style={{ gridTemplateColumns: "70px minmax(0, 1fr)", rowGap: 6, fontSize: 14 }}>
          <span>To</span><span style={{ fontWeight: 600 }}>{txn.payee?.name}</span>
          <span>Case</span><span>{c.caseId}</span>
        </div>
        <div style={{ height: 2, background: "var(--color-divider)" }} />
        <div className="soft" style={{ fontSize: 13, lineHeight: 1.6 }}>
          Your account has no assigned advisor, so Second Look asks a few questions before large first-time transfers. A person reviews every answer.
        </div>
      </aside>
      <div className="chat-main">
        <div className="chat-head">
          <div className="brand-mark" style={{ width: 28, height: 28, background: "var(--color-text)" }} />
          <div>
            <div className="big" style={{ fontSize: 15 }}>Second Look scam check</div>
            <div className="muted" style={{ fontSize: 12 }}>Automated assistant · a specialist is one tap away</div>
          </div>
        </div>
        <div className="chat-log" ref={logRef} aria-live="polite">
          <div className="bubble-bot">Your {money(txn.amount)} transfer to {txn.payee?.name} is waiting for a quick safety check. A few questions, about a minute.</div>
          <div className="bubble-bot">
            <div style={{ fontWeight: 800, fontSize: 17 }}>Did someone contact you first?</div>
            <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>A call, text, email or pop-up all count.</div>
          </div>
          {turns.map((t) => (
            <div key={t.responseId} style={{ display: "contents" }}>
              <div className="bubble-me">{t.text}</div>
              {t.chatReply && <div className="bubble-bot" style={t.done ? { fontWeight: 800 } : undefined}>{t.chatReply}</div>}
            </div>
          ))}
          {busy && <div className="bubble-bot muted">…</div>}
        </div>
        <div className="chat-foot">
          {done ? (
            <>
              <button className="btn btn-primary" style={{ padding: "11px 16px", fontSize: 14 }}><PhoneIcon />Talk to a fraud specialist</button>
              <button className="btn btn-secondary" style={{ padding: "11px 16px", fontSize: 14 }}>Cancel this transfer</button>
            </>
          ) : (
            <>
              {(turns.length ? LATER_REPLIES : FIRST_REPLIES).map((label) => (
                <button key={label} className="btn btn-secondary" style={{ padding: "11px 16px", fontSize: 14 }} disabled={busy} onClick={() => send(label)}>{label}</button>
              ))}
              <form style={{ display: "flex", gap: 8, flex: "1 1 260px" }} onSubmit={(e) => { e.preventDefault(); send(text); }}>
                <input className="input" placeholder="Or type your answer" value={text} onChange={(e) => setText(e.target.value)} aria-label="Your answer" />
                <button className="btn btn-secondary" disabled={busy || !text.trim()}>Send</button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
