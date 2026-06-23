'use client';

import { usePathname } from 'next/navigation';
import Providers from "./providers";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login';

  if (isAuthPage) {
    return (
      <Providers>
        <main className="flex-1 bg-[#060a12] flex items-center justify-center min-h-screen p-4">
          {children}
        </main>
      </Providers>
    );
  }

  return (
    <Providers>
      <Sidebar />
      <div className="flex flex-col flex-1 w-full min-w-0">
        <Header />
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-[#060a12]">
          {children}
        </main>
      </div>
    </Providers>
  );
}
