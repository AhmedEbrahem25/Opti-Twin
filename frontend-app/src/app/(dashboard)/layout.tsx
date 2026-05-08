"use client";
import { useWorkspaceStore } from "@/store/workspace-store";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { RealtimeProvider } from "@/components/realtime-provider";
import { motion } from "framer-motion";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed } = useWorkspaceStore();

  return (
    <RealtimeProvider>
      <div className="flex h-screen overflow-hidden bg-bg">
        <Sidebar />
        <motion.main
          className="flex-1 flex flex-col min-h-0 overflow-hidden"
          animate={{ marginLeft: sidebarCollapsed ? 64 : 260 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        >
          <Topbar />
          <div className="flex-1 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="p-6"
            >
              {children}
            </motion.div>
          </div>
        </motion.main>
      </div>
    </RealtimeProvider>
  );
}
