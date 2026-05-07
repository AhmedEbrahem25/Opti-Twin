"use client";
import { useEffect, useRef, useState } from "react";
import { useMotionValue, useSpring, useTransform } from "framer-motion";

export function useAnimatedCounter(target: number, duration = 1.5) {
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { stiffness: 100, damping: 30, duration: duration * 1000 });
  const rounded = useTransform(springValue, (v) => Math.round(v));
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    motionValue.set(target);
  }, [target, motionValue]);

  useEffect(() => {
    const unsubscribe = rounded.on("change", (v) => setDisplay(v));
    return unsubscribe;
  }, [rounded]);

  return display;
}

export function useSpotlight() {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    ref.current.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
    ref.current.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
  };

  return { ref, handleMouseMove };
}

export function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(query);
    setMatches(mq.matches);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [query]);

  return matches;
}

export function useLiveTelemetry(machineIds: string[], intervalMs = 3000) {
  const { addTelemetryPoint } = useTelemetryStoreImport();

  useEffect(() => {
    const { generateTelemetryPoint } = require("@/services/mock-data");
    const interval = setInterval(() => {
      machineIds.forEach((id) => {
        addTelemetryPoint(generateTelemetryPoint(id));
      });
    }, intervalMs);
    return () => clearInterval(interval);
  }, [machineIds, intervalMs, addTelemetryPoint]);
}

function useTelemetryStoreImport() {
  const { useTelemetryStore } = require("@/store/telemetry-store");
  return useTelemetryStore();
}
