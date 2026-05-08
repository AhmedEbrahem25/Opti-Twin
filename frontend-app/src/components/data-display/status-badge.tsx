"use client";
import { cn } from "@/lib/utils";
import type { MachineStatus } from "@/types";

interface StatusBadgeProps {
  status: MachineStatus;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const statusConfig: Record<MachineStatus, { label: string; color: string; bgColor: string; borderColor: string }> = {
  RUNNING: { label: "Running", color: "bg-success", bgColor: "bg-success/10", borderColor: "border-success/20" },
  IDLE: { label: "Idle", color: "bg-text-tertiary", bgColor: "bg-bg-400", borderColor: "border-border" },
  WARNING: { label: "Warning", color: "bg-warning", bgColor: "bg-warning/10", borderColor: "border-warning/20" },
  CRITICAL: { label: "Critical", color: "bg-danger", bgColor: "bg-danger/10", borderColor: "border-danger/20" },
  FAULT: { label: "Fault", color: "bg-danger", bgColor: "bg-danger/10", borderColor: "border-danger/20" },
  OFFLINE: { label: "Offline", color: "bg-text-muted", bgColor: "bg-bg-400", borderColor: "border-border" },
  MAINTENANCE: { label: "Maintenance", color: "bg-info", bgColor: "bg-info/10", borderColor: "border-info/20" },
};

export function StatusBadge({ status, showLabel = true, size = "md", className }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.OFFLINE;
  const isLive = status === "RUNNING" || status === "WARNING" || status === "CRITICAL";

  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 rounded-full border font-medium",
      config.bgColor, config.borderColor,
      size === "sm" && "px-2 py-0.5 text-[10px]",
      size === "md" && "px-2.5 py-0.5 text-[11px]",
      size === "lg" && "px-3 py-1 text-xs",
      className,
    )}>
      <span className="relative flex h-2 w-2 shrink-0">
        {isLive && (
          <span className={cn("absolute inline-flex h-full w-full rounded-full opacity-75 pulse-live", config.color)} />
        )}
        <span className={cn("relative inline-flex rounded-full h-2 w-2", config.color)} />
      </span>
      {showLabel && <span>{config.label}</span>}
    </span>
  );
}
