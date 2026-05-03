/**
 * CommandPalette — global Ctrl+K / ⌘K search surface.
 *
 * Renders into a portal at document.body. Hidden by default; toggled by a
 * global keydown listener. Debounced 80ms input → /api/v1/search → result
 * list with arrow-key nav. Enter on a row dispatches a custom `opti:focus`
 * event so other dashboard components can scroll to that timestamp.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  type DocType,
  type SearchResult,
  type Severity,
  searchOpti,
  isArabic,
} from "../../lib/search";

type TypeFilter = "all" | DocType;
type SevFilter = "all" | Severity;

const TYPE_OPTIONS: { id: TypeFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "decision", label: "Decisions" },
  { id: "crisis", label: "Crises" },
  { id: "safety_rollback", label: "Safety overrides" },
];

const SEV_OPTIONS: { id: SevFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "critical", label: "Critical" },
  { id: "warning", label: "Warning" },
  { id: "info", label: "Info" },
];

type Props = {
  /** Optional: pre-fill the query when the palette opens. */
  initialQuery?: string;
  /** Optional: pre-fill the type filter when the palette opens. */
  initialType?: TypeFilter;
  /** External open/close control; if omitted, palette manages its own state. */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
};

const TYPE_ICON: Record<DocType, string> = {
  decision: "⚡",
  crisis: "🔥",
  safety_rollback: "🛡",
};

const SEV_COLOR: Record<Severity, string> = {
  critical: "text-red-400",
  warning: "text-flame-400",
  info: "text-steel-100/60",
};

export default function CommandPalette({
  initialQuery = "",
  initialType = "all",
  open: controlledOpen,
  onOpenChange,
}: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const setOpen = useCallback(
    (v: boolean) => {
      if (onOpenChange) onOpenChange(v);
      else setInternalOpen(v);
    },
    [onOpenChange]
  );

  const [q, setQ] = useState(initialQuery);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>(initialType);
  const [sevFilter, setSevFilter] = useState<SevFilter>("all");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [tookMs, setTookMs] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const [mounted, setMounted] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Mount guard for portal SSR safety.
  useEffect(() => setMounted(true), []);

  // Global Ctrl+K / ⌘K toggle.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(!open);
      } else if (e.key === "Escape" && open) {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, setOpen]);

  // Focus input when opening.
  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [open]);

  // Debounced search whenever the query or filters change AND the palette is open.
  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(async () => {
      setLoading(true);
      try {
        const resp = await searchOpti(q, {
          types: typeFilter === "all" ? undefined : [typeFilter],
          severity: sevFilter === "all" ? undefined : [sevFilter],
          limit: 20,
          lang: "auto",
        });
        setResults(resp.results);
        setTotal(resp.total);
        setTookMs(resp.took_ms);
        setActiveIdx(0);
      } catch (_) {
        setResults([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    }, 80);
    return () => clearTimeout(handle);
  }, [q, typeFilter, sevFilter, open]);

  // Arrow-key nav + Enter to deep-link.
  const onListKey = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIdx((i) => Math.min(i + 1, Math.max(0, results.length - 1)));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIdx((i) => Math.max(0, i - 1));
      } else if (e.key === "Enter" && results[activeIdx]) {
        e.preventDefault();
        const r = results[activeIdx];
        window.dispatchEvent(
          new CustomEvent("opti:focus", { detail: { ts: r.ts, doc_id: r.id, type: r.type } })
        );
        setOpen(false);
      }
    },
    [results, activeIdx, setOpen]
  );

  // Keep the active row scrolled into view.
  useEffect(() => {
    if (!listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(
      `[data-idx="${activeIdx}"]`
    );
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIdx]);

  const tipQueries = useMemo(
    () => ["wall overheat", "EMERGENCY_COOLING", "تبريد طارئ"],
    []
  );

  if (!mounted) return null;

  const body = (
    <div
      className={`fixed inset-0 z-50 transition-opacity ${open ? "opacity-100" : "pointer-events-none opacity-0"}`}
      onClick={() => setOpen(false)}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative mx-auto mt-24 w-full max-w-2xl rounded-xl border border-steel-500/30 bg-steel-900/95 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-steel-500/20 px-4 py-3">
          <span className="text-xl">🔍</span>
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={onListKey}
            placeholder="Search decisions, crises, safety overrides…"
            className="flex-1 bg-transparent text-sm text-steel-100 placeholder-steel-100/40 outline-none"
            dir={isArabic(q) ? "rtl" : "ltr"}
          />
          <kbd className="rounded bg-steel-700/60 px-2 py-0.5 text-xs text-steel-100/70">
            ⌘K
          </kbd>
        </div>

        {/* Filter chips */}
        <div className="flex flex-wrap gap-2 border-b border-steel-500/20 px-4 py-2 text-xs">
          <FilterGroup
            label="Type"
            options={TYPE_OPTIONS}
            value={typeFilter}
            onChange={(v) => setTypeFilter(v as TypeFilter)}
          />
          <FilterGroup
            label="Severity"
            options={SEV_OPTIONS}
            value={sevFilter}
            onChange={(v) => setSevFilter(v as SevFilter)}
          />
        </div>

        {/* Result list */}
        <div ref={listRef} className="max-h-[420px] overflow-auto">
          {loading && results.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs text-steel-100/50">
              Searching…
            </div>
          ) : results.length === 0 ? (
            <EmptyState tipQueries={tipQueries} onPick={setQ} />
          ) : (
            results.map((r, i) => (
              <ResultRow
                key={r.id}
                r={r}
                active={i === activeIdx}
                idx={i}
                onClick={() => {
                  setActiveIdx(i);
                  window.dispatchEvent(
                    new CustomEvent("opti:focus", {
                      detail: { ts: r.ts, doc_id: r.id, type: r.type },
                    })
                  );
                  setOpen(false);
                }}
              />
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-steel-500/20 px-4 py-2 text-[11px] text-steel-100/50">
          <span>
            {loading
              ? "…"
              : `${total.toLocaleString()} result${total === 1 ? "" : "s"} · ${tookMs} ms`}
          </span>
          <span>↑↓ navigate · ↵ open · esc close</span>
        </div>
      </div>
    </div>
  );

  return createPortal(body, document.body);
}

// ── Subcomponents ──────────────────────────────────────────────────────────

type FilterOpt = { id: string; label: string };

function FilterGroup({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: FilterOpt[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-steel-100/40 mr-1">{label}:</span>
      {options.map((opt) => (
        <button
          key={opt.id}
          onClick={() => onChange(opt.id)}
          className={`rounded px-2 py-0.5 transition-colors ${
            value === opt.id
              ? "bg-flame-500/30 text-flame-200"
              : "bg-steel-700/40 text-steel-100/70 hover:bg-steel-700/70"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function ResultRow({
  r,
  active,
  idx,
  onClick,
}: {
  r: SearchResult;
  active: boolean;
  idx: number;
  onClick: () => void;
}) {
  const ts = new Date(r.ts).toLocaleString();
  const isAr = isArabic(r.title);
  return (
    <button
      data-idx={idx}
      onClick={onClick}
      className={`block w-full border-b border-steel-500/10 px-4 py-2.5 text-left transition-colors ${
        active ? "bg-steel-700/60" : "hover:bg-steel-700/30"
      }`}
    >
      <div className="flex items-baseline gap-2">
        <span>{TYPE_ICON[r.type]}</span>
        <span
          className="flex-1 text-sm font-medium text-steel-100"
          dir={isAr ? "rtl" : "ltr"}
        >
          {r.title}
        </span>
        <span className={`text-[11px] uppercase ${SEV_COLOR[r.severity]}`}>
          {r.severity}
        </span>
      </div>
      <div className="mt-0.5 text-[11px] text-steel-100/50">
        {r.type} · {ts}
      </div>
      {r.snippet && (
        <div
          className="mt-1 text-xs text-steel-100/70"
          dir={isArabic(r.snippet) ? "rtl" : "ltr"}
          dangerouslySetInnerHTML={{ __html: r.snippet }}
        />
      )}
    </button>
  );
}

function EmptyState({
  tipQueries,
  onPick,
}: {
  tipQueries: string[];
  onPick: (q: string) => void;
}) {
  return (
    <div className="px-4 py-6 text-center text-xs text-steel-100/50">
      <p className="mb-2">No results. Try one of:</p>
      <div className="flex flex-wrap justify-center gap-2">
        {tipQueries.map((tip) => (
          <button
            key={tip}
            onClick={() => onPick(tip)}
            className="rounded bg-steel-700/40 px-2 py-1 text-steel-100/80 hover:bg-steel-700/70"
            dir={isArabic(tip) ? "rtl" : "ltr"}
          >
            {tip}
          </button>
        ))}
      </div>
    </div>
  );
}
