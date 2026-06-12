import { create } from 'zustand';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'analyst' | 'viewer';
}

interface AppState {
  user: User | null;
  setUser: (user: User | null) => void;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  activeAlertsCount: number;
  setActiveAlertsCount: (count: number) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  isSidebarOpen: true,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  activeAlertsCount: 0,
  setActiveAlertsCount: (count) => set({ activeAlertsCount: count }),
}));
