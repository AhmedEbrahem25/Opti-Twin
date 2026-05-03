import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

type LogEntry = {
  ts: string;
  level: string;
  service: string;
  module?: string;
  func?: string;
  line?: number;
  msg: string;
  exc?: string;
  [key: string]: unknown;
};

type Stats = {
  total: number;
  by_level: Record<string, number>;
  services: string[];
};

const LEVELS = ["", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

const LEVEL_STYLE: Record<string, string> = {
  DEBUG:    "text-slate-400 bg-slate-800/60 border-slate-600/40",
  INFO:     "text-blue-300  bg-blue-900/40  border-blue-600/40",
  WARNING:  "text-amber-300 bg-amber-900/40 border-amber-600/40",
  ERROR:    "text-red-300   bg-red-900/40   border-red-600/40",
  CRITICAL: "text-red-200   bg-red-800/60   border-red-500/60 animate-pulse",
};

const SERVICE_STYLE: Record<string, string> = {
  "backend":    "text-purple-300 bg-purple-900/40 border-purple-600/40",
  "ai-engine":  "text-cyan-300   bg-cyan-900/40   border-cyan-600/40",
  "simulator":  "text-orange-300 bg-orange-900/40 border-orange-600/40",
};

function fmt(iso: string): string {
  try {
    return iso.slice(11, 23);  // HH:MM:SS.mmm
  } catch {
    return iso;
  }
}

function LevelBadge({ level }: { level: string }) {
  const style = LEVEL_STYLE[level] ?? "text-gray-400 bg-gray-800/60 border-gray-600/40";
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${style} shrink-0`}>
      {level}
    </span>
  );
}

function ServiceBadge({ service }: { service: string }) {
  const style = SERVICE_STYLE[service] ?? "text-slate-300 bg-slate-800/60 border-slate-600/40";
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${style} shrink-0`}>
      {service}
    </span>
  );
}

function LogRow({ entry }: { entry: LogEntry }) {
  const [expanded, setExpanded] = useState(false);
  const isError = entry.level === "ERROR" || entry.level === "CRITICAL";

  const extraKeys = Object.keys(entry).filter(
    (k) => !["ts", "level", "service", "module", "func", "line", "msg", "logger", "exc"].includes(k)
  );

  return (
    <div
      className={`border-b border-white/5 py-1 px-2 font-mono text-[11px] cursor-pointer
        hover:bg-white/[0.03] ${isError ? "bg-red-950/20" : ""}`}
      onClick={() => setExpanded((v) => !v)}
    >
      <div className="flex items-start gap-2 min-w-0">
        <span className="text-slate-500 shrink-0 w-[88px]">{fmt(entry.ts)}</span>
        <LevelBadge level={entry.level} />
        <ServiceBadge service={entry.service} />
        <span className={`flex-1 min-w-0 break-all ${isError ? "text-red-200" : "text-slate-200"}`}>
          {entry.msg}
        </span>
        {entry.module && (
          <span className="text-slate-600 shrink-0 text-[10px] hidden md:block">
            {entry.module}.{entry.func}:{entry.line}
          </span>
        )}
      </div>

      {expanded && (
        <div className="mt-1.5 ml-[120px] space-y-0.5 text-[10px]">
          {extraKeys.map((k) => (
            <div key={k} className="flex gap-2">
              <span className="text-slate-500 shrink-0">{k}:</span>
              <span className="text-slate-300">{String(entry[k])}</span>
            </div>
          ))}
          {entry.module && (
            <div className="text-slate-600">
              {entry.module}.{entry.func}:{entry.line}
            </div>
          )}
          {entry.exc && (
            <pre className="text-red-400 whitespace-pre-wrap break-all mt-1 bg-red-950/30 p-1.5 rounded">
              {entry.exc}
            </pre>
          )}
          <div className="text-slate-700">{entry.ts}</div>
        </div>
      )}
    </div>
  );
}

export default function LogViewer() {
  const [logs, setLogs]           = useState<LogEntry[]>([]);
  const [stats, setStats]         = useState<Stats | null>(null);
  const [levelFilter, setLevel]   = useState("");
  const [svcFilter, setSvc]       = useState("");
  const [q, setQ]                 = useState("");
  const [autoRefresh, setAuto]    = useState(true);
  const [autoScroll, setScroll]   = useState(true);
  const [open, setOpen]           = useState(false);
  const bottomRef                 = useRef<HTMLDivElement>(null);
  const debRef                    = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchLogs = async (lv: string, svc: string, query: string) => {
    try {
      const res = await api.getLogs({ level: lv || undefined, service: svc || undefined, q: query || undefined, limit: 200 });
      setLogs(res.logs ?? []);
      setStats(res.stats ?? null);
    } catch {}
  };

  useEffect(() => {
    if (debRef.current) clearTimeout(debRef.current);
    debRef.current = setTimeout(() => fetchLogs(levelFilter, svcFilter, q), 300);
    return () => { if (debRef.current) clearTimeout(debRef.current); };
  }, [levelFilter, svcFilter, q]);

  useEffect(() => {
    if (!autoRefresh || !open) return;
    const id = setInterval(() => fetchLogs(levelFilter, svcFilter, q), 2000);
    return () => clearInterval(id);
  }, [autoRefresh, open, levelFilter, svcFilter, q]);

  useEffect(() => {
    if (autoScroll && open && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll, open]);

  const errCount  = stats?.by_level["ERROR"]    ?? 0;
  const warnCount = stats?.by_level["WARNING"]  ?? 0;
  const critCount = stats?.by_level["CRITICAL"] ?? 0;

  return (
    <div className="glass rounded-xl mt-4">
      {/* Header bar (always visible) */}
      <button
        onClick={() => { setOpen((v) => !v); if (!open) fetchLogs(levelFilter, svcFilter, q); }}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-white uppercase tracking-wide">
            System Logs
          </span>
          {stats && (
            <span className="text-xs text-slate-500">{stats.total} entries</span>
          )}
          <div className="flex gap-1.5">
            {critCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-800/60 border border-red-500/60 text-red-200 animate-pulse">
                {critCount} CRITICAL
              </span>
            )}
            {errCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/40 border border-red-600/40 text-red-300">
                {errCount} errors
              </span>
            )}
            {warnCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/40 border border-amber-600/40 text-amber-300">
                {warnCount} warnings
              </span>
            )}
            {stats?.services?.map((svc) => (
              <span key={svc} className={`text-[10px] px-1.5 py-0.5 rounded border ${SERVICE_STYLE[svc] ?? "text-slate-400 border-slate-600/40"}`}>
                {svc}
              </span>
            ))}
          </div>
        </div>
        <span className="text-steel-100/40 text-xs">{open ? "▲ collapse" : "▼ expand"}</span>
      </button>

      {open && (
        <div className="px-4 pb-4">
          {/* Toolbar */}
          <div className="flex flex-wrap gap-2 mb-3">
            <div className="relative flex-1 min-w-[160px]">
              <input
                type="text"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search logs…"
                className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-blue-500/50 font-mono"
              />
              {q && (
                <button
                  onClick={() => setQ("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white text-xs"
                >✕</button>
              )}
            </div>

            <select
              value={levelFilter}
              onChange={(e) => setLevel(e.target.value)}
              className="bg-slate-900 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-slate-200 outline-none"
            >
              {LEVELS.map((l) => (
                <option key={l} value={l}>{l || "All levels"}</option>
              ))}
            </select>

            <select
              value={svcFilter}
              onChange={(e) => setSvc(e.target.value)}
              className="bg-slate-900 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-slate-200 outline-none"
            >
              <option value="">All services</option>
              {(stats?.services ?? []).map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            <button
              onClick={() => setAuto((v) => !v)}
              className={`text-[11px] px-2 py-1 rounded-full border ${
                autoRefresh
                  ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                  : "bg-slate-800 text-slate-500 border-white/10"
              }`}
            >
              {autoRefresh ? "● live" : "paused"}
            </button>

            <button
              onClick={() => setScroll((v) => !v)}
              className={`text-[11px] px-2 py-1 rounded-full border ${
                autoScroll
                  ? "bg-slate-700 text-slate-300 border-white/10"
                  : "bg-slate-800 text-slate-500 border-white/10"
              }`}
            >
              {autoScroll ? "↓ auto-scroll" : "scroll off"}
            </button>

            {(levelFilter || svcFilter || q) && (
              <button
                onClick={() => { setLevel(""); setSvc(""); setQ(""); }}
                className="text-xs text-slate-500 hover:text-white px-2"
              >
                Clear
              </button>
            )}
          </div>

          {/* Log terminal */}
          <div className="h-64 overflow-y-auto rounded-lg bg-slate-950/80 border border-white/5">
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-xs text-slate-600 font-mono">
                {q || levelFilter || svcFilter
                  ? "No logs match the current filters."
                  : "Waiting for log entries…"}
              </div>
            ) : (
              <>
                {[...logs].reverse().map((entry, i) => (
                  <LogRow key={`${entry.ts}-${i}`} entry={entry} />
                ))}
                <div ref={bottomRef} />
              </>
            )}
          </div>

          <div className="text-[10px] text-slate-600 mt-1.5 text-right font-mono">
            {logs.length} {logs.length !== 1 ? "entries" : "entry"}
            {(q || levelFilter || svcFilter) && " (filtered)"}
            {" · "}click a row to expand
          </div>
        </div>
      )}
    </div>
  );
}
