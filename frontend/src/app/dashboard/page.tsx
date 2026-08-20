"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardOverview() {
  const [productCount, setProductCount] = useState(0);
  const [lowStockCount, setLowStockCount] = useState(0);
  const [outOfStockCount, setOutOfStockCount] = useState(0);
  const [activeOrderCount, setActiveOrderCount] = useState(0);

  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Ürünleri Çek
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setProductCount(data.length);
          
          let low = 0;
          let out = 0;
          data.forEach(p => {
            const totalStock = p.inventories?.reduce((acc: number, curr: any) => acc + curr.quantity, 0) || 0;
            if (totalStock === 0) out++;
            else if (totalStock < 5) low++;
          });
          
          setLowStockCount(low);
          setOutOfStockCount(out);
        }
      })
      .catch(console.error);

      // Siparişleri Çek
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/orders`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          const oneDayAgo = new Date(Date.now() - 24 * 3600 * 1000);
          const recentOrders = data.filter((o: any) => new Date(o.order_date || o.created_at || new Date()) >= oneDayAgo);
          setActiveOrderCount(recentOrders.length);
        }
      })
      .catch(console.error);
    }
  }, []);

  return (
    <>
      <h1 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '1.5rem' }}>Genel Bakış</h1>
      
      <div className="stats-grid">
        <div 
          className="card stat-card hoverable-card" 
          onClick={() => router.push('/dashboard/inventory')}
          style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
        >
          <span className="stat-label">Toplam Ürün</span>
          <span className="stat-value">{productCount}</span>
          <span className="stat-change positive">Güncel</span>
        </div>
        <div 
          className="card stat-card hoverable-card"
          onClick={() => router.push('/dashboard/orders?filter=last_24h')}
          style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
        >
          <span className="stat-label">Aktif Siparişler (24s)</span>
          <span className="stat-value">{activeOrderCount}</span>
          <span className={activeOrderCount > 0 ? "stat-change positive" : "stat-change neutral"}>
            {activeOrderCount > 0 ? "Yeni siparişler var" : "Henüz sipariş yok"}
          </span>
        </div>
        <div 
          className="card stat-card hoverable-card"
          onClick={() => router.push('/dashboard/inventory?filter=low_stock')}
          style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
        >
          <span className="stat-label">Düşük Stok Uyarıları</span>
          <span className="stat-value">{lowStockCount}</span>
          <span className={lowStockCount > 0 ? "stat-change negative" : "stat-change positive"}>
            {lowStockCount > 0 ? "Kritik seviye" : "Her şey yolunda"}
          </span>
        </div>
        <div 
          className="card stat-card hoverable-card"
          onClick={() => router.push('/dashboard/inventory?filter=out_of_stock')}
          style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
        >
          <span className="stat-label">Tükenen Ürünler</span>
          <span className="stat-value">{outOfStockCount}</span>
          <span className={outOfStockCount > 0 ? "stat-change negative" : "stat-change positive"}>
            {outOfStockCount > 0 ? "Stok eklenmeli" : "Tükenen ürün yok"}
          </span>
        </div>
      </div>

      <div className="card" style={{ marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Son Hareketler</h3>
        <p style={{ color: 'var(--text-secondary)' }}>
          Şu an tüm pazaryerleri senkronize durumdadır. Yakın zamanda bir sipariş hareketi bulunmamaktadır.
        </p>
      </div>
    </>
  );
}
