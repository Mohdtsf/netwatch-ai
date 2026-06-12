'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ShieldAlert, CheckCircle, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

type Alert = {
  id: string;
  time: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  message: string;
  source_ip: string;
  auto_blocked: boolean;
  acknowledged: boolean;
};

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const { alerts: liveAlerts } = useWebSocket();
  const [displayAlerts, setDisplayAlerts] = useState<Alert[]>([]);

  const { data: historicalAlertsData, isLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const response = await api.get('/alerts?page=1&page_size=50');
      return response.data;
    },
    refetchInterval: 30000
  });

  useEffect(() => {
    // Merge historical alerts with live alerts
    const historical = historicalAlertsData?.alerts || [];
    
    // Simple dedup by ID
    const merged = [...liveAlerts, ...historical];
    const uniqueAlerts = Array.from(new Map(merged.map(item => [item.id, item])).values());
    
    // Sort by time descending
    uniqueAlerts.sort((a, b) => b.time - a.time);
    
    setDisplayAlerts(uniqueAlerts);
  }, [liveAlerts, historicalAlertsData]);

  const acknowledgeAlert = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/alerts/${id}/acknowledge`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    }
  });

  const severityColor = {
    low: 'text-cyan bg-cyan/10',
    medium: 'text-yellow-500 bg-yellow-500/10',
    high: 'text-orange-500 bg-orange-500/10',
    critical: 'text-danger bg-danger/10',
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Threat Alerts</h2>
        <div className="text-sm text-slate-400">Real-time threat detection</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-accent" />
            </div>
          ) : (
            <div className="space-y-4">
              {displayAlerts.length === 0 ? (
                <div className="text-center py-12 text-slate-500 flex flex-col items-center">
                  <ShieldAlert className="w-12 h-12 mb-4 opacity-20" />
                  No active threats detected.
                </div>
              ) : (
                displayAlerts.map((alert, i) => (
                  <div key={alert.id || i} className={`flex items-start gap-4 p-4 rounded-lg border border-slate-800 ${alert.acknowledged ? 'bg-slate-900/30 opacity-70' : 'bg-slate-900/50'}`}>
                    <div className={`p-2 rounded-full ${severityColor[alert.severity] || severityColor.low}`}>
                      <ShieldAlert className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <h4 className="font-semibold">{alert.type}</h4>
                        <span className="text-xs text-slate-500">
                          {new Date(alert.time * 1000).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-1">{alert.message}</p>
                      <div className="mt-3 flex items-center gap-4 text-xs">
                        {alert.source_ip && <span className="font-mono text-cyan">Source: {alert.source_ip}</span>}
                        {alert.auto_blocked && (
                          <span className="flex items-center gap-1 text-safe font-medium">
                            <CheckCircle className="w-3 h-3" /> Auto-blocked via Firewall
                          </span>
                        )}
                        {alert.acknowledged && (
                          <span className="flex items-center gap-1 text-slate-500 font-medium">
                            <CheckCircle className="w-3 h-3" /> Acknowledged
                          </span>
                        )}
                      </div>
                    </div>
                    {!alert.acknowledged && (
                      <button 
                        onClick={() => acknowledgeAlert.mutate(alert.id)}
                        disabled={acknowledgeAlert.isPending}
                        className="px-3 py-1.5 text-xs font-medium border border-slate-700 rounded hover:bg-slate-800 transition-colors disabled:opacity-50"
                      >
                        Acknowledge
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
