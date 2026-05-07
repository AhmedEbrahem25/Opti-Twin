import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number, decimals = 1): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(decimals)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(decimals)}K`;
  return value.toFixed(decimals);
}

export function formatCurrency(value: number, currency = "EGP"): string {
  return `${value.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ${currency}`;
}

export function formatPercentage(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function formatTemperature(value: number): string {
  return `${value.toFixed(1)}°C`;
}

export function formatEnergy(value: number): string {
  return `${value.toFixed(1)} kWh`;
}

export function formatTimestamp(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function getRelativeTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const diff = Date.now() - d.getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    RUNNING: "text-success",
    ONLINE: "text-success",
    SAFE: "text-success",
    ON_TRACK: "text-success",
    WARNING: "text-warning",
    ELEVATED: "text-warning",
    CRITICAL: "text-danger",
    FAULT: "text-danger",
    OFFLINE: "text-text-muted",
    IDLE: "text-text-tertiary",
    MAINTENANCE: "text-info",
  };
  return map[status] || "text-text-secondary";
}

export function getStatusBgColor(status: string): string {
  const map: Record<string, string> = {
    RUNNING: "bg-success-muted",
    ONLINE: "bg-success-muted",
    SAFE: "bg-success-muted",
    ON_TRACK: "bg-success-muted",
    WARNING: "bg-warning-muted",
    ELEVATED: "bg-warning-muted",
    CRITICAL: "bg-danger-muted",
    FAULT: "bg-danger-muted",
    OFFLINE: "bg-bg-400",
    IDLE: "bg-bg-400",
    MAINTENANCE: "bg-info-muted",
  };
  return map[status] || "bg-bg-400";
}

export function randomInRange(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}
