"use client";
import { useEffect, useRef } from "react";
import { useTelemetryStore } from "@/store/telemetry-store";
import { api } from "@/lib/api";
import {
  adaptKPI,
  adaptRecommendation,
  adaptTelemetry,
  adaptToXAILog,
  crisisFlagsToAlerts,
  maintenanceAlertToAlert,
} from "@/lib/adapters";
import type { WSFrame } from "@/lib/backend-types";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live-feed";
const STATS_POLL_MS = 2000;
const PRICING_POLL_MS = 30_000;
const SCHEDULE_POLL_MS = 60_000;
const REC_POLL_MS = 5_000;

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    let backoff = 1000;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const store = useTelemetryStore.getState();

    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        backoff = 1000;
        useTelemetryStore.getState().setConnected(true);
      };

      ws.onmessage = (msg) => {
        try {
          const parsed: WSFrame = JSON.parse(msg.data);
          const s = useTelemetryStore.getState();
          if (parsed.type === "telemetry") {
            const adapted = adaptTelemetry(parsed.data);
            s.addTelemetryPoint(adapted);
            const maintenanceAlerts = s.liveAlerts.filter((a) =>
              a.id.startsWith("maintenance-"),
            );
            s.setLiveAlerts([
              ...crisisFlagsToAlerts(parsed.data.crisis_flags, adapted.timestamp),
              ...maintenanceAlerts,
            ].slice(0, 20));
          } else if (parsed.type === "recommendation") {
            s.addRecommendation(adaptRecommendation(parsed.data));
            s.addXAILog(adaptToXAILog(parsed.data));
            if (parsed.data.maintenance_alert) {
              s.upsertLiveAlert({
                id: `maintenance-rec-${parsed.data.machine_id ?? "machine"}-${parsed.data.timestamp}`,
                factoryId: "factory-1",
                machineId: "factory-1-m1",
                machineName: "EAF #2 — 185t Danieli",
                severity:
                  parsed.data.maintenance_risk_level === "CRITICAL"
                    ? "critical"
                    : "warning",
                title:
                  parsed.data.maintenance_risk_level === "CRITICAL"
                    ? "Predictive failure risk"
                    : "Predictive maintenance warning",
                message:
                  parsed.data.maintenance_xai_reason ||
                  parsed.data.maintenance_fault_prediction ||
                  "Machine behavior is drifting from the safe operating envelope.",
                timestamp: parsed.data.timestamp ?? new Date().toISOString(),
                acknowledged: false,
              });
            }
          } else if (parsed.type === "pricing") {
            s.setLivePrice(parsed.data);
          } else if (parsed.type === "maintenance_alert") {
            s.upsertLiveAlert(maintenanceAlertToAlert(parsed.data));
          }
        } catch {
          // malformed frame; drop silently
        }
      };

      ws.onclose = () => {
        useTelemetryStore.getState().setConnected(false);
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, backoff);
          backoff = Math.min(backoff * 2, 15000);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();

    const pollStats = async () => {
      try {
        const k = await api.getStats();
        const fallback = useTelemetryStore.getState().kpis;
        useTelemetryStore.getState().setKPIs(adaptKPI(k, fallback));
      } catch {
        // backend unavailable; KPIs stay at last known values
      }
    };

    pollStats();
    const statsInterval = setInterval(pollStats, STATS_POLL_MS);

    const pollPricing = async () => {
      const s = useTelemetryStore.getState();
      try {
        const live = await api.getLivePrice();
        s.setLivePrice(live);
      } catch { /* offline */ }
      try {
        const fc = await api.getForecast();
        s.setForecast(fc);
      } catch { /* offline */ }
      try {
        const rev = await api.getRevenue();
        s.setRevenue(rev);
      } catch { /* offline */ }
      try {
        const m = await api.getPricingMode();
        s.setDPEMode(m.mode);
      } catch { /* offline */ }
      try {
        const dr = await api.getDREvents();
        s.setDRSnapshot(dr);
      } catch { /* offline */ }
    };

    pollPricing();
    const pricingInterval = setInterval(pollPricing, PRICING_POLL_MS);

    // Poll optimal heat schedule once per minute.
    const pollSchedule = async () => {
      try {
        const sched = await api.getSchedule();
        useTelemetryStore.getState().setSchedule(sched);
      } catch { /* offline */ }
    };
    pollSchedule();
    const scheduleInterval = setInterval(pollSchedule, SCHEDULE_POLL_MS);

    // Poll latest recommendation as a REST fallback (WS is primary source).
    const pollRec = async () => {
      try {
        const rec = await api.getRecommendation();
        if (rec) {
          const s = useTelemetryStore.getState();
          s.addRecommendation(adaptRecommendation(rec));
          s.addXAILog(adaptToXAILog(rec));
        }
      } catch { /* offline */ }
    };
    pollRec();
    const recInterval = setInterval(pollRec, REC_POLL_MS);

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      clearInterval(statsInterval);
      clearInterval(pricingInterval);
      clearInterval(scheduleInterval);
      clearInterval(recInterval);
      wsRef.current?.close();
      store.setConnected(false);
    };
  }, []);

  return <>{children}</>;
}
