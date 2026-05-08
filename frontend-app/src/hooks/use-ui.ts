"use client";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
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
  const subscribe = (onChange: () => void) => {
    if (typeof window === "undefined") return () => {};
    const mq = window.matchMedia(query);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  };
  const getSnapshot = () =>
    typeof window === "undefined" ? false : window.matchMedia(query).matches;
  const getServerSnapshot = () => false;
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

