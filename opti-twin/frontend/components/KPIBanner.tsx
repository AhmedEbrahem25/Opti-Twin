import type { Telemetry, Recommendation } from "../lib/ws";

type Props = {
  telemetry?: Telemetry;
  lastRec?: Recommendation;
  egpSavedToday: number;
  co2SavedKg: number;
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

  const costNow = t ? t.arc_power_mw * 1000 * t.electricity_price : 0; // EGP/hour

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-4">
      <Card title="💰 Saved Today" value={`${fmt(egpSavedToday, 0)} EGP`} sub="modelled" />
      <Card title="⚡ Cost Now" value={`${fmt(costNow, 0)} EGP/hr`} sub={`@ ${t?.electricity_price?.toFixed(2) ?? "—"} EGP/kWh`} />
      <Card title="🌡️ Bath Temp" value={`${fmt(t?.furnace_bath_temp ?? 0, 0)} °C`} sub="target 1,600–1,650" />
      <Card title="🔌 Power Factor" value={t ? t.power_factor.toFixed(2) : "—"} sub={pfBracket ? "⚠ penalty bracket" : "✓ above 0.92"} valueClass={pfBracket ? "text-amber-400" : "text-emerald-400"} />
      <Card title="🏭 Health" value={health} sub={lastRec?.production_status || "—"} valueClass={healthColor} />
      <Card title="♻️ CO₂ Saved" value={`${fmt(co2SavedKg, 1)} kg`} sub="today" />
    </div>
  );
}

function Card({ title, value, sub, valueClass }: { title: string; value: string; sub?: string; valueClass?: string }) {
  return (
    <div className="glass rounded-xl p-3">
      <div className="text-xs text-steel-100/60 uppercase tracking-wide">{title}</div>
      <div className={`text-xl font-semibold mt-1 ${valueClass ?? "text-white"}`}>{value}</div>
      {sub && <div className="text-xs text-steel-100/50 mt-0.5">{sub}</div>}
    </div>
  );
}
