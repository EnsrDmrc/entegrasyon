"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardOverview() {
  const [productCount, setProductCount] = useState(0);
  const [lowStockCount, setLowStockCount] = useState(0);
  const [outOfStockCount, setOutOfStockCount] = useState(0);
  const [activeOrderCount, setActiveOrderCount] = useState(0);
  const [activeOrdersList, setActiveOrdersList] = useState<any[]>([]);

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
            const totalStock = p.inventories && p.inventories.length > 0 ? p.inventories[0].quantity : 0;
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
          setActiveOrdersList(recentOrders);
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

      {activeOrdersList.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem', color: '#1e293b' }}>Son 24 Saatteki Siparişler</h2>
          <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
            <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>Sipariş No</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>Pazaryeri</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>Müşteri</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>Durum</th>
                  <th style={{ textAlign: 'right', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>Tutar</th>
                </tr>
              </thead>
              <tbody>
                {activeOrdersList.map(order => (
                  <tr key={order.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px', color: '#0f172a', fontWeight: 500 }}>{order.order_number}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ 
                        background: order.marketplace === 'n11' ? '#5b21b6' : '#10b981', 
                        color: 'white', 
                        padding: '2px 8px', 
                        borderRadius: '12px', 
                        fontSize: '0.75rem', 
                        fontWeight: 600 
                      }}>
                        {order.marketplace.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#475569' }}>{order.customer_name}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ 
                        background: '#f1f5f9', 
                        color: '#334155', 
                        padding: '4px 8px', 
                        borderRadius: '4px', 
                        fontSize: '0.875rem' 
                      }}>
                        {order.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: '#0f172a', fontWeight: 600 }}>
                      {order.total_price} TL
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
