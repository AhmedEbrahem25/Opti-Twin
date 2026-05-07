"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MetricRingProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  suffix?: string;
  color?: string;
  className?: string;
}

export function MetricRing({
  value, max = 100, size = 80, strokeWidth = 6,
  label, suffix = "%", color, className,
}: MetricRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(value / max, 1);
  const strokeDashoffset = circumference * (1 - percentage);

  const getColor = () => {
    if (color) return color;
    if (percentage >= 0.8) return "var(--color-success)";
    if (percentage >= 0.5) return "var(--color-accent)";
    if (percentage >= 0.3) return "var(--color-warning)";
    return "var(--color-danger)";
  };

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="var(--color-bg-400)"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={getColor()} strokeWidth={strokeWidth}
          strokeLinecap="round" strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          style={{ filter: `drop-shadow(0 0 6px ${getColor()})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-sm font-bold text-text-primary font-[family-name:var(--font-display)]">
          {Math.round(value)}{suffix}
        </span>
        {label && <span className="text-[9px] text-text-tertiary mt-0.5">{label}</span>}
      </div>
    </div>
  );
}
