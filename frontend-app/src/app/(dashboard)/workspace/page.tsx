"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { KPICard } from "@/components/data-display/kpi-card";
import { StatusBadge } from "@/components/data-display/status-badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Factory, Zap, DollarSign, Brain, Activity, AlertTriangle,
  ArrowRight, TrendingUp, Clock, Plus,
} from "lucide-react";
import { useTelemetryStore } from "@/store/telemetry-store";
import { generateMockAlerts, generateMockXAILogs } from "@/services/mock-data";
import { formatCurrency, getRelativeTime } from "@/lib/utils";

const factories = [
  { id: "factory-1", name: "Cairo Industrial Complex", location: "Cairo, Egypt", status: "RUNNING" as const, machines: 5, alerts: 2, energy: 847.3, saved: 2340, efficiency: 87 },
  { id: "factory-2", name: "Alexandria Port Facility", location: "Alexandria, Egypt", status: "RUNNING" as const, machines: 4, alerts: 0, energy: 623.1, saved: 1580, efficiency: 91 },
  { id: "factory-3", name: "Alamein Processing Plant", location: "El Alamein, Egypt", status: "WARNING" as const, machines: 3, alerts: 4, energy: 412.8, saved: 900, efficiency: 73 },
];

const stagger = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 } };

export default function WorkspacePage() {
  const { kpis } = useTelemetryStore();
  const alerts = generateMockAlerts();
  const xaiLogs = generateMockXAILogs(5);

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            Workspace
          </h1>
          <p className="text-sm text-text-tertiary mt-0.5">Alamein Manufacturing — Overview</p>
        </div>
        <Button variant="outline" size="sm">
          <Plus size={14} /> Add Factory
        </Button>
      </div>

      {/* KPI Row */}
      <motion.div
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        initial="initial" animate="animate"
        transition={{ staggerChildren: 0.08 }}
      >
        <motion.div {...stagger}><KPICard label="Total Factories" value={kpis.totalFactories} icon={<Factory size={16} />} accentColor="var(--color-accent)" /></motion.div>
        <motion.div {...stagger}><KPICard label="Active Machines" value={kpis.activeMachines} suffix="" trend={5.2} icon={<Activity size={16} />} accentColor="var(--color-cyan)" /></motion.div>
        <motion.div {...stagger}><KPICard label="Energy Saved" value={kpis.totalEnergySavedKwh} suffix=" kWh" trend={12.8} icon={<Zap size={16} />} accentColor="var(--color-success)" /></motion.div>
        <motion.div {...stagger}><KPICard label="Cost Saved Today" value={kpis.totalCostSaved} prefix="" suffix=" EGP" trend={18.3} icon={<DollarSign size={16} />} accentColor="var(--color-accent)" /></motion.div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Factories Grid */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold text-text-primary">Factories</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {factories.map((f, i) => (
              <motion.div key={f.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + i * 0.08, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}>
                <Link href={`/factory/${f.id}`}>
                  <Card spotlight className="group cursor-pointer hover:border-accent/20 transition-all duration-300">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="group-hover:text-accent transition-colors">{f.name}</CardTitle>
                        <StatusBadge status={f.status} size="sm" />
                      </div>
                      <p className="text-[11px] text-text-tertiary">{f.location}</p>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-mono">Machines</p>
                          <p className="text-sm font-semibold text-text-primary">{f.machines}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-mono">Energy</p>
                          <p className="text-sm font-semibold text-text-primary">{f.energy} <span className="text-[10px] text-text-tertiary">kWh</span></p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-mono">Saved</p>
                          <p className="text-sm font-semibold text-success">{formatCurrency(f.saved)}</p>
                        </div>
                      </div>
                      {f.alerts > 0 && (
                        <div className="mt-3 flex items-center gap-1.5 text-[11px] text-warning">
                          <AlertTriangle size={12} />
                          <span>{f.alerts} active alert{f.alerts > 1 ? "s" : ""}</span>
                        </div>
                      )}
                      <div className="mt-3 flex items-center justify-between">
                        <div className="flex items-center gap-1 text-[11px] text-text-tertiary">
                          <TrendingUp size={11} />
                          <span>{f.efficiency}% efficiency</span>
                        </div>
                        <ArrowRight size={14} className="text-text-muted group-hover:text-accent transition-colors" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right Column — Alerts + AI Activity */}
        <div className="space-y-4">
          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2"><AlertTriangle size={14} className="text-warning" /> Recent Alerts</CardTitle>
                <Link href="/alerts"><Badge variant="outline" size="sm" className="cursor-pointer">View All</Badge></Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alerts.slice(0, 3).map((a) => (
                  <div key={a.id} className="flex gap-3 text-xs">
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${a.severity === "critical" ? "bg-danger" : a.severity === "warning" ? "bg-warning" : "bg-info"}`} />
                    <div className="min-w-0">
                      <p className="text-text-primary font-medium truncate">{a.title}</p>
                      <p className="text-text-tertiary truncate">{a.machineName || "Factory-wide"}</p>
                      <p className="text-text-muted text-[10px] mt-0.5">{getRelativeTime(a.timestamp)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Activity */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2"><Brain size={14} className="text-accent" /> AI Activity</CardTitle>
                <Link href="/ai-control"><Badge variant="accent" size="sm" className="cursor-pointer">Control Center</Badge></Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {xaiLogs.slice(0, 4).map((log) => (
                  <div key={log.id} className="flex gap-3 text-xs">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 bg-accent" />
                    <div className="min-w-0">
                      <p className="text-text-primary font-medium">{log.action.replace(/_/g, " ")}</p>
                      <p className="text-text-tertiary truncate">{log.machineName}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-success text-[10px]">~{Math.round(log.savingsEstimate)} EGP/hr</span>
                        <span className="text-text-muted text-[10px]">{getRelativeTime(log.timestamp)}</span>
                      </div>
                    </div>
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
