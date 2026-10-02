import { useState } from "react";
import { api, USING_MOCK } from "./api.js";
import ClientView from "./views/ClientView.jsx";
import AdvisorView from "./views/AdvisorView.jsx";
import FraudView from "./views/FraudView.jsx";

const ROLES = [
  { id: "client", label: "Client", viewer: "Signed in as a client" },
  { id: "advisor", label: "Advisor", viewer: "Advisor" },
  { id: "fraud", label: "Fraud team", viewer: "Fraud operations" },
];

export default function App() {
  const [role, setRole] = useState("fraud");
  const [resetKey, setResetKey] = useState(0);
  // The client's most recent case, so the scam check and other views can follow it.
  const [clientCaseId, setClientCaseId] = useState(null);

  async function resetDemo() {
    await api.resetDemo(role);
    setClientCaseId(null);
    setResetKey((k) => k + 1);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" />
          <span className="brand-name">Speed Bump</span>
          <span className="brand-firm">Halden Private Wealth</span>
        </div>
        <div className="role-switch">
          <span className="kicker">View as</span>
          <div className="roles">
            {ROLES.map((r) => (
              <button key={r.id} className={role === r.id ? "on" : ""} onClick={() => setRole(r.id)}>
                {r.label}
              </button>
            ))}
          </div>
        </div>
        <div className="viewer">
          <span>{ROLES.find((r) => r.id === role).viewer}</span>
          <span className="source-tag">{USING_MOCK ? "Mock data" : "Live API"}</span>
          <button className="btn btn-secondary" onClick={resetDemo}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
            Reset demo
          </button>
        </div>
      </header>
      <div key={resetKey}>
        {role === "client" && <ClientView caseId={clientCaseId} onCase={setClientCaseId} />}
        {role === "advisor" && <AdvisorView />}
        {role === "fraud" && <FraudView />}
      </div>
    </div>
  );
}
