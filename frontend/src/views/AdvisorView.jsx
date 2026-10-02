// TODO(Thomas): alert banner styling, only this advisor's clients
import { useState } from "react";
import { api } from "../api.js";
import CaseList from "./CaseList.jsx";
import { money, Responses, RiskPanel } from "./shared.jsx";

export default function AdvisorView() {
  const [caseData, setCaseData] = useState(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  const open = (id) => api.getCase("advisor", id).then(setCaseData).catch((e) => setError(e.message));

  async function addNote() {
    try {
      setCaseData(await api.postResponse("advisor", caseData.caseId, "note", note));
      setNote("");
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="split">
      <CaseList role="advisor" onSelect={open} selectedId={caseData?.caseId} />
      {caseData && (
        <div>
          <section className="card alert">
            {caseData.clientName} has a held withdrawal: {money(caseData.transaction.amount)} to {caseData.transaction.payee.name}
          </section>
          <RiskPanel risk={caseData.risk} />
          <section className="card">
            <h3>Notes</h3>
            <Responses responses={caseData.responses} />
            <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="What do you know? e.g. this isn't like her" />
            <button disabled={!note} onClick={addNote}>
              Add note
            </button>
          </section>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
