"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { KPICard } from "@/components/data-display/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTelemetryStore } from "@/store/telemetry-store";
import { api, type DPEMode, type DREventType, type ProfileName } from "@/lib/api";
import { getRelativeTime } from "@/lib/utils";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { Brain, DollarSign, Activity, Power, CheckCircle, XCircle, Lightbulb, Shield, Zap, Settings2 } from "lucide-react";

const PROFILES: { id: ProfileName; label: string; hint: string }[] = [
  { id: "default", label: "Default", hint: "Balanced α=1.0 β=0.9 γ=1.8" },
  { id: "cost_first", label: "Cost-first", hint: "Maximise EGP saved" },
  { id: "equipment_sensitive", label: "Equipment-safe", hint: "Protect refractory" },
  { id: "production_critical", label: "Production-first", hint: "Hit batch targets" },
  { id: "quality_focused", label: "Quality-focused", hint: "Steady bath temp" },
];

const DPE_MODES: { id: DPEMode; label: string; hint: string }[] = [
  { id: "flat", label: "Flat", hint: "1.60 EGP/kWh (current EgyptERA)" },
  { id: "sim_tou", label: "TOU", hint: "Peak/off-peak (reform)" },
  { id: "sim_spot", label: "Spot", hint: "Synthetic intraday" },
  { id: "live_eehc", label: "Live EEHC", hint: "Real-time stub" },
];

const DR_TYPES: { id: DREventType; label: string }[] = [
  { id: "CURTAILMENT", label: "Curtailment" },
  { id: "INTERRUPTIBLE", label: "Interruptible" },
  { id: "FREQUENCY_RESPONSE", label: "Freq. response" },
];

const PROFILE_WEIGHTS: Record<ProfileName, { alpha: number; beta: number; gamma: number }> = {
  default:              { alpha: 1.0, beta: 0.9, gamma: 1.8 },
  cost_first:          { alpha: 2.0, beta: 0.5, gamma: 0.8 },
  equipment_sensitive: { alpha: 0.8, beta: 2.0, gamma: 1.0 },
  production_critical: { alpha: 0.8, beta: 0.7, gamma: 2.5 },
  quality_focused:     { alpha: 1.2, beta: 1.5, gamma: 1.5 },
};

const AI_MODELS = [
  { id: "M1", name: "PPO Policy", desc: "SB3 actor-critic", activeWhen: "ai", badge: "Core" },
  { id: "M2", name: "LSTM Forecaster", desc: "24 h price ahead", activeWhen: "always", badge: "Forecast" },
  { id: "M3", name: "Anomaly AE", desc: "Sensor autoencoder", activeWhen: "always", badge: "Safety" },
  { id: "M6", name: "Predictive Maintenance", desc: "Risk + safe recovery", activeWhen: "always", badge: "Live" },
  { id: "M4", name: "Behavioral Clone", desc: "Operator imitation", activeWhen: "passive", badge: "Stub" },
  { id: "M5", name: "Preference Reward", desc: "Profile α–γ injector", activeWhen: "ai", badge: "Reward" },
] as const;

function buildHourlyActions(xaiLogs: { timestamp: string; savingsEstimate: number }[]) {
  const now = new Date();
  const buckets: Record<string, { actions: number; savings: number }> = {};
  // Pre-fill last 12 hours so the chart always has shape.
  for (let i = 11; i >= 0; i--) {
    const h = new Date(now.getTime() - i * 3_600_000);
    const key = `${h.getHours().toString().padStart(2, "0")}:00`;
    buckets[key] = { actions: 0, savings: 0 };
  }
  for (const log of xaiLogs) {
    const h = new Date(log.timestamp).getHours().toString().padStart(2, "0") + ":00";
    if (buckets[h]) {
      buckets[h].actions += 1;
      buckets[h].savings += log.savingsEstimate;
    }
  }
  return Object.entries(buckets).map(([hour, v]) => ({
    hour,
    actions: v.actions,
    savings: Math.round(v.savings),
  }));
}

export default function AIControlPage() {
  const aiEnabled = useTelemetryStore((s) => s.aiEnabled);
  const toggleAI = useTelemetryStore((s) => s.toggleAI);
  const kpis = useTelemetryStore((s) => s.kpis);
  const xaiLogsLive = useTelemetryStore((s) => s.xaiLogs);
  const aiProfile = useTelemetryStore((s) => s.aiProfile);
  const setAIProfile = useTelemetryStore((s) => s.setAIProfile);
  const dpeMode = useTelemetryStore((s) => s.dpeMode);
  const setDPEMode = useTelemetryStore((s) => s.setDPEMode);
  const touMode = useTelemetryStore((s) => s.touMode);
  const setTouMode = useTelemetryStore((s) => s.setTouMode);
  const drSnapshot = useTelemetryStore((s) => s.drSnapshot);
  const xaiLogs = xaiLogsLive.slice(0, 12);
  const [selectedLog, setSelectedLog] = useState<string | null>(null);
  const livePrice = useTelemetryStore((s) => s.livePrice);
  const hourlyActions = buildHourlyActions(xaiLogsLive);

  const w = PROFILE_WEIGHTS[aiProfile];
  const rewardData = [
    { name: "Energy Savings (α)", value: w.alpha, color: "#22c55e" },
    { name: "Machine Stress (β)", value: w.beta,  color: "#ef4444" },
    { name: "Production Delay (γ)", value: w.gamma, color: "#f59e0b" },
  ];

  const handleToggle = () => {
    const next = !aiEnabled;
    toggleAI();
    api.toggleAI(next).catch((err) => {
      console.error("toggleAI failed", err);
      toggleAI();
    });
  };

  const handleProfile = (p: ProfileName) => {
    setAIProfile(p);
    api.setProfile(p).catch((err) => console.error("setProfile failed", err));
  };

  const handleDPEMode = (m: DPEMode) => {
    setDPEMode(m);
    api.setPricingMode(m).catch((err) => console.error("setPricingMode failed", err));
  };

  const handleTou = () => {
    const next = !touMode;
    setTouMode(next);
    api.setTariffMode(next).catch((err) => console.error("setTariffMode failed", err));
  };

  const handleDR = (t: DREventType) => {
    api.injectDREvent(t, 30, 30).catch((err) =>
      console.error("injectDREvent failed", err),
    );
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            AI Control Center
          </h1>
          <p className="text-sm text-text-tertiary mt-0.5">Reinforcement Learning Agent — PPO Algorithm</p>
        </div>
        {/* AI Toggle */}
        <motion.button
          onClick={handleToggle}
          className={`flex items-center gap-3 px-5 py-2.5 rounded-xl border-2 transition-all cursor-pointer ${
            aiEnabled
              ? "bg-accent/10 border-accent/40 text-accent shadow-[0_0_24px_rgba(245,158,11,0.12)]"
              : "bg-bg-300 border-border text-text-tertiary"
          }`}
          whileTap={{ scale: 0.97 }}
        >
          <Power size={18} />
          <span className="text-sm font-semibold">{aiEnabled ? "AI Agent Active" : "AI Agent Off"}</span>
          <span className={`w-2.5 h-2.5 rounded-full ${aiEnabled ? "bg-accent pulse-live" : "bg-text-muted"}`} />
        </motion.button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="AI Actions Today" value={kpis.aiActionsToday} icon={<Brain size={16} />} trend={8.5} accentColor="var(--color-accent)" />
        <KPICard label="Total Savings" value={kpis.totalCostSaved} suffix=" EGP" icon={<DollarSign size={16} />} trend={18.3} accentColor="var(--color-success)" />
        <KPICard label="Ops Efficiency" value={kpis.avgOperationalEfficiency || kpis.avgEfficiency} suffix="%" icon={<CheckCircle size={16} />} accentColor="var(--color-info)" />
        <KPICard label="Maint. Risk" value={kpis.avgMaintenanceRisk * 100} suffix="%" icon={<Shield size={16} />} accentColor={kpis.avgMaintenanceRisk >= 0.55 ? "var(--color-danger)" : "var(--color-cyan)"} />
      </div>

      {/* Policy / Pricing controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Reward profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2"><Settings2 size={14} className="text-accent" /> Reward Profile</CardTitle>
              <Badge variant="outline" size="sm">{aiProfile}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {PROFILES.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleProfile(p.id)}
                  className={`text-left rounded-lg border px-3 py-2 transition-all ${aiProfile === p.id ? "bg-accent/10 border-accent/50 text-accent" : "bg-bg-300 border-border text-text-secondary hover:border-border-hover"}`}
                >
                  <div className="text-xs font-semibold">{p.label}</div>
                  <div className="text-[10px] text-text-tertiary mt-0.5">{p.hint}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Pricing engine */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2"><Zap size={14} className="text-cyan" /> Pricing Engine</CardTitle>
              <Badge variant="outline" size="sm">{dpeMode}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {DPE_MODES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => handleDPEMode(m.id)}
                  className={`text-left rounded-lg border px-3 py-2 transition-all ${dpeMode === m.id ? "bg-cyan/10 border-cyan/50 text-cyan" : "bg-bg-300 border-border text-text-secondary hover:border-border-hover"}`}
                >
                  <div className="text-xs font-semibold">{m.label}</div>
                  <div className="text-[10px] text-text-tertiary mt-0.5">{m.hint}</div>
                </button>
              ))}
            </div>
            <div className="flex items-center justify-between text-xs py-2 border-t border-border">
              <div>
                <div className="font-medium text-text-secondary">Tariff TOU mode (simulator)</div>
                <div className="text-[10px] text-text-tertiary">When on, the simulator applies peak/off-peak prices</div>
              </div>
              <button
                onClick={handleTou}
                className={`px-3 py-1 rounded-md border text-[11px] font-semibold transition-all ${touMode ? "bg-warning/10 border-warning/40 text-warning" : "bg-bg-300 border-border text-text-tertiary"}`}
              >
                {touMode ? "ON" : "OFF"}
              </button>
            </div>
            <div className="flex items-center justify-between text-xs pt-3 mt-2 border-t border-border">
              <div>
                <div className="font-medium text-text-secondary">Inject DR event</div>
                <div className="text-[10px] text-text-tertiary">
                  Today payments: {drSnapshot?.total_payments_today?.toFixed(0) ?? "0"} EGP
                </div>
              </div>
              <div className="flex gap-1">
                {DR_TYPES.map((d) => (
                  <Button key={d.id} variant="outline" size="sm" onClick={() => handleDR(d.id)} className="text-[10px]">
                    {d.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left — Charts + Decision Log */}
        <div className="lg:col-span-2 space-y-4">
          {/* Actions Per Hour */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Activity size={14} className="text-accent" /> AI Actions Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourlyActions}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="actions" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* XAI Decision Log */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2"><Lightbulb size={14} className="text-accent" /> Explainable AI Decision Log</CardTitle>
                <Badge variant="accent" pulse size="sm">Streaming</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {xaiLogs.length === 0 && (
                  <p className="text-[11px] text-text-tertiary px-3 py-6 text-center">
                    Waiting for AI decisions from the backend…
                  </p>
                )}
                {xaiLogs.map((log, i) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03, duration: 0.3 }}
                    className={`p-3 rounded-lg border transition-all cursor-pointer ${
                      selectedLog === log.id ? "bg-bg-400 border-accent/30" : "bg-bg-300 border-border hover:border-border-hover"
                    }`}
                    onClick={() => setSelectedLog(selectedLog === log.id ? null : log.id)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <Badge variant={log.applied ? "success" : "outline"} size="sm">
                          {log.applied ? <><CheckCircle size={10} /> Applied</> : <><XCircle size={10} /> Skipped</>}
                        </Badge>
                        <span className="text-xs font-medium text-text-primary">{log.action.replace(/_/g, " ")}</span>
                      </div>
                      <span className="text-[10px] text-text-muted font-mono">{getRelativeTime(log.timestamp)}</span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="text-text-tertiary">{log.machineName}</span>
                      <span className="text-success">~{Math.round(log.savingsEstimate)} EGP/hr</span>
                      <span className="text-text-muted">{log.confidence.toFixed(0)}%</span>
                    </div>
                    {selectedLog === log.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        className="mt-2 pt-2 border-t border-border"
                      >
                        <p className="text-[11px] text-text-tertiary leading-relaxed">
                          <span className="text-text-secondary font-medium">XAI Reason:</span> {log.reason}
                        </p>
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right — Reward Function + Stats */}
        <div className="space-y-4">
          {/* Reward Function */}
          <Card>
            <CardHeader>
              <CardTitle>Reward Function Weights</CardTitle>
              <p className="text-[10px] text-text-tertiary mt-0.5">R = α(E_saved) − β(M_stress) − γ(P_delay)</p>
            </CardHeader>
            <CardContent>
              <div className="h-40 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={rewardData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" startAngle={90} endAngle={-270}>
                      {rewardData.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {rewardData.map((r) => (
                  <div key={r.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ background: r.color }} />
                      <span className="text-text-secondary">{r.name}</span>
                    </div>
                    <span className="font-mono text-text-primary">{r.value.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Model Stack */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2"><Brain size={14} className="text-accent" /> AI Model Stack</CardTitle>
                {livePrice && (
                  <Badge variant={livePrice.is_peak ? "warning" : "success"} size="sm">
                    {livePrice.is_peak ? "Peak" : "Off-peak"} · {livePrice.price_egp_kwh.toFixed(2)} EGP
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {AI_MODELS.map((m) => {
                  const isActive =
                    m.activeWhen === "always" ||
                    (m.activeWhen === "ai" && aiEnabled) ||
                    m.activeWhen === "passive";
                  const statusColor =
                    m.activeWhen === "passive"
                      ? "text-text-muted"
                      : isActive
                      ? "text-success"
                      : "text-text-muted";
                  const dot =
                    m.activeWhen === "passive"
                      ? "bg-text-muted"
                      : isActive
                      ? "bg-success pulse-live"
                      : "bg-text-muted";
                  return (
                    <div key={m.id} className="flex items-center justify-between bg-bg-300 rounded-lg px-3 py-2 border border-border">
                      <div className="flex items-center gap-2.5">
                        <span className={`w-2 h-2 rounded-full ${dot}`} />
                        <div>
                          <div className="text-xs font-semibold text-text-primary">
                            <span className="font-mono text-text-muted mr-1">{m.id}</span>{m.name}
                          </div>
                          <div className="text-[10px] text-text-tertiary">{m.desc}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Badge variant="outline" size="sm">{m.badge}</Badge>
                        <span className={`text-[10px] font-semibold ${statusColor}`}>
                          {m.activeWhen === "passive" ? "Stub" : isActive ? "Online" : "Standby"}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-3 pt-3 border-t border-border grid grid-cols-2 gap-x-4 gap-y-1">
                {[
                  { label: "Framework", value: "Stable Baselines3" },
                  { label: "Env", value: "OptiTwinFactoryEnv" },
                  { label: "Interval", value: "3 s" },
                  { label: "Version", value: "v2.1-prod" },
                ].map((r) => (
                  <div key={r.label} className="flex items-center justify-between text-[10px] py-0.5">
                    <span className="text-text-tertiary">{r.label}</span>
                    <span className="font-mono text-text-secondary">{r.value}</span>
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
