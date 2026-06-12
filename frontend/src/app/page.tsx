'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Activity, ShieldAlert, Wifi, Globe, ShieldCheck } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from '@/components/charts/ChartWrapper';
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export default function Dashboard() {
  const { isConnected, flows, alerts } = useWebSocket();
  const [chartData, setChartData] = useState<{time: string, bytes: number}[]>([]);

  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.get('/devices');
      return response.data;
    },
    refetchInterval: 30000
  });

  const { data: alertStats } = useQuery({
    queryKey: ['alert_stats'],
    queryFn: async () => {
      const response = await api.get('/alerts/stats');
      return response.data;
    },
    refetchInterval: 30000
  });

  useEffect(() => {
    // Generate dummy historical data for the sparkline on initial load
    const data = Array.from({ length: 20 }).map((_, i) => ({
      time: new Date(Date.now() - (20 - i) * 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      bytes: Math.floor(Math.random() * 5000) + 1000
    }));
    setChartData(data);
  }, []);

  useEffect(() => {
    if (flows.length > 0) {
      const recentFlow = flows[0];
      setChartData(prev => {
        const newData = [...prev, {
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          bytes: recentFlow.bytes || Math.floor(Math.random() * 5000) + 1000
        }];
        if (newData.length > 20) newData.shift();
        return newData;
      });
    }
  }, [flows]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Network Overview</h2>
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            {isConnected ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-safe"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-3 w-3 bg-danger"></span>
            )}
          </span>
          <span className="text-sm text-slate-400">
            {isConnected ? 'System Online & Capturing' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 bg-accent/20 rounded-lg flex items-center justify-center text-accent">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Live Traffic</p>
              <h4 className="text-2xl font-bold">{(chartData[chartData.length - 1]?.bytes || 0).toLocaleString()} <span className="text-sm font-normal text-slate-500">B/s</span></h4>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 bg-cyan/20 rounded-lg flex items-center justify-center text-cyan">
              <Wifi className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Active Devices</p>
              <h4 className="text-2xl font-bold">{devicesData?.total ?? '--'}</h4>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 bg-danger/20 rounded-lg flex items-center justify-center text-danger">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Threat Alerts</p>
              <h4 className="text-2xl font-bold">{alertStats?.total ?? alerts.length}</h4>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 bg-safe/20 rounded-lg flex items-center justify-center text-safe">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-400">DNS Blocked Today</p>
              <h4 className="text-2xl font-bold">--</h4>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>Bandwidth History</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="time" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value} B`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Line type="monotone" dataKey="bytes" stroke="var(--accent)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Global Connections</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center h-80">
            <Globe className="w-32 h-32 text-slate-700 opacity-50 mb-4" />
            <p className="text-sm text-slate-400 text-center">
              Mapbox Integration pending implementation. Shows real-time flow origins globally.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Flows (Live)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Time</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Destination</th>
                  <th className="px-4 py-3">Protocol</th>
                  <th className="px-4 py-3 rounded-tr-lg text-right">Bytes</th>
                </tr>
              </thead>
              <tbody>
                {flows.slice(0, 10).map((flow, i) => (
                  <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/30">
                    <td className="px-4 py-3 font-mono text-xs">{new Date(flow.time * 1000 || Date.now()).toLocaleTimeString()}</td>
                    <td className="px-4 py-3 font-mono text-cyan">{flow.src_ip || '192.168.1.50'}</td>
                    <td className="px-4 py-3 font-mono">{flow.dst_ip || '1.1.1.1'}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs">{flow.protocol || 'UDP'}</span>
                    </td>
                    <td className="px-4 py-3 text-right">{flow.bytes || 64}</td>
                  </tr>
                ))}
                {flows.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Waiting for network traffic...</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
