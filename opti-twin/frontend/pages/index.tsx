import Head from "next/head";
import { useEffect, useState } from "react";
import { useLiveFeed } from "../lib/ws";
import KPIBanner from "../components/KPIBanner";
import EnergyChart from "../components/EnergyChart";
import ThermalGauge from "../components/ThermalGauge";
import EAFStatusCard from "../components/EAFStatusCard";
import XAIDecisionLog from "../components/XAIDecisionLog";
import Controls from "../components/Controls";
import DynamicPricingPanel from "../components/DynamicPricingPanel";
import PricingEventLog from "../components/PricingEventLog";
import LogViewer from "../components/LogViewer";
import CommandPalette from "../components/search/CommandPalette";
import SavedSearchBanner from "../components/search/SavedSearchBanner";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Dashboard() {
  const frame = useLiveFeed();
  const [stats, setStats] = useState<{
    egp_saved_today: number;
    co2_saved_kg: number;
  }>({ egp_saved_today: 0, co2_saved_kg: 0 });

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/stats`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch {}
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const t = frame.telemetry;
  const peakActive = !!(t?.tou_mode && t?.is_peak);
  const [paletteOpen, setPaletteOpen] = useState(false);

  return (
    <>
      <Head>
        <title>Opti-Twin · Live Dashboard</title>
      </Head>
      <div className="min-h-screen px-4 md:px-8 py-6">
        <header className="flex items-baseline justify-between mb-5">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              Opti-Twin <span className="text-flame-400">Live</span>
            </h1>
            <p className="text-xs text-steel-100/60 mt-1">
              EAF Energy Optimization · NextCity AI 2026
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPaletteOpen(true)}
              className="hidden md:flex items-center gap-2 rounded-lg border border-steel-500/30 bg-steel-800/40 px-3 py-1.5 text-xs text-steel-100/70 hover:bg-steel-700/60"
              title="Search decisions, crises, safety overrides"
            >
              🔍 <span>Search</span>
              <kbd className="rounded bg-steel-700/60 px-1.5 py-0.5 text-[10px]">⌘K</kbd>
            </button>
            <ConnectionBadge state={frame.connection} />
          </div>
        </header>

        <SavedSearchBanner onOpenPalette={() => setPaletteOpen(true)} />

        <KPIBanner
          telemetry={t}
          lastRec={frame.recommendations[0]}
          egpSavedToday={stats.egp_saved_today}
          co2SavedKg={stats.co2_saved_kg}
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <EnergyChart data={frame.energySeries} peakActive={peakActive} />
          <ThermalGauge
            bath={t?.furnace_bath_temp ?? 1300}
            wall={t?.wall_panel_temp ?? 100}
          />
          <EAFStatusCard t={t} />
        </div>

        <div className="grid grid-cols-1 mt-4">
          <XAIDecisionLog items={frame.recommendations} />
        </div>

        <Controls />

        <DynamicPricingPanel livePrice={frame.livePrice} />

        <PricingEventLog />

        <LogViewer />

        <footer className="text-center text-xs text-steel-100/40 mt-6 py-4 border-t border-white/5">
          Tariff: 1.60 EGP/kWh · Furnace ref: Ezz Flat Steel Ain Sokhna EAF #2 · Grid CO₂: 0.50 kg/kWh · Numbers are modelled estimates.
        </footer>
      </div>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </>
  );
}

function ConnectionBadge({ state }: { state: string }) {
  const color =
    state === "open" ? "bg-emerald-500" : state === "connecting" ? "bg-amber-500" : "bg-red-500";
  const label =
    state === "open" ? "Live" : state === "connecting" ? "Connecting…" : "Reconnecting…";
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`w-2 h-2 rounded-full ${color} animate-pulse`} />
      <span className="text-steel-100/70">{label}</span>
    </div>
  );
}
