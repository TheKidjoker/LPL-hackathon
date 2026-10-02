import { useState } from "react";
import { api, USING_MOCK } from "./api.js";
import ClientView from "./views/ClientView.jsx";
import AdvisorView from "./views/AdvisorView.jsx";
import FraudView from "./views/FraudView.jsx";

const ROLES = [
  { id: "client", label: "Client" },
  { id: "advisor", label: "Advisor" },
  { id: "fraud", label: "Fraud team" },
];

export default function App() {
  const [role, setRole] = useState("client");
  const [resetKey, setResetKey] = useState(0);

  async function resetDemo() {
    await api.resetDemo(role);
    setResetKey((k) => k + 1);
  }

  return (
    <div className="app">
      <header className="topbar">
        <strong>Speed Bump</strong>
        <nav className="roles">
          {ROLES.map((r) => (
            <button key={r.id} className={role === r.id ? "active" : ""} onClick={() => setRole(r.id)}>
              {r.label}
            </button>
          ))}
        </nav>
        <span className="muted">{USING_MOCK ? "Mock data" : "Live API"}</span>
        <button onClick={resetDemo}>Reset demo</button>
      </header>
      <main key={resetKey}>
        {role === "client" && <ClientView />}
        {role === "advisor" && <AdvisorView />}
        {role === "fraud" && <FraudView />}
      </main>
    </div>
  );
}
