import type {
  BackendKPI,
  BackendLivePrice,
  BackendRecommendation,
  BackendForecast,
  BackendRevenue,
  BackendSchedule,
  BackendDRSnapshot,
  BackendPricingSearchResult,
  BackendLogsResponse,
} from "./backend-types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export type ProfileName =
  | "default"
  | "cost_first"
  | "equipment_sensitive"
  | "production_critical"
  | "quality_focused";

export type CrisisEvent =
  | "wall_overheat"
  | "electrode_break"
  | "grid_spike"
  | "transformer_alarm";

export type DPEMode = "flat" | "sim_tou" | "sim_spot" | "live_eehc";

export type DREventType =
  | "CURTAILMENT"
  | "INTERRUPTIBLE"
  | "FREQUENCY_RESPONSE";

export const api = {
  // AI controls
  toggleAI: (enabled: boolean) =>
    post<{ ok: boolean; enabled: boolean }>("/api/v1/ai/toggle", { enabled }),
  setProfile: (profile: ProfileName) =>
    post<{ ok: boolean; profile: string }>("/api/v1/ai/profile", { profile }),
  injectCrisis: (event: CrisisEvent) =>
    post<{ ok: boolean; event: string }>("/api/v1/sim/inject", { event }),
  setTariffMode: (enabled: boolean) =>
    post<{ ok: boolean; tou_mode: boolean }>("/api/v1/tariff/mode", { enabled }),

  // KPIs / latest decision
  getStats: () => get<BackendKPI>("/api/v1/stats"),
  getRecommendation: () =>
    get<BackendRecommendation | null>("/api/v1/recommendation"),

  // Dynamic pricing engine
  getLivePrice: () => get<BackendLivePrice>("/api/v1/pricing/live"),
  getForecast: () => get<BackendForecast>("/api/v1/pricing/forecast"),
  getPricingMode: () => get<{ mode: DPEMode }>("/api/v1/pricing/mode"),
  setPricingMode: (mode: DPEMode) =>
    post<{ ok: boolean; mode: DPEMode }>("/api/v1/pricing/mode", { mode }),
  getRevenue: () => get<BackendRevenue>("/api/v1/pricing/revenue"),
  getSchedule: () => get<BackendSchedule>("/api/v1/pricing/schedule"),

  // Demand-response
  getDREvents: () => get<BackendDRSnapshot>("/api/v1/pricing/dr/events"),
  injectDREvent: (
    event_type: DREventType,
    mw_requested: number,
    duration_minutes: number,
  ) =>
    post<{ event: Record<string, unknown>; assessment: Record<string, unknown> }>(
      "/api/v1/pricing/dr/inject",
      { event_type, mw_requested, duration_minutes },
    ),

  // Search & logs
  searchPricingEvents: (params: {
    q?: string;
    event_kind?: string;
    dr_status?: string;
    dr_type?: string;
    is_peak?: boolean;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set("q", params.q);
    if (params.event_kind) qs.set("event_kind", params.event_kind);
    if (params.dr_status) qs.set("dr_status", params.dr_status);
    if (params.dr_type) qs.set("dr_type", params.dr_type);
    if (params.is_peak !== undefined) qs.set("is_peak", String(params.is_peak));
    if (params.limit) qs.set("limit", String(params.limit));
    return get<BackendPricingSearchResult>(
      `/api/v1/pricing/events/search?${qs.toString()}`,
    );
  },
  getLogs: (params?: {
    level?: string;
    service?: string;
    q?: string;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.level) qs.set("level", params.level);
    if (params?.service) qs.set("service", params.service);
    if (params?.q) qs.set("q", params.q);
    if (params?.limit) qs.set("limit", String(params.limit));
    return get<BackendLogsResponse>(`/api/v1/logs?${qs.toString()}`);
  },
};
