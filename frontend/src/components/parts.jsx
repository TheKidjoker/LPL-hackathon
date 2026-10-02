import { useEffect, useState } from "react";
import { riskOf, signalLabel, statusOf } from "../lib/format.js";

export function useNow(ms = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(t);
  }, [ms]);
  return now;
}

export const StatusPill = ({ status }) => {
  const s = statusOf(status);
  return <span className="pill" style={{ background: s.bg, color: s.ink }}>{s.label}</span>;
};

export const LevelPill = ({ level, suffix = " risk" }) => {
  const r = riskOf(level);
  return <span className="level-pill" style={{ background: r.bg, color: r.ink }}>{r.label}{level === "unknown" ? "" : suffix}</span>;
};

export function SignalChips({ signals, level }) {
  const r = riskOf(level);
  return (
    <div className="chips">
      {(signals || []).map((s) => (
        <span key={s.name} className="chip" style={{ background: r.bg, color: r.ink }} title={s.detail}>
          <i style={{ background: r.fg }} />
          <span><b style={{ fontWeight: 600 }}>{signalLabel(s)}</b> · {s.detail}</span>
        </span>
      ))}
    </div>
  );
}

// Semicircle gauge from the design: green, amber, red bands with a filled arc for the score.
export function RiskGauge({ score, level }) {
  const r = riskOf(level);
  const dash = `${(((score ?? 0) / 100) * 282.7).toFixed(1)} 400`;
  return (
    <div>
      <div style={{ position: "relative", width: 240, maxWidth: "100%", marginTop: 10 }}>
        <svg viewBox="0 0 220 112" style={{ width: "100%", display: "block" }} role="img" aria-label={`Risk score ${score ?? "unknown"} of 100`}>
          <path d="M6 110 A104 104 0 0 1 77.9 11.1" fill="none" stroke="var(--risk-low)" strokeWidth="4" />
          <path d="M77.9 11.1 A104 104 0 0 1 171.2 25.9" fill="none" stroke="var(--risk-medium)" strokeWidth="4" />
          <path d="M171.2 25.9 A104 104 0 0 1 214 110" fill="none" stroke="var(--risk-high)" strokeWidth="4" />
          <path d="M20 110 A90 90 0 0 1 200 110" fill="none" stroke="var(--color-neutral-300)" strokeWidth="18" />
          <path d="M20 110 A90 90 0 0 1 200 110" fill="none" stroke={r.fg} strokeWidth="18" strokeDasharray={dash} />
        </svg>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 2, textAlign: "center" }}>
          <span className="big" style={{ fontSize: 40, letterSpacing: "-0.03em" }}>{score ?? "?"}</span>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: 240, maxWidth: "100%", fontSize: 11, marginTop: 6 }} className="muted">
        <span>0</span>
        <LevelPill level={level} />
        <span>100</span>
      </div>
    </div>
  );
}

export const SparkIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="var(--brand-orange)" strokeWidth="2" aria-hidden="true">
    <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
  </svg>
);

export const LockIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <rect width="18" height="11" x="3" y="11" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

export const ShieldIcon = ({ check = false, size = 16, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" aria-hidden="true" style={{ flex: "none" }}>
    <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    {check ? <path d="m9 12 2 2 4-4" /> : <><path d="M12 8v4" /><path d="M12 16h.01" /></>}
  </svg>
);

export const PhoneIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
  </svg>
);
