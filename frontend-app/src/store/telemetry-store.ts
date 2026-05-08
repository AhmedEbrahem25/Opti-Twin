import { create } from "zustand";
import type { TelemetryPoint, KPISnapshot, Recommendation, XAILogEntry, Alert } from "@/types";
import type {
  BackendDRSnapshot,
  BackendForecast,
  BackendLivePrice,
  BackendRevenue,
  BackendSchedule,
} from "@/lib/backend-types";
import type { DPEMode, ProfileName } from "@/lib/api";

interface TelemetryState {
  liveData: Map<string, TelemetryPoint[]>;
  latestPoints: Map<string, TelemetryPoint>;
  kpis: KPISnapshot;
  recommendations: Recommendation[];
  xaiLogs: XAILogEntry[];
  liveAlerts: Alert[];
  isConnected: boolean;
  lastUpdate: string | null;
  aiEnabled: boolean;
  // Pricing & policy state
  livePrice: BackendLivePrice | null;
  forecast: BackendForecast | null;
  revenue: BackendRevenue | null;
  drSnapshot: BackendDRSnapshot | null;
  schedule: BackendSchedule | null;
  dpeMode: DPEMode;
  touMode: boolean;
  aiProfile: ProfileName;
  // Mutators
  addTelemetryPoint: (point: TelemetryPoint) => void;
  addRecommendation: (rec: Recommendation) => void;
  addXAILog: (log: XAILogEntry) => void;
  setLiveAlerts: (alerts: Alert[]) => void;
  upsertLiveAlert: (alert: Alert) => void;
  setKPIs: (kpis: KPISnapshot) => void;
  setConnected: (connected: boolean) => void;
  toggleAI: () => void;
  setLivePrice: (p: BackendLivePrice) => void;
  setForecast: (f: BackendForecast) => void;
  setRevenue: (r: BackendRevenue) => void;
  setDRSnapshot: (s: BackendDRSnapshot) => void;
  setSchedule: (s: BackendSchedule) => void;
  setDPEMode: (m: DPEMode) => void;
  setTouMode: (b: boolean) => void;
  setAIProfile: (p: ProfileName) => void;
}

const MAX_POINTS = 200;

export const useTelemetryStore = create<TelemetryState>((set) => ({
  liveData: new Map(),
  latestPoints: new Map(),
  kpis: {
    totalFactories: 1,
    activeMachines: 1,
    totalEnergySavedKwh: 0,
    totalCostSaved: 0,
    aiActionsToday: 0,
    avgEfficiency: 0,
    activeAlerts: 0,
    uptime: 99.2,
    maintenanceAlertsToday: 0,
    avgMaintenanceRisk: 0,
    avgOperationalEfficiency: 0,
    avgProcessStability: 0,
    idleMinutesToday: 0,
  },
  recommendations: [],
  xaiLogs: [],
  liveAlerts: [],
  isConnected: false,
  lastUpdate: null,
  aiEnabled: true,
  livePrice: null,
  forecast: null,
  revenue: null,
  drSnapshot: null,
  schedule: null,
  dpeMode: "flat",
  touMode: false,
  aiProfile: "default",

  addTelemetryPoint: (point) =>
    set((state) => {
      const newLiveData = new Map(state.liveData);
      const existing = newLiveData.get(point.machineId) || [];
      const updated = [...existing, point].slice(-MAX_POINTS);
      newLiveData.set(point.machineId, updated);

      const newLatest = new Map(state.latestPoints);
      newLatest.set(point.machineId, point);

      return { liveData: newLiveData, latestPoints: newLatest, lastUpdate: point.timestamp };
    }),

  addRecommendation: (rec) =>
    set((state) => {
      if (state.recommendations[0]?.id === rec.id) return state;
      return { recommendations: [rec, ...state.recommendations].slice(0, 50) };
    }),

  addXAILog: (log) =>
    set((state) => {
      if (state.xaiLogs[0]?.id === log.id) return state;
      // Allow up to 5000 logs to ensure the 12-hour 'AI Actions Over Time' chart stays populated
      return { xaiLogs: [log, ...state.xaiLogs].slice(0, 5000) };
    }),

  setLiveAlerts: (alerts) => set({ liveAlerts: alerts }),
  upsertLiveAlert: (alert) =>
    set((state) => {
      const rest = state.liveAlerts.filter((a) => a.id !== alert.id);
      return { liveAlerts: [alert, ...rest].slice(0, 20) };
    }),
  setKPIs: (kpis) => set({ kpis }),
  setConnected: (connected) => set({ isConnected: connected }),
  toggleAI: () => set((s) => ({ aiEnabled: !s.aiEnabled })),
  setLivePrice: (p) => set({ livePrice: p }),
  setForecast: (f) => set({ forecast: f }),
  setRevenue: (r) => set({ revenue: r }),
  setDRSnapshot: (s) => set({ drSnapshot: s }),
  setSchedule: (s) => set({ schedule: s }),
  setDPEMode: (m) => set({ dpeMode: m }),
  setTouMode: (b) => set({ touMode: b }),
  setAIProfile: (p) => set({ aiProfile: p }),
}));
