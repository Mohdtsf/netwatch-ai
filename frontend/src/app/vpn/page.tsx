'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Network, Plus, QrCode, Download, Trash2, Loader2, Server, X, Shield, ArrowUpDown, Wifi, WifiOff } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '@/lib/api';

interface VpnPeer {
  id: string;
  peer_name: string;
  device_id: string | null;
  public_key: string;
  assigned_ip: string;
  tunnel_mode: string;
  enabled: boolean;
  last_handshake: number | null;
  rx_bytes: number;
  tx_bytes: number;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function timeAgo(timestamp: number | null): string {
  if (!timestamp || timestamp === 0) return 'Never';
  const seconds = Math.floor(Date.now() / 1000) - timestamp;
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export default function VPNPage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showQR, setShowQR] = useState<{ id: string; code: string; name: string } | null>(null);
  const [peerName, setPeerName] = useState('');
  const [tunnelMode, setTunnelMode] = useState<'full' | 'split'>('full');
  const [addError, setAddError] = useState('');

  const { data: peers = [], isLoading, error } = useQuery<VpnPeer[]>({
    queryKey: ['vpn_peers'],
    queryFn: async () => {
      const response = await api.get('/vpn/peers');
      return response.data;
    },
    refetchInterval: 10000,
  });

  const addPeer = useMutation({
    mutationFn: async (data: { peer_name: string; tunnel_mode: string }) => {
      const response = await api.post('/vpn/peers', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vpn_peers'] });
      setShowAddModal(false);
      setPeerName('');
      setTunnelMode('full');
      setAddError('');
    },
    onError: (err: any) => {
      setAddError(err.response?.data?.detail || 'Failed to add peer.');
    },
  });

  const revokePeer = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/vpn/peers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vpn_peers'] });
    },
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
    } catch {
      alert('Failed to download config.');
    }
  };

  const displayQR = async (id: string, name: string) => {
    try {
      const response = await api.get(`/vpn/peers/${id}/qrcode`);
      const code = response.data.qrcode || response.data;
      setShowQR({ id, code, name });
    } catch {
      alert('Failed to fetch QR code.');
    }
  };

  const handleAddPeer = (e: React.FormEvent) => {
    e.preventDefault();
    if (!peerName.trim()) {
      setAddError('Peer name is required.');
      return;
    }
    setAddError('');
    addPeer.mutate({ peer_name: peerName.trim(), tunnel_mode: tunnelMode });
  };

  const isConnected = (peer: VpnPeer) => {
    if (!peer.last_handshake || peer.last_handshake === 0) return false;
    const secondsAgo = Math.floor(Date.now() / 1000) - peer.last_handshake;
    return secondsAgo < 180; // Connected if handshake within 3 minutes
  };

  const connectedCount = peers.filter(isConnected).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6 text-accent" />
            WireGuard VPN
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Manage VPN peers and secure remote access
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-md font-medium transition-all duration-200 hover:shadow-lg hover:shadow-accent/20"
        >
          <Plus className="w-4 h-4" /> Add Peer
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-accent/10 rounded-lg">
              <Network className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-2xl font-bold">{peers.length}</p>
              <p className="text-xs text-slate-400">Total Peers</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-safe/10 rounded-lg">
              <Wifi className="w-5 h-5 text-safe" />
            </div>
            <div>
              <p className="text-2xl font-bold">{connectedCount}</p>
              <p className="text-xs text-slate-400">Connected</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-cyan/10 rounded-lg">
              <ArrowUpDown className="w-5 h-5 text-cyan" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {formatBytes(peers.reduce((sum, p) => sum + p.rx_bytes + p.tx_bytes, 0))}
              </p>
              <p className="text-xs text-slate-400">Total Transfer</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-safe/10 rounded-lg">
              <Server className="w-5 h-5 text-safe" />
            </div>
            <div>
              <p className="text-2xl font-bold text-safe">Running</p>
              <p className="text-xs text-slate-400">wg0 · :{51820}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Peers Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>VPN Peers</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
              </div>
            ) : error ? (
              <div className="m-6 p-4 bg-danger/10 text-danger border border-danger/30 rounded-md text-sm">
                Failed to load VPN peers. Please check your connection and try again.
              </div>
            ) : peers.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <div className="p-4 bg-slate-800/50 rounded-full mb-4">
                  <WifiOff className="w-8 h-8 text-slate-500" />
                </div>
                <p className="text-slate-400 mb-1">No VPN peers configured</p>
                <p className="text-xs text-slate-500 mb-4">Add a peer to get started with secure remote access</p>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="text-sm text-accent hover:text-accent/80 font-medium"
                >
                  + Add your first peer
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-800/30">
                    <tr>
                      <th className="px-5 py-3">Peer</th>
                      <th className="px-5 py-3">IP Address</th>
                      <th className="px-5 py-3">Mode</th>
                      <th className="px-5 py-3">Transfer</th>
                      <th className="px-5 py-3">Last Handshake</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {peers.map((peer) => {
                      const connected = isConnected(peer);
                      return (
                        <tr
                          key={peer.id}
                          className="border-t border-slate-800/50 hover:bg-slate-800/20 transition-colors"
                        >
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-2.5">
                              <div className={`w-2 h-2 rounded-full shrink-0 ${connected ? 'bg-safe shadow-sm shadow-safe/50' : 'bg-slate-600'}`} />
                              <span className="font-medium">{peer.peer_name}</span>
                            </div>
                          </td>
                          <td className="px-5 py-3.5 font-mono text-cyan text-xs">{peer.assigned_ip}</td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              peer.tunnel_mode === 'full'
                                ? 'bg-accent/10 text-accent'
                                : 'bg-amber-500/10 text-amber-400'
                            }`}>
                              {peer.tunnel_mode === 'full' ? 'Full Tunnel' : 'Split Tunnel'}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-xs text-slate-400">
                            <span className="text-safe">↓{formatBytes(peer.rx_bytes)}</span>
                            {' / '}
                            <span className="text-accent">↑{formatBytes(peer.tx_bytes)}</span>
                          </td>
                          <td className="px-5 py-3.5 text-slate-400 text-xs">
                            {timeAgo(peer.last_handshake)}
                          </td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              connected
                                ? 'bg-safe/10 text-safe'
                                : peer.enabled
                                  ? 'bg-slate-700/50 text-slate-400'
                                  : 'bg-danger/10 text-danger'
                            }`}>
                              {connected ? 'Connected' : peer.enabled ? 'Idle' : 'Disabled'}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => displayQR(peer.id, peer.peer_name)}
                                className="text-slate-400 hover:text-white p-1.5 rounded hover:bg-slate-800 transition-colors"
                                title="Show QR Code"
                              >
                                <QrCode className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => downloadConfig(peer.id, peer.peer_name)}
                                className="text-slate-400 hover:text-white p-1.5 rounded hover:bg-slate-800 transition-colors"
                                title="Download .conf"
                              >
                                <Download className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => {
                                  if (window.confirm(`Revoke peer "${peer.peer_name}"? This cannot be undone.`))
                                    revokePeer.mutate(peer.id);
                                }}
                                disabled={revokePeer.isPending}
                                className="text-slate-400 hover:text-danger p-1.5 rounded hover:bg-danger/10 transition-colors disabled:opacity-50"
                                title="Revoke Peer"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* Server Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-4 h-4 text-safe" />
                Server Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-slate-800/50">
                <span className="text-slate-400 text-sm">Interface</span>
                <span className="font-mono text-sm text-white bg-slate-800 px-2 py-0.5 rounded">wg0</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800/50">
                <span className="text-slate-400 text-sm">Listen Port</span>
                <span className="font-mono text-sm text-white">51820</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800/50">
                <span className="text-slate-400 text-sm">Subnet</span>
                <span className="font-mono text-sm text-cyan">10.8.0.0/24</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400 text-sm">Status</span>
                <span className="px-2.5 py-1 bg-safe/15 text-safe rounded text-xs font-semibold tracking-wide">
                  Running
                </span>
              </div>
            </CardContent>
          </Card>

          {/* QR Code Display */}
          {showQR && (
            <Card className="animate-in fade-in duration-200">
              <CardHeader className="flex flex-row justify-between items-center">
                <CardTitle className="text-sm">QR Code — {showQR.name}</CardTitle>
                <button
                  onClick={() => setShowQR(null)}
                  className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center p-6">
                <div className="bg-white p-3 rounded-xl shadow-lg">
                  <img
                    src={showQR.code.startsWith('data:') ? showQR.code : `data:image/png;base64,${showQR.code}`}
                    alt={`WireGuard QR for ${showQR.name}`}
                    className="w-48 h-48"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-3 text-center">
                  Scan with WireGuard mobile app
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Peer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => { setShowAddModal(false); setAddError(''); }}
          />
          <div className="relative bg-[#0f1729] border border-slate-700/50 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 flex justify-between items-center">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Plus className="w-5 h-5 text-accent" />
                Add VPN Peer
              </h3>
              <button
                onClick={() => { setShowAddModal(false); setAddError(''); }}
                className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddPeer} className="p-6 space-y-5">
              {addError && (
                <div className="p-3 bg-danger/10 text-danger border border-danger/30 rounded-md text-sm">
                  {addError}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Peer Name</label>
                <input
                  type="text"
                  value={peerName}
                  onChange={(e) => setPeerName(e.target.value)}
                  placeholder="e.g. My Phone, Work Laptop"
                  className="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 text-slate-200 placeholder:text-slate-600 transition-colors"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Tunnel Mode</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setTunnelMode('full')}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      tunnelMode === 'full'
                        ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                        : 'border-slate-700 bg-slate-900/50 hover:border-slate-600'
                    }`}
                  >
                    <div className="font-medium text-sm mb-0.5">Full Tunnel</div>
                    <div className="text-xs text-slate-400">Route all traffic through VPN</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTunnelMode('split')}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      tunnelMode === 'split'
                        ? 'border-amber-500 bg-amber-500/10 ring-1 ring-amber-500/30'
                        : 'border-slate-700 bg-slate-900/50 hover:border-slate-600'
                    }`}
                  >
                    <div className="font-medium text-sm mb-0.5">Split Tunnel</div>
                    <div className="text-xs text-slate-400">Only route LAN traffic</div>
                  </button>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowAddModal(false); setAddError(''); }}
                  className="flex-1 px-4 py-2.5 border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-800 font-medium transition-colors text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addPeer.isPending || !peerName.trim()}
                  className="flex-1 flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2.5 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {addPeer.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" /> Create Peer
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
