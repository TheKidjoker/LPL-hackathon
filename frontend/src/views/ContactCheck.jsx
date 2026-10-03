import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import accounts from "../../../data/accounts.json";

// "Is this a scam?": a client describes a call, text or email and Juno says whether it looks like
// a scam, before any money moves. Each check is saved to the client's contact log for staff.

const ROLE = "client";

const CHANNELS = [
  ["phone", "Phone call"],
  ["text", "Text"],
  ["email", "Email"],
  ["popup", "Pop-up"],
  ["social", "Social or dating site"],
  ["in_person", "In person"],
];

const EXAMPLES = [
  { channel: "phone", label: "\"Bank security\" call", text: "A man from the bank's security department called. He says my account was hacked and I need to move my money to a safe account today. He's still on the other line." },
  { channel: "text", label: "Grandson in trouble", text: "I got a text from my grandson. He says he's in jail and needs $5,000 in gift cards for bail, and asked me not to tell his parents." },
  { channel: "popup", label: "Virus pop-up", text: "A pop-up said my computer has a virus and to call Microsoft. The man on the phone wants to refund me $300 but needs to connect to my computer first." },
  { channel: "phone", label: "Advisor voicemail", text: "My advisor left a voicemail about our annual review and asked me to call back on the office number on my statement." },
];

const VERDICT = {
  likely_scam: { label: "This looks like a scam", color: "var(--risk-high)", bg: "var(--risk-high-bg)" },
  suspicious: { label: "Be careful with this", color: "var(--risk-medium)", bg: "var(--risk-medium-bg)" },
  looks_safe: { label: "This looks safe", color: "var(--risk-low)", bg: "var(--risk-low-bg)" },
};

const newCheckId = () => `chk-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;

export default function ContactCheck() {
  const [accountId, setAccountId] = useState("acc-1001");
  const [channel, setChannel] = useState("phone");
  const [checkId, setCheckId] = useState(newCheckId);
  const [turns, setTurns] = useState([]); // {role: "user"|"assistant", text, result?}
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const logRef = useRef(null);
  const account = accounts.find((a) => a.accountId === accountId);
  const last = [...turns].reverse().find((t) => t.result)?.result;
  const suggestions = last?.suggestions || [];

  useEffect(() => {
    logRef.current?.lastElementChild?.scrollIntoView({ block: "nearest" });
  }, [turns.length, busy]);

  function reset(nextAccount = accountId) {
    setAccountId(nextAccount);
    setTurns([]);
    setText("");
    setError("");
    setCheckId(newCheckId());
  }

  async function send(message, viaChannel = channel) {
    const clean = message.trim();
    if (!clean || busy) return;
    const next = [...turns, { role: "user", text: clean }];
    setTurns(next);
    setText("");
    setBusy(true);
    setError("");
    try {
      const result = await api.checkContact(ROLE, {
        accountId, checkId, channel: viaChannel,
        messages: next.map(({ role, text }) => ({ role, text })),
      });
      setTurns([...next, { role: "assistant", text: result.reply, result }]);
    } catch (e) {
      setError(e.message);
      setTurns(turns);
      setText(clean);
    } finally {
      setBusy(false);
    }
  }

  function tryExample(ex) {
    setChannel(ex.channel);
    send(ex.text, ex.channel);
  }

  return (
    <div className="chat">
      <aside>
        <div className="field">
          <label htmlFor="who">Demo client</label>
          <select id="who" className="input" value={accountId} onChange={(e) => reset(e.target.value)}>
            {accounts.map((a) => <option key={a.accountId} value={a.accountId}>{a.clientName}, {a.clientAge}</option>)}
          </select>
        </div>
        <div>
          <div className="kicker" style={{ marginBottom: 8 }}>How did they reach you?</div>
          <div className="chips">
            {CHANNELS.map(([id, label]) => (
              <button key={id} className={`btn ${channel === id ? "btn-primary" : "btn-secondary"}`} style={{ padding: "6px 10px", fontSize: 13 }} disabled={busy || turns.length > 0} onClick={() => setChannel(id)}>{label}</button>
            ))}
          </div>
        </div>
        <div style={{ height: 2, background: "var(--color-divider)" }} />
        <div style={{ fontSize: 14, lineHeight: 1.6 }}><b>We will never ask you to move money to keep it safe,</b> buy gift cards or crypto, share a code, or keep a secret from your family or advisor.</div>
        <div className="soft" style={{ fontSize: 13, lineHeight: 1.6 }}>
          {account?.advisor ? `Your advisor is ${account.advisor.name}. ` : ""}To check anything, hang up and call the number on your statement.
        </div>
        {turns.length > 0 && <button className="btn btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => reset()}>Check something else</button>}
      </aside>

      <div className="chat-main">
        <div className="chat-head">
          <div className="brand-mark" style={{ width: 28, height: 28, background: "var(--color-text)" }} />
          <div>
            <div className="big" style={{ fontSize: 15 }}>Is this a scam? Ask Juno</div>
            <div className="muted" style={{ fontSize: 12 }}>Tell us who contacted you and what they asked. Nothing moves from your account.</div>
          </div>
        </div>
        <div className="chat-log" ref={logRef} aria-live="polite">
          <div className="bubble-bot">Did someone call, text or email you about your money? Tell me what they said and I'll help you check it.</div>
          {turns.map((t, i) => t.role === "user"
            ? <div key={i} className="bubble-me">{t.text}</div>
            : <JunoAnswer key={i} result={t.result} />)}
          {busy && <div className="bubble-bot"><span className="typing"><i /><i /><i /></span></div>}
          {!turns.length && !busy && (
            <div className="contact-examples">
              <div className="muted" style={{ fontSize: 12 }}>Try an example</div>
              {EXAMPLES.map((ex) => <button key={ex.label} className="btn btn-secondary" onClick={() => tryExample(ex)}>{ex.label}</button>)}
            </div>
          )}
        </div>
        {error && <p className="error" style={{ paddingLeft: 32 }}>{error}</p>}
        <div className="chat-foot">
          {suggestions.map((s) => (
            <button key={s} className="btn btn-secondary" style={{ padding: "9px 14px", fontSize: 14 }} disabled={busy} onClick={() => send(s)}>{s}</button>
          ))}
          <form style={{ display: "flex", gap: 8, flex: "1 1 100%" }} onSubmit={(e) => { e.preventDefault(); send(text); }}>
            <input className="input" placeholder={turns.length ? "Add more detail or ask a question" : "What did they say or ask you to do?"} value={text} onChange={(e) => setText(e.target.value)} aria-label="Describe the contact" maxLength={2000} />
            <button className="btn btn-primary" disabled={busy || !text.trim()}>Check</button>
          </form>
        </div>
      </div>
    </div>
  );
}

function JunoAnswer({ result }) {
  const v = VERDICT[result.verdict];
  return (
    <div className="bubble-bot juno-answer" style={v ? { borderLeft: `4px solid ${v.color}` } : undefined}>
      {v && (
        <div className="verdict" style={{ background: v.bg }}>
          <span style={{ background: v.color }} />
          <b>{v.label}</b>{result.scamType && <em>{result.scamType}</em>}
        </div>
      )}
      <div>{result.reply}</div>
      {result.nextSteps?.length > 0 && (
        <ol className="next-steps">
          {result.nextSteps.map((s) => <li key={s}>{s}</li>)}
        </ol>
      )}
    </div>
  );
}
