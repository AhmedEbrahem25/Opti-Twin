"use client";
import { motion } from "framer-motion";
import { KPICard } from "@/components/data-display/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { BarChart3, Zap, DollarSign, TrendingUp, Download, Calendar, Factory } from "lucide-react";

const energyData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i.toString().padStart(2, "0")}:00`,
  baseline: Math.floor(Math.random() * 40) + 80,
  optimized: Math.floor(Math.random() * 30) + 60,
  isPeak: i >= 18 && i < 22,
}));

const factoryCostData = [
  { name: "Cairo Complex", cost: 4200, saved: 2340, color: "#f59e0b" },
  { name: "Alexandria Port", cost: 3100, saved: 1580, color: "#22d3ee" },
  { name: "Alamein Plant", cost: 2400, saved: 900, color: "#22c55e" },
];

const machineTypeData = [
  { name: "Motors", value: 5, color: "#f59e0b" },
  { name: "Furnaces", value: 3, color: "#ef4444" },
  { name: "Cooling", value: 3, color: "#22d3ee" },
  { name: "Compressors", value: 2, color: "#3b82f6" },
  { name: "HVAC", value: 2, color: "#22c55e" },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">Analytics & Reports</h1>
          <p className="text-sm text-text-tertiary mt-0.5">Energy, cost, and performance analysis</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm"><Calendar size={14} /> Last 24 Hours</Button>
          <Button variant="outline" size="sm"><Download size={14} /> Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Energy Used" value={1883.2} suffix=" kWh" trend={-12.4} icon={<Zap size={16} />} accentColor="var(--color-warning)" />
        <KPICard label="Total Cost Saved" value={4820} suffix=" EGP" trend={18.3} icon={<DollarSign size={16} />} accentColor="var(--color-success)" />
        <KPICard label="Avg Efficiency" value={87.3} suffix="%" trend={3.1} icon={<TrendingUp size={16} />} accentColor="var(--color-accent)" />
        <KPICard label="Peak Reduction" value={23.5} suffix="%" trend={5.8} icon={<BarChart3 size={16} />} accentColor="var(--color-cyan)" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Energy Comparison Chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Energy: Baseline vs Optimized</CardTitle>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-text-tertiary" /> Baseline</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-accent" /> Optimized</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={energyData}>
                  <defs>
                    <linearGradient id="optGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} interval={3} />
                  <YAxis tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} />
                  <Area type="monotone" dataKey="baseline" stroke="#555" fill="none" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
                  <Area type="monotone" dataKey="optimized" stroke="#f59e0b" fill="url(#optGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Cost by Factory */}
        <Card>
          <CardHeader>
            <CardTitle>Cost Savings by Factory</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={factoryCostData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 10, fill: "#555" }} tickLine={false} axisLine={false} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: "#888" }} tickLine={false} axisLine={false} width={110} />
                  <Tooltip contentStyle={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="saved" fill="#22c55e" radius={[0, 4, 4, 0]} name="Saved (EGP)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
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
            <div className="grid grid-cols-3 gap-2 mt-2">
              {machineTypeData.map((m) => (
                <div key={m.name} className="flex items-center gap-1.5 text-[10px]">
                  <span className="w-2 h-2 rounded-sm shrink-0" style={{ background: m.color }} />
                  <span className="text-text-tertiary">{m.name} ({m.value})</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Factory Performance Table */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Factory size={14} /> Factory Performance</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {factoryCostData.map((f) => (
                <div key={f.name} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <div>
                    <p className="text-sm text-text-primary font-medium">{f.name}</p>
                    <p className="text-[10px] text-text-tertiary">Total cost: {f.cost.toLocaleString()} EGP</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-success">{f.saved.toLocaleString()} EGP</p>
                    <p className="text-[10px] text-text-tertiary">saved today</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
