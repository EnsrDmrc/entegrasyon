"use client";

import React, { useEffect, useState } from 'react';
import { apiFetch } from '@/utils/api';
import { FiAlertCircle, FiTrendingDown, FiClock, FiExternalLink, FiSearch } from 'react-helper-icons'; // Or similar, I will just use SVGs to be safe

export default function RepricingReportPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

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

  const filteredProducts = products.filter(p => 
    p.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="report-container" style={{
      padding: '2rem',
      background: 'linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)',
      minHeight: '100vh',
      fontFamily: "'Inter', sans-serif"
    }}>
      <style>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.85);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-radius: 20px;
          border: 1px solid rgba(255, 255, 255, 0.4);
          box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
          padding: 2rem;
          margin-bottom: 2rem;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .glass-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1);
        }
        .header-gradient {
          background: linear-gradient(120deg, #2563eb, #7c3aed);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .search-input {
          width: 100%;
          max-width: 400px;
          padding: 0.75rem 1.5rem 0.75rem 3rem;
          border-radius: 999px;
          border: 1px solid rgba(0,0,0,0.1);
          background: white;
          font-size: 0.95rem;
          transition: all 0.2s;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .search-input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .styled-table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0 12px;
        }
        .styled-table th {
          background: transparent;
          color: #64748b;
          font-weight: 600;
          text-transform: uppercase;
          font-size: 0.75rem;
          letter-spacing: 0.05em;
          padding: 1rem 1.5rem;
          text-align: left;
          border-bottom: 2px solid #e2e8f0;
        }
        .styled-table td {
          background: white;
          padding: 1.25rem 1.5rem;
          color: #334155;
          font-size: 0.95rem;
        }
        .styled-table tr td:first-child {
          border-top-left-radius: 12px;
          border-bottom-left-radius: 12px;
        }
        .styled-table tr td:last-child {
          border-top-right-radius: 12px;
          border-bottom-right-radius: 12px;
        }
        .styled-table tbody tr {
          box-shadow: 0 2px 4px rgba(0,0,0,0.02);
          transition: all 0.2s;
        }
        .styled-table tbody tr:hover {
          transform: scale(1.005);
          box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        }
        .sku-badge {
          background: #f1f5f9;
          color: #475569;
          padding: 0.25rem 0.75rem;
          border-radius: 6px;
          font-size: 0.8rem;
          font-weight: 600;
          font-family: monospace;
          border: 1px solid #e2e8f0;
        }
        .price-diff-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.4rem 0.8rem;
          border-radius: 999px;
          font-weight: 700;
          font-size: 0.85rem;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border: 1px solid rgba(239, 68, 68, 0.2);
        }
        .competitor-badge {
          background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
          color: #be185d;
          padding: 0.35rem 0.85rem;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 600;
          border: 1px solid #f9a8d4;
        }
      `}</style>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 className="header-gradient" style={{ fontSize: '2.5rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>
            Fiyat Fırsatları Raporu
          </h1>
          <p style={{ color: '#64748b', fontSize: '1.05rem', marginTop: '0.5rem', maxWidth: '600px', lineHeight: 1.5 }}>
            Rakip fiyatlarının gerisinde kalarak satış kaçırdığınız ürünleri burada keşfedin. Pazar payınızı geri almak için fiyatlarınızı optimize edin.
          </p>
        </div>
        
        <div style={{ position: 'relative' }}>
          <svg style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="text" 
            placeholder="Ürün adı veya SKU ara..." 
            className="search-input"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', borderLeft: '4px solid #ef4444', color: '#991b1b', padding: '1rem 1.5rem', borderRadius: '8px', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 500 }}>
          <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          {error}
        </div>
      )}

      {loading ? (
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid #e2e8f0', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <p style={{ marginTop: '1rem', color: '#64748b', fontWeight: 500 }}>Veriler analiz ediliyor...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : products.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div style={{ width: '80px', height: '80px', background: '#dcfce7', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
            <svg width="40" height="40" fill="none" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          </div>
          <h2 style={{ color: '#0f172a', fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Her Şey Mükemmel!</h2>
          <p style={{ color: '#64748b', fontSize: '1.1rem', maxWidth: '500px', margin: '0 auto' }}>
            Şu anda rekabette geride kaldığınız hiçbir ürün bulunmuyor. Sistemimiz tüm ürünlerinizde en rekabetçi fiyatı sizin adınıza koruyor. 🎉
          </p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto', paddingBottom: '2rem' }}>
          <table className="styled-table">
            <thead>
              <tr>
                <th>Ürün Bilgisi</th>
                <th>Sizin Fiyatınız</th>
                <th>Rakip Fiyatı</th>
                <th>En Ucuz Satıcı</th>
                <th>Fiyat Farkı (Kayıp)</th>
                <th>Tespit Zamanı</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((p, idx) => {
                const diff = (p.our_cart_price || p.our_price || 0) - (p.cheapest_competitor_price || 0);
                return (
                  <tr key={idx}>
                    <td style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <span style={{ fontWeight: 600, color: '#0f172a', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.name}</span>
                      <span className="sku-badge" style={{ alignSelf: 'flex-start' }}>{p.sku}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#334155' }}>
                          {(p.our_cart_price || p.our_price)?.toLocaleString('tr-TR')} TL
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                          {p.our_cart_price ? 'N11 Sepet Fiyatı' : 'İndirimsiz DB Fiyatı'}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#16a34a' }}>
                          {p.cheapest_competitor_price?.toLocaleString('tr-TR')} TL
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="competitor-badge">
                        {p.cheapest_competitor_name || 'Bilinmiyor'}
                      </span>
                    </td>
                    <td>
                      <div className="price-diff-badge">
                        <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
                        +{diff.toLocaleString('tr-TR')} TL
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#64748b', fontSize: '0.85rem' }}>
                        <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        {p.last_checked ? new Date(p.last_checked).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
