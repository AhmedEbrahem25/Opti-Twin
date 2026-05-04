/**
 * useSearchFocus — single source of truth for "which doc is the dashboard
 * currently focused on" after a deep-link from the search palette.
 *
 * Two input paths converge here:
 *   1. The `opti:focus` CustomEvent dispatched by CommandPalette on click.
 *   2. URL query params `?ts=&focus=&type=` so a result is bookmarkable.
 *
 * Consumers (XAIDecisionLog, LogViewer, …) take the returned `focused`
 * and decide whether to claim it (by matching `type`) — scrolling the
 * matching row into view and applying `.opti-flash` for 2 seconds.
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/router";

import type { DocType } from "./search";

export interface SearchFocus {
  ts: string;
  doc_id: string;
  type: DocType;
}

interface OptiFocusEventDetail {
  ts?: unknown;
  doc_id?: unknown;
  type?: unknown;
}

const VALID_TYPES: DocType[] = ["decision", "crisis", "safety_rollback"];

function coerce(detail: OptiFocusEventDetail): SearchFocus | null {
  const ts = typeof detail.ts === "string" ? detail.ts : null;
  const doc_id = typeof detail.doc_id === "string" ? detail.doc_id : null;
  const type =
    typeof detail.type === "string" && (VALID_TYPES as string[]).includes(detail.type)
      ? (detail.type as DocType)
      : null;
  if (!ts || !doc_id || !type) return null;
  return { ts, doc_id, type };
}

export function useSearchFocus(): {
  focused: SearchFocus | null;
  clearFocus: () => void;
} {
  const router = useRouter();
  const [focused, setFocused] = useState<SearchFocus | null>(null);

  // Path 1: custom event from the palette.
  useEffect(() => {
    const onFocus = (e: Event) => {
      const detail = (e as CustomEvent<OptiFocusEventDetail>).detail || {};
      const next = coerce(detail);
      if (next) setFocused(next);
    };
    window.addEventListener("opti:focus", onFocus);
    return () => window.removeEventListener("opti:focus", onFocus);
  }, []);

  // Path 2: URL query params on mount + on route change.
  useEffect(() => {
    if (!router.isReady) return;
    const { ts, focus, type } = router.query;
    if (typeof ts === "string" && typeof focus === "string" && typeof type === "string") {
      const next = coerce({ ts, doc_id: focus, type });
      if (next) setFocused(next);
    }
  }, [router.isReady, router.query]);

  const clearFocus = useCallback(() => setFocused(null), []);

  return { focused, clearFocus };
}
