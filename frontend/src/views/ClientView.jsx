// TODO(Thomas): scam warning signs, emergency contact form, scam-check chat for no-advisor clients
import { useState } from "react";
import { api } from "../api.js";
import { money, Responses } from "./shared.jsx";

const DEMO_REQUEST = {
  accountId: "acc-1001",
  amount: 180000,
  payee: { name: "CoinVault Exchange", type: "crypto_exchange", addedAt: "2026-10-02T12:01:00Z" },
  channel: "web",
  clientNote: "Moving funds to a safe account as instructed by bank security.",
};

export default function ClientView() {
  const [request, setRequest] = useState(DEMO_REQUEST);
  const [caseData, setCaseData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(fn) {
    setBusy(true);
    setError("");
    try {
      setCaseData(await fn());
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!caseData) {
    return (
      <section className="card">
        <h2>Withdraw funds</h2>
        <label>
          Amount
          <input type="number" value={request.amount} onChange={(e) => setRequest({ ...request, amount: Number(e.target.value) })} />
        </label>
        <label>
          Send to
          <input value={request.payee.name} onChange={(e) => setRequest({ ...request, payee: { ...request.payee, name: e.target.value } })} />
        </label>
        <label>
          Note
          <input value={request.clientNote} onChange={(e) => setRequest({ ...request, clientNote: e.target.value })} />
        </label>
        <button disabled={busy} onClick={() => run(() => api.submitWithdrawal("client", request))}>
          {busy ? "Reviewing..." : "Submit withdrawal"}
        </button>
        {error && <p className="error">{error}</p>}
      </section>
    );
  }

  const held = caseData.status === "HELD" || caseData.status === "EXTENDED";
  return (
    <section className="card">
      <h2>{held ? "We paused a withdrawal to protect you" : `Withdrawal ${caseData.status.toLowerCase()}`}</h2>
      <p>
        {money(caseData.transaction.amount)} to {caseData.transaction.payee.name}
        {held && ` is on hold until ${caseData.holdEndsAt}.`}
      </p>
      {held && (
        <>
          <p>Did you request this?</p>
          <button disabled={busy} onClick={() => run(() => api.postResponse("client", caseData.caseId, "confirm", "Yes, I requested this."))}>
            Yes, it was me
          </button>
          <button disabled={busy} onClick={() => run(() => api.postResponse("client", caseData.caseId, "deny", "No, I did not request this."))}>
            No, I did not
          </button>
        </>
      )}
      <h3>Your answers</h3>
      <Responses responses={caseData.responses} />
      {error && <p className="error">{error}</p>}
    </section>
  );
}
