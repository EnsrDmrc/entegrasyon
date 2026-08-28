'use client';

import React, { useState, useEffect } from 'react';

export default function TransferPage() {
  const [activeIntegrations, setActiveIntegrations] = useState<any[]>([]);
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  
  const [transferring, setTransferring] = useState(false);
  const [transferResult, setTransferResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchActiveIntegrations();
  }, []);

  const fetchActiveIntegrations = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/active`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setActiveIntegrations(data);
      }
    } catch (err) {
      console.error("Aktif entegrasyonlar çekilemedi", err);
    }
  };

  const handleBulkTransfer = async () => {
    if (!source || !target) {
      setError("Lütfen kaynak ve hedef pazaryerlerini seçin.");
      return;
    }
    if (source === target) {
      setError("Kaynak ve hedef aynı olamaz.");
      return;
    }

    setTransferring(true);
    setError(null);
    setTransferResult(null);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/bulk-transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          source_marketplace: source,
          target_marketplace: target
        })
      });
      
      const data = await res.json();
      if (res.ok) {
        setTransferResult(data);
      } else {
        setError(data.detail || "Aktarım sırasında hata oluştu.");
      }
    } catch (err: any) {
      setError(err.message || "Bağlantı hatası.");
    } finally {
      setTransferring(false);
    }
  };

  return (
    <div className="dashboard-content">
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>Pazaryerinden Pazaryerine Aktarım</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Ürünlerinizi bir platformdan diğerine yapay zeka destekli kategori eşleştirmesi ile kusursuzca aktarın.</p>
      </div>

      <div className="card" style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem' }}>
        {error && (
          <div className="badge badge-red" style={{ marginBottom: '1.5rem', display: 'block', padding: '1rem' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
          <div style={{ flex: 1 }}>
            <label className="input-label">Ürünleri Çekeceğimiz Mağaza (Kaynak)</label>
            <select 
              className="input-field" 
              value={source}
              onChange={e => setSource(e.target.value)}
              disabled={transferring}
            >
              <option value="">Seçiniz...</option>
              {activeIntegrations.map((intg, idx) => (
                <option key={idx} value={intg.marketplace_name}>{intg.marketplace_name.toUpperCase()}</option>
              ))}
            </select>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.5rem', color: 'var(--primary-color)' }}>➔</span>
          </div>

          <div style={{ flex: 1 }}>
            <label className="input-label">Ürünleri Aktaracağımız Mağaza (Hedef)</label>
            <select 
              className="input-field" 
              value={target}
              onChange={e => setTarget(e.target.value)}
              disabled={transferring}
            >
              <option value="">Seçiniz...</option>
              {activeIntegrations.map((intg, idx) => (
                <option key={idx} value={intg.marketplace_name}>{intg.marketplace_name.toUpperCase()}</option>
              ))}
            </select>
          </div>
        </div>

        <button 
          className="btn btn-primary" 
          style={{ width: '100%', padding: '1rem', fontSize: '1.1rem' }}
          onClick={handleBulkTransfer}
          disabled={transferring || !source || !target}
        >
          {transferring ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <span className="spinner" style={{ width: '20px', height: '20px', border: '3px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></span>
              Aktarılıyor... Bu işlem ürün sayısına göre uzun sürebilir.
            </span>
          ) : 'Ürünleri Aktar'}
        </button>
      </div>

      {transferResult && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--success-color)' }}>
            Aktarım Tamamlandı!
          </h3>
          <p style={{ fontWeight: 500, marginBottom: '1rem' }}>{transferResult.message}</p>
          
          {transferResult.results && transferResult.results.length > 0 && (
            <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Ürün Adı</th>
                    <th>Durum</th>
                    <th>Detay</th>
                  </tr>
                </thead>
                <tbody>
                  {transferResult.results.map((r: any, idx: number) => (
                    <tr key={idx}>
                      <td>{r.sku}</td>
                      <td>{r.name}</td>
                      <td>
                        <span className={`badge ${r.status === 'success' ? 'badge-green' : 'badge-red'}`}>
                          {r.status === 'success' ? 'Başarılı' : 'Hatalı'}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{r.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
      `}} />
    </div>
  );
}
