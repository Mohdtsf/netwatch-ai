'use client';

import { Menu, Bell, User, LogOut } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function Header() {
  const { toggleSidebar, activeAlertsCount, user, setUser } = useAppStore();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      console.error("Logout failed", e);
    } finally {
      localStorage.removeItem('access_token');
      setUser(null);
      router.push('/login');
    }
  };

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
        
        <div className="flex items-center gap-4 pl-4 border-l border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
              <User className="w-4 h-4" />
            </div>
            <span className="text-sm font-medium text-slate-300">
              {user ? user.username : 'Admin'}
            </span>
          </div>
          <button 
            onClick={handleLogout}
            className="p-2 text-slate-400 hover:text-danger rounded-md hover:bg-slate-800 transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
