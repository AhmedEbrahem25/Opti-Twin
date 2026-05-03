const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function post(path: string, body: unknown) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

async function get(path: string) {
  const res = await fetch(`${BACKEND_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  // Existing controls
  toggleAI: (enabled: boolean) => post("/api/v1/ai/toggle", { enabled }),
  setProfile: (profile: string) => post("/api/v1/ai/profile", { profile }),
  injectCrisis: (event: string) => post("/api/v1/sim/inject", { event }),
  setTariffMode: (enabled: boolean) => post("/api/v1/tariff/mode", { enabled }),

  // Dynamic Pricing Engine
  getPricingMode: () => get("/api/v1/pricing/mode"),
  setPricingMode: (mode: string) => post("/api/v1/pricing/mode", { mode }),
  getLivePrice: () => get("/api/v1/pricing/live"),
  getForecast: () => get("/api/v1/pricing/forecast"),
  getRevenue: () => get("/api/v1/pricing/revenue"),
  getSchedule: () => get("/api/v1/pricing/schedule"),
  getDREvents: () => get("/api/v1/pricing/dr/events"),
  injectDREvent: (event_type: string, mw_requested: number, duration_minutes: number) =>
    post("/api/v1/pricing/dr/inject", { event_type, mw_requested, duration_minutes }),

  // Log viewer
  getLogs: (params?: {
    level?: string;
    service?: string;
    q?: string;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.level)   qs.set("level",   params.level);
    if (params?.service) qs.set("service", params.service);
    if (params?.q)       qs.set("q",       params.q);
    if (params?.limit)   qs.set("limit",   String(params.limit));
    return get(`/api/v1/logs?${qs.toString()}`);
  },

  // Pricing Event Search
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
    return get(`/api/v1/pricing/events/search?${qs.toString()}`);
  },
};
