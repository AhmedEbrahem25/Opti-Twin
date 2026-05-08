"use client";
import { use, useMemo } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { KPICard } from "@/components/data-display/kpi-card";
import { StatusBadge } from "@/components/data-display/status-badge";
import { MetricRing } from "@/components/data-display/metric-ring";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MACHINE_SCHEMAS } from "@/lib/constants";
import { Zap, DollarSign, Activity, ArrowRight, Thermometer, Gauge, AlertTriangle, Settings } from "lucide-react";
import { generateMockMachines, FACTORY_FIXTURES } from "@/services/mock-data";
import { useTelemetryStore } from "@/store/telemetry-store";
import { LIVE_FACTORY_ID, LIVE_MACHINE_ID } from "@/lib/backend-types";

export default function FactoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const factory = FACTORY_FIXTURES.find((f) => f.id === id);
  const machines = useMemo(() => generateMockMachines(id), [id]);
  const isLive = id === LIVE_FACTORY_ID;
  const liveLatest = useTelemetryStore((s) => s.latestPoints.get(LIVE_MACHINE_ID));
  const liveKpis = useTelemetryStore((s) => s.kpis);

  const headerName = factory?.name ?? "Factory";
  const headerLocation = factory
    ? `${factory.location} — ${factory.machineCount} machine${factory.machineCount === 1 ? "" : "s"}`
    : "";
  const headerStatus = factory?.status ?? "RUNNING";

  const kpiActive = isLive ? machines.length : factory?.machineCount ?? machines.length;
  const kpiEnergy = isLive
    ? liveLatest?.energyKwh ?? 0
    : factory?.energyUsageKwh ?? 0;
  const kpiSaved = isLive ? liveKpis.totalCostSaved : factory?.costSavedToday ?? 0;
  const kpiEfficiency = isLive
    ? liveKpis.avgEfficiency
    : factory?.efficiencyScore ?? 0;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            {headerName}
          </h1>
          <p className="text-sm text-text-tertiary mt-0.5">{headerLocation}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={headerStatus} />
          <Button variant="ghost" size="icon-sm"><Settings size={15} /></Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Active Machines" value={kpiActive} icon={<Activity size={16} />} accentColor="var(--color-cyan)" />
        <KPICard label="Energy Usage" value={kpiEnergy} suffix=" kWh" icon={<Zap size={16} />} accentColor="var(--color-warning)" />
        <KPICard label="Cost Saved Today" value={kpiSaved} suffix=" EGP" icon={<DollarSign size={16} />} accentColor="var(--color-success)" />
        <KPICard label="Efficiency Score" value={kpiEfficiency} suffix="%" icon={<Gauge size={16} />} accentColor="var(--color-accent)" />
      </div>

      {/* Machine Grid */}
      <div>
        <h2 className="text-sm font-semibold text-text-primary mb-4">Machines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {machines.map((m, i) => {
            const schema = MACHINE_SCHEMAS[m.type] || MACHINE_SCHEMAS.generic;
            const isLiveMachine = m.id === LIVE_MACHINE_ID;
            const tempDisplay = isLiveMachine
              ? liveLatest?.temperature
              : m.metrics.temperature;
            const energyDisplay = isLiveMachine
              ? liveLatest?.energyKwh
              : m.metrics.energyKwh;
            const liveTemp = isLiveMachine ? liveLatest?.temperature : undefined;
            const healthDisplay = liveTemp !== undefined
              ? Math.max(0, Math.min(100, Math.round(100 - Math.max(0, (liveTemp - 1600) / 50) * 100)))
              : m.healthScore;
            return (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              >
                <Link href={`/machine/${m.id}`}>
                  <Card spotlight className="group cursor-pointer hover:border-accent/20 transition-all">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center border border-border" style={{ backgroundColor: `${schema.color}15`, borderColor: `${schema.color}25` }}>
                            <Thermometer size={15} style={{ color: schema.color }} />
                          </div>
                          <div>
                            <CardTitle className="group-hover:text-accent transition-colors text-xs">{m.name}</CardTitle>
                            <p className="text-[10px] text-text-tertiary">{schema.displayName}</p>
                          </div>
                        </div>
                        <StatusBadge status={m.status} size="sm" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-text-tertiary">Temperature</span>
                            <span className="text-text-primary font-mono">{tempDisplay !== undefined ? `${tempDisplay.toFixed(1)}°C` : "—"}</span>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-text-tertiary">Energy</span>
                            <span className="text-text-primary font-mono">{energyDisplay !== undefined ? `${energyDisplay.toFixed(1)} kWh` : "—"}</span>
                          </div>
                          {m.metrics.rpm && (
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-text-tertiary">RPM</span>
                              <span className="text-text-primary font-mono">{Math.round(m.metrics.rpm)}</span>
                            </div>
                          )}
                        </div>
                        <div className="ml-4">
                          <MetricRing value={healthDisplay} size={56} strokeWidth={4} label="Health" />
                        </div>
                      </div>
                      {m.status === "WARNING" && (
                        <div className="mt-3 flex items-center gap-1.5 text-[11px] text-warning">
                          <AlertTriangle size={11} />
                          <span>Elevated temperature detected</span>
                        </div>
                      )}
                      <div className="mt-3 flex items-center justify-end">
                        <ArrowRight size={14} className="text-text-muted group-hover:text-accent transition-colors" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
