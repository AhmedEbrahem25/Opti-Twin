import type { Recommendation } from "../lib/ws";

type Props = { items: Recommendation[] };

export default function XAIDecisionLog({ items }: Props) {
  return (
    <div className="glass rounded-xl p-3 max-h-[400px] flex flex-col">
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
            <DecisionEntry key={i} r={r} />
          ))}
        </div>
      )}
    </div>
  );
}

function DecisionEntry({ r }: { r: Recommendation }) {
  const ts = r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : "—";
  const dim = r.action_label === "HOLD_STEADY" ? "opacity-60" : "";
  const accent =
    r.action_label === "EMERGENCY_COOLING"
      ? "border-red-500/50"
      : r.action_label === "HOLD_STEADY"
      ? "border-steel-500/40"
      : "border-flame-500/40";

  return (
    <div className={`border-l-2 pl-3 py-1.5 ${accent} ${dim}`}>
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
      </div>
    </div>
  );
}
