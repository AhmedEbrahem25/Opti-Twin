"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { KPICard } from "@/components/data-display/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTelemetryStore } from "@/store/telemetry-store";
import { generateMockXAILogs, generateMockRecommendation } from "@/services/mock-data";
import { getRelativeTime } from "@/lib/utils";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { Brain, Zap, DollarSign, TrendingDown, Activity, Power, CheckCircle, XCircle, Lightbulb, Shield } from "lucide-react";

const rewardData = [
  { name: "Energy Savings (α)", value: 1.0, color: "#22c55e" },
  { name: "Machine Stress (β)", value: 0.8, color: "#ef4444" },
  { name: "Production Delay (γ)", value: 1.5, color: "#f59e0b" },
];

const hourlyActions = Array.from({ length: 12 }, (_, i) => ({
  hour: `${(8 + i).toString().padStart(2, "0")}:00`,
  actions: Math.floor(Math.random() * 8) + 1,
  savings: Math.floor(Math.random() * 400) + 100,
}));

export default function AIControlPage() {
  const { aiEnabled, toggleAI, kpis } = useTelemetryStore();
  const xaiLogs = generateMockXAILogs(12);
  const [selectedLog, setSelectedLog] = useState<string | null>(null);

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
          onClick={toggleAI}
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
        <KPICard label="Avg Confidence" value={89.4} suffix="%" icon={<Shield size={16} />} accentColor="var(--color-cyan)" />
        <KPICard label="Applied Rate" value={87} suffix="%" icon={<CheckCircle size={16} />} accentColor="var(--color-info)" />
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

          {/* Agent Info */}
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2.5">
                {[
                  { label: "Algorithm", value: "PPO (Proximal Policy Optimization)" },
                  { label: "Framework", value: "Stable Baselines3" },
                  { label: "Environment", value: "OptiTwinFactoryEnv" },
                  { label: "Decision Interval", value: "3 seconds" },
                  { label: "Model Version", value: "v2.1.0-prod" },
                  { label: "Last Trained", value: "2 days ago" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between text-xs py-1.5 border-b border-border last:border-0">
                    <span className="text-text-tertiary">{item.label}</span>
                    <span className="text-text-primary font-mono text-[11px]">{item.value}</span>
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
