import { create } from "zustand";
import type { Organization, Factory, Machine } from "@/types";

interface WorkspaceState {
  currentOrg: Organization | null;
  factories: Factory[];
  selectedFactory: Factory | null;
  selectedMachine: Machine | null;
  sidebarCollapsed: boolean;
  sidebarMobileOpen: boolean;
  setCurrentOrg: (org: Organization) => void;
  setFactories: (factories: Factory[]) => void;
  selectFactory: (factory: Factory | null) => void;
  selectMachine: (machine: Machine | null) => void;
  toggleSidebar: () => void;
  setSidebarMobileOpen: (open: boolean) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  currentOrg: {
    id: "org-1",
    name: "Alamein Manufacturing",
    slug: "alamein-mfg",
    plan: "enterprise",
    factoryCount: 3,
    machineCount: 12,
  },
  factories: [],
  selectedFactory: null,
  selectedMachine: null,
  sidebarCollapsed: false,
  sidebarMobileOpen: false,
  setCurrentOrg: (org) => set({ currentOrg: org }),
  setFactories: (factories) => set({ factories }),
  selectFactory: (factory) => set({ selectedFactory: factory }),
  selectMachine: (machine) => set({ selectedMachine: machine }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarMobileOpen: (open) => set({ sidebarMobileOpen: open }),
}));
