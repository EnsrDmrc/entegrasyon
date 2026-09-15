"use client";

import React, { useEffect, useState } from 'react';
import { apiFetch } from '@/utils/api';

export default function RepricingReportPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/repricing/expensive-products`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data.data || []);
      } else {
        setError('Rapor alınırken bir hata oluştu.');
      }
    } catch (err) {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
        Fiyat Fırsatları Raporu
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Aşağıdaki ürünlerde en ucuz satıcı siz değilsiniz. Satışları kaçırmamak için N11 panelinizden fiyatlarınızı güncelleyerek tekrar rekabete dahil olabilirsiniz.
      </p>

      {error && (
        <div style={{ backgroundColor: 'rgba(255, 68, 68, 0.1)', color: '#ff4444', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Yükleniyor...</div>
      ) : products.length === 0 ? (
        <div style={{ 
          backgroundColor: 'var(--bg-secondary)', 
          padding: '3rem', 
          borderRadius: '12px', 
          textAlign: 'center',
          color: 'var(--text-secondary)'
        }}>
          Harika! Şu anda pahalı olduğunuz veya rekabette geride kaldığınız hiçbir ürün yok. Tüm ürünlerinizde en ucuz satıcı sizsiniz. 🎉
        </div>
      ) : (
        <div className="card">
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Ürün SKU</th>
                  <th>Ürün Adı</th>
                  <th>Bizim Fiyatımız</th>
                  <th>En Ucuz Rakip</th>
                  <th>Rakip Fiyatı</th>
                  <th>Fiyat Farkı</th>
                  <th>Son Kontrol</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p, idx) => {
                  const diff = p.our_price - (p.cheapest_competitor_price || 0);
                  const isLoss = diff > 0;
                  return (
                    <tr key={idx}>
                      <td><span className="badge" style={{ backgroundColor: 'var(--bg-primary)' }}>{p.sku}</span></td>
                      <td style={{ maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={p.name}>
                        {p.name}
                      </td>
                      <td style={{ fontWeight: 'bold' }}>{p.our_price?.toLocaleString('tr-TR')} TL</td>
                      <td>
                        <span className="badge badge-purple">{p.cheapest_competitor_name || 'Bilinmiyor'}</span>
                      </td>
                      <td style={{ color: '#00e676', fontWeight: 'bold' }}>
                        {p.cheapest_competitor_price?.toLocaleString('tr-TR')} TL
                      </td>
                      <td style={{ color: isLoss ? '#ff4444' : '#00e676', fontWeight: 'bold' }}>
                        +{diff.toLocaleString('tr-TR')} TL
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        {p.last_checked ? new Date(p.last_checked).toLocaleString('tr-TR') : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
