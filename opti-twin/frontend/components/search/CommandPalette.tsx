/**
 * CommandPalette — global Ctrl+K / ⌘K search surface.
 *
 * Renders into a portal at document.body. Hidden by default; toggled by a
 * global keydown listener. Debounced 80ms input → /api/v1/search → result
 * list with arrow-key nav. Enter on a row dispatches a custom `opti:focus`
 * event AND pushes the deeplink to the URL so other dashboard components
 * can scroll to that timestamp + the result is bookmarkable.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/router";
import {
  type DocType,
  type SearchResult,
  type Severity,
  searchOpti,
  isArabic,
  getDefaultSavedSearch,
} from "../../lib/search";

type TypeFilter = "all" | DocType;
type SevFilter = "all" | Severity;
type RangeFilter = "all" | "1h" | "shift" | "24h" | "7d" | "30d";

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

const RANGE_OPTIONS: { id: RangeFilter; label: string }[] = [
  { id: "all", label: "All time" },
  { id: "1h", label: "Last hour" },
  { id: "shift", label: "This shift" },
  { id: "24h", label: "24h" },
  { id: "7d", label: "7d" },
  { id: "30d", label: "30d" },
];

type Props = {
  initialQuery?: string;
  initialType?: TypeFilter;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
};

const TYPE_ICON: Record<DocType, string> = {
  decision: "⚡",
  crisis: "🔥",
  safety_rollback: "🛡",
};

// Severity styling — mirrors LogViewer.tsx so palette and dashboard read as one product.
const SEV_ROW: Record<Severity, string> = {
  critical: "border-l-2 border-red-500/60 bg-red-900/15",
  warning:  "border-l-2 border-amber-500/40 bg-amber-900/5",
  info:     "border-l-2 border-transparent",
};

const SEV_BADGE: Record<Severity, string> = {
  critical: "text-red-300 bg-red-900/40 border-red-600/40",
  warning:  "text-amber-300 bg-amber-900/40 border-amber-600/40",
  info:     "text-blue-300 bg-blue-900/40 border-blue-600/40",
};

const SEV_DOT: Record<Severity, string> = {
  critical: "h-2 w-2 bg-red-400",
  warning:  "h-1.5 w-1.5 bg-amber-400",
  info:     "h-1.5 w-1.5 bg-blue-400/70",
};

function rangeToFromIso(range: RangeFilter, shiftStart: string | null): string | undefined {
  if (range === "all") return undefined;
  if (range === "shift") return shiftStart ?? undefined;
  const now = Date.now();
  const ms =
    range === "1h" ? 60 * 60 * 1000 :
    range === "24h" ? 24 * 60 * 60 * 1000 :
    range === "7d" ? 7 * 24 * 60 * 60 * 1000 :
    30 * 24 * 60 * 60 * 1000;
  return new Date(now - ms).toISOString();
}

export default function CommandPalette({
  initialQuery = "",
  initialType = "all",
  open: controlledOpen,
  onOpenChange,
}: Props) {
  const router = useRouter();
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
  const [rangeFilter, setRangeFilter] = useState<RangeFilter>("all");
  const [shiftStart, setShiftStart] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [tookMs, setTookMs] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [activeIdx, setActiveIdx] = useState(0);
  const [mounted, setMounted] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => setMounted(true), []);

  // Learn shift-start from backend once at mount; backend is the source of truth.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const preset = await getDefaultSavedSearch();
        if (!cancelled && preset.query.from) setShiftStart(preset.query.from);
      } catch {
        // shift filter just falls back to "all" silently
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

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

  // Focus management — capture previous focus on open, restore on close.
  useEffect(() => {
    if (open) {
      previouslyFocused.current = (document.activeElement as HTMLElement) ?? null;
      // Defer to ensure the input is in the DOM after the open transition.
      requestAnimationFrame(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      });
    } else if (previouslyFocused.current) {
      previouslyFocused.current.focus();
      previouslyFocused.current = null;
    }
  }, [open]);

  // Debounced search whenever the query or filters change AND the palette is open.
  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await searchOpti(q, {
          types: typeFilter === "all" ? undefined : [typeFilter],
          severity: sevFilter === "all" ? undefined : [sevFilter],
          from: rangeToFromIso(rangeFilter, shiftStart),
          limit: 20,
          lang: "auto",
        });
        setResults(resp.results);
        setTotal(resp.total);
        setTookMs(resp.took_ms);
        setActiveIdx(0);
      } catch (err) {
        setResults([]);
        setTotal(0);
        setError(err instanceof Error ? err.message : "Search unavailable");
      } finally {
        setLoading(false);
      }
    }, 80);
    return () => clearTimeout(handle);
  }, [q, typeFilter, sevFilter, rangeFilter, shiftStart, open, retryNonce]);

  const selectResult = useCallback(
    (r: SearchResult) => {
      window.dispatchEvent(
        new CustomEvent("opti:focus", { detail: { ts: r.ts, doc_id: r.id, type: r.type } })
      );
      // Bookmarkable URL — additive to the in-page event.
      router.replace(
        { pathname: router.pathname, query: { ...router.query, ts: r.ts, focus: r.id, type: r.type } },
        undefined,
        { shallow: true }
      );
      setOpen(false);
    },
    [router, setOpen]
  );

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
        selectResult(results[activeIdx]);
      }
    },
    [results, activeIdx, selectResult]
  );

  // Trap Tab inside the dialog while open.
  const onDialogKey = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key !== "Tab" || !dialogRef.current) return;
      const focusables = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, [tabindex]:not([tabindex="-1"])'
      );
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    []
  );

  // Keep the active row scrolled into view.
  useEffect(() => {
    if (!listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(`[data-idx="${activeIdx}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIdx]);

  const tipQueries = useMemo(
    () => ["wall overheat", "EMERGENCY_COOLING", "تبريد طارئ", "شيفت اليوم"],
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
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Search Opti-Twin"
        onKeyDown={onDialogKey}
        className={`relative mx-auto mt-24 w-full max-w-2xl rounded-xl border border-steel-500/30 bg-steel-900/95 shadow-2xl ${open ? "opti-pop" : ""}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-steel-500/20 px-4 py-3">
          <span className="text-xl" aria-hidden="true">🔍</span>
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={onListKey}
            placeholder="Search decisions, crises, safety overrides…"
            aria-label="Search query"
            aria-controls="opti-search-results"
            className="flex-1 bg-transparent text-sm text-steel-100 placeholder-steel-100/40 outline-none"
            dir={isArabic(q) ? "rtl" : "ltr"}
          />
          <kbd className="rounded bg-steel-700/60 px-2 py-0.5 text-xs text-steel-100/70">
            ⌘K
          </kbd>
        </div>

        {/* Filter chips */}
        <div className="flex flex-wrap gap-3 border-b border-steel-500/20 px-4 py-2 text-xs">
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
          <FilterGroup
            label="When"
            options={RANGE_OPTIONS}
            value={rangeFilter}
            onChange={(v) => setRangeFilter(v as RangeFilter)}
          />
        </div>

        {/* Error strip */}
        {error && (
          <div
            role="alert"
            aria-live="polite"
            className="flex items-center justify-between gap-3 border-b border-red-500/30 bg-red-900/30 px-4 py-2 text-xs text-red-200"
          >
            <span>⚠ Search unavailable — Meili offline?</span>
            <button
              onClick={() => setRetryNonce((n) => n + 1)}
              className="rounded bg-red-500/20 px-2 py-0.5 text-red-100 hover:bg-red-500/30"
            >
              Retry
            </button>
          </div>
        )}

        {/* Result list */}
        <div
          id="opti-search-results"
          ref={listRef}
          role="listbox"
          aria-label="Search results"
          className="max-h-[420px] overflow-auto"
        >
          {loading && results.length === 0 ? (
            <Skeletons />
          ) : results.length === 0 && !error ? (
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
                  selectResult(r);
                }}
              />
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-steel-500/20 px-4 py-2 text-[11px] text-steel-100/50">
          <span aria-live="polite">
            {loading
              ? "…"
              : error
              ? "—"
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
          aria-pressed={value === opt.id}
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
  const titleIsAr = isArabic(r.title);
  const snippetIsAr = isArabic(r.snippet);
  return (
    <button
      data-idx={idx}
      onClick={onClick}
      role="option"
      aria-selected={active}
      className={`block w-full border-b border-steel-500/10 px-4 py-2.5 text-left transition-colors ${SEV_ROW[r.severity]} ${
        active ? "bg-steel-700/60" : "hover:bg-steel-700/30"
      }`}
    >
      <div className="flex items-baseline gap-2">
        <span aria-hidden="true">{TYPE_ICON[r.type]}</span>
        <span className={`inline-block shrink-0 rounded-full ${SEV_DOT[r.severity]}`} aria-hidden="true" />
        <span
          className={`flex-1 text-sm text-steel-100 ${r.severity === "critical" ? "font-semibold" : "font-medium"}`}
          dir={titleIsAr ? "rtl" : "ltr"}
        >
          {r.title}
        </span>
        {titleIsAr && (
          <span className="text-[10px] uppercase tracking-wide text-steel-100/50">AR</span>
        )}
        <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase ${SEV_BADGE[r.severity]}`}>
          {r.severity}
        </span>
      </div>
      <div className="mt-0.5 text-[11px] text-steel-100/50">
        {r.type} · {ts}
      </div>
      {r.snippet && (
        <div
          className="mt-1 text-xs text-steel-100/70"
          dir={snippetIsAr ? "rtl" : "ltr"}
          dangerouslySetInnerHTML={{ __html: r.snippet }}
        />
      )}
    </button>
  );
}

function Skeletons() {
  return (
    <div className="px-4 py-3 space-y-2" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="animate-pulse rounded-md border border-steel-500/10 bg-steel-700/20 px-3 py-3"
        >
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-steel-500/30" />
            <div className="h-3 flex-1 rounded bg-steel-500/30" />
            <div className="h-3 w-12 rounded bg-steel-500/30" />
          </div>
          <div className="mt-2 h-2 w-2/3 rounded bg-steel-500/20" />
        </div>
      ))}
    </div>
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
