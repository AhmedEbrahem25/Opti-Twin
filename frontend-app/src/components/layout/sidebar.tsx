"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspace-store";
import {
  LayoutDashboard, Brain, BarChart3, Search, Bell, Settings,
  Factory, ChevronDown, ChevronRight, PanelLeftClose, PanelLeft,
  Zap, Box, Plus, ChevronsUpDown, LogOut, User,
} from "lucide-react";

const navSections = [
  {
    title: "Platform",
    items: [
      { label: "Workspace", href: "/workspace", icon: LayoutDashboard },
      { label: "AI Control Center", href: "/ai-control", icon: Brain },
      { label: "Analytics", href: "/analytics", icon: BarChart3 },
      { label: "Digital Twin", href: "/digital-twin/factory-1-m1", icon: Box },
    ],
  },
  {
    title: "Operations",
    items: [
      { label: "Search", href: "/search", icon: Search },
      { label: "Alerts", href: "/alerts", icon: Bell, badge: 3 },
      { label: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

const mockFactories = [
  { id: "factory-1", name: "Cairo Industrial Complex", machines: 5, status: "RUNNING" as const },
  { id: "factory-2", name: "Alexandria Port Facility", machines: 4, status: "RUNNING" as const },
  { id: "factory-3", name: "Alamein Processing Plant", machines: 3, status: "WARNING" as const },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, currentOrg } = useWorkspaceStore();
  const [factoriesOpen, setFactoriesOpen] = useState(true);
  const [orgMenuOpen, setOrgMenuOpen] = useState(false);

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <motion.aside
      className={cn(
        "fixed top-0 left-0 bottom-0 z-40 flex flex-col border-r border-border bg-bg-100",
        "transition-none" // framer motion handles width
      )}
      animate={{ width: sidebarCollapsed ? 64 : 260 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* ─── Logo + Org Switcher ─────────────────── */}
      <div className="flex items-center h-14 px-3 border-b border-border shrink-0">
        <Link href="/workspace" className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/25 flex items-center justify-center shrink-0">
            <Zap size={16} className="text-accent" />
          </div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <span className="text-sm font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight whitespace-nowrap">
                  Opti-Twin
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
        <AnimatePresence>
          {!sidebarCollapsed && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={toggleSidebar}
              className="ml-auto p-1.5 rounded-md text-text-tertiary hover:text-text-secondary hover:bg-bg-300 transition-colors cursor-pointer"
              title="Collapse sidebar"
            >
              <PanelLeftClose size={16} />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* ─── Org Switcher ─────────────────────────── */}
      {!sidebarCollapsed && (
        <div className="px-3 py-2 border-b border-border">
          <button
            onClick={() => setOrgMenuOpen(!orgMenuOpen)}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-bg-300 transition-colors text-left cursor-pointer"
          >
            <div className="w-6 h-6 rounded-md bg-bg-400 border border-border flex items-center justify-center text-[10px] font-bold text-text-secondary">
              {currentOrg?.name?.[0] || "O"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">{currentOrg?.name || "Organization"}</p>
              <p className="text-[10px] text-text-tertiary capitalize">{currentOrg?.plan || "free"} plan</p>
            </div>
            <ChevronsUpDown size={12} className="text-text-tertiary shrink-0" />
          </button>
        </div>
      )}

      {/* ─── Collapsed expand button ──────────────── */}
      {sidebarCollapsed && (
        <div className="px-3 py-2 border-b border-border">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center justify-center p-1.5 rounded-md text-text-tertiary hover:text-text-secondary hover:bg-bg-300 transition-colors cursor-pointer"
            title="Expand sidebar"
          >
            <PanelLeft size={16} />
          </button>
        </div>
      )}

      {/* ─── Navigation ──────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-4">
        {navSections.map((section) => (
          <div key={section.title}>
            {!sidebarCollapsed && (
              <p className="type-label px-2 mb-1.5">{section.title}</p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all duration-200",
                      "hover:bg-bg-300 group relative",
                      active
                        ? "bg-bg-300 text-text-primary"
                        : "text-text-secondary hover:text-text-primary",
                      sidebarCollapsed && "justify-center px-0"
                    )}
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    {active && (
                      <motion.div
                        layoutId="sidebar-active"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 rounded-full bg-accent"
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}
                    <Icon size={18} className={cn("shrink-0", active && "text-accent")} />
                    <AnimatePresence>
                      {!sidebarCollapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: "auto" }}
                          exit={{ opacity: 0, width: 0 }}
                          className="whitespace-nowrap overflow-hidden"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {!sidebarCollapsed && item.badge && (
                      <span className="ml-auto text-[10px] font-medium bg-danger/15 text-danger border border-danger/20 rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}

        {/* ─── Factories Tree ────────────────────── */}
        {!sidebarCollapsed && (
          <div>
            <button
              onClick={() => setFactoriesOpen(!factoriesOpen)}
              className="flex items-center gap-2 px-2 mb-1.5 w-full cursor-pointer group"
            >
              <span className="type-label flex-1 text-left">Factories</span>
              {factoriesOpen ? (
                <ChevronDown size={12} className="text-text-tertiary" />
              ) : (
                <ChevronRight size={12} className="text-text-tertiary" />
              )}
            </button>
            <AnimatePresence>
              {factoriesOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden space-y-0.5"
                >
                  {mockFactories.map((f) => (
                    <Link
                      key={f.id}
                      href={`/factory/${f.id}`}
                      className={cn(
                        "flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors",
                        "hover:bg-bg-300 text-text-secondary hover:text-text-primary",
                        isActive(`/factory/${f.id}`) && "bg-bg-300 text-text-primary"
                      )}
                    >
                      <Factory size={14} className="shrink-0 text-text-tertiary" />
                      <span className="truncate">{f.name}</span>
                      <span className={cn(
                        "ml-auto w-1.5 h-1.5 rounded-full shrink-0",
                        f.status === "RUNNING" && "bg-success",
                        f.status === "WARNING" && "bg-warning",
                      )} />
                    </Link>
                  ))}
                  <button className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-text-tertiary hover:text-accent hover:bg-bg-300 transition-colors w-full cursor-pointer">
                    <Plus size={14} />
                    <span>Add Factory</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </nav>

      {/* ─── Bottom: User ────────────────────────── */}
      <div className="border-t border-border px-3 py-2 shrink-0">
        <div className={cn(
          "flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-bg-300 transition-colors cursor-pointer",
          sidebarCollapsed && "justify-center px-0"
        )}>
          <div className="w-7 h-7 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center shrink-0">
            <User size={14} className="text-accent" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">Ahmed Ibrahim</p>
              <p className="text-[10px] text-text-tertiary">Admin</p>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
