'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Lock, Plus, Trash2, Cpu, Loader2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface FirewallRule {
  id: string;
  rule_type: string;
  target: string;
  direction: string;
  action: string;
  auto_block: boolean;
  enabled: boolean;
}

export default function FirewallPage() {
  const queryClient = useQueryClient();

  const { data: rules = [], isLoading, error } = useQuery<FirewallRule[]>({
    queryKey: ['firewall_rules'],
    queryFn: async () => {
      const response = await api.get('/firewall/rules');
      return response.data;
    },
    refetchInterval: 15000
  });

  const deleteRule = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/firewall/rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firewall_rules'] });
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Packet Firewall (nftables)</h2>
        <button className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-md font-medium transition-colors">
          <Plus className="w-4 h-4" /> Add Rule
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Rules</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-accent" />
            </div>
          ) : error ? (
            <div className="p-4 bg-danger/20 text-danger border border-danger/50 rounded-md">
              Failed to load firewall rules. Please try again.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                  <tr>
                    <th className="px-4 py-3 rounded-tl-lg">Target</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Direction</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Source</th>
                    <th className="px-4 py-3 rounded-tr-lg text-right">Manage</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-slate-400 border-b border-slate-800">
                        No firewall rules found.
                      </td>
                    </tr>
                  ) : rules.map((rule) => (
                    <tr key={rule.id} className={`border-b border-slate-800 hover:bg-slate-800/30 ${!rule.enabled ? 'opacity-50' : ''}`}>
                      <td className="px-4 py-3 font-mono font-medium">{rule.target}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs">
                          {rule.rule_type.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 capitalize">{rule.direction}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs ${rule.action === 'drop' ? 'bg-danger/20 text-danger' : 'bg-safe/20 text-safe'}`}>
                          {rule.action.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {rule.auto_block ? (
                          <span className="flex items-center gap-1 text-xs text-accent">
                            <Cpu className="w-3 h-3" /> Auto (ML)
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">Manual</span>
                        )}
                      </td>
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
    </div>
  );
}
