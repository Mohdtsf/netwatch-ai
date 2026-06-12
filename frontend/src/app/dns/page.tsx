'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ShieldBan, Plus, Trash2, Loader2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface DnsRule {
  id: string;
  domain_pattern: string;
  action: string;
  category: string;
  device_id: string;
}

export default function DNSFirewallPage() {
  const queryClient = useQueryClient();

  const { data: rules = [], isLoading: loadingRules } = useQuery<DnsRule[]>({
    queryKey: ['dns_rules'],
    queryFn: async () => {
      const response = await api.get('/dns/rules');
      return response.data;
    },
    refetchInterval: 15000
  });

  const { data: blocklistConfig, isLoading: loadingConfig } = useQuery({
    queryKey: ['dns_blocklist_config'],
    queryFn: async () => {
      const response = await api.get('/dns/blocklist/config');
      return response.data;
    },
  });

  const deleteRule = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/dns/rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dns_rules'] });
    }
  });

  const toggleBlocklist = useMutation({
    mutationFn: async (listId: string) => {
      if (!blocklistConfig?.config) return;
      const currentEnabled = blocklistConfig.config.enabled_lists || [];
      const isEnabled = currentEnabled.includes(listId);
      const newEnabled = isEnabled 
        ? currentEnabled.filter((id: string) => id !== listId)
        : [...currentEnabled, listId];
        
      const newConfig = { ...blocklistConfig.config, enabled_lists: newEnabled };
      await api.post('/dns/blocklist/config', newConfig);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dns_blocklist_config'] });
    }
  });

  const enabledLists = blocklistConfig?.config?.enabled_lists || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">DNS Firewall</h2>
        <button className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-md font-medium transition-colors">
          <Plus className="w-4 h-4" /> Add Rule
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="col-span-1 md:col-span-2">
          <CardHeader>
            <CardTitle>Custom Rules</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingRules ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg">Domain</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Device</th>
                      <th className="px-4 py-3 rounded-tr-lg text-right">Manage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rules.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-slate-400 border-b border-slate-800">
                          No DNS rules found.
                        </td>
                      </tr>
                    ) : rules.map((rule) => (
                      <tr key={rule.id} className="border-b border-slate-800 hover:bg-slate-800/30">
                        <td className="px-4 py-3 font-mono">{rule.domain_pattern}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs ${rule.action === 'block' ? 'bg-danger/20 text-danger' : 'bg-safe/20 text-safe'}`}>
                            {rule.action.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3">{rule.device_id || 'Global'}</td>
                        <td className="px-4 py-3 text-right">
                          <button 
                            onClick={() => {
                              if (window.confirm('Delete this rule?')) {
                                deleteRule.mutate(rule.id);
                              }
                            }}
                            disabled={deleteRule.isPending}
                            className="text-slate-400 hover:text-danger p-1 disabled:opacity-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Blocklists</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loadingConfig ? (
              <div className="flex items-center justify-center p-6">
                <Loader2 className="w-6 h-6 animate-spin text-accent" />
              </div>
            ) : blocklistConfig?.available_lists ? (
              <>
                {Object.entries(blocklistConfig.available_lists).map(([id, info]: [string, any]) => (
                  <div key={id} className="flex items-center justify-between p-3 border border-slate-800 rounded-lg bg-slate-800/20">
                    <div>
                      <h4 className="font-medium">{info.name || id}</h4>
                      <p className="text-xs text-slate-400">{info.description || 'Blocklist'}</p>
                    </div>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={enabledLists.includes(id)}
                        onChange={() => toggleBlocklist.mutate(id)}
                        disabled={toggleBlocklist.isPending}
                      />
                      <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent peer-disabled:opacity-50"></div>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <p className="text-sm text-slate-400">Failed to load blocklists.</p>
            )}
            
            <div className="pt-4 border-t border-slate-800 flex items-center justify-center gap-2 text-sm text-slate-400">
              <ShieldBan className="w-4 h-4 text-safe" />
              DNS filtering active
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
