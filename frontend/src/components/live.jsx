import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

// Re-runs `load` every `ms` while the tab is visible, so all three role views stay in sync
// during the demo (a client's answer shows up on the fraud team's screen within seconds).
export function usePolling(load, deps, ms = 4000) {
  const saved = useRef(load);
  saved.current = load;
  useEffect(() => {
    let alive = true;
    const tick = () => alive && document.visibilityState === "visible" && saved.current();
    saved.current();
    const t = setInterval(tick, ms);
    return () => {
      alive = false;
      clearInterval(t);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const push = useCallback((text, kind = "ok") => {
    const id = Math.random();
    setToasts((t) => [...t, { id, text, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => <div key={t.id} className={`toast ${t.kind === "error" ? "error" : ""}`}>{t.text}</div>)}
      </div>
    </ToastContext.Provider>
  );
}

export const LiveDot = () => <span className="live-dot" title="Updates live" />;
