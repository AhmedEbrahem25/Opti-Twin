"use client";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KPICardProps {
  label: string;
  value: number;
  previousValue?: number;
  suffix?: string;
  prefix?: string;
  format?: (v: number) => string;
  trend?: number;
  icon?: React.ReactNode;
  accentColor?: string;
  className?: string;
}

export function KPICard({
  label, value, previousValue, suffix = "", prefix = "", format,
  trend, icon, accentColor, className,
}: KPICardProps) {
  const motionValue = useMotionValue(previousValue ?? 0);
  const springValue = useSpring(motionValue, { stiffness: 80, damping: 25 });
  const [displayValue, setDisplayValue] = useState(previousValue ?? 0);

  useEffect(() => {
    motionValue.set(value);
  }, [value, motionValue]);

  useEffect(() => {
    const unsub = springValue.on("change", (v) => setDisplayValue(v));
    return unsub;
  }, [springValue]);

  const formatted = format ? format(displayValue) : Math.round(displayValue).toLocaleString();
  const trendValue = trend ?? (previousValue ? ((value - previousValue) / previousValue) * 100 : 0);
  const trendDir = trendValue > 0 ? "up" : trendValue < 0 ? "down" : "neutral";

  return (
    <Card spotlight className={cn("group relative overflow-hidden", className)}>
      {accentColor && (
        <div
          className="absolute top-0 left-0 right-0 h-[2px] opacity-60"
          style={{ background: accentColor }}
        />
      )}
      <div className="p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="type-label">{label}</span>
          {icon && (
            <div className="text-text-tertiary group-hover:text-accent transition-colors duration-300">
              {icon}
            </div>
          )}
        </div>
        <div className="flex items-end gap-2">
          <motion.span
            className="text-2xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          >
            {prefix}{formatted}{suffix}
          </motion.span>
          {trendValue !== 0 && (
            <motion.div
              className={cn(
                "flex items-center gap-0.5 text-xs font-medium mb-0.5",
                trendDir === "up" && "text-success",
                trendDir === "down" && "text-danger",
                trendDir === "neutral" && "text-text-tertiary",
              )}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.3 }}
            >
              {trendDir === "up" && <TrendingUp size={12} />}
              {trendDir === "down" && <TrendingDown size={12} />}
              {trendDir === "neutral" && <Minus size={12} />}
              <span>{trendValue > 0 ? "+" : ""}{trendValue.toFixed(1)}%</span>
            </motion.div>
          )}
        </div>
      </div>
    </Card>
  );
}
