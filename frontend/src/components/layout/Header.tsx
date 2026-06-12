'use client';

import { Menu, Bell, User } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';

export default function Header() {
  const { toggleSidebar, activeAlertsCount } = useAppStore();

  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-4 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <button 
          onClick={toggleSidebar}
          className="p-2 text-slate-400 hover:text-white rounded-md hover:bg-slate-800"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-400 hover:text-white rounded-md hover:bg-slate-800">
          <Bell className="w-5 h-5" />
          {activeAlertsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full animate-pulse" />
          )}
        </button>
        
        <div className="flex items-center gap-2 pl-4 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
            <User className="w-4 h-4" />
          </div>
          <span className="text-sm font-medium text-slate-300">Admin</span>
        </div>
      </div>
    </header>
  );
}
