'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '@/lib/api';
import { useAppStore } from '@/stores/appStore';

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { setUser } = useAppStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const isAuthPage = pathname === '/login';
      const token = localStorage.getItem('access_token');

      if (!token && !isAuthPage) {
        router.push('/login');
        setIsInitializing(false);
        return;
      }

      if (token) {
        try {
          // Fetch current user
          const response = await api.get('/auth/me');
          setUser(response.data);
          
          if (isAuthPage) {
            router.push('/');
          }
        } catch (error) {
          console.error("Auth check failed", error);
          localStorage.removeItem('access_token');
          setUser(null);
          if (!isAuthPage) {
            router.push('/login');
          }
        }
      }
      setIsInitializing(false);
    };

    checkAuth();
  }, [pathname, router, setUser]);

  if (isInitializing) {
    return <div className="flex h-screen w-full items-center justify-center bg-[#060a12] text-accent">Loading...</div>;
  }

  return <>{children}</>;
}
