import { useEffect, useMemo, useRef, useState } from "react";
import type { Recommendation } from "../lib/ws";
import type { SearchFocus } from "../lib/searchFocus";

type Props = {
  items: Recommendation[];
  focused?: SearchFocus | null;
};

const FLASH_TOLERANCE_MS = 5_000;

export default function XAIDecisionLog({ items, focused }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rowRefs = useRef<Array<HTMLDivElement | null>>([]);
  const [flashIdx, setFlashIdx] = useState<number | null>(null);

  // Decide if this panel claims the current focus + which row matches.
  const matchedIdx = useMemo(() => {
    if (!focused) return null;
    if (focused.type !== "decision" && focused.type !== "safety_rollback") return null;
    const target = new Date(focused.ts).getTime();
    if (!Number.isFinite(target)) return null;
    let best = -1;
    let bestDelta = FLASH_TOLERANCE_MS;
    items.forEach((r, i) => {
      if (!r.timestamp) return;
      const ts = new Date(r.timestamp).getTime();
      if (!Number.isFinite(ts)) return;
      const delta = Math.abs(ts - target);
      if (delta <= bestDelta) {
        best = i;
        bestDelta = delta;
      }
    });
    return best >= 0 ? best : null;
  }, [focused, items]);

  useEffect(() => {
    if (matchedIdx === null) return;
    const el = rowRefs.current[matchedIdx];
    if (!el) return;
    el.scrollIntoView({ block: "center", behavior: "smooth" });
    setFlashIdx(matchedIdx);
    const t = setTimeout(() => setFlashIdx(null), 2_000);
    return () => clearTimeout(t);
  }, [matchedIdx, focused?.doc_id]);

  return (
    <div ref={containerRef} className="glass rounded-xl p-3 max-h-[400px] flex flex-col">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-steel-100/80 mb-2">
        🧠 AI Decision Log
      </h3>

      {items.length === 0 ? (
        <div className="text-xs text-steel-100/40 py-4 text-center">
          No decisions yet — enable AI or wait for telemetry.
        </div>
      ) : (
        <div className="overflow-auto flex-1 pr-1 space-y-2">
          {items.map((r, i) => (
            <DecisionEntry
              key={i}
              r={r}
              flash={flashIdx === i}
              registerRef={(el) => {
                rowRefs.current[i] = el;
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function DecisionEntry({
  r,
  flash,
  registerRef,
}: {
  r: Recommendation;
  flash: boolean;
  registerRef: (el: HTMLDivElement | null) => void;
}) {
  const ts = r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : "—";
  const dim = r.action_label === "HOLD_STEADY" ? "opacity-60" : "";
  const accent =
    r.action_label === "EMERGENCY_COOLING"
      ? "border-red-500/50"
      : r.action_label === "HOLD_STEADY"
      ? "border-steel-500/40"
      : "border-flame-500/40";

  return (
    <div
      ref={registerRef}
      className={`border-l-2 pl-3 py-1.5 ${accent} ${dim} ${flash ? "opti-flash" : ""}`}
    >
      <div className="flex justify-between text-xs text-steel-100/70">
        <span>{ts}</span>
        <span>
          {r.action_label}
          {r.action_magnitude_pct !== 0 && (
            <span className="ml-1 text-flame-400">
              ({r.action_magnitude_pct > 0 ? "+" : ""}
              {r.action_magnitude_pct.toFixed(0)}%)
            </span>
          )}
        </span>
      </div>
      <div className="text-sm text-steel-100/90 mt-1 leading-snug">
        {r.xai_reason}
      </div>
      <div className="text-xs text-steel-100/50 mt-1 flex gap-3">
        {r.estimated_savings_egp_per_hour > 0 && (
          <span>💰 {r.estimated_savings_egp_per_hour.toFixed(0)} EGP/hr saved</span>
        )}
        {r.pf_penalty_avoided_egp > 0 && (
          <span>🔌 {r.pf_penalty_avoided_egp.toFixed(0)} EGP/hr PF penalty avoided</span>
        )}
        <span className={
          r.machine_health === "CRITICAL" ? "text-red-400"
          : r.machine_health === "WARNING" ? "text-amber-400"
          : "text-emerald-400"
        }>{r.machine_health}</span>
        {r.maintenance_risk_level && r.maintenance_risk_level !== "NOMINAL" && (
          <span className={r.maintenance_risk_level === "CRITICAL" ? "text-red-400" : "text-amber-400"}>
            maint {r.maintenance_risk_level} ({((r.maintenance_risk_score ?? 0) * 100).toFixed(0)}%)
          </span>
        )}
      </div>
    </div>
  );
}
