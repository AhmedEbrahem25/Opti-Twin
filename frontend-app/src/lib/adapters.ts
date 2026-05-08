import type {
  Alert,
  KPISnapshot,
  MachineStatus,
  Recommendation,
  RecommendationAction,
  TelemetryPoint,
  XAILogEntry,
} from "@/types";
import type {
  BackendCrisisFlags,
  BackendKPI,
  BackendRecommendation,
  BackendTelemetry,
} from "./backend-types";
import { LIVE_FACTORY_ID, LIVE_MACHINE_ID, LIVE_MACHINE_NAME } from "./backend-types";

const KNOWN_STATUSES: ReadonlySet<string> = new Set([
  "RUNNING",
  "IDLE",
  "WARNING",
  "CRITICAL",
  "FAULT",
  "OFFLINE",
  "MAINTENANCE",
]);

function normaliseStatus(raw: string): MachineStatus {
  const upper = raw.toUpperCase();
  return (KNOWN_STATUSES.has(upper) ? upper : "RUNNING") as MachineStatus;
}

export function adaptTelemetry(t: BackendTelemetry): TelemetryPoint {
  // arc_power_mw is current draw in MW; convert to kWh-rate equivalent for display.
  // 1 MW sustained for 1 hour = 1000 kWh, so kW = MW * 1000.
  const energyKwh = t.arc_power_mw * 1000;
  return {
    machineId: LIVE_MACHINE_ID,
    timestamp:
      typeof t.timestamp === "string" ? t.timestamp : new Date().toISOString(),
    temperature: t.furnace_bath_temp,
    energyKwh,
    costRate: t.electricity_price,
    isPeak: t.is_peak,
    status: normaliseStatus(t.status),
    pressure: t.cooling_water_flow_lmin / 100,
    // Use power-factor deviation from 1.0 as a proxy "vibration" so the existing
    // sensor card stays visually populated; real backend has no vibration sensor.
    vibration: Math.max(0, (1 - t.power_factor) * 10),
    flowRate: t.cooling_water_flow_lmin,
  };
}

const ACTION_LABELS: ReadonlySet<RecommendationAction> = new Set<RecommendationAction>([
  "REDUCE_MOTOR_SPEED",
  "INCREASE_COOLING_POWER",
  "SHIFT_LOAD",
  "REDUCE_FURNACE_BATCH",
  "INCREASE_MOTOR_SPEED",
  "DECREASE_COOLING_POWER",
  "SCHEDULE_MAINTENANCE",
  "OPTIMIZE_CYCLE_TIME",
  "HOLD_STEADY",
  "REDUCE_ARC_POWER",
  "RAISE_PF_COMPENSATION",
  "EMERGENCY_COOLING",
  "PRE_PEAK_DROP",
  "GRID_RIDE_THROUGH",
  "TRANSFORMER_DERATE",
]);

function normaliseAction(raw: string): RecommendationAction {
  return (ACTION_LABELS.has(raw as RecommendationAction)
    ? raw
    : "HOLD_STEADY") as RecommendationAction;
}

function recIdFor(r: BackendRecommendation): string {
  const ts = r.timestamp ?? new Date().toISOString();
  return `rec-${ts}-${r.action_label}`;
}

function toEnergySavingsScore(r: BackendRecommendation): number {
  const v = r.reward_components?.energy ?? r.reward_components?.energy_savings;
  return typeof v === "number" ? Math.abs(v) * 100 : 0;
}

function toMachineStress(r: BackendRecommendation): number {
  const v = r.reward_components?.machine_stress ?? r.reward_components?.stress;
  return typeof v === "number" ? Math.abs(v) * 100 : 0;
}

function toProductionDelay(r: BackendRecommendation): number {
  const v = r.reward_components?.production_delay ?? r.reward_components?.production;
  return typeof v === "number" ? Math.abs(v) * 100 : 0;
}

export function adaptRecommendation(r: BackendRecommendation): Recommendation {
  return {
    id: recIdFor(r),
    machineId: LIVE_MACHINE_ID,
    machineName: LIVE_MACHINE_NAME,
    timestamp: r.timestamp ?? new Date().toISOString(),
    actionLabel: normaliseAction(r.action_label),
    magnitudePct: r.action_magnitude_pct,
    savingsEgpHr: r.estimated_savings_egp_per_hour,
    xaiReason: r.xai_reason,
    xaiReasonAr: r.xai_reason_ar,
    dominantReason: r.dominant_reason,
    machineHealth: r.machine_health,
    productionStatus: r.production_status,
    confidence: 90,
    rewardComponents: {
      energySavingsScore: toEnergySavingsScore(r),
      machineStressPenalty: toMachineStress(r),
      productionDelayPenalty: toProductionDelay(r),
    },
  };
}

export function adaptToXAILog(r: BackendRecommendation): XAILogEntry {
  return {
    id: recIdFor(r),
    timestamp: r.timestamp ?? new Date().toISOString(),
    machineId: LIVE_MACHINE_ID,
    machineName: LIVE_MACHINE_NAME,
    action: normaliseAction(r.action_label),
    reason: r.xai_reason,
    savingsEstimate: r.estimated_savings_egp_per_hour,
    confidence: 90,
    applied: r.ai_enabled && r.action_label !== "HOLD_STEADY",
  };
}

// Heat duration assumption for converting batches → kWh.
// Ezz Steel EAF #2 typical heat ≈ 50 minutes ≈ 0.83 h.
const HEAT_DURATION_HOURS = 50 / 60;

export function adaptKPI(k: BackendKPI, fallback: KPISnapshot): KPISnapshot {
  const totalEnergyMWh = k.avg_arc_power_mw * k.batches_completed * HEAT_DURATION_HOURS;
  return {
    totalFactories: fallback.totalFactories,
    activeMachines: fallback.activeMachines,
    totalEnergySavedKwh: Math.round(totalEnergyMWh * 1000),
    totalCostSaved: Math.round(k.egp_saved_today),
    aiActionsToday: k.ai_decisions_today,
    avgEfficiency: Math.round(k.avg_power_factor * 100 * 10) / 10,
    activeAlerts: k.thermal_incidents_today,
    uptime: fallback.uptime,
  };
}

export function crisisFlagsToAlerts(
  flags: BackendCrisisFlags | undefined,
  timestamp: string,
): Alert[] {
  if (!flags) return [];
  const out: Alert[] = [];
  const meta: Record<keyof BackendCrisisFlags, { title: string; message: string }> = {
    wall_overheat: {
      title: "Wall panel overheat",
      message: "Furnace wall panel temperature exceeded the safety threshold. Emergency cooling engaged.",
    },
    electrode_break: {
      title: "Electrode fracture detected",
      message: "Electrode position telemetry indicates a fracture. Production paused for replacement.",
    },
    grid_spike: {
      title: "Grid frequency excursion",
      message: "Grid frequency dropped outside ±0.5 Hz. AI engaging ride-through.",
    },
    transformer_alarm: {
      title: "Transformer alarm",
      message: "Transformer protection alarm raised. Reducing arc power.",
    },
  };
  (Object.keys(meta) as (keyof BackendCrisisFlags)[]).forEach((k) => {
    if (flags[k]) {
      out.push({
        id: `crisis-${k}-${timestamp}`,
        factoryId: LIVE_FACTORY_ID,
        machineId: LIVE_MACHINE_ID,
        machineName: LIVE_MACHINE_NAME,
        severity: "critical",
        title: meta[k].title,
        message: meta[k].message,
        timestamp,
        acknowledged: false,
      });
    }
  });
  return out;
}
