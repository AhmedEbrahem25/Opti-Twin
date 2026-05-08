"use client";
import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getRelativeTime } from "@/lib/utils";
import { Search, Filter, Brain, AlertTriangle, Activity, Clock, ChevronRight, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { BackendLogEntry } from "@/lib/backend-types";

type ResultItem = {
  id: string;
  kind: "ai_decision" | "alert" | "telemetry" | "pricing";
  title: string;
  desc: string;
  timestamp: string;
  meta: string;
};

function logToResult(log: BackendLogEntry, index: number): ResultItem {
  const kind: ResultItem["kind"] =
    log.level === "ERROR" || log.level === "CRITICAL"
      ? "alert"
      : log.service === "ai_engine"
      ? "ai_decision"
      : "telemetry";
  return {
    id: `log-${index}-${log.timestamp}`,
    kind,
    title: log.message.slice(0, 80),
    desc: `${log.service} — ${log.level}`,
    timestamp: log.timestamp,
    meta: log.service,
  };
}

const kindConfig: Record<
  ResultItem["kind"],
  { icon: typeof Brain; color: string; label: string; variant: "accent" | "danger" | "info" | "warning" }
> = {
  ai_decision: { icon: Brain, color: "text-accent", label: "AI Decision", variant: "accent" },
  alert: { icon: AlertTriangle, color: "text-danger", label: "Alert", variant: "danger" },
  telemetry: { icon: Activity, color: "text-cyan", label: "Log", variant: "info" },
  pricing: { icon: Activity, color: "text-warning", label: "Pricing Event", variant: "warning" },
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState("all");
  const [results, setResults] = useState<ResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const [logsResp, pricingResp] = await Promise.allSettled([
          api.getLogs({ q: query || undefined, limit: 30 }),
          api.searchPricingEvents({ q: query || undefined, limit: 20 }),
        ]);

        const logItems: ResultItem[] =
          logsResp.status === "fulfilled"
            ? logsResp.value.logs.map(logToResult)
            : [];

        const pricingItems: ResultItem[] =
          pricingResp.status === "fulfilled"
            ? pricingResp.value.results.slice(0, 10).map((r, i) => ({
                id: `price-${i}`,
                kind: "pricing" as const,
                title: String(r.label ?? r.event_kind ?? "Pricing event"),
                desc: `${r.price_egp_kwh ?? "—"} EGP/kWh · ${r.tariff_class ?? ""}`,
                timestamp: String(r.timestamp ?? new Date().toISOString()),
                meta: String(r.price_source ?? "DPE"),
              }))
            : [];

        setResults([...logItems, ...pricingItems]);
      } finally {
        setLoading(false);
      }
    }, 350);
  }, [query]);

  const filtered = results.filter((r) => {
    if (kindFilter === "all") return true;
    if (kindFilter === "ai_decision") return r.kind === "ai_decision";
    if (kindFilter === "alert") return r.kind === "alert";
    if (kindFilter === "pricing") return r.kind === "pricing";
    return r.kind === "telemetry";
  });

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
          Search Console
        </h1>
        <p className="text-sm text-text-tertiary mt-0.5">
          Search across AI decisions, pricing events, and system logs
        </p>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        {loading && (
          <Loader2 size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted animate-spin" />
        )}
        <Input
          placeholder="Search events, decisions, logs…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-10 pr-10 h-11 bg-bg-200 text-base"
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter size={14} className="text-text-tertiary" />
        {[
          { id: "all", label: "All" },
          { id: "ai_decision", label: "AI Decisions" },
          { id: "alert", label: "Alerts" },
          { id: "pricing", label: "Pricing" },
          { id: "telemetry", label: "Logs" },
        ].map((f) => (
          <Button
            key={f.id}
            variant={kindFilter === f.id ? "accent" : "ghost"}
            size="sm"
            onClick={() => setKindFilter(f.id)}
            className="text-xs"
          >
            {f.label}
          </Button>
        ))}
        <span className="ml-auto text-[11px] text-text-muted">{filtered.length} results</span>
      </div>

      {/* Results */}
      {filtered.length === 0 && !loading && (
        <p className="text-[11px] text-text-tertiary py-12 text-center">
          {results.length === 0
            ? "No backend results yet — start the Opti-Twin backend to enable live search."
            : "No results matching current filter."}
        </p>
      )}

      <div className="space-y-2">
        {filtered.map((r, i) => {
          const config = kindConfig[r.kind];
          const Icon = config.icon;
          return (
            <motion.div
              key={r.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03, duration: 0.25 }}
            >
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
                      <span className="font-mono">{r.meta}</span>
                      <span className="flex items-center gap-1">
                        <Clock size={10} /> {getRelativeTime(r.timestamp)}
                      </span>
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
