"use client";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { generateMockAlerts } from "@/services/mock-data";
import { getRelativeTime } from "@/lib/utils";
import { Clock, Check, Zap } from "lucide-react";
import { useTelemetryStore } from "@/store/telemetry-store";
import { api, type CrisisEvent } from "@/lib/api";
import type { Alert as AlertT } from "@/types";

const CRISIS_EVENTS: { event: CrisisEvent; label: string }[] = [
  { event: "wall_overheat", label: "Wall overheat" },
  { event: "electrode_break", label: "Electrode break" },
  { event: "grid_spike", label: "Grid spike" },
  { event: "transformer_alarm", label: "Transformer alarm" },
];

export default function AlertsPage() {
  const liveAlerts = useTelemetryStore((s) => s.liveAlerts);
  const allAlerts = useMemo<AlertT[]>(
    // Show only live alerts when the backend is connected; fall back to mock so
    // the page is never empty during an offline demo.
    () => liveAlerts.length > 0 ? liveAlerts : generateMockAlerts(),
    [liveAlerts],
  );
  const [filter, setFilter] = useState<string>("all");
  const alerts = filter === "all" ? allAlerts : allAlerts.filter((a) => a.severity === filter);
  const [acknowledgedIds, setAcknowledgedIds] = useState<Set<string>>(new Set());
  const [injectingEvent, setInjectingEvent] = useState<CrisisEvent | null>(null);
  const [injectedEvent, setInjectedEvent] = useState<CrisisEvent | null>(null);

  const handleInject = async (event: CrisisEvent) => {
    setInjectingEvent(event);
    try {
      await api.injectCrisis(event);
      setInjectedEvent(event);
      setTimeout(() => setInjectedEvent(null), 2000);
    } catch {
      // backend unavailable — swallow silently in demo
    } finally {
      setInjectingEvent(null);
    }
  };

  const handleAcknowledge = (id: string) => {
    setAcknowledgedIds((prev) => { const next = new Set(prev); next.add(id); return next; });
  };

  const severityIcon = (severity: string) => {
    if (severity === "critical" || severity === "emergency") return <span className="w-2 h-2 rounded-full bg-danger shrink-0" />;
    if (severity === "warning") return <span className="w-2 h-2 rounded-full bg-warning shrink-0" />;
    return <span className="w-2 h-2 rounded-full bg-info shrink-0" />;
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">Alerts & Incidents</h1>
          <p className="text-sm text-text-tertiary mt-0.5">{allAlerts.filter((a) => !a.acknowledged).length} unacknowledged alerts</p>
        </div>
        <div className="flex items-center gap-2">
          {["all", "critical", "warning", "info"].map((f) => (
            <Button key={f} variant={filter === f ? "accent" : "ghost"} size="sm" onClick={() => setFilter(f)} className="capitalize text-xs">
              {f}
            </Button>
          ))}
        </div>
      </div>

      {/* Crisis injection (demo) */}
      <Card>
        <div className="p-4 flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 text-xs text-text-tertiary mr-2">
            <Zap size={14} className="text-accent" />
            <span>Inject crisis (simulator):</span>
          </div>
          {CRISIS_EVENTS.map(({ event, label }) => (
            <Button
              key={event}
              variant={injectedEvent === event ? "accent" : "outline"}
              size="sm"
              onClick={() => handleInject(event)}
              disabled={injectingEvent !== null}
              className="text-xs"
            >
              {injectedEvent === event ? <><Check size={12} /> Injected</> : label}
            </Button>
          ))}
        </div>
      </Card>

      <div className="space-y-3">
        {alerts.map((alert, i) => (
          <motion.div key={alert.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05, duration: 0.3 }}>
            <Card className={`transition-all ${!alert.acknowledged ? "border-l-2" : ""} ${alert.severity === "critical" ? "border-l-danger" : alert.severity === "warning" ? "border-l-warning" : "border-l-info"}`}>
              <div className="p-4 flex items-start gap-4">
                <div className="mt-1">{severityIcon(alert.severity)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-text-primary">{alert.title}</h3>
                    <Badge variant={alert.severity === "critical" ? "danger" : alert.severity === "warning" ? "warning" : "info"} size="sm">{alert.severity}</Badge>
                    {!alert.acknowledged && !acknowledgedIds.has(alert.id) && <Badge variant="outline" size="sm">New</Badge>}
                  </div>
                  <p className="text-xs text-text-tertiary mb-2">{alert.message}</p>
                  <div className="flex items-center gap-4 text-[10px] text-text-muted">
                    {alert.machineName && <span>{alert.machineName}</span>}
                    <span className="flex items-center gap-1"><Clock size={10} /> {getRelativeTime(alert.timestamp)}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => handleAcknowledge(alert.id)}
                  title="Acknowledge"
                  disabled={acknowledgedIds.has(alert.id) || alert.acknowledged}
                >
                  {acknowledgedIds.has(alert.id) || alert.acknowledged
                    ? <Check size={14} className="text-success" />
                    : <Check size={14} />}
                </Button>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
