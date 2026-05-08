import type { Factory, Machine, TelemetryPoint, Recommendation, XAILogEntry, Alert } from "@/types";
import { randomInRange } from "@/lib/utils";


export const FACTORY_FIXTURES: Factory[] = [
  {
    id: "factory-1", organizationId: "org-1", name: "EAF Workshop — Ain Sokhna",
    location: "Ain Sokhna, Egypt", status: "RUNNING", productionLines: [],
    machineCount: 1, activeAlerts: 0, energyUsageKwh: 0,
    costSavedToday: 0, efficiencyScore: 0,
  },
  {
    id: "factory-2", organizationId: "org-1", name: "Alexandria Port Facility",
    location: "Alexandria, Egypt", status: "RUNNING", productionLines: [],
    machineCount: 4, activeAlerts: 1, energyUsageKwh: 623.1,
    costSavedToday: 1580, efficiencyScore: 91,
  },
  {
    id: "factory-3", organizationId: "org-1", name: "Alamein Processing Plant",
    location: "El Alamein, Egypt", status: "WARNING", productionLines: [],
    machineCount: 3, activeAlerts: 4, energyUsageKwh: 412.8,
    costSavedToday: 900, efficiencyScore: 73,
  },
];

export function generateMockFactories(): Factory[] {
  return FACTORY_FIXTURES;
}

// factory-1's single machine is the live EAF — its metrics are overwritten at
// runtime by RealtimeProvider via the telemetry store. Other factories stay
// fully mocked so the multi-factory shell remains visually populated.
export function generateMockMachines(factoryId: string): Machine[] {
  if (factoryId === "factory-1") {
    return [
      {
        id: "factory-1-m1", factoryId, productionLineId: "line-1",
        name: "EAF #2 — 185t Danieli", type: "furnace",
        status: "RUNNING", healthScore: 88,
        sensors: [], lastUpdate: new Date().toISOString(),
        metrics: { temperature: 1580, energyKwh: 95000 },
      },
    ];
  }
  const configs = [
    { id: `${factoryId}-m1`, name: "Machine A — Motor", type: "motor" as const, status: "RUNNING" as const, healthScore: 92 },
    { id: `${factoryId}-m2`, name: "Machine B — Cooling System", type: "cooling_system" as const, status: "RUNNING" as const, healthScore: 88 },
    { id: `${factoryId}-m3`, name: "Machine C — Furnace", type: "furnace" as const, status: "WARNING" as const, healthScore: 71 },
    { id: `${factoryId}-m4`, name: "Compressor Unit D", type: "compressor" as const, status: "RUNNING" as const, healthScore: 95 },
    { id: `${factoryId}-m5`, name: "HVAC System E", type: "hvac" as const, status: "IDLE" as const, healthScore: 100 },
  ];
  return configs.map((c) => ({
    ...c, factoryId, productionLineId: "line-1", sensors: [], lastUpdate: new Date().toISOString(),
    metrics: { rpm: randomInRange(1200, 1600), temperature: randomInRange(55, 85), energyKwh: randomInRange(80, 150) },
  }));
}

export function generateTelemetryPoint(machineId: string): TelemetryPoint {
  const hour = new Date().getHours();
  const isPeak = hour >= 18 && hour < 22;
  return {
    machineId, timestamp: new Date().toISOString(),
    rpm: randomInRange(1200, 1650), temperature: randomInRange(55, 88),
    energyKwh: randomInRange(80, 160), costRate: isPeak ? 2.5 : 1.2,
    isPeak, status: "RUNNING", pressure: randomInRange(4, 8), vibration: randomInRange(1, 5),
  };
}

const ACTION_LABELS: Recommendation["actionLabel"][] = [
  "REDUCE_MOTOR_SPEED", "INCREASE_COOLING_POWER", "SHIFT_LOAD", "REDUCE_FURNACE_BATCH",
];
const REASONS = [
  "Peak pricing detected (2.5 EGP/kWh). Motor temp safe (68°C < 90°C). Backlog nominal. Optimal to reduce speed.",
  "Motor stress detected (87°C > 85°C threshold). β-weight override activated. Machine health prioritized.",
  "Off-peak window approaching. Shift non-critical loads to reduce peak demand charges by estimated 15%.",
  "Furnace batch size exceeds optimal efficiency point. Reducing batch size improves energy per unit ratio.",
];

export function generateMockRecommendation(): Recommendation {
  const idx = Math.floor(Math.random() * ACTION_LABELS.length);
  return {
    id: `rec-${Date.now()}`, machineId: "factory-1-m1", machineName: "Machine A — Motor",
    timestamp: new Date().toISOString(), actionLabel: ACTION_LABELS[idx],
    magnitudePct: -randomInRange(5, 25), savingsEgpHr: randomInRange(80, 250),
    xaiReason: REASONS[idx], machineHealth: "SAFE", productionStatus: "ON_TRACK",
    confidence: randomInRange(78, 98),
    rewardComponents: { energySavingsScore: randomInRange(70, 98), machineStressPenalty: randomInRange(0, 15), productionDelayPenalty: randomInRange(0, 10) },
  };
}

export function generateMockXAILogs(count = 10): XAILogEntry[] {
  return Array.from({ length: count }, (_, i) => {
    const idx = Math.floor(Math.random() * ACTION_LABELS.length);
    const ts = new Date(Date.now() - i * 180_000);
    return {
      id: `xai-${i}`, timestamp: ts.toISOString(), machineId: `factory-1-m${(i % 3) + 1}`,
      machineName: ["Machine A — Motor", "Machine B — Cooling", "Machine C — Furnace"][i % 3],
      action: ACTION_LABELS[idx], reason: REASONS[idx],
      savingsEstimate: randomInRange(50, 300), confidence: randomInRange(75, 99), applied: Math.random() > 0.2,
    };
  });
}

export function generateMockAlerts(): Alert[] {
  return [
    { id: "alert-1", factoryId: "factory-1", machineId: "factory-1-m3", machineName: "Machine C — Furnace", severity: "critical", title: "Temperature Exceeding Threshold", message: "Furnace temperature reached 94°C, exceeding the 90°C critical threshold. Immediate cooling recommended.", timestamp: new Date(Date.now() - 120_000).toISOString(), acknowledged: false },
    { id: "alert-2", factoryId: "factory-1", machineId: "factory-1-m1", machineName: "Machine A — Motor", severity: "warning", title: "Vibration Level Elevated", message: "Motor vibration at 4.8mm/s — approaching warning threshold of 5.0mm/s. Schedule maintenance inspection.", timestamp: new Date(Date.now() - 300_000).toISOString(), acknowledged: false },
    { id: "alert-3", factoryId: "factory-3", severity: "warning", title: "Peak Hour Energy Spike", message: "Factory energy consumption 23% above baseline during peak hours. AI recommends load shifting.", timestamp: new Date(Date.now() - 600_000).toISOString(), acknowledged: true },
    { id: "alert-4", factoryId: "factory-2", machineId: "factory-2-m2", machineName: "Cooling Unit B", severity: "info", title: "Scheduled Maintenance Due", message: "Cooling system B is due for quarterly maintenance in 3 days.", timestamp: new Date(Date.now() - 3600_000).toISOString(), acknowledged: true },
  ];
}
