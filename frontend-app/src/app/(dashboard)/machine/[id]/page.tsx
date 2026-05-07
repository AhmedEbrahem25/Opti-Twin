"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { KPICard } from "@/components/data-display/kpi-card";
import { StatusBadge } from "@/components/data-display/status-badge";
import { MetricRing } from "@/components/data-display/metric-ring";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MACHINE_SCHEMAS } from "@/lib/constants";
import { generateTelemetryPoint, generateMockXAILogs } from "@/services/mock-data";
import { formatTemperature, formatEnergy, getRelativeTime } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine,
} from "recharts";
import {
  Zap, DollarSign, Thermometer, Gauge, Activity, Brain,
  AlertTriangle, Box, ArrowRight, Settings, TrendingDown,
} from "lucide-react";
import type { TelemetryPoint } from "@/types";

export default function MachinePage({ params }: { params: Promise<{ id: string }> }) {
  const [data, setData] = useState<TelemetryPoint[]>([]);
  const xaiLogs = generateMockXAILogs(6);

  useEffect(() => {
    // Generate initial data
    const initial = Array.from({ length: 30 }, (_, i) => {
      const p = generateTelemetryPoint("factory-1-m1");
      const ts = new Date(Date.now() - (30 - i) * 3000);
      return { ...p, timestamp: ts.toISOString() };
    });
    setData(initial);

    // Live updates
    const interval = setInterval(() => {
      const point = generateTelemetryPoint("factory-1-m1");
      setData((prev) => [...prev.slice(-59), point]);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const latest = data[data.length - 1];
  const chartData = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    temperature: d.temperature,
    energy: d.energyKwh,
    rpm: d.rpm,
  }));

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
                Machine A — Motor
              </h1>
              <StatusBadge status={latest?.status || "RUNNING"} />
            </div>
            <p className="text-sm text-text-tertiary mt-0.5">Electric Motor · Cairo Industrial Complex · Line 1</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="accent" size="sm"><Box size={14} /> Digital Twin</Button>
          <Button variant="ghost" size="icon-sm"><Settings size={15} /></Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard label="Temperature" value={latest?.temperature || 0} suffix="°C" icon={<Thermometer size={16} />} accentColor="var(--color-danger)" />
        <KPICard label="RPM" value={latest?.rpm || 0} suffix="" icon={<Gauge size={16} />} accentColor="var(--color-cyan)" format={(v) => Math.round(v).toString()} />
        <KPICard label="Energy Usage" value={latest?.energyKwh || 0} suffix=" kWh" icon={<Zap size={16} />} accentColor="var(--color-warning)" />
        <KPICard label="Cost Rate" value={latest?.costRate || 0} suffix=" EGP/kWh" icon={<DollarSign size={16} />} accentColor={latest?.isPeak ? "var(--color-danger)" : "var(--color-success)"} />
        <div className="flex items-center justify-center">
          <MetricRing value={88} size={72} strokeWidth={5} label="Health" />
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
                    <YAxis tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} domain={[40, 100]} />
                    <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} />
                    <ReferenceLine y={90} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: "Critical 90°C", position: "right", style: { fontSize: 9, fill: "#ef4444" } }} />
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
              <div className="space-y-3">
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
                  { label: "Temperature", value: `${latest?.temperature?.toFixed(1) || "—"}°C`, status: (latest?.temperature || 0) > 85 ? "warning" : "normal" },
                  { label: "RPM", value: `${Math.round(latest?.rpm || 0)}`, status: "normal" },
                  { label: "Vibration", value: `${latest?.vibration?.toFixed(1) || "—"} mm/s`, status: (latest?.vibration || 0) > 4.5 ? "warning" : "normal" },
                  { label: "Pressure", value: `${latest?.pressure?.toFixed(1) || "—"} bar`, status: "normal" },
                  { label: "Energy", value: `${latest?.energyKwh?.toFixed(1) || "—"} kWh`, status: "normal" },
                  { label: "Cost Rate", value: `${latest?.costRate || "—"} EGP`, status: latest?.isPeak ? "peak" : "normal" },
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
