"use client";
import { KPICard } from "@/components/data-display/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { BarChart3, Zap, DollarSign, TrendingUp, Download, Calendar, Activity } from "lucide-react";
import { useTelemetryStore } from "@/store/telemetry-store";

const machineTypeData = [
  { name: "EAF Furnace", value: 1, color: "#ef4444" },
  { name: "Cooling", value: 3, color: "#22d3ee" },
  { name: "Compressors", value: 2, color: "#3b82f6" },
  { name: "Motors", value: 4, color: "#f59e0b" },
];

export default function AnalyticsPage() {
  const kpis = useTelemetryStore((s) => s.kpis);
  const forecast = useTelemetryStore((s) => s.forecast);
  const revenue = useTelemetryStore((s) => s.revenue);
  const drSnapshot = useTelemetryStore((s) => s.drSnapshot);
  const livePrice = useTelemetryStore((s) => s.livePrice);
  const schedule = useTelemetryStore((s) => s.schedule);

  const forecastPoints = forecast?.forecast ?? [];
  const forecastData = forecastPoints.map((p: any, i) => {
    const hr = p.t_hour ?? p.hour ?? i;
    const hourStr = `${Math.floor(hr).toString().padStart(2, "0")}:${Math.round((hr % 1) * 60).toString().padStart(2, "0")}`;
    return {
      hour: p.timestamp
        ? new Date(p.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
        : hourStr,
      price: p.p50 ?? p.price_egp_kwh ?? 0,
      p05: p.p10 ?? p.p05,
      p95: p.p90 ?? p.p95,
      isPeak: p.is_peak,
    };
  });

  const revenueData = revenue
    ? [
        { name: "Energy Savings", value: revenue.energy_savings_egp, color: "#22c55e" },
        { name: "DR Payments", value: revenue.dr_payments_egp, color: "#f59e0b" },
        { name: "Capacity Credits", value: revenue.capacity_credits_egp, color: "#22d3ee" },
        { name: "Ancillary", value: revenue.ancillary_egp, color: "#3b82f6" },
      ]
    : [];

  const drEvents = drSnapshot?.events ?? [];

  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            Analytics & Reports
          </h1>
          <p className="text-sm text-text-tertiary mt-0.5">Energy, cost, and performance analysis</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm"><Calendar size={14} /> Last 24 Hours</Button>
          <Button variant="outline" size="sm"><Download size={14} /> Export</Button>
        </div>
      </div>

      {/* KPI Row — live from backend */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Energy Saved" value={kpis.totalEnergySavedKwh} suffix=" kWh" trend={-12.4} icon={<Zap size={16} />} accentColor="var(--color-warning)" />
        <KPICard label="Cost Saved Today" value={kpis.totalCostSaved} suffix=" EGP" trend={18.3} icon={<DollarSign size={16} />} accentColor="var(--color-success)" />
        <KPICard label="Avg Efficiency (PF)" value={kpis.avgEfficiency} suffix="%" trend={3.1} icon={<TrendingUp size={16} />} accentColor="var(--color-accent)" />
        <KPICard label="AI Actions" value={kpis.aiActionsToday} trend={5.8} icon={<BarChart3 size={16} />} accentColor="var(--color-cyan)" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 24h Price Forecast */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap size={14} className="text-accent" /> 24h Price Forecast
              </CardTitle>
              {livePrice && (
                <Badge variant={livePrice.is_peak ? "danger" : "success"} size="sm">
                  Now: {livePrice.price_egp_kwh.toFixed(3)} EGP
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {forecastData.length === 0 ? (
              <p className="text-[11px] text-text-tertiary py-16 text-center">
                Waiting for forecast data from backend…
              </p>
            ) : (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={forecastData}>
                    <defs>
                      <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.25} />
                        <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#22c55e" stopOpacity={0.1} />
                        <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} interval={3} />
                    <YAxis tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} tickFormatter={(v: number) => v.toFixed(2)} />
                    <Tooltip
                      contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
                      formatter={(v) => [`${Number(v).toFixed(3)} EGP/kWh`]}
                    />
                    {forecastData.some((d) => d.p05 !== undefined) && (
                      <Area type="monotone" dataKey="p05" stroke="none" fill="url(#bandGrad)" strokeWidth={0} dot={false} name="P05" />
                    )}
                    <Area type="monotone" dataKey="price" stroke="#f59e0b" fill="url(#priceGrad)" strokeWidth={2} dot={false} name="Price" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Revenue Breakdown */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <DollarSign size={14} className="text-success" /> Revenue Breakdown
              </CardTitle>
              {revenue && (
                <Badge variant="success" size="sm">
                  {revenue.total_revenue_egp.toFixed(0)} EGP total
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {revenueData.length === 0 ? (
              <p className="text-[11px] text-text-tertiary py-16 text-center">
                Waiting for revenue data from backend…
              </p>
            ) : (
              <>
                <div className="h-40 mb-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={revenueData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" startAngle={90} endAngle={-270}>
                        {revenueData.map((e) => <Cell key={e.name} fill={e.color} stroke="none" />)}
                      </Pie>
                      <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }} formatter={(v) => [`${Number(v).toFixed(0)} EGP`]} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2">
                  {revenueData.map((r) => (
                    <div key={r.name} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-sm" style={{ background: r.color }} />
                        <span className="text-text-secondary">{r.name}</span>
                      </div>
                      <span className="font-mono text-text-primary">{r.value.toFixed(0)} EGP</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Machine Type Distribution */}
        <Card>
          <CardHeader><CardTitle>Machine Type Distribution</CardTitle></CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={machineTypeData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" startAngle={90} endAngle={-270}>
                    {machineTypeData.map((e) => <Cell key={e.name} fill={e.color} stroke="none" />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {machineTypeData.map((m) => (
                <div key={m.name} className="flex items-center gap-1.5 text-[10px]">
                  <span className="w-2 h-2 rounded-sm shrink-0" style={{ background: m.color }} />
                  <span className="text-text-tertiary">{m.name} ({m.value})</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* DR Events Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Activity size={14} className="text-warning" /> Demand Response Events
              </CardTitle>
              {drSnapshot && (
                <Badge variant="outline" size="sm">
                  {drSnapshot.total_payments_today.toFixed(0)} EGP today
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {drEvents.length === 0 ? (
              <p className="text-[11px] text-text-tertiary py-6 text-center">
                No DR events today — inject one via AI Control Center.
              </p>
            ) : (
              <div className="space-y-2">
                {drEvents.slice(0, 6).map((e) => (
                  <div key={e.event_id} className="flex items-center justify-between bg-bg-300 rounded-lg px-3 py-2 border border-border text-xs">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={e.status === "ACCEPTED" ? "success" : e.status === "PENDING" ? "warning" : e.status === "COMPLETED" ? "outline" : "danger"}
                          size="sm"
                        >
                          {e.status}
                        </Badge>
                        <span className="text-text-secondary font-medium">{e.event_type.replace(/_/g, " ")}</span>
                      </div>
                      <div className="text-[10px] text-text-muted">
                        {e.mw_requested} MW req · {e.duration_minutes} min
                        {e.reason && ` · ${e.reason}`}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-success font-semibold">{e.payment_earned_egp.toFixed(0)} EGP</div>
                      {e.accepted_mw !== undefined && (
                        <div className="text-[10px] text-text-muted">{e.accepted_mw} MW accepted</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Optimal Heat Schedule — full-width */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Calendar size={14} className="text-accent" /> Optimal Heat Schedule
              </CardTitle>
              {schedule && (
                <Badge variant="success" size="sm">
                  +{schedule.savings_vs_backtoback_egp.toFixed(0)} EGP vs back-to-back
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!schedule || schedule.slots.length === 0 ? (
              <p className="text-[11px] text-text-tertiary py-6 text-center">
                Waiting for schedule data from backend…
              </p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                {schedule.slots.map((slot: any, i) => {
                  const isPeak = slot.is_peak || (slot.melting_avg_price_egp > 1.5);
                  const isOffPeak = slot.recommended_action === "RUN" || (slot.melting_avg_price_egp <= 1.5);
                  const startH = Math.floor(slot.start_hour).toString().padStart(2, "0");
                  const startM = Math.round((slot.start_hour % 1) * 60).toString().padStart(2, "0");
                  return (
                  <div
                    key={i}
                    className={`rounded-lg border px-3 py-2.5 text-xs space-y-1 flex flex-col justify-center ${
                      isPeak
                        ? "bg-danger/5 border-danger/20"
                        : isOffPeak
                        ? "bg-success/5 border-success/20"
                        : "bg-bg-300 border-border"
                    }`}
                  >
                    <div className="flex items-center justify-between border-b border-border/50 pb-1 mb-1">
                      <span className="font-mono font-semibold text-text-primary text-[10px]">
                        {startH}:{startM}
                      </span>
                      <Badge
                        variant={isPeak ? "danger" : "success"}
                        size="sm"
                      >
                        {slot.label ?? (isPeak ? "Peak" : "Off")}
                      </Badge>
                    </div>
                    <div className="text-[10px] text-text-tertiary flex justify-between">
                      <span>Avg:</span>
                      <span className="font-mono text-text-primary">{(slot.expected_price_egp ?? slot.melting_avg_price_egp ?? 0).toFixed(2)}</span>
                    </div>
                    <div className="text-[10px] text-text-tertiary flex justify-between">
                      <span>Cost:</span>
                      <span className="font-mono text-text-primary">{slot.total_cost_egp ? Math.round(slot.total_cost_egp).toLocaleString() : '--'}</span>
                    </div>
                  </div>
                )})}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
