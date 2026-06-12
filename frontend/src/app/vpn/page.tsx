'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Network, Plus, QrCode, Download, Trash2, Loader2, Server } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '@/lib/api';

interface VpnPeer {
  id: string;
  peer_name: string;
  public_key: string;
  assigned_ip: string;
  last_handshake: number | null;
  enabled: boolean;
}

export default function VPNPage() {
  const queryClient = useQueryClient();
  const [showQR, setShowQR] = useState<{ id: string, code: string } | null>(null);

  const { data: peers = [], isLoading, error } = useQuery<VpnPeer[]>({
    queryKey: ['vpn_peers'],
    queryFn: async () => {
      const response = await api.get('/vpn/peers');
      return response.data;
    },
    refetchInterval: 10000
  });

  const revokePeer = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/vpn/peers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vpn_peers'] });
    }
  });

  const downloadConfig = async (id: string, name: string) => {
    try {
      const response = await api.get(`/vpn/peers/${id}/config`);
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name.replace(/\s+/g, '_')}.conf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to download config.');
    }
  };

  const displayQR = async (id: string) => {
    try {
      const response = await api.get(`/vpn/peers/${id}/qrcode`);
      setShowQR({ id, code: response.data.qrcode });
    } catch (e) {
      alert('Failed to fetch QR code.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">WireGuard VPN</h2>
        <button className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-md font-medium transition-colors">
          <Plus className="w-4 h-4" /> Add Peer
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="col-span-1 md:col-span-2">
          <CardHeader>
            <CardTitle>VPN Peers</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
              </div>
            ) : error ? (
              <div className="p-4 bg-danger/20 text-danger border border-danger/50 rounded-md">
                Failed to load VPN peers. Please try again.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg">Peer Name</th>
                      <th className="px-4 py-3">IP Address</th>
                      <th className="px-4 py-3">Last Handshake</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 rounded-tr-lg text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {peers.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-slate-400 border-b border-slate-800">
                          No VPN peers found.
                        </td>
                      </tr>
                    ) : peers.map((peer) => (
                      <tr key={peer.id} className="border-b border-slate-800 hover:bg-slate-800/30">
                        <td className="px-4 py-3 font-medium">{peer.peer_name}</td>
                        <td className="px-4 py-3 font-mono text-cyan">{peer.assigned_ip}</td>
                        <td className="px-4 py-3 text-slate-400">
                          {peer.last_handshake ? new Date(peer.last_handshake * 1000).toLocaleString() : 'Never'}
                        </td>
                        <td className="px-4 py-3">
                          <div className={`w-3 h-3 rounded-full ${peer.last_handshake ? 'bg-safe' : 'bg-slate-600'}`} />
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button onClick={() => displayQR(peer.id)} className="text-slate-400 hover:text-white p-1" title="Show QR">
                              <QrCode className="w-4 h-4" />
                            </button>
                            <button onClick={() => downloadConfig(peer.id, peer.peer_name)} className="text-slate-400 hover:text-white p-1" title="Download .conf">
                              <Download className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => {
                                if (window.confirm('Revoke this peer?')) revokePeer.mutate(peer.id);
                              }}
                              disabled={revokePeer.isPending}
                              className="text-slate-400 hover:text-danger p-1 disabled:opacity-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6 col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Server Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Interface</span>
                <span className="font-mono text-white">wg0</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Listen Port</span>
                <span className="font-mono text-white">51820</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Status</span>
                <span className="px-2 py-1 bg-safe/20 text-safe rounded text-xs font-medium">Running</span>
              </div>
            </CardContent>
          </Card>

          {showQR && (
            <Card>
              <CardHeader className="flex flex-row justify-between items-center">
                <CardTitle>Peer QR Code</CardTitle>
                <button onClick={() => setShowQR(null)} className="text-slate-400 hover:text-white text-sm">Close</button>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center p-6 bg-white rounded-b-xl">
                <img src={`data:image/png;base64,${showQR.code}`} alt="WireGuard QR" className="max-w-[200px]" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
