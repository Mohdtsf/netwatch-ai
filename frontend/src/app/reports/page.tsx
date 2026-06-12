'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { FileText, Download, Calendar } from 'lucide-react';

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Reports</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Generate Report</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Report Type</label>
              <select className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-sm focus:outline-none focus:border-accent">
                <option>Network Traffic Summary</option>
                <option>Security Alerts & Threats</option>
                <option>DNS Blocking Statistics</option>
                <option>Device Activity Logs</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Date Range</label>
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <Calendar className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input type="date" className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm focus:outline-none focus:border-accent text-slate-300 [color-scheme:dark]" />
                </div>
                <span className="text-slate-500">to</span>
                <div className="relative flex-1">
                  <Calendar className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input type="date" className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm focus:outline-none focus:border-accent text-slate-300 [color-scheme:dark]" />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Format</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="format" value="pdf" defaultChecked className="text-accent bg-slate-900 border-slate-700 focus:ring-accent" />
                  <span className="text-sm">PDF Report</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="format" value="csv" className="text-accent bg-slate-900 border-slate-700 focus:ring-accent" />
                  <span className="text-sm">CSV Data</span>
                </label>
              </div>
            </div>

            <button className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-md font-medium transition-colors mt-4">
              <Download className="w-4 h-4" /> Generate & Download
            </button>
          </CardContent>
        </Card>

        <Card className="col-span-1 md:col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-slate-500 flex flex-col items-center">
              <FileText className="w-12 h-12 mb-4 opacity-20" />
              No reports generated yet.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
