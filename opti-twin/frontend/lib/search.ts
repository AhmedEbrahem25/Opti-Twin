/**
 * Opti-Search client.
 *
 * Wraps `/api/v1/search` and `/api/v1/search/saved/default`. The full saved-
 * search CRUD surface is post-event — only the canonical default preset is
 * exposed here.
 */

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export type DocType = "decision" | "crisis" | "safety_rollback";
export type Severity = "info" | "warning" | "critical";

export interface SearchResult {
  id: string;
  type: DocType;
  ts: string;
  severity: Severity;
  title: string;
  snippet: string;
  score: number;
  deeplink: string;
}

export interface SearchResponse {
  query: string;
  took_ms: number;
  total: number;
  results: SearchResult[];
  facets: Record<string, Record<string, number>>;
  next_offset: number | null;
}

export interface SearchFilters {
  types?: DocType[];
  severity?: Severity[];
  from?: string; // ISO 8601
  to?: string;
  lang?: "en" | "ar" | "auto";
  limit?: number;
  offset?: number;
}

export async function searchOpti(
  q: string,
  filters: SearchFilters = {}
): Promise<SearchResponse> {
  const qs = new URLSearchParams();
  if (q) qs.set("q", q);
  if (filters.types?.length) qs.set("types", filters.types.join(","));
  if (filters.severity?.length) qs.set("severity", filters.severity.join(","));
  if (filters.from) qs.set("from", filters.from);
  if (filters.to) qs.set("to", filters.to);
  if (filters.lang) qs.set("lang", filters.lang);
  if (filters.limit) qs.set("limit", String(filters.limit));
  if (filters.offset) qs.set("offset", String(filters.offset));

  const res = await fetch(`${BACKEND_URL}/api/v1/search?${qs}`);
  if (!res.ok) throw new Error(`search failed: ${res.status}`);
  return res.json();
}

export interface SavedSearchDefault {
  id: string;
  title_en: string;
  title_ar: string;
  query: SearchFilters;
}

export async function getDefaultSavedSearch(): Promise<SavedSearchDefault> {
  const res = await fetch(`${BACKEND_URL}/api/v1/search/saved/default`);
  if (!res.ok) throw new Error(`saved/default failed: ${res.status}`);
  return res.json();
}

export interface SearchHealth {
  meili: "ok" | "degraded" | "down";
  docs: number;
}

export async function getSearchHealth(): Promise<SearchHealth> {
  const res = await fetch(`${BACKEND_URL}/api/v1/search/health`);
  if (!res.ok) {
    return { meili: "down", docs: 0 };
  }
  return res.json();
}

/** Detects whether a query string contains Arabic codepoints. */
export function isArabic(s: string): boolean {
  return /[؀-ۿݐ-ݿࢠ-ࣿ]/.test(s);
}
