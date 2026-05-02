import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

type PricingEvent = {
  ts: string;
  event_kind: string;
  label: string;
  price_egp_kwh?: number;
  is_peak?: boolean;
  dr_status?: string;
  dr_type?: string;
  dr_payment_egp?: number;
  net_benefit_egp?: number;
  mode_from?: string;
  mode_to?: string;
  jump_pct?: number;
  decline_reason?: string;
};

type Stats = {
  total_events: number;
  peak_transitions: number;
  price_spikes: number;
  dr_accepted: number;
  dr_declined: number;
  forecast_updates: number;
  mode_changes: number;
};

const EVENT_KINDS = [
  { id: "", label: "All events" },
  { id: "peak_start", label: "Peak start" },
  { id: "peak_end", label: "Peak end" },
  { id: "price_spike", label: "Price spike" },
  { id: "dr_event", label: "DR event" },
  { id: "forecast_update", label: "Forecast update" },
  { id: "mode_change", label: "Mode change" },
];

const DR_STATUSES = [
  { id: "", label: "Any status" },
  { id: "ACCEPTED", label: "Accepted" },
  { id: "DECLINED", label: "Declined" },
];

function kindIcon(kind: string, drStatus?: string): string {
  if (kind === "peak_start") return "🔴";
  if (kind === "peak_end") return "🟢";
  if (kind === "price_spike") return "⚡";
  if (kind === "dr_event") return drStatus === "ACCEPTED" ? "💰" : "✗";
  if (kind === "forecast_update") return "📈";
  if (kind === "mode_change") return "⚙";
  return "•";
}

function kindColor(kind: string, drStatus?: string): string {
  if (kind === "peak_start") return "text-red-400";
  if (kind === "peak_end") return "text-emerald-400";
  if (kind === "price_spike") return "text-amber-400";
  if (kind === "dr_event") return drStatus === "ACCEPTED" ? "text-emerald-300" : "text-steel-400";
  if (kind === "forecast_update") return "text-blue-300";
  if (kind === "mode_change") return "text-purple-400";
  return "text-steel-300";
}

function formatTs(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso.slice(11, 19);
  }
}

function EventRow({ ev }: { ev: PricingEvent }) {
  const [expanded, setExpanded] = useState(false);
  const color = kindColor(ev.event_kind, ev.dr_status);
  const icon = kindIcon(ev.event_kind, ev.dr_status);

  // Extract just the English part of the bilingual label
  const labelParts = ev.label.split(" | ");
  const labelEn = labelParts[labelParts.length - 1] ?? ev.label;
  const labelAr = labelParts[0] !== labelParts[labelParts.length - 1] ? labelParts[0] : null;

  return (
    <div
      className="border-b border-white/5 py-1.5 px-1 hover:bg-white/5 cursor-pointer select-none"
      onClick={() => setExpanded((x) => !x)}
    >
      <div className="flex items-start gap-2 text-xs">
        <span className="text-steel-100/40 shrink-0 w-16">{formatTs(ev.ts)}</span>
        <span className="shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <span className={`${color} font-medium`}>{labelEn}</span>
          {labelAr && (
            <span className="text-steel-100/40 ml-2 text-[11px]" dir="rtl">{labelAr}</span>
          )}
          {ev.event_kind === "dr_event" && ev.dr_payment_egp !== undefined && ev.dr_payment_egp > 0 && (
            <span className="ml-2 text-emerald-400">+{ev.dr_payment_egp.toFixed(0)} EGP</span>
          )}
          {ev.event_kind === "price_spike" && ev.jump_pct !== undefined && (
            <span className="ml-2 text-amber-300/60 text-[11px]">+{ev.jump_pct}%</span>
          )}
        </div>
        <span className="text-steel-100/30 text-[10px] shrink-0">{ev.event_kind.replace("_", " ")}</span>
      </div>

      {expanded && (
        <div className="mt-1 ml-[72px] text-[11px] text-steel-100/50 space-y-0.5">
          {ev.price_egp_kwh !== undefined && (
            <div>Price: <span className="text-steel-200">{ev.price_egp_kwh.toFixed(4)} EGP/kWh</span>
              {ev.is_peak !== undefined && (
                <span className={`ml-2 ${ev.is_peak ? "text-red-400" : "text-emerald-400"}`}>
                  {ev.is_peak ? "PEAK" : "off-peak"}
                </span>
              )}
            </div>
          )}
          {ev.dr_type && <div>DR type: <span className="text-steel-200">{ev.dr_type}</span></div>}
          {ev.dr_status && <div>Status: <span className={ev.dr_status === "ACCEPTED" ? "text-emerald-400" : "text-red-400"}>{ev.dr_status}</span></div>}
          {ev.net_benefit_egp !== undefined && (
            <div>Net benefit: <span className={ev.net_benefit_egp >= 0 ? "text-emerald-400" : "text-red-400"}>{ev.net_benefit_egp >= 0 ? "+" : ""}{ev.net_benefit_egp.toFixed(0)} EGP</span></div>
          )}
          {ev.decline_reason && <div>Reason: <span className="text-steel-200">{ev.decline_reason}</span></div>}
          {ev.mode_from && <div>Changed: <span className="text-steel-200">{ev.mode_from} → {ev.mode_to}</span></div>}
          <div className="text-steel-100/30">{ev.ts}</div>
        </div>
      )}
    </div>
  );
}

export default function PricingEventLog() {
  const [events, setEvents] = useState<PricingEvent[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [q, setQ] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [drStatusFilter, setDrStatusFilter] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const debouncerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchEvents = async (query: string, kind: string, drStatus: string) => {
    try {
      const params: Record<string, string> = { limit: "80" };
      if (query.trim()) params.q = query.trim();
      if (kind) params.event_kind = kind;
      if (drStatus) params.dr_status = drStatus;
      const res = await api.searchPricingEvents(params as any);
      setEvents(res.results ?? []);
      setStats(res.stats ?? null);
    } catch {}
  };

  // Debounced search on filter change
  useEffect(() => {
    if (debouncerRef.current) clearTimeout(debouncerRef.current);
    debouncerRef.current = setTimeout(() => {
      fetchEvents(q, kindFilter, drStatusFilter);
    }, 300);
    return () => { if (debouncerRef.current) clearTimeout(debouncerRef.current); };
  }, [q, kindFilter, drStatusFilter]);

  // Auto-refresh every 4 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(() => fetchEvents(q, kindFilter, drStatusFilter), 4000);
    return () => clearInterval(id);
  }, [autoRefresh, q, kindFilter, drStatusFilter]);

  const drAccepted = stats?.dr_accepted ?? 0;
  const drDeclined = stats?.dr_declined ?? 0;
  const spikes = stats?.price_spikes ?? 0;
  const peakTrans = stats?.peak_transitions ?? 0;

  return (
    <div className="glass rounded-xl p-4 mt-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wide">
            Pricing Event Log
          </h2>
          {stats && (
            <span className="text-xs text-steel-100/40">({stats.total_events} events)</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Stats pills */}
          {spikes > 0 && (
            <span className="text-[11px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/30">
              ⚡ {spikes} spike{spikes !== 1 ? "s" : ""}
            </span>
          )}
          {drAccepted > 0 && (
            <span className="text-[11px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30">
              💰 {drAccepted} DR paid
            </span>
          )}
          {peakTrans > 0 && (
            <span className="text-[11px] bg-red-500/20 text-red-300 px-2 py-0.5 rounded-full border border-red-500/30">
              🔴 {peakTrans} peak
            </span>
          )}
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh((v) => !v)}
            className={`text-[11px] px-2 py-0.5 rounded-full border ${
              autoRefresh
                ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                : "bg-steel-700 text-steel-400 border-white/10"
            }`}
          >
            {autoRefresh ? "● live" : "paused"}
          </button>
        </div>
      </div>

      {/* Search bar + filters */}
      <div className="flex flex-wrap gap-2 mb-3">
        <div className="flex-1 min-w-[160px] relative">
          <input
            ref={inputRef}
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search events… (EN/AR)"
            className="w-full bg-steel-800 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-steel-100/30 outline-none focus:border-blue-500/50"
          />
          {q && (
            <button
              onClick={() => setQ("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-steel-100/40 hover:text-white text-xs"
            >✕</button>
          )}
        </div>
        <select
          value={kindFilter}
          onChange={(e) => setKindFilter(e.target.value)}
          className="bg-steel-800 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-steel-100 outline-none"
        >
          {EVENT_KINDS.map((k) => (
            <option key={k.id} value={k.id}>{k.label}</option>
          ))}
        </select>
        <select
          value={drStatusFilter}
          onChange={(e) => setDrStatusFilter(e.target.value)}
          className="bg-steel-800 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-steel-100 outline-none"
        >
          {DR_STATUSES.map((s) => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
        {(q || kindFilter || drStatusFilter) && (
          <button
            onClick={() => { setQ(""); setKindFilter(""); setDrStatusFilter(""); }}
            className="text-xs text-steel-100/40 hover:text-white px-2"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Quick-filter chips */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {[
          { label: "DR accepted", kind: "dr_event", drStatus: "ACCEPTED" },
          { label: "DR declined", kind: "dr_event", drStatus: "DECLINED" },
          { label: "Price spikes", kind: "price_spike", drStatus: "" },
          { label: "Peak events", kind: "peak_start", drStatus: "" },
          { label: "Mode changes", kind: "mode_change", drStatus: "" },
          { label: "Forecasts", kind: "forecast_update", drStatus: "" },
        ].map((chip) => (
          <button
            key={chip.label}
            onClick={() => {
              setKindFilter(kindFilter === chip.kind && drStatusFilter === chip.drStatus ? "" : chip.kind);
              setDrStatusFilter(kindFilter === chip.kind && drStatusFilter === chip.drStatus ? "" : chip.drStatus);
            }}
            className={`text-[11px] px-2 py-0.5 rounded-full border transition-colors ${
              kindFilter === chip.kind && drStatusFilter === chip.drStatus
                ? "bg-blue-500/30 text-blue-200 border-blue-500/50"
                : "bg-steel-800 text-steel-400 border-white/10 hover:border-white/20"
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Results */}
      <div className="max-h-64 overflow-y-auto rounded-lg bg-steel-900/50 border border-white/5">
        {events.length === 0 ? (
          <div className="text-xs text-steel-100/30 text-center py-8">
            {q || kindFilter || drStatusFilter
              ? "No events match your filters"
              : "Waiting for pricing events… (events appear after the first price tick)"}
          </div>
        ) : (
          events.map((ev, i) => <EventRow key={`${ev.ts}-${i}`} ev={ev} />)
        )}
      </div>

      {events.length > 0 && (
        <div className="text-[11px] text-steel-100/30 mt-1.5 text-right">
          {events.length} result{events.length !== 1 ? "s" : ""}
          {(q || kindFilter || drStatusFilter) && " (filtered)"}
          {" · "}Click any row to expand
        </div>
      )}
    </div>
  );
}
