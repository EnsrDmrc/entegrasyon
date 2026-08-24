"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [tenantName, setTenantName] = useState('Yükleniyor...');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      setIsAuthorized(true);
      // Backend'den profil bilgilerini al
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data.tenant && data.tenant.name) {
          setTenantName(data.tenant.name);
        }
      })
      .catch(() => {
        localStorage.removeItem('token');
        router.push('/login');
      });
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  if (!isAuthorized) return <div style={{ padding: '2rem', textAlign: 'center' }}>Yetki kontrol ediliyor...</div>;

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Link href="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            Vendora
          </Link>
        </div>
        <nav className="sidebar-nav">
          <Link 
            href="/dashboard" 
            className={`sidebar-link ${pathname === '/dashboard' ? 'active' : ''}`}
          >
            Genel Bakış
          </Link>
          <Link 
            href="/dashboard/inventory" 
            className={`sidebar-link ${pathname.includes('/inventory') ? 'active' : ''}`}
          >
            Envanter
          </Link>
          <Link 
            href="/dashboard/orders" 
            className={`sidebar-link ${pathname.includes('/orders') ? 'active' : ''}`}
          >
            Siparişler
          </Link>
          <Link 
            href="/dashboard/settings" 
            className={`sidebar-link ${pathname.includes('/settings') ? 'active' : ''}`}
          >
            Ayarlar
          </Link>
        </nav>
        <div style={{ padding: '1rem' }}>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ width: '100%' }}>
            Çıkış Yap
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="dashboard-main bg-primary">
        <header className="dashboard-header">
          <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
            Mağaza: <span style={{ color: 'var(--text-primary)' }}>{tenantName}</span>
          </div>
          <div>
            <span className="badge badge-green">Sistem Çevrimiçi</span>
          </div>
        </header>
        
        <div className="dashboard-content animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
