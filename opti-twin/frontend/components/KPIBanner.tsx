import type { Telemetry, Recommendation } from "../lib/ws";

type Props = {
  telemetry?: Telemetry;
  lastRec?: Recommendation;
  egpSavedToday: number;
  co2SavedKg: number;
  maintenanceAlertsToday?: number;
  avgMaintenanceRisk?: number;
  avgOperationalEfficiency?: number;
  avgProcessStability?: number;
};

function fmt(n: number, d = 0): string {
  return n.toLocaleString(undefined, {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

export default function KPIBanner({
  telemetry,
  lastRec,
  egpSavedToday,
  co2SavedKg,
  maintenanceAlertsToday = 0,
  avgMaintenanceRisk = 0,
  avgOperationalEfficiency = 0,
  avgProcessStability = 0,
}: Props) {
  const t = telemetry;
  const pfBracket = t?.pf_penalty_bracket;
  const health = lastRec?.machine_health || "SAFE";
  const healthColor =
    health === "CRITICAL"
      ? "text-red-400"
      : health === "WARNING"
      ? "text-amber-400"
      : "text-emerald-400";

  const cf = t?.crisis_flags;
  const anyCrisis = cf && (cf.wall_overheat || cf.electrode_break || cf.grid_spike || cf.transformer_alarm);

  const crisisLabel = cf
    ? cf.wall_overheat ? "🚨 Wall Overheat"
    : cf.electrode_break ? "🚨 Electrode Break"
    : cf.grid_spike ? "🚨 Grid Frequency Spike"
    : cf.transformer_alarm ? "🚨 Transformer Alarm"
    : null
    : null;

  const costNow = t ? t.arc_power_mw * 1000 * t.electricity_price : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 mb-4">
      <Card title="Saved Today" value={`${fmt(egpSavedToday, 0)} EGP`} sub="est. savings" />
      <Card
        title="Running Cost"
        value={`${fmt(costNow, 0)} EGP/hr`}
        sub={`${t?.electricity_price?.toFixed(2) ?? "—"} EGP/kWh`}
        pulse={cf?.grid_spike}
      />
      <Card
        title="Bath Temp"
        value={`${fmt(t?.furnace_bath_temp ?? 0, 0)} °C`}
        sub="target 1,600–1,650 °C"
        pulse={cf?.wall_overheat}
        valueClass={cf?.wall_overheat ? "text-red-400" : undefined}
      />
      <Card
        title="Power Factor"
        value={t ? t.power_factor.toFixed(2) : "—"}
        sub={pfBracket ? "⚠ penalty active" : "✓ OK (above 0.92)"}
        valueClass={pfBracket ? "text-amber-400" : "text-emerald-400"}
      />
      <Card
        title="Machine Health"
        value={anyCrisis ? "CRISIS" : health}
        sub={crisisLabel ?? lastRec?.production_status ?? "—"}
        valueClass={anyCrisis ? "text-red-400 animate-pulse" : healthColor}
      />
      <Card title="CO₂ Saved" value={`${fmt(co2SavedKg, 1)} kg`} sub="today" />
      <Card
        title="Ops Efficiency"
        value={`${fmt(avgOperationalEfficiency || t?.cycle_efficiency_pct || 0, 0)}%`}
        sub={`stability ${fmt(avgProcessStability || 0, 0)}%`}
      />
      <Card
        title="Maint. Risk"
        value={`${fmt(avgMaintenanceRisk * 100, 0)}%`}
        sub={`${maintenanceAlertsToday} alert${maintenanceAlertsToday === 1 ? "" : "s"} today`}
        valueClass={avgMaintenanceRisk >= 0.55 ? "text-red-400" : "text-emerald-400"}
        pulse={avgMaintenanceRisk >= 0.75}
      />
    </div>
  );
}

function Card({ title, value, sub, valueClass, pulse }: { title: string; value: string; sub?: string; valueClass?: string; pulse?: boolean }) {
  return (
    <div className={`glass rounded-xl p-3 ${pulse ? "ring-1 ring-red-500/60" : ""}`}>
      <div className="text-xs text-steel-100/60 uppercase tracking-wide">{title}</div>
      <div className={`text-xl font-semibold mt-1 ${pulse ? "animate-pulse" : ""} ${valueClass ?? "text-white"}`}>{value}</div>
      {sub && <div className={`text-xs mt-0.5 ${pulse ? "text-red-400/70" : "text-steel-100/50"}`}>{sub}</div>}
    </div>
  );
}
