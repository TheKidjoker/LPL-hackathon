export const money = (n) => (n == null ? "" : n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }));

export function RiskPanel({ risk }) {
  if (!risk) return null;
  return (
    <section className="card">
      <h3>
        Risk {risk.score ?? "?"} <span className={`badge ${risk.level}`}>{risk.level}</span>
      </h3>
      <ul>
        {risk.signals.map((s) => (
          <li key={s.name}>
            <strong>{s.name.replaceAll("_", " ")}</strong>: {s.detail}
          </li>
        ))}
      </ul>
      <p className="memo">{risk.memo}</p>
    </section>
  );
}

export function Responses({ responses }) {
  if (!responses?.length) return <p className="muted">No responses yet.</p>;
  return (
    <ul>
      {responses.map((r) => (
        <li key={r.responseId}>
          <strong>{r.role}</strong> ({r.kind}): {r.text}
          {r.chatReply && <div className="muted">Assistant: {r.chatReply}</div>}
        </li>
      ))}
    </ul>
  );
}
