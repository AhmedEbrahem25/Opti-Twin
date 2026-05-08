"use client";
import { use, useEffect, useMemo, useState } from "react";
import { KPICard } from "@/components/data-display/kpi-card";
import { StatusBadge } from "@/components/data-display/status-badge";
import { MetricRing } from "@/components/data-display/metric-ring";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { generateTelemetryPoint, generateMockMachines } from "@/services/mock-data";
import { getRelativeTime } from "@/lib/utils";
import { useTelemetryStore } from "@/store/telemetry-store";
import { LIVE_MACHINE_ID } from "@/lib/backend-types";
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine,
} from "recharts";
import {
  Zap, DollarSign, Thermometer, Gauge, Activity, Brain,
  Box, Settings, TrendingDown,
} from "lucide-react";
import type { TelemetryPoint } from "@/types";

function findMachineName(id: string): string {
  // Walk known factory IDs to find the matching machine config.
  for (const factoryId of ["factory-1", "factory-2", "factory-3"]) {
    const m = generateMockMachines(factoryId).find((mm) => mm.id === id);
    if (m) return m.name;
  }
  return "Machine";
}

export default function MachinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const isLive = id === LIVE_MACHINE_ID;

  const liveSeries = useTelemetryStore((s) => s.liveData.get(id));
  const liveLatest = useTelemetryStore((s) => s.latestPoints.get(id));
  const xaiLogsLive = useTelemetryStore((s) => s.xaiLogs);
  const latestRec = useTelemetryStore((s) => isLive ? s.recommendations[0] : undefined);

  const [mockData, setMockData] = useState<TelemetryPoint[]>(() =>
    Array.from({ length: 30 }, (_, i) => {
      const p = generateTelemetryPoint(id);
      const ts = new Date(Date.now() - (30 - i) * 3000);
      return { ...p, timestamp: ts.toISOString() };
    }),
  );

  useEffect(() => {
    if (isLive) return;
    const interval = setInterval(() => {
      const point = generateTelemetryPoint(id);
      setMockData((prev) => [...prev.slice(-59), point]);
    }, 3000);
    return () => clearInterval(interval);
  }, [id, isLive]);

  const data: TelemetryPoint[] = isLive ? liveSeries ?? [] : mockData;
  const latest: TelemetryPoint | undefined = isLive ? liveLatest : data[data.length - 1];

  const machineName = useMemo(() => findMachineName(id), [id]);
  const xaiLogs = isLive ? xaiLogsLive.slice(0, 6) : [];

  // Derive health score from temperature: 100 when cool, 0 at/above critical.
  const healthScore = useMemo(() => {
    const t = latest?.temperature;
    if (t === undefined) return 88;
    if (isLive) return Math.max(0, Math.min(100, Math.round(100 - Math.max(0, (t - 1600) / 50) * 100)));
    return Math.max(0, Math.min(100, Math.round(100 - Math.max(0, (t - 85) / 15) * 100)));
  }, [latest?.temperature, isLive]);

  const chartData = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    temperature: d.temperature,
    energy: d.energyKwh,
    rpm: d.rpm,
  }));

  // For EAF the bath temperature axis is ~1500–1700 °C; for everything else it
  // is ~40–100 °C. Pick a sensible Y domain so the chart isn't a flatline.
  const tempDomain: [number, number] = isLive ? [1400, 1700] : [40, 100];
  const tempCriticalLine = isLive ? 1650 : 90;
  const tempCriticalLabel = isLive ? "Critical 1650°C" : "Critical 90°C";

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center">
            <Gauge size={24} className="text-accent" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
                {machineName}
              </h1>
              <StatusBadge status={latest?.status || "RUNNING"} />
              {isLive && <Badge variant="accent" pulse size="sm">Live</Badge>}
            </div>
            <p className="text-sm text-text-tertiary mt-0.5">
              {isLive
                ? "Electric Arc Furnace · Ezz Steel — Ain Sokhna · Line 2"
                : "Industrial machine"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="accent" size="sm"><Box size={14} /> Digital Twin</Button>
          <Button variant="ghost" size="icon-sm"><Settings size={15} /></Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <KPICard label="Temperature" value={latest?.temperature || 0} suffix="°C" icon={<Thermometer size={16} />} accentColor="var(--color-danger)" />
        <KPICard label={isLive ? "Power Draw" : "RPM"} value={isLive ? (latest?.energyKwh ?? 0) / 1000 : latest?.rpm || 0} suffix={isLive ? " MW" : ""} icon={<Gauge size={16} />} accentColor="var(--color-cyan)" format={(v) => isLive ? v.toFixed(1) : Math.round(v).toString()} />
        <KPICard label="Energy Usage" value={latest?.energyKwh || 0} suffix=" kWh" icon={<Zap size={16} />} accentColor="var(--color-warning)" />
        <KPICard label="Cost Rate" value={latest?.costRate || 0} suffix=" EGP/kWh" icon={<DollarSign size={16} />} accentColor={latest?.isPeak ? "var(--color-danger)" : "var(--color-success)"} />
        <KPICard label="Cycle Eff." value={latest?.cycleEfficiencyPct || latestRec?.operationalEfficiencyScore || 0} suffix="%" icon={<Activity size={16} />} accentColor="var(--color-info)" />
        <KPICard label="Maint. Risk" value={(latestRec?.maintenanceRiskScore ?? 0) * 100} suffix="%" icon={<Brain size={16} />} accentColor={(latestRec?.maintenanceRiskScore ?? 0) >= 0.55 ? "var(--color-danger)" : "var(--color-cyan)"} />
        <div className="flex items-center justify-center">
          <MetricRing value={healthScore} size={72} strokeWidth={5} label="Health" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Charts */}
        <div className="lg:col-span-2 space-y-4">
          {/* Temperature Chart */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Thermometer size={14} className="text-danger" /> Temperature
                  <Badge variant="danger" pulse size="sm">Live</Badge>
                </CardTitle>
                <span className="text-lg font-bold text-text-primary font-mono">
                  {latest?.temperature?.toFixed(1) || "—"}°C
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                    <YAxis tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} domain={tempDomain} />
                    <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} />
                    <ReferenceLine y={tempCriticalLine} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: tempCriticalLabel, position: "right", style: { fontSize: 9, fill: "#ef4444" } }} />
                    <Area type="monotone" dataKey="temperature" stroke="#ef4444" fill="url(#tempGrad)" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Energy Chart */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Zap size={14} className="text-accent" /> Energy Consumption
                  <Badge variant="accent" pulse size="sm">Live</Badge>
                </CardTitle>
                <span className="text-lg font-bold text-text-primary font-mono">
                  {latest?.energyKwh?.toFixed(1) || "—"} kWh
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                    <YAxis tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} />
                    <Area type="monotone" dataKey="energy" stroke="#f59e0b" fill="url(#energyGrad)" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column — AI + Sensors */}
        <div className="space-y-4">
          {/* AI Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Brain size={14} className="text-accent" /> AI Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Latest Decision — full detail with Arabic reason */}
              {latestRec && (
                <div className="mb-3 p-3 rounded-lg bg-accent/5 border border-accent/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="accent" size="sm">{latestRec.actionLabel.replace(/_/g, " ")}</Badge>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={latestRec.machineHealth === "SAFE" ? "success" : latestRec.machineHealth === "CRITICAL" ? "danger" : "warning"}
                        size="sm"
                      >
                        {latestRec.machineHealth}
                      </Badge>
                      <span className="text-[10px] text-text-muted">{getRelativeTime(latestRec.timestamp)}</span>
                    </div>
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed">{latestRec.xaiReason}</p>
                  {latestRec.xaiReasonAr && (
                    <p className="text-[11px] text-text-tertiary leading-relaxed text-right" dir="rtl">{latestRec.xaiReasonAr}</p>
                  )}
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-success flex items-center gap-1">
                      <TrendingDown size={10} /> ~{Math.round(latestRec.savingsEgpHr)} EGP/hr
                    </span>
                    <span className="text-[10px] text-text-muted">{latestRec.magnitudePct.toFixed(0)}% magnitude</span>
                  </div>
                  {latestRec.maintenanceAlert && (
                    <div className="pt-2 border-t border-accent/10 text-[10px] text-warning leading-relaxed">
                      {latestRec.maintenanceRiskLevel} maintenance risk: {latestRec.maintenanceFaultPrediction || latestRec.maintenanceRecommendedAction}
                    </div>
                  )}
                </div>
              )}
              <div className="space-y-3">
                {xaiLogs.length === 0 && !latestRec && (
                  <p className="text-[11px] text-text-tertiary">
                    {isLive ? "Waiting for AI decisions…" : "Live data only available on the EAF."}
                  </p>
                )}
                {xaiLogs.slice(0, 3).map((log) => (
                  <div key={log.id} className="p-3 rounded-lg bg-bg-300 border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="accent" size="sm">{log.action.replace(/_/g, " ")}</Badge>
                      <span className="text-[10px] text-text-muted">{getRelativeTime(log.timestamp)}</span>
                    </div>
                    <p className="text-[11px] text-text-tertiary leading-relaxed line-clamp-2">{log.reason}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-success flex items-center gap-1">
                        <TrendingDown size={10} /> ~{Math.round(log.savingsEstimate)} EGP/hr
                      </span>
                      <span className="text-[10px] text-text-muted">{log.confidence.toFixed(0)}% confidence</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Sensor Readings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Activity size={14} className="text-cyan" /> Sensor Readings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { label: "Temperature", value: `${latest?.temperature?.toFixed(1) || "—"}°C`, status: (latest?.temperature || 0) > (isLive ? 1650 : 85) ? "warning" : "normal" },
                  { label: isLive ? "Arc Power" : "RPM", value: isLive ? `${((latest?.energyKwh ?? 0) / 1000).toFixed(1)} MW` : `${Math.round(latest?.rpm || 0)}`, status: "normal" },
                  { label: isLive ? "PF Δ proxy" : "Vibration", value: `${latest?.vibration?.toFixed(2) || "—"} ${isLive ? "" : "mm/s"}`, status: (latest?.vibration || 0) > 4.5 ? "warning" : "normal" },
                  { label: "Vibration", value: `${latest?.vibrationMmS?.toFixed(2) || "—"} mm/s`, status: (latest?.vibrationMmS || 0) > 5 ? "warning" : "normal" },
                  { label: "Thermal Stress", value: `${latest?.thermalStressIndex?.toFixed(0) || "—"}/100`, status: (latest?.thermalStressIndex || 0) > 55 ? "warning" : "normal" },
                  { label: "Idle Today", value: `${latest?.idleMinutesToday?.toFixed(1) || "0.0"} min`, status: (latest?.idleMinutesToday || 0) > 20 ? "warning" : "normal" },
                  { label: isLive ? "Cooling Flow" : "Pressure", value: isLive ? `${latest?.flowRate?.toFixed(0) || "—"} L/min` : `${latest?.pressure?.toFixed(1) || "—"} bar`, status: "normal" },
                  { label: "Energy", value: `${latest?.energyKwh?.toFixed(1) || "—"} kWh`, status: "normal" },
                  { label: "Cost Rate", value: `${latest?.costRate?.toFixed(2) || "—"} EGP`, status: latest?.isPeak ? "peak" : "normal" },
                ].map((s) => (
                  <div key={s.label} className="flex items-center justify-between text-xs py-1.5 border-b border-border last:border-0">
                    <span className="text-text-tertiary">{s.label}</span>
                    <span className={`font-mono font-medium ${s.status === "warning" ? "text-warning" : s.status === "peak" ? "text-danger" : "text-text-primary"}`}>
                      {s.value}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
