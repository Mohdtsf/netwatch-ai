'use client';

import { useState, useEffect } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useWebSocket } from '@/hooks/useWebSocket';

type Flow = {
  id: number;
  time: number;
  src_ip: string;
  dst_ip: string;
  protocol: string;
  bytes: number;
  domain?: string;
  threat_label?: string;
};

const columnHelper = createColumnHelper<Flow>();

const columns = [
  columnHelper.accessor('time', {
    header: 'Time',
    cell: info => new Date((info.getValue() || Date.now() / 1000) * 1000).toLocaleTimeString(),
  }),
  columnHelper.accessor('src_ip', {
    header: 'Source IP',
    cell: info => <span className="font-mono text-cyan">{info.getValue() || '192.168.1.50'}</span>,
  }),
  columnHelper.accessor('dst_ip', {
    header: 'Dest IP',
    cell: info => <span className="font-mono">{info.getValue() || '8.8.8.8'}</span>,
  }),
  columnHelper.accessor('domain', {
    header: 'Domain / SNI',
    cell: info => info.getValue() || '-',
  }),
  columnHelper.accessor('protocol', {
    header: 'Protocol',
    cell: info => (
      <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs">
        {info.getValue() || 'TCP'}
      </span>
    ),
  }),
  columnHelper.accessor('bytes', {
    header: 'Bytes',
    cell: info => info.getValue() || 128,
  }),
  columnHelper.accessor('threat_label', {
    header: 'Threat',
    cell: info => {
      const val = info.getValue();
      if (!val || val === 'Normal') return <span className="text-safe text-xs">Normal</span>;
      return <span className="text-danger font-bold text-xs">{val}</span>;
    },
  }),
];

export default function FlowsPage() {
  const { flows } = useWebSocket();
  const [data, setData] = useState<Flow[]>([]);

  useEffect(() => {
    setData(flows);
  }, [flows]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Network Flows</h2>
        <div className="text-sm text-slate-400">Live Traffic Feed</div>
      </div>

      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader>
          <CardTitle>All Captured Flows</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-auto p-0">
          <table className="w-full text-sm text-left relative">
            <thead className="text-xs text-slate-400 uppercase bg-slate-800/50 sticky top-0 z-10 backdrop-blur-sm">
              {table.getHeaderGroups().map(headerGroup => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map(header => (
                    <th key={header.id} className="px-4 py-3 font-medium">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map(row => (
                <tr key={row.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-slate-500">
                    Listening for flows...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
