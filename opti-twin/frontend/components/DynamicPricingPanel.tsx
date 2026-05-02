import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { LivePrice } from "../lib/ws";

type ForecastStep = {
  t_offset_h: number;
  t_hour: number;
  p50: number;
  p10: number;
  p90: number;
  is_peak: boolean;
};

type Revenue = {
  energy_savings_egp: number;
  dr_payments_egp: number;
  capacity_credits_egp: number;
  ancillary_egp: number;
  total_revenue_egp: number;
};

type HeatSlot = {
  heat_number: number;
  start_hour: string | number;
  end_hour: string | number;
  melting_avg_price_egp: number;
  total_cost_egp: number;
  label: string;
};

type DREvent = {
  event_id: string;
  event_type: string;
  status: string;
  accepted_mw: number;
  payment_earned_egp: number;
  net_benefit_egp: number;
  duration_minutes: number;
  issued_at: string;
};

type Props = {
  livePrice?: LivePrice;
};

const PRICING_MODES = [
  { id: "flat", label: "Flat (EgyptERA 1.60)" },
  { id: "sim_tou", label: "TOU Schedule" },
  { id: "sim_spot", label: "Spot (Synthetic)" },
];

const DR_TYPES = [
  { id: "CURTAILMENT", label: "Curtailment (250 EGP/MWh)" },
  { id: "INTERRUPTIBLE", label: "Interruptible (450 EGP/MWh)" },
  { id: "FREQUENCY_RESPONSE", label: "Frequency Response (950 EGP/MWh)" },
];

export default function DynamicPricingPanel({ livePrice }: Props) {
  const [mode, setMode] = useState("flat");
  const [revenue, setRevenue] = useState<Revenue | null>(null);
  const [forecast, setForecast] = useState<ForecastStep[]>([]);
  const [schedule, setSchedule] = useState<{ slots: HeatSlot[]; savings_vs_backtoback_egp: number } | null>(null);
  const [drEvents, setDrEvents] = useState<{ history: DREvent[] }>({ history: [] });
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const [rev, fc, sch, dr, modeRes] = await Promise.all([
          api.getRevenue(),
          api.getForecast(),
          api.getSchedule(),
          api.getDREvents(),
          api.getPricingMode(),
        ]);
        if (!alive) return;
        if (rev) setRevenue(rev);
        if (fc?.forecast) setForecast(fc.forecast.slice(0, 8));
        if (sch) setSchedule(sch);
        if (dr) setDrEvents(dr);
        if (modeRes?.mode) setMode(modeRes.mode);
      } catch {}
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  async function changeMode(m: string) {
    setBusy("mode");
    try { await api.setPricingMode(m); setMode(m); } finally { setBusy(null); }
  }

  async function injectDR(type: string) {
    setBusy("dr");
    try { await api.injectDREvent(type, 30, 30); } finally { setBusy(null); }
  }

  const price = livePrice?.price_egp_kwh ?? 1.60;
  const isPeak = livePrice?.is_peak ?? false;
  const isDynamic = mode !== "flat";

  const priceColor = price > 2.2 ? "text-red-400" : price > 1.8 ? "text-amber-400" : "text-emerald-400";
  const peakBadge = isPeak
    ? "bg-red-500/20 text-red-300 border border-red-500/40"
    : "bg-steel-700 text-steel-300";

  const totalRevenue = revenue?.total_revenue_egp ?? 0;
  const revenueStreams = [
    { label: "Energy Savings", value: revenue?.energy_savings_egp ?? 0, color: "bg-emerald-500" },
    { label: "DR Payments", value: revenue?.dr_payments_egp ?? 0, color: "bg-blue-500" },
    { label: "Capacity Credits", value: revenue?.capacity_credits_egp ?? 0, color: "bg-purple-500" },
    { label: "Ancillary", value: revenue?.ancillary_egp ?? 0, color: "bg-amber-500" },
  ];

  const maxStream = Math.max(...revenueStreams.map((s) => s.value), 1);

  return (
    <div className="glass rounded-xl p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wide">
          Dynamic Pricing Engine
        </h2>
        <span className={`text-xs px-2 py-0.5 rounded-full ${isDynamic ? "bg-blue-500/20 text-blue-300 border border-blue-500/40" : "bg-steel-700 text-steel-400"}`}>
          {mode === "flat" ? "Flat tariff" : mode === "sim_spot" ? "Spot market" : "TOU"}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

        {/* Live price + mode */}
        <div className="space-y-2">
          <div className="text-xs text-steel-100/50 uppercase">Live Price</div>
          <div className={`text-3xl font-bold ${priceColor}`}>
            {price.toFixed(3)}
            <span className="text-sm font-normal text-steel-300 ml-1">EGP/kWh</span>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full ${peakBadge}`}>
            {isPeak ? "PEAK" : livePrice?.label ?? "—"}
          </span>

          <div className="text-xs text-steel-100/50 uppercase mt-3">Pricing Mode</div>
          <select
            value={mode}
            onChange={(e) => changeMode(e.target.value)}
            disabled={busy === "mode"}
            className="w-full py-2 text-xs rounded-lg bg-steel-700 text-steel-100 px-2 outline-none"
          >
            {PRICING_MODES.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </div>

        {/* 4h Forecast mini-chart */}
        <div>
          <div className="text-xs text-steel-100/50 uppercase mb-2">4h Price Forecast</div>
          {forecast.length > 0 ? (
            <div className="flex items-end gap-0.5 h-16">
              {forecast.map((step, i) => {
                const maxP = Math.max(...forecast.map((s) => s.p90), 2.0);
                const h = Math.max(4, (step.p50 / maxP) * 64);
                const barColor = step.is_peak ? "bg-red-500/70" : "bg-emerald-500/50";
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-0.5" title={`+${step.t_offset_h}h: ${step.p50.toFixed(2)} EGP`}>
                    <div className={`w-full rounded-sm ${barColor}`} style={{ height: h }} />
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-xs text-steel-100/30 mt-4">Waiting for forecast…</div>
          )}
          <div className="flex justify-between text-xs text-steel-100/30 mt-1">
            <span>now</span><span>+4h</span>
          </div>
          {forecast.length > 0 && (
            <div className="text-xs text-steel-100/50 mt-1">
              Max: <span className="text-amber-400">{Math.max(...forecast.map((s) => s.p50)).toFixed(2)}</span>{" "}
              Min: <span className="text-emerald-400">{Math.min(...forecast.map((s) => s.p50)).toFixed(2)}</span>
            </div>
          )}
        </div>

        {/* Revenue streams */}
        <div>
          <div className="text-xs text-steel-100/50 uppercase mb-2">Revenue Streams Today</div>
          <div className="space-y-1.5">
            {revenueStreams.map((s) => (
              <div key={s.label}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-steel-300">{s.label}</span>
                  <span className="text-white font-medium">{s.value.toFixed(0)} EGP</span>
                </div>
                <div className="h-1.5 rounded-full bg-steel-700">
                  <div
                    className={`h-full rounded-full ${s.color}`}
                    style={{ width: `${Math.min(100, (s.value / maxStream) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t border-white/10 flex justify-between text-xs">
            <span className="text-steel-400">Total stacked</span>
            <span className="text-white font-bold">{totalRevenue.toFixed(0)} EGP</span>
          </div>
        </div>

        {/* DR Events + Schedule */}
        <div className="space-y-2">
          <div className="text-xs text-steel-100/50 uppercase">Demand Response</div>
          <select
            onChange={(e) => { if (e.target.value) { injectDR(e.target.value); (e.target as HTMLSelectElement).value = ""; }}}
            disabled={busy === "dr"}
            className="w-full py-2 text-xs rounded-lg bg-blue-700/50 hover:bg-blue-700/80 text-white px-2 outline-none"
            defaultValue=""
          >
            <option value="" disabled>Inject DR event…</option>
            {DR_TYPES.map((d) => (
              <option key={d.id} value={d.id}>{d.label}</option>
            ))}
          </select>

          <div className="text-xs text-steel-100/50 uppercase mt-2">Recent DR</div>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {drEvents.history.length === 0 && (
              <div className="text-xs text-steel-100/30">No DR events today</div>
            )}
            {drEvents.history.slice(0, 4).map((ev) => (
              <div key={ev.event_id} className="flex justify-between text-xs">
                <span className={ev.status === "ACCEPTED" ? "text-emerald-400" : "text-steel-400"}>
                  {ev.event_type.slice(0, 8)} {ev.status === "ACCEPTED" ? "✓" : "✗"}
                </span>
                <span className={ev.status === "ACCEPTED" ? "text-emerald-300" : "text-steel-500"}>
                  {ev.status === "ACCEPTED" ? `+${ev.payment_earned_egp.toFixed(0)} EGP` : "declined"}
                </span>
              </div>
            ))}
          </div>

          {schedule && schedule.slots.length > 0 && (
            <>
              <div className="text-xs text-steel-100/50 uppercase mt-2">Schedule Savings</div>
              <div className="text-xs text-emerald-400 font-medium">
                {schedule.savings_vs_backtoback_egp.toFixed(0)} EGP vs back-to-back
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
