"use client";

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function OrdersContent() {
  const searchParams = useSearchParams();
  const filter = searchParams.get('filter');
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const getBadgeClass = (status: string) => {
    if (!status) return 'badge-blue';
    const s = status.toLowerCase();
    if (s.includes('teslim') || s.includes('ödendi') || s.includes('paid') || s.includes('tamamlandı')) return 'badge-green';
    if (s.includes('bekliyor') || s.includes('pending') || s.includes('yeni')) return 'badge-yellow';
    if (s.includes('iptal') || s.includes('iade') || s.includes('reddedildi') || s.includes('rejected')) return 'badge-red';
    return 'badge-blue'; // Onaylandı, Kargolandı, etc.
  };

  const getStatusLabel = (status: string) => {
    if (!status) return 'Belirsiz';
    if (status === 'paid') return 'Ödendi';
    if (status === 'pending') return 'Bekliyor';
    return status;
  };

  const formatOrderDate = (dateString: any) => {
    if (!dateString) return new Date().toLocaleString('tr-TR');
    let str = String(dateString);
    // Veritabanı ve API tarihleri genellikle UTC işaretiyle ('Z' veya '+00:00') gelir.
    // Ancak pazaryerinden (örn: N11) saat Türkiye saati (lokal) olarak çekildiği için,
    // UTC işaretini kaldırıp tarayıcının yerel saatmiş gibi anlamasını sağlıyoruz.
    if (str.endsWith('Z')) str = str.slice(0, -1);
    if (str.endsWith('+00:00')) str = str.slice(0, -6);
    return new Date(str).toLocaleString('tr-TR');
  };

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/orders`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (filter === 'last_24h') {
            const oneDayAgo = new Date(Date.now() - 24 * 3600 * 1000);
            setOrders(data.filter((o: any) => new Date(o.order_date || o.created_at || new Date()) >= oneDayAgo));
          } else {
            setOrders(data);
          }
        }
      } catch (error) {
        console.error("Siparişler çekilemedi", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchOrders();
  }, [filter]);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700 }}>Siparişler</h1>
        {filter === 'last_24h' && (
          <span className="badge badge-green">Son 24 Saat Filtresi Aktif</span>
        )}
      </div>

      <div className="table-container animate-fade-in">
        <table className="data-table">
          <thead>
            <tr>
              <th>Sipariş No</th>
              <th>Pazaryeri</th>
              <th>Müşteri</th>
              <th>Sipariş Edilen Ürün(ler)</th>
              <th>Tarih</th>
              <th>Tutar</th>
              <th>Durum</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}>Yükleniyor...</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}>Sipariş bulunmuyor.</td></tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id}>
                  <td style={{ fontWeight: 500 }}>#{order.order_number}</td>
                  <td>
                    {order.marketplace === 'shopify' ? (
                      <span className="badge" style={{ backgroundColor: '#95bf47', color: 'white' }}>Shopify</span>
                    ) : order.marketplace === 'n11' ? (
                      <span className="badge" style={{ backgroundColor: '#5c3d99', color: 'white' }}>n11</span>
                    ) : order.marketplace === 'hepsiburada' ? (
                      <span className="badge" style={{ backgroundColor: '#f97316', color: 'white' }}>Hepsiburada</span>
                    ) : order.marketplace === 'trendyol' ? (
                      <span className="badge" style={{ backgroundColor: '#f27a1a', color: 'white' }}>Trendyol</span>
                    ) : (
                      <span className="badge badge-blue">{order.marketplace}</span>
                    )}
                  </td>
                  <td>{order.customer_name || 'Bilinmeyen Müşteri'}</td>
                  <td>
                    {order.items && order.items.length > 0 ? (
                      order.items.map((item: any, index: number) => (
                        <div key={index} style={{ marginBottom: index !== order.items.length - 1 ? '0.5rem' : 0 }}>
                          <div style={{ fontWeight: 500 }}>{item.product_name}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>SKU: {item.product_sku} <span style={{ marginLeft: '0.5rem' }}>Adet: {item.quantity}</span></div>
                        </div>
                      ))
                    ) : (
                      <span style={{ color: 'var(--text-secondary)' }}>Belirtilmemiş</span>
                    )}
                  </td>
                  <td>{formatOrderDate(order.order_date || order.created_at)}</td>
                  <td>{order.total_price} ₺</td>
                  <td>
                    <span className={`badge ${getBadgeClass(order.status)}`}>
                      {getStatusLabel(order.status)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function OrdersPage() {
  return (
    <Suspense fallback={<div>Yükleniyor...</div>}>
      <OrdersContent />
    </Suspense>
  );
}
