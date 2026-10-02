import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const STARTERS = {
  fraud: ["Why was this held?", "What should I verify before releasing?", "Summarize the evidence for my notes"],
  advisor: ["What should I ask the client on the call?", "Explain the risk in plain English", "What happens next with this hold?"],
};

// "Ask Claude about this case": a grounded Q&A for the fraud team and advisors.
// Answers come only from this case's data; every question is written to the audit log.
export default function Assistant({ role, c }) {
  const [messages, setMessages] = useState([]);
  const [suggestions, setSuggestions] = useState(STARTERS[role]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const logRef = useRef(null);

  // A new case starts a new conversation.
  useEffect(() => {
    setMessages([]);
    setSuggestions(STARTERS[role]);
    setError("");
  }, [c.caseId, role]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, busy]);

  async function ask(question) {
    const q = question.trim();
    if (!q || busy) return;
    const next = [...messages, { role: "user", text: q }];
    setMessages(next);
    setText("");
    setBusy(true);
    setError("");
    try {
      const { reply, suggestions } = await api.askAssistant(role, c.caseId, next);
      setMessages([...next, { role: "assistant", text: reply }]);
      if (suggestions?.length) setSuggestions(suggestions);
    } catch (e) {
      setError(e.message);
      setMessages(messages);
      setText(q);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="assistant" aria-label="Ask Claude about this case">
      <div className="assistant-head">
        <span className="ai-mark">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ai)" strokeWidth="2" aria-hidden="true">
            <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
          </svg>
        </span>
        <div>
          <div style={{ fontWeight: 800, fontSize: 15 }}>Ask Claude about {c.clientName || "this case"}</div>
          <div className="muted" style={{ fontSize: 12 }}>Answers only from this case's data · every question is logged to the audit trail · Claude never decides a hold</div>
        </div>
      </div>
      {(messages.length > 0 || busy) && (
        <div className="assistant-log" ref={logRef}>
          {messages.map((m, i) => <div key={i} className={m.role === "user" ? "from-me" : "from-ai"}>{m.text}</div>)}
          {busy && <div className="from-ai"><span className="typing"><i /><i /><i /></span></div>}
        </div>
      )}
      <div className="assistant-foot" style={messages.length || busy ? undefined : { paddingTop: 16 }}>
        {error && <div className="error">{error}</div>}
        <div className="suggest">
          {suggestions.map((s) => <button key={s} className="btn btn-secondary" disabled={busy} onClick={() => ask(s)}>{s}</button>)}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); ask(text); }}>
          <input className="input" placeholder={role === "fraud" ? "Ask about this client, the signals, or what to check next" : "Ask about your client's held withdrawal"} value={text} onChange={(e) => setText(e.target.value)} aria-label="Question for Claude" maxLength={2000} />
          <button className="btn btn-primary" disabled={busy || !text.trim()}>Ask</button>
        </form>
      </div>
    </section>
  );
}
