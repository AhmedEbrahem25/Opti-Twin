"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getRelativeTime } from "@/lib/utils";
import { Search, Filter, Brain, AlertTriangle, Activity, Zap, Clock, ChevronRight } from "lucide-react";

const mockResults = [
  { id: "1", type: "ai_decision", title: "REDUCE_MOTOR_SPEED — Machine A Motor", desc: "Peak pricing (2.5 EGP/kWh). Motor temp safe (68°C < 90°C). Savings ~185 EGP/hr.", timestamp: new Date(Date.now() - 180_000).toISOString(), factory: "Cairo Industrial Complex" },
  { id: "2", type: "alert", title: "Temperature Exceeding Threshold — Furnace #1", desc: "Furnace temperature reached 94°C, exceeding the 90°C critical threshold.", timestamp: new Date(Date.now() - 600_000).toISOString(), factory: "Cairo Industrial Complex" },
  { id: "3", type: "telemetry", title: "Energy Spike Detected — Compressor Unit D", desc: "Energy consumption jumped 34% above baseline during peak hours.", timestamp: new Date(Date.now() - 1200_000).toISOString(), factory: "Alexandria Port Facility" },
  { id: "4", type: "ai_decision", title: "INCREASE_COOLING_POWER — Cooling System B", desc: "Motor stress detected (87°C > 85°C threshold). β-weight override activated.", timestamp: new Date(Date.now() - 2400_000).toISOString(), factory: "Cairo Industrial Complex" },
  { id: "5", type: "alert", title: "Vibration Level Elevated — Motor A", desc: "Motor vibration at 4.8mm/s — approaching warning threshold of 5.0mm/s.", timestamp: new Date(Date.now() - 3600_000).toISOString(), factory: "Alamein Processing Plant" },
  { id: "6", type: "ai_decision", title: "SHIFT_LOAD — Production Line 2", desc: "Off-peak window approaching. Shift non-critical loads to reduce peak demand.", timestamp: new Date(Date.now() - 5400_000).toISOString(), factory: "Alexandria Port Facility" },
];

const typeConfig: Record<string, { icon: typeof Brain; color: string; label: string; variant: "accent" | "danger" | "info" }> = {
  ai_decision: { icon: Brain, color: "text-accent", label: "AI Decision", variant: "accent" },
  alert: { icon: AlertTriangle, color: "text-danger", label: "Alert", variant: "danger" },
  telemetry: { icon: Activity, color: "text-cyan", label: "Telemetry", variant: "info" },
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = mockResults.filter((r) => {
    const matchesQuery = !query || r.title.toLowerCase().includes(query.toLowerCase()) || r.desc.toLowerCase().includes(query.toLowerCase());
    const matchesType = typeFilter === "all" || r.type === typeFilter;
    return matchesQuery && matchesType;
  });

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">Search Console</h1>
        <p className="text-sm text-text-tertiary mt-0.5">Search across AI decisions, alerts, and telemetry events</p>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <Input
          placeholder="Search events, decisions, alerts..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-10 h-11 bg-bg-200 text-base"
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter size={14} className="text-text-tertiary" />
        {["all", "ai_decision", "alert", "telemetry"].map((t) => (
          <Button key={t} variant={typeFilter === t ? "accent" : "ghost"} size="sm" onClick={() => setTypeFilter(t)} className="text-xs capitalize">
            {t === "all" ? "All" : t === "ai_decision" ? "AI Decisions" : t === "alert" ? "Alerts" : "Telemetry"}
          </Button>
        ))}
        <span className="ml-auto text-[11px] text-text-muted">{filtered.length} results</span>
      </div>

      {/* Results */}
      <div className="space-y-2">
        {filtered.map((r, i) => {
          const config = typeConfig[r.type];
          const Icon = config.icon;
          return (
            <motion.div key={r.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04, duration: 0.3 }}>
              <Card className="hover:border-border-hover transition-all cursor-pointer">
                <div className="p-4 flex items-start gap-3">
                  <div className={`mt-0.5 ${config.color}`}><Icon size={16} /></div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-text-primary truncate">{r.title}</h3>
                      <Badge variant={config.variant} size="sm">{config.label}</Badge>
                    </div>
                    <p className="text-xs text-text-tertiary line-clamp-1 mb-1.5">{r.desc}</p>
                    <div className="flex items-center gap-3 text-[10px] text-text-muted">
                      <span>{r.factory}</span>
                      <span className="flex items-center gap-1"><Clock size={10} /> {getRelativeTime(r.timestamp)}</span>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-text-muted mt-1" />
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
