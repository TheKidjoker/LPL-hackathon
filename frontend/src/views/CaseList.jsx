import { useEffect, useState } from "react";
import { api } from "../api.js";
import { money } from "./shared.jsx";

// Case queue for the advisor and fraud views. Calls onSelect(caseId).
export default function CaseList({ role, onSelect, selectedId }) {
  const [cases, setCases] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listCases(role).then((d) => setCases(d.cases)).catch((e) => setError(e.message));
  }, [role]);

  if (error) return <p className="error">{error}</p>;
  return (
    <ul className="caselist">
      {cases.map((c) => (
        <li key={c.caseId} className={c.caseId === selectedId ? "active" : ""} onClick={() => onSelect(c.caseId)}>
          <strong>{c.clientName}</strong> {money(c.amount)} to {c.payeeName}
          <div>
            <span className={`badge ${c.level}`}>{c.score}</span> {c.status}
          </div>
        </li>
      ))}
    </ul>
  );
}
