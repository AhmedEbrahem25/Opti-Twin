export type BackendCrisisFlags = {
  wall_overheat: boolean;
  electrode_break: boolean;
  grid_spike: boolean;
  transformer_alarm: boolean;
};

export type BackendTelemetry = {
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
  crisis_flags?: BackendCrisisFlags;
};

export type BackendRecommendation = {
  timestamp?: string;
  machine_id?: string;
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

export type BackendKPI = {
  egp_saved_today: number;
  batches_completed: number;
  avg_arc_power_mw: number;
  avg_power_factor: number;
  co2_saved_kg: number;
  thermal_incidents_today: number;
  pf_penalty_avoided_today_egp: number;
  ai_decisions_today: number;
};

export type BackendLivePrice = {
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

export type BackendForecastPoint = {
  hour?: number;
  timestamp?: string;
  price_egp_kwh: number;
  is_peak?: boolean;
  tariff_class?: string;
  p05?: number;
  p50?: number;
  p95?: number;
  label?: string;
};

export type BackendForecast = {
  forecast: BackendForecastPoint[];
  generated_at?: string;
  horizon_hours?: number;
  step_minutes?: number;
  source?: string;
};

export type BackendRevenue = {
  energy_savings_egp: number;
  dr_payments_egp: number;
  capacity_credits_egp: number;
  ancillary_egp: number;
  total_revenue_egp: number;
};

export type BackendScheduleSlot = {
  start_hour: number;
  end_hour: number;
  expected_price_egp: number;
  is_peak: boolean;
  recommended_action?: string;
  heat_index?: number;
};

export type BackendSchedule = {
  slots: BackendScheduleSlot[];
  savings_vs_backtoback_egp: number;
  generated_for_hour?: number;
  note?: string;
};

export type BackendDREvent = {
  event_id: string;
  event_type: "CURTAILMENT" | "INTERRUPTIBLE" | "FREQUENCY_RESPONSE";
  status: "PENDING" | "ACCEPTED" | "REJECTED" | "COMPLETED";
  mw_requested: number;
  accepted_mw?: number;
  duration_minutes: number;
  payment_earned_egp: number;
  reason?: string;
  start_time?: string;
};

export type BackendDRSnapshot = {
  events: BackendDREvent[];
  total_payments_today: number;
  active_event?: BackendDREvent | null;
};

export type BackendPricingSearchResult = {
  total: number;
  results: Array<Record<string, unknown>>;
  stats: Record<string, unknown>;
};

export type BackendLogEntry = {
  timestamp: string;
  level: string;
  service: string;
  message: string;
};

export type BackendLogsResponse = {
  logs: BackendLogEntry[];
  stats: Record<string, unknown>;
};

export type WSFrame =
  | { type: "telemetry"; data: BackendTelemetry }
  | { type: "recommendation"; data: BackendRecommendation }
  | { type: "pricing"; data: BackendLivePrice };

export const LIVE_MACHINE_ID = "factory-1-m1";
export const LIVE_MACHINE_NAME = "EAF #2 — 185t Danieli";
export const LIVE_FACTORY_ID = "factory-1";
