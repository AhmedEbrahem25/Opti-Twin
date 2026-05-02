import { useEffect, useRef, useState } from "react";

export type Telemetry = {
  machine_id: string;
  factory: string;
  manufacturer?: string;
  timestamp: string;
  sim_hour?: number;
  arc_power_mw: number;
  energy_kwh: number;
  energy_this_heat_kwh: number;
  power_factor: number;
  pf_penalty_bracket: boolean;
  pf_penalty_egp_per_hour_est: number;
  furnace_bath_temp: number;
  electrode_temp: number;
  wall_panel_temp: number;
  cooling_water_outlet_temp: number;
  heat_progress_pct: number;
  current_batch_weight: number;
  batches_today: number;
  production_backlog: number;
  electricity_price: number;
  tariff_class: string;
  tou_mode: boolean;
  is_peak: boolean;
  tariff_label: string;
  grid_frequency: number;
  oxygen_injection_m3hr: number;
  cooling_water_flow_lmin: number;
  status: string;
  ai_active: boolean;
  reactive_power_comp_mvar?: number;
  electrode_consumption_today_kg?: number;
  crisis_flags?: {
    wall_overheat: boolean;
    electrode_break: boolean;
    grid_spike: boolean;
    transformer_alarm: boolean;
  };
};

export type Recommendation = {
  timestamp: string;
  action_label: string;
  action_magnitude_pct: number;
  estimated_savings_egp_per_hour: number;
  pf_penalty_avoided_egp: number;
  co2_saved_kg: number;
  xai_reason: string;
  xai_reason_ar: string;
  machine_health: "SAFE" | "WARNING" | "CRITICAL";
  production_status: "ON_TRACK" | "AT_RISK" | "BEHIND";
  reward_components: Record<string, number>;
  dominant_reason: string;
  ai_enabled: boolean;
};

export type LivePrice = {
  timestamp: string;
  price_egp_kwh: number;
  price_source: string;
  tariff_class: string;
  is_peak: boolean;
  is_dr_event: boolean;
  dr_event_id: string | null;
  confidence: number;
  label: string;
};

export type LiveFrame = {
  telemetry?: Telemetry;
  recommendations: Recommendation[];
  energySeries: { t: number; mw: number; price: number; bath: number }[];
  connection: "connecting" | "open" | "closed";
  livePrice?: LivePrice;
};

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live-feed";

const MAX_SERIES = 120; // 6 minutes at 3s ticks
const MAX_LOG = 80;

export function useLiveFeed(): LiveFrame {
  const [frame, setFrame] = useState<LiveFrame>({
    recommendations: [],
    energySeries: [],
    connection: "connecting",
  });
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    let backoff = 1000;

    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      ws.onopen = () => {
        backoff = 1000;
        setFrame((f) => ({ ...f, connection: "open" }));
      };
      ws.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data);
          if (parsed.type === "telemetry") {
            const t = parsed.data as Telemetry;
            setFrame((f) => {
              const series = [
                ...f.energySeries,
                {
                  t: Date.now(),
                  mw: t.arc_power_mw,
                  price: t.electricity_price,
                  bath: t.furnace_bath_temp,
                },
              ];
              if (series.length > MAX_SERIES) series.shift();
              return { ...f, telemetry: t, energySeries: series };
            });
          } else if (parsed.type === "recommendation") {
            const r = parsed.data as Recommendation;
            setFrame((f) => {
              const recs = [r, ...f.recommendations];
              if (recs.length > MAX_LOG) recs.pop();
              return { ...f, recommendations: recs };
            });
          } else if (parsed.type === "pricing") {
            const p = parsed.data as LivePrice;
            setFrame((f) => ({ ...f, livePrice: p }));
          }
        } catch {}
      };
      ws.onclose = () => {
        setFrame((f) => ({ ...f, connection: "closed" }));
        if (!cancelled) {
          setTimeout(connect, backoff);
          backoff = Math.min(backoff * 2, 15000);
        }
      };
      ws.onerror = () => ws.close();
    }
    connect();

    return () => {
      cancelled = true;
      wsRef.current?.close();
    };
  }, []);

  return frame;
}
