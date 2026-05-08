import type { MachineSchema } from "@/types";

export const MACHINE_SCHEMAS: Record<string, MachineSchema> = {
  motor: {
    type: "motor",
    displayName: "Electric Motor",
    icon: "Cog",
    primaryMetric: "rpm",
    color: "#f59e0b",
    metrics: [
      { key: "rpm", label: "RPM", unit: "rpm", icon: "Gauge", format: "number", warningThreshold: 1600, criticalThreshold: 1800 },
      { key: "temperature", label: "Temperature", unit: "°C", icon: "Thermometer", format: "temperature", warningThreshold: 80, criticalThreshold: 90 },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
      { key: "vibration", label: "Vibration", unit: "mm/s", icon: "Activity", format: "number", warningThreshold: 4.5, criticalThreshold: 7.1 },
    ],
  },
  furnace: {
    type: "furnace",
    displayName: "Industrial Furnace",
    icon: "Flame",
    primaryMetric: "temperature",
    color: "#ef4444",
    metrics: [
      { key: "temperature", label: "Temperature", unit: "°C", icon: "Thermometer", format: "temperature", warningThreshold: 850, criticalThreshold: 950 },
      { key: "batchSize", label: "Batch Size", unit: "units", icon: "Package", format: "number" },
      { key: "cycleTime", label: "Cycle Time", unit: "min", icon: "Clock", format: "number" },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
    ],
  },
  chiller: {
    type: "chiller",
    displayName: "Chiller Unit",
    icon: "Snowflake",
    primaryMetric: "temperature",
    color: "#22d3ee",
    metrics: [
      { key: "temperature", label: "Coolant Temp", unit: "°C", icon: "Thermometer", format: "temperature", warningThreshold: 12, criticalThreshold: 18 },
      { key: "coolingPower", label: "Cooling Power", unit: "%", icon: "Gauge", format: "percentage" },
      { key: "flowRate", label: "Flow Rate", unit: "L/min", icon: "Droplets", format: "number" },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
    ],
  },
  compressor: {
    type: "compressor",
    displayName: "Air Compressor",
    icon: "Wind",
    primaryMetric: "pressure",
    color: "#3b82f6",
    metrics: [
      { key: "pressure", label: "Pressure", unit: "bar", icon: "Gauge", format: "number", warningThreshold: 8, criticalThreshold: 10 },
      { key: "temperature", label: "Temperature", unit: "°C", icon: "Thermometer", format: "temperature", warningThreshold: 85, criticalThreshold: 95 },
      { key: "flowRate", label: "Flow Rate", unit: "m³/min", icon: "Wind", format: "number" },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
    ],
  },
  hvac: {
    type: "hvac",
    displayName: "HVAC System",
    icon: "AirVent",
    primaryMetric: "temperature",
    color: "#22c55e",
    metrics: [
      { key: "temperature", label: "Zone Temp", unit: "°C", icon: "Thermometer", format: "temperature" },
      { key: "humidity", label: "Humidity", unit: "%", icon: "Droplets", format: "percentage" },
      { key: "airflow", label: "Airflow", unit: "CFM", icon: "Wind", format: "number" },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
    ],
  },
  pump: {
    type: "pump",
    displayName: "Industrial Pump",
    icon: "Droplets",
    primaryMetric: "flowRate",
    color: "#6366f1",
    metrics: [
      { key: "flowRate", label: "Flow Rate", unit: "L/min", icon: "Droplets", format: "number" },
      { key: "pressure", label: "Pressure", unit: "bar", icon: "Gauge", format: "number" },
      { key: "temperature", label: "Temperature", unit: "°C", icon: "Thermometer", format: "temperature" },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
    ],
  },
  cooling_system: {
    type: "cooling_system",
    displayName: "Cooling System",
    icon: "Snowflake",
    primaryMetric: "temperature",
    color: "#06b6d4",
    metrics: [
      { key: "temperature", label: "Temp Load", unit: "°C", icon: "Thermometer", format: "temperature", warningThreshold: 15, criticalThreshold: 20 },
      { key: "coolingPower", label: "Cooling Power", unit: "%", icon: "Gauge", format: "percentage" },
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
    ],
  },
  generic: {
    type: "generic",
    displayName: "Industrial Equipment",
    icon: "Settings",
    primaryMetric: "energyKwh",
    color: "#888888",
    metrics: [
      { key: "energyKwh", label: "Energy", unit: "kWh", icon: "Zap", format: "energy" },
      { key: "temperature", label: "Temperature", unit: "°C", icon: "Thermometer", format: "temperature" },
      { key: "status", label: "Status", unit: "", icon: "Activity", format: "number" },
    ],
  },
};

export const NAV_ITEMS = [
  { label: "Workspace", href: "/workspace", icon: "LayoutDashboard" },
  { label: "AI Control Center", href: "/ai-control", icon: "Brain" },
  { label: "Analytics", href: "/analytics", icon: "BarChart3" },
  { label: "Search", href: "/search", icon: "Search" },
  { label: "Alerts", href: "/alerts", icon: "Bell" },
  { label: "Settings", href: "/settings", icon: "Settings" },
] as const;

export const PEAK_HOURS = { start: 18, end: 22 };
export const PEAK_PRICE = 2.5;
export const OFF_PEAK_PRICE = 1.2;

export const ANIMATION_CONFIG = {
  spring: { type: "spring" as const, stiffness: 300, damping: 30 },
  springBouncy: { type: "spring" as const, stiffness: 400, damping: 25 },
  smooth: { duration: 0.25, ease: [0.16, 1, 0.3, 1] as const },
  cinematic: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] as const },
  slow: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
};
