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
};
