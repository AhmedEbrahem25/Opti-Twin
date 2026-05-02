import type { Telemetry } from "../lib/ws";

const PHASE_LABELS: Record<string, string> = {
  CHARGING: "Charging",
  BORE_DOWN: "Bore-down",
  MELTING_PHASE_1: "Melting Phase 1",
  MELTING_PHASE_2: "Melting Phase 2",
  REFINING: "Refining",
  TAPPING: "Tapping",
  IDLE: "Idle",
};

const CRISIS_META: Record<string, { label: string; labelAr: string; color: string }> = {
  wall_overheat:     { label: "Wall Overheat",       labelAr: "ارتفاع حرارة الجدار",   color: "border-red-500/60 bg-red-500/15 text-red-300" },
  electrode_break:   { label: "Electrode Break",     labelAr: "كسر قطب كهربائي",       color: "border-orange-500/60 bg-orange-500/15 text-orange-300" },
  grid_spike:        { label: "Grid Hz Spike",       labelAr: "اضطراب تردد الشبكة",    color: "border-amber-500/60 bg-amber-500/15 text-amber-300" },
  transformer_alarm: { label: "Transformer Alarm",   labelAr: "إنذار المحول",           color: "border-yellow-500/60 bg-yellow-500/15 text-yellow-300" },
};

export default function EAFStatusCard({ t }: { t?: Telemetry }) {
  if (!t) {
    return (
      <div className="glass rounded-xl p-3 h-72 flex items-center justify-center text-steel-100/50">
        Waiting for telemetry…
      </div>
    );
  }

  const cf = t.crisis_flags ?? {};
  const activeCrises = (Object.entries(cf) as [string, boolean][]).filter(([, v]) => v);

  const phaseLabel = PHASE_LABELS[t.status] ?? t.status;
  return (
    <div className="glass rounded-xl p-3 h-72 overflow-y-auto">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-steel-100/80 mb-2">
        EAF Status
      </h3>

      {/* Active crisis banners */}
      {activeCrises.map(([key]) => {
        const meta = CRISIS_META[key] ?? { label: key, labelAr: key, color: "border-red-500/60 bg-red-500/15 text-red-300" };
        return (
          <div
            key={key}
            className={`flex items-center gap-2 rounded-lg border px-2 py-1 mb-2 text-xs font-semibold animate-pulse ${meta.color}`}
          >
            <span>🚨</span>
            <span>{meta.label}</span>
            <span className="opacity-60" dir="rtl">{meta.labelAr}</span>
          </div>
        );
      })}

      <div className="text-lg font-semibold text-white">{t.factory}</div>
      <div className="text-xs text-steel-100/60 mb-3">
        {t.machine_id} · {t.manufacturer ?? "—"}
      </div>

      <Row k="Phase" v={phaseLabel} />
      <Row k="Heat progress" v={`${t.heat_progress_pct.toFixed(0)} %`} />
      <Row k="Batch #" v={`${t.batches_today + 1} (today: ${t.batches_today})`} />
      <Row k="Charge weight" v={`${t.current_batch_weight.toFixed(0)} t`} />
      <Row k="O₂ injection" v={`${t.oxygen_injection_m3hr.toFixed(0)} m³/hr`} />
      <Row k="Cooling water" v={`${t.cooling_water_flow_lmin.toFixed(0)} l/min`} />
      <Row k="Grid Hz" v={t.grid_frequency.toFixed(2)} />
      <Row k="Tariff class" v={t.tariff_class} />

      {t.ai_active && (
        <div className="mt-3 px-2 py-1 inline-block rounded bg-flame-500/20 border border-flame-500/40 text-flame-400 text-xs">
          🤖 AI Agent Active
        </div>
      )}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string | number }) {
  return (
    <div className="flex justify-between py-0.5 text-sm">
      <span className="text-steel-100/60">{k}</span>
      <span className="font-medium text-steel-100">{v}</span>
    </div>
  );
}
