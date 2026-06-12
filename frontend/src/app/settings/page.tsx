'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Settings, Save, User, Database, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Settings</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5 text-accent" /> System Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border border-slate-700 rounded-lg bg-slate-800/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h4 className="font-medium text-lg text-white">Resource Profile</h4>
                  <p className="text-sm text-slate-400">Controls the level of ML features to fit available RAM.</p>
                </div>
                <select defaultValue="standard" className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent min-w-32">
                  <option value="minimal">Minimal (512MB)</option>
                  <option value="standard">Standard (600MB)</option>
                  <option value="full">Full (1.2GB+)</option>
                </select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-accent" /> Notifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 border-b border-slate-800">
                <div>
                  <h4 className="font-medium">Critical Threat Alerts</h4>
                  <p className="text-xs text-slate-400">Push notifications for critical anomalies</p>
                </div>
                <div className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border-b border-slate-800">
                <div>
                  <h4 className="font-medium">New Device Discovered</h4>
                  <p className="text-xs text-slate-400">Notify when a new MAC address joins the network</p>
                </div>
                <div className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5 text-accent" /> Account
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Username</label>
                <input type="text" value="admin" disabled className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-400 cursor-not-allowed" />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Email</label>
                <input type="email" defaultValue="admin@netwatch.local" className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm focus:outline-none focus:border-accent" />
              </div>

              <button className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-md font-medium transition-colors mt-4 border border-slate-700">
                <Save className="w-4 h-4" /> Save Changes
              </button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Version</span>
                <span>2.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Database Size</span>
                <span>42.5 MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Uptime</span>
                <span>4d 12h 30m</span>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800 flex justify-center">
                <button className="text-danger hover:underline text-sm">
                  Restart Services
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
