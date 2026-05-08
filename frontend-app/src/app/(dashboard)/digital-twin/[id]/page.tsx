"use client";
import { use, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/data-display/status-badge";
import { MetricRing } from "@/components/data-display/metric-ring";
import { generateTelemetryPoint } from "@/services/mock-data";
import { useTelemetryStore } from "@/store/telemetry-store";
import { LIVE_MACHINE_ID } from "@/lib/backend-types";
import { Box, Thermometer, Gauge, Zap, Activity, RotateCcw, Maximize2, Eye } from "lucide-react";
import type { TelemetryPoint } from "@/types";

export default function DigitalTwinPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const isLive = id === LIVE_MACHINE_ID;
  const liveLatest = useTelemetryStore((s) => s.latestPoints.get(id));

  const [mockLatest, setMockLatest] = useState<TelemetryPoint | null>(() =>
    generateTelemetryPoint(id),
  );

  useEffect(() => {
    if (isLive) return;
    const interval = setInterval(() => {
      setMockLatest(generateTelemetryPoint(id));
    }, 3000);
    return () => clearInterval(interval);
  }, [id, isLive]);

  const latest: TelemetryPoint | undefined = isLive ? liveLatest : mockLatest ?? undefined;

  // Derive health from temperature: 100 at cool, 0 at/above critical threshold.
  const healthScore = (() => {
    const t = latest?.temperature;
    if (t === undefined) return 88;
    if (isLive) return Math.max(0, Math.min(100, Math.round(100 - Math.max(0, (t - 1600) / 50) * 100)));
    return Math.max(0, Math.min(100, Math.round(100 - Math.max(0, (t - 85) / 15) * 100)));
  })();

  const headerTitle = isLive ? "Digital Twin — EAF #2" : "Digital Twin";
  const headerSub = isLive
    ? "EAF #2 · Ezz Steel — Ain Sokhna · Line 2"
    : "Industrial machine";

  // Sensor overlay points adapted to whichever telemetry shape is current.
  const sensorPoints = isLive
    ? [
        { id: "s1", label: "Bath Temp", value: `${(latest?.temperature ?? 1580).toFixed(0)}°C`, x: 35, y: 30, status: "normal" as const },
        { id: "s2", label: "Arc Power", value: `${((latest?.energyKwh ?? 95000) / 1000).toFixed(1)} MW`, x: 50, y: 45, status: "normal" as const },
        { id: "s3", label: "PF Δ proxy", value: `${(latest?.vibration ?? 0).toFixed(2)}`, x: 65, y: 35, status: (latest?.vibration ?? 0) > 4 ? "warning" as const : "normal" as const },
        { id: "s4", label: "Cooling Flow", value: `${(latest?.flowRate ?? 200).toFixed(0)} L/min`, x: 40, y: 60, status: "normal" as const },
      ]
    : [
        { id: "s1", label: "Bearing Temp", value: `${(latest?.temperature || 72).toFixed(1)}°C`, x: 35, y: 30, status: "normal" as const },
        { id: "s2", label: "Shaft RPM", value: `${Math.round(latest?.rpm || 1450)}`, x: 50, y: 45, status: "normal" as const },
        { id: "s3", label: "Vibration", value: `${(latest?.vibration || 2.3).toFixed(1)} mm/s`, x: 65, y: 35, status: (latest?.vibration || 0) > 4 ? "warning" as const : "normal" as const },
        { id: "s4", label: "Current Draw", value: `${(latest?.energyKwh || 112).toFixed(0)} kWh`, x: 40, y: 60, status: "normal" as const },
      ];

  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cyan/10 border border-cyan/20 flex items-center justify-center">
            <Box size={24} className="text-cyan" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">{headerTitle}</h1>
              <StatusBadge status={latest?.status ?? "RUNNING"} />
              <Badge variant="info" pulse size="sm">Live Sync</Badge>
            </div>
            <p className="text-sm text-text-tertiary mt-0.5">{headerSub}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon-sm" title="Refresh telemetry"><RotateCcw size={15} /></Button>
          <Button variant="ghost" size="icon-sm" title="Fullscreen (Three.js integration pending)"><Maximize2 size={15} /></Button>
          <Button variant="secondary" size="sm" title="Thermal overlay (Three.js integration pending)"><Eye size={14} /> Thermal View</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 3D Viewport Placeholder */}
        <div className="lg:col-span-2">
          <Card className="overflow-hidden">
            <div className="relative bg-bg-100 h-[500px] flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-to-b from-bg-200 via-bg-100 to-bg-300" />
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.15),transparent_60%)]" />
              <div className="absolute bottom-0 left-0 right-0 h-48 opacity-10" style={{ background: "linear-gradient(transparent, rgba(34,211,238,0.05))", backgroundImage: "repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0px, transparent 1px, transparent 40px), repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0px, transparent 1px, transparent 40px)" }} />

              <motion.div
                className="relative z-10"
                animate={{ rotateY: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                style={{ perspective: 800 }}
              >
                <div className="w-48 h-48 rounded-2xl border-2 border-cyan/30 bg-gradient-to-br from-bg-400 to-bg-300 flex items-center justify-center shadow-[0_0_60px_rgba(34,211,238,0.1)]">
                  <div className="w-32 h-32 rounded-xl border border-cyan/20 bg-bg-200 flex items-center justify-center">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }}>
                      <Gauge size={48} className="text-cyan/60" />
                    </motion.div>
                  </div>
                </div>
              </motion.div>

              {sensorPoints.map((sp) => (
                <motion.div
                  key={sp.id}
                  className="absolute z-20 group"
                  style={{ left: `${sp.x}%`, top: `${sp.y}%` }}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.3 }}
                >
                  <div className={`w-3 h-3 rounded-full border-2 cursor-pointer transition-all group-hover:scale-150 ${sp.status === "warning" ? "bg-warning border-warning/50 shadow-[0_0_12px_rgba(245,158,11,0.4)]" : "bg-cyan border-cyan/50 shadow-[0_0_12px_rgba(34,211,238,0.3)]"}`} />
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                    <div className="bg-bg-400 border border-border rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                      <p className="text-[10px] text-text-tertiary">{sp.label}</p>
                      <p className={`text-xs font-mono font-bold ${sp.status === "warning" ? "text-warning" : "text-text-primary"}`}>{sp.value}</p>
                    </div>
                  </div>
                </motion.div>
              ))}

              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
                <span className="type-label bg-bg-400/80 backdrop-blur px-2 py-1 rounded text-[10px]">
                  Placeholder — Three.js / R3F integration ready
                </span>
                <span className="type-label bg-bg-400/80 backdrop-blur px-2 py-1 rounded text-[10px] flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan pulse-live" /> Real-time sync active
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right — Live Metrics Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Activity size={14} className="text-cyan" /> Live Metrics</CardTitle></CardHeader>
            <CardContent>
              <div className="flex justify-center mb-4">
                <MetricRing value={healthScore} size={90} strokeWidth={6} label="Health" color="var(--color-cyan)" />
              </div>
              <div className="space-y-3">
                {(isLive
                  ? [
                      { icon: Thermometer, label: "Bath Temp", value: `${latest?.temperature?.toFixed(0) || "—"}°C`, color: "text-danger" },
                      { icon: Gauge, label: "Arc Power", value: `${((latest?.energyKwh ?? 0) / 1000).toFixed(1)} MW`, color: "text-cyan" },
                      { icon: Activity, label: "PF Δ proxy", value: `${latest?.vibration?.toFixed(2) || "—"}`, color: "text-accent" },
                      { icon: Zap, label: "Energy", value: `${latest?.energyKwh?.toFixed(0) || "—"} kWh`, color: "text-warning" },
                    ]
                  : [
                      { icon: Thermometer, label: "Temperature", value: `${latest?.temperature?.toFixed(1) || "—"}°C`, color: "text-danger" },
                      { icon: Gauge, label: "RPM", value: `${Math.round(latest?.rpm || 0)}`, color: "text-cyan" },
                      { icon: Activity, label: "Vibration", value: `${latest?.vibration?.toFixed(1) || "—"} mm/s`, color: "text-accent" },
                      { icon: Zap, label: "Energy", value: `${latest?.energyKwh?.toFixed(1) || "—"} kWh`, color: "text-warning" },
                    ]
                ).map((m) => (
                  <div key={m.label} className="flex items-center justify-between text-xs py-1.5 border-b border-border last:border-0">
                    <div className="flex items-center gap-2">
                      <m.icon size={13} className={m.color} />
                      <span className="text-text-tertiary">{m.label}</span>
                    </div>
                    <span className="font-mono font-medium text-text-primary">{m.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Sensor Overlay</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-text-tertiary mb-3">Hover over sensor points on the 3D model to view live readings.</p>
              <div className="space-y-2">
                {sensorPoints.map((sp) => (
                  <div key={sp.id} className="flex items-center justify-between text-xs py-1 border-b border-border last:border-0">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${sp.status === "warning" ? "bg-warning" : "bg-cyan"}`} />
                      <span className="text-text-secondary">{sp.label}</span>
                    </div>
                    <span className={`font-mono ${sp.status === "warning" ? "text-warning" : "text-text-primary"}`}>{sp.value}</span>
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
