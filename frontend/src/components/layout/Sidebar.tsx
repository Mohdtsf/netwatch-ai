'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  MonitorSmartphone, 
  Activity, 
  ShieldAlert, 
  ShieldBan, 
  Lock, 
  Network, 
  FileText, 
  Settings 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';

const navItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Devices', href: '/devices', icon: MonitorSmartphone },
  { name: 'Flows', href: '/flows', icon: Activity },
  { name: 'Alerts', href: '/alerts', icon: ShieldAlert },
  { name: 'DNS Firewall', href: '/dns', icon: ShieldBan },
  { name: 'Packet Firewall', href: '/firewall', icon: Lock },
  { name: 'VPN', href: '/vpn', icon: Network },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isSidebarOpen } = useAppStore();

  if (!isSidebarOpen) return null;

  return (
    <aside className="w-64 bg-card border-r border-border h-full flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <h1 className="text-xl font-bold text-accent flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-cyan" />
          NetWatch AI
        </h1>
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                isActive 
                  ? "bg-accent/20 text-accent" 
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
              )}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="text-xs text-slate-500">v2.0.0 • Connected</div>
      </div>
    </aside>
  );
}
