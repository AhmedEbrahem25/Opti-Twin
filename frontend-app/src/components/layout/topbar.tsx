"use client";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Search, Bell, Wifi, WifiOff, Brain, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTelemetryStore } from "@/store/telemetry-store";
import { Badge } from "@/components/ui/badge";

const routeNames: Record<string, string> = {
  "/workspace": "Workspace",
  "/ai-control": "AI Control Center",
  "/analytics": "Analytics & Reports",
  "/search": "Search Console",
  "/alerts": "Alerts & Incidents",
  "/settings": "Settings",
  "/onboarding": "Machine Onboarding",
};

function getBreadcrumbs(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];

  if (parts[0] === "factory") {
    crumbs.push({ label: "Factories", href: "/workspace" });
    crumbs.push({ label: parts[1]?.replace("factory-", "Factory ") || "Factory", href: pathname });
  } else if (parts[0] === "machine") {
    crumbs.push({ label: "Machines", href: "/workspace" });
    crumbs.push({ label: parts[1]?.replace(/-/g, " ") || "Machine", href: pathname });
  } else if (parts[0] === "digital-twin") {
    crumbs.push({ label: "Digital Twin", href: pathname });
  } else {
    const name = routeNames[`/${parts[0]}`] || parts[0];
    crumbs.push({ label: name, href: pathname });
  }
  return crumbs;
}

export function Topbar() {
  const pathname = usePathname();
  const { isConnected, aiEnabled, kpis } = useTelemetryStore();
  const breadcrumbs = getBreadcrumbs(pathname);

  return (
    <header className="h-14 border-b border-border bg-bg-100/80 backdrop-blur-xl flex items-center px-5 gap-4 shrink-0 sticky top-0 z-30">
      {/* ─── Breadcrumbs ─────────────────────────── */}
      <nav className="flex items-center gap-1.5 text-sm min-w-0">
        {breadcrumbs.map((crumb, i) => (
          <div key={crumb.href} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight size={12} className="text-text-muted" />}
            <span className={cn(
              i === breadcrumbs.length - 1 ? "text-text-primary font-medium" : "text-text-tertiary"
            )}>
              {crumb.label}
            </span>
          </div>
        ))}
      </nav>

      <div className="flex-1" />

      {/* ─── Status Indicators ───────────────────── */}
      <div className="flex items-center gap-3">
        {/* Connection Status */}
        <div className={cn(
          "flex items-center gap-1.5 text-[11px] font-mono",
          isConnected ? "text-success" : "text-text-muted"
        )}>
          {isConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
          <span className="hidden sm:inline">{isConnected ? "Live" : "Offline"}</span>
        </div>

        {/* AI Status */}
        <div className={cn(
          "flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-mono border",
          aiEnabled
            ? "text-accent bg-accent/8 border-accent/20"
            : "text-text-tertiary bg-bg-300 border-border"
        )}>
          <Brain size={13} />
          <span className="hidden sm:inline">{aiEnabled ? "AI Active" : "AI Off"}</span>
        </div>

        {/* Search */}
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-300 border border-border text-text-tertiary text-xs hover:border-border-hover hover:text-text-secondary transition-colors cursor-pointer">
          <Search size={13} />
          <span className="hidden md:inline">Search</span>
          <kbd className="hidden md:inline text-[10px] bg-bg-400 px-1.5 py-0.5 rounded border border-border ml-2 font-mono">⌘K</kbd>
        </button>

        {/* Alerts */}
        <button className="relative p-2 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-bg-300 transition-colors cursor-pointer">
          <Bell size={16} />
          {kpis.activeAlerts > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-danger text-[9px] font-bold text-white flex items-center justify-center"
            >
              {kpis.activeAlerts}
            </motion.span>
          )}
        </button>
      </div>
    </header>
  );
}
