'use client';

import { Card, CardContent } from '@/components/ui/Card';
import { MonitorSmartphone, Laptop, Tv, Search, Server, Smartphone, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface Device {
  id: string;
  mac_address: string;
  ip_address: string;
  hostname: string;
  custom_name: string;
  device_type: string;
  vendor: string;
  os_type: string;
  first_seen: number;
  last_seen: number;
  is_online: boolean;
  is_blocked: boolean;
}

export default function DevicesPage() {
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.get('/devices');
      return response.data;
    },
    refetchInterval: 10000 // Refetch every 10 seconds
  });

  const devices: Device[] = data?.devices || [];

  const getIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'laptop': return <Laptop className="w-6 h-6" />;
      case 'desktop': return <Server className="w-6 h-6" />;
      case 'tv': return <Tv className="w-6 h-6" />;
      case 'phone': return <Smartphone className="w-6 h-6" />;
      default: return <MonitorSmartphone className="w-6 h-6" />;
    }
  };

  const filteredDevices = devices.filter(d => 
    (d.custom_name || d.hostname || d.mac_address).toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Network Devices</h2>
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search devices..." 
            className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm focus:outline-none focus:border-accent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-accent" />
        </div>
      ) : error ? (
        <div className="p-4 bg-danger/20 text-danger border border-danger/50 rounded-md">
          Failed to load devices. Please try again.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDevices.map(device => (
            <Card key={device.id} className="hover:border-accent transition-colors cursor-pointer">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-800 rounded-lg text-slate-300">
                      {getIcon(device.device_type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg line-clamp-1">{device.custom_name || device.hostname || 'Unknown Device'}</h3>
                      <p className="text-sm text-slate-400 line-clamp-1">{device.vendor || 'Unknown Vendor'}</p>
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full shrink-0 ${device.is_online ? 'bg-safe' : 'bg-slate-600'}`} />
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">IP Address</span>
                    <span className="font-mono text-cyan">{device.ip_address || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">MAC Address</span>
                    <span className="font-mono">{device.mac_address}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Last Seen</span>
                    <span>{device.last_seen ? new Date(device.last_seen * 1000).toLocaleString() : 'Never'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {filteredDevices.length === 0 && (
            <div className="col-span-full p-8 text-center text-slate-400 border border-dashed border-slate-700 rounded-lg">
              No devices found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
