// TODO(Thomas): hold countdown timer, audit timeline styling
import { useState } from "react";
import { api } from "../api.js";
import CaseList from "./CaseList.jsx";
import { money, Responses, RiskPanel } from "./shared.jsx";

export default function FraudView() {
  const [caseData, setCaseData] = useState(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  const open = (id) => api.getCase("fraud", id).then(setCaseData).catch((e) => setError(e.message));

  async function decide(action) {
    try {
      setCaseData(await api.postDecision("fraud", caseData.caseId, action, note));
      setNote("");
    } catch (e) {
      setError(e.message);
    }
  }

  const canDecide = caseData && (caseData.status === "HELD" || caseData.status === "EXTENDED");
  return (
    <div className="split">
      <CaseList role="fraud" onSelect={open} selectedId={caseData?.caseId} />
      {caseData && (
        <div>
          <section className="card">
            <h2>
              {caseData.clientName}: {money(caseData.transaction.amount)} to {caseData.transaction.payee.name}
            </h2>
            <p>
              Status {caseData.status}
              {caseData.holdEndsAt && `, hold ends ${caseData.holdEndsAt}`}
            </p>
          </section>
          <RiskPanel risk={caseData.risk} />
          <section className="card">
            <h3>Client and advisor</h3>
            <Responses responses={caseData.responses} />
          </section>
          <section className="card">
            <h3>Decision</h3>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Reason" />
            <button disabled={!canDecide} onClick={() => decide("release")}>Release</button>
            <button disabled={!canDecide || caseData.status === "EXTENDED"} onClick={() => decide("extend")}>Extend</button>
            <button disabled={!canDecide} onClick={() => decide("escalate")}>Escalate</button>
          </section>
          <section className="card">
            <h3>Audit log</h3>
            <ul>
              {caseData.audit.map((a) => (
                <li key={a.timestamp + a.action}>
                  {a.timestamp} {a.actor}: {a.action} {a.detail}
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
