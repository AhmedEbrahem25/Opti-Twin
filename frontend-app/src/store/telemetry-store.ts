import { create } from "zustand";
import type { TelemetryPoint, KPISnapshot, Recommendation, XAILogEntry } from "@/types";

interface TelemetryState {
  liveData: Map<string, TelemetryPoint[]>;
  latestPoints: Map<string, TelemetryPoint>;
  kpis: KPISnapshot;
  recommendations: Recommendation[];
  xaiLogs: XAILogEntry[];
  isConnected: boolean;
  lastUpdate: string | null;
  aiEnabled: boolean;
  addTelemetryPoint: (point: TelemetryPoint) => void;
  addRecommendation: (rec: Recommendation) => void;
  addXAILog: (log: XAILogEntry) => void;
  setKPIs: (kpis: KPISnapshot) => void;
  setConnected: (connected: boolean) => void;
  toggleAI: () => void;
}

const MAX_POINTS = 200;

export const useTelemetryStore = create<TelemetryState>((set) => ({
  liveData: new Map(),
  latestPoints: new Map(),
  kpis: {
    totalFactories: 3,
    activeMachines: 8,
    totalEnergySavedKwh: 1247.5,
    totalCostSaved: 4820,
    aiActionsToday: 47,
    avgEfficiency: 87.3,
    activeAlerts: 3,
    uptime: 99.2,
  },
  recommendations: [],
  xaiLogs: [],
  isConnected: false,
  lastUpdate: null,
  aiEnabled: true,

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
    set((state) => ({
      recommendations: [rec, ...state.recommendations].slice(0, 50),
    })),

  addXAILog: (log) =>
    set((state) => ({
      xaiLogs: [log, ...state.xaiLogs].slice(0, 100),
    })),

  setKPIs: (kpis) => set({ kpis }),
  setConnected: (connected) => set({ isConnected: connected }),
  toggleAI: () => set((s) => ({ aiEnabled: !s.aiEnabled })),
}));
