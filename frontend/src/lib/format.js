// Formatting and display rules shared by every view. Times show in US Eastern.

const TZ = "America/New_York";

export const money = (n, cents = false) =>
  n == null ? "" : n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: cents ? 2 : 0, minimumFractionDigits: cents ? 2 : 0 });

const part = (iso, opts) => new Date(iso).toLocaleString("en-US", { timeZone: TZ, ...opts });
export const fmtAt = (iso) => (iso ? `${part(iso, { month: "short", day: "numeric" })} · ${part(iso, { hour: "2-digit", minute: "2-digit", hour12: false })}` : "");
export const fmtClock = (iso) => (iso ? part(iso, { hour: "2-digit", minute: "2-digit", hour12: false }) : "");

// holdEndsAt is a date ("2026-10-16"); a hold ends at 5:00 PM Eastern that day.
export const holdEndMs = (date) => (date ? Date.parse(`${date}T21:00:00Z`) : null);
export const fmtDay = (date) =>
  date ? new Date(`${date}T16:00:00Z`).toLocaleDateString("en-US", { timeZone: TZ, weekday: "long", month: "long", day: "numeric" }) : "";

export function countdown(endMs, now) {
  const r = Math.max(0, endMs - now) / 1000;
  const p2 = (n) => String(Math.floor(n)).padStart(2, "0");
  return `${Math.floor(r / 86400)}d ${p2((r % 86400) / 3600)}:${p2((r % 3600) / 60)}:${p2(r % 60)}`;
}

export const RISK = {
  high: { label: "High", fg: "var(--risk-high)", bg: "var(--risk-high-bg)", ink: "var(--risk-high-ink)" },
  medium: { label: "Medium", fg: "var(--risk-medium)", bg: "var(--risk-medium-bg)", ink: "var(--risk-medium-ink)" },
  low: { label: "Low", fg: "var(--risk-low)", bg: "var(--risk-low-bg)", ink: "var(--risk-low-ink)" },
  unknown: { label: "Manual review", fg: "var(--color-neutral-600)", bg: "var(--color-neutral-200)", ink: "var(--color-neutral-900)" },
};
export const riskOf = (level) => RISK[level] || RISK.unknown;

export const STATUS = {
  HELD: { label: "Held", bg: "var(--color-text)", ink: "var(--color-bg)" },
  EXTENDED: { label: "Extended", bg: "var(--color-text)", ink: "var(--color-bg)" },
  ESCALATED: { label: "Escalated", bg: "var(--brand-orange)", ink: "#fff" },
  RELEASED: { label: "Released", bg: "var(--risk-low-bg)", ink: "var(--risk-low-ink)" },
};
export const statusOf = (s) => STATUS[s] || { label: s, bg: "var(--color-neutral-300)", ink: "var(--color-neutral-900)" };
export const isOpen = (s) => s === "HELD" || s === "EXTENDED";

const SIGNAL_LABELS = {
  new_payee: "New payee",
  payee_added_recently: "Payee added recently",
  full_liquidation: "Most of the balance",
  senior_client: "Senior client",
  first_crypto: "First crypto",
  unusual_timing: "Unusual timing",
  large_vs_history: "Large for this account",
};
export const signalLabel = (s) => SIGNAL_LABELS[s.name] || s.name.replaceAll("_", " ");
