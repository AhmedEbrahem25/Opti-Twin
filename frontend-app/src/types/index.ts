export type MachineType =
  | "furnace"
  | "chiller"
  | "compressor"
  | "hvac"
  | "pump"
  | "boiler"
  | "cnc"
  | "cooling_system"
  | "motor"
  | "production_line"
  | "generic";

export type MachineStatus = "RUNNING" | "IDLE" | "WARNING" | "CRITICAL" | "FAULT" | "OFFLINE" | "MAINTENANCE";

export type AlertSeverity = "info" | "warning" | "critical" | "emergency";

export type RecommendationAction =
  | "REDUCE_MOTOR_SPEED"
  | "INCREASE_COOLING_POWER"
  | "SHIFT_LOAD"
  | "REDUCE_FURNACE_BATCH"
  | "INCREASE_MOTOR_SPEED"
  | "DECREASE_COOLING_POWER"
  | "SCHEDULE_MAINTENANCE"
  | "OPTIMIZE_CYCLE_TIME"
  // Backend EAF agent labels (opti-twin/ai_engine/environment.py)
  | "HOLD_STEADY"
  | "REDUCE_ARC_POWER"
  | "RAISE_PF_COMPENSATION"
  | "EMERGENCY_COOLING"
  | "PRE_PEAK_DROP"
  | "GRID_RIDE_THROUGH"
  | "TRANSFORMER_DERATE";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo?: string;
  plan: "starter" | "professional" | "enterprise";
  factoryCount: number;
  machineCount: number;
}

export interface Factory {
  id: string;
  organizationId: string;
  name: string;
  location: string;
  status: MachineStatus;
  productionLines: ProductionLine[];
  machineCount: number;
  activeAlerts: number;
  energyUsageKwh: number;
  costSavedToday: number;
  efficiencyScore: number;
}

export interface ProductionLine {
  id: string;
  factoryId: string;
  name: string;
  machines: Machine[];
  status: MachineStatus;
  throughput: number;
}

export interface Machine {
  id: string;
  factoryId: string;
  productionLineId: string;
  name: string;
  type: MachineType;
  status: MachineStatus;
  healthScore: number;
  lastUpdate: string;
  sensors: Sensor[];
  metrics: Record<string, number>;
}

export interface Sensor {
  id: string;
  machineId: string;
  name: string;
  unit: string;
  currentValue: number;
  minValue: number;
  maxValue: number;
  warningThreshold: number;
  criticalThreshold: number;
}

export interface TelemetryPoint {
  machineId: string;
  timestamp: string;
  rpm?: number;
  temperature?: number;
  energyKwh: number;
  costRate: number;
  isPeak: boolean;
  status: MachineStatus;
  pressure?: number;
  vibration?: number;
  flowRate?: number;
  humidity?: number;
}

export interface Recommendation {
  id: string;
  machineId: string;
  machineName: string;
  timestamp: string;
  actionLabel: RecommendationAction;
  magnitudePct: number;
  savingsEgpHr: number;
  xaiReason: string;
  xaiReasonAr?: string;
  dominantReason?: string;
  machineHealth: string;
  productionStatus: string;
  confidence: number;
  rewardComponents: {
    energySavingsScore: number;
    machineStressPenalty: number;
    productionDelayPenalty: number;
  };
}

export interface XAILogEntry {
  id: string;
  timestamp: string;
  machineId: string;
  machineName: string;
  action: RecommendationAction;
  reason: string;
  savingsEstimate: number;
  confidence: number;
  applied: boolean;
}

export interface Alert {
  id: string;
  factoryId: string;
  machineId?: string;
  machineName?: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  resolvedAt?: string;
}

export interface KPISnapshot {
  totalFactories: number;
  activeMachines: number;
  totalEnergySavedKwh: number;
  totalCostSaved: number;
  aiActionsToday: number;
  avgEfficiency: number;
  activeAlerts: number;
  uptime: number;
}

export interface MetricDefinition {
  key: string;
  label: string;
  unit: string;
  icon: string;
  warningThreshold?: number;
  criticalThreshold?: number;
  format: "number" | "temperature" | "percentage" | "energy" | "currency";
}

export interface MachineSchema {
  type: MachineType;
  displayName: string;
  icon: string;
  primaryMetric: string;
  metrics: MetricDefinition[];
  color: string;
}
