'use client';

import React, { useState, useEffect } from 'react';

export default function TransferPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const [transferData, setTransferData] = useState({
    target_marketplace: 'pazarama',
    target_category_id: '',
    target_brand_id: '',
    vat_rate: '20'
  });
  const [transferring, setTransferring] = useState(false);
  const [transferMessage, setTransferMessage] = useState<{type: 'success'|'error', text: string} | null>(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      } else {
        setError('Ürünler yüklenemedi.');
      }
    } catch (err) {
      setError('Bağlantı hatası.');
    } finally {
      setLoading(false);
    }
  };

  const openTransferModal = (product: any) => {
    setSelectedProduct(product);
    setTransferMessage(null);
    
    // Son kullanılan ID'leri localStorage'dan al
    const savedCategoryId = localStorage.getItem('lastPazaramaCategoryId') || '';
    const savedBrandId = localStorage.getItem('lastPazaramaBrandId') || '';
    
    setTransferData(prev => ({
      ...prev,
      target_category_id: savedCategoryId,
      target_brand_id: savedBrandId
    }));
    
    setIsModalOpen(true);
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setTransferring(true);
    setTransferMessage(null);
    
    // Başarılı olursa diye girilen ID'leri kaydet
    localStorage.setItem('lastPazaramaCategoryId', transferData.target_category_id);
    localStorage.setItem('lastPazaramaBrandId', transferData.target_brand_id);
    
    try {
      const token = localStorage.getItem('token');
      // Şu anki senaryoda ürünlerin orijinal kaynağını bilmiyoruz DB'de,
      // bu yüzden MVP olarak varsayılan kaynak N11 kabul ediyoruz.
      // Gerçek bir senaryoda DB'deki Inventory tablosundan kaynağı buluruz.
      
      const payload = {
        sku: selectedProduct.sku,
        source_marketplace: 'n11',
        target_marketplace: transferData.target_marketplace,
        target_category_id: parseInt(transferData.target_category_id),
        target_brand_id: parseInt(transferData.target_brand_id),
        vat_rate: parseInt(transferData.vat_rate)
      };

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setTransferMessage({ type: 'success', text: 'Ürün başarıyla aktarıldı!' });
      } else {
        setTransferMessage({ type: 'error', text: data.detail || 'Aktarım başarısız oldu.' });
      }
    } catch (err: any) {
      setTransferMessage({ type: 'error', text: err.message || 'Bağlantı hatası' });
    } finally {
      setTransferring(false);
    }
  };

  return (
    <div className="dashboard-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>Pazaryerleri Arası Ürün Aktarımı</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Bir pazaryerindeki ürününüzü diğerine tek tıkla kopyalayın.</p>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p>Yükleniyor...</p>
        ) : error ? (
          <div className="badge badge-red">{error}</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Ürün Kodu (SKU)</th>
                <th>Ürün Adı</th>
                <th>Fiyat</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {products.map(product => (
                <tr key={product.id}>
                  <td>{product.sku}</td>
                  <td>{product.name}</td>
                  <td>{product.price} TL</td>
                  <td>
                    <button 
                      className="btn btn-primary" 
                      style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                      onClick={() => openTransferModal(product)}
                    >
                      Aktar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {isModalOpen && selectedProduct && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '500px', maxWidth: '90%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Ürün Aktarımı</h3>
            <p style={{ marginBottom: '1.5rem' }}>
              <strong>{selectedProduct.name}</strong> ürününü N11'den Pazarama'ya aktarıyorsunuz.
            </p>
            
            {transferMessage && (
              <div className={`badge ${transferMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '1rem' }}>
                {transferMessage.text}
              </div>
            )}

            <form onSubmit={handleTransfer}>
              <div className="input-group">
                <label className="input-label">Hedef Pazaryeri</label>
                <select 
                  className="input-field" 
                  value={transferData.target_marketplace}
                  onChange={e => setTransferData({...transferData, target_marketplace: e.target.value})}
                  disabled
                >
                  <option value="pazarama">Pazarama</option>
                </select>
              </div>
              
              <div className="input-group">
                <label className="input-label">Pazarama Kategori ID</label>
                <input 
                  type="number" 
                  className="input-field" 
                  placeholder="Örn: 10245" 
                  value={transferData.target_category_id}
                  onChange={e => setTransferData({...transferData, target_category_id: e.target.value})}
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label">Pazarama Marka ID</label>
                <input 
                  type="number" 
                  className="input-field" 
                  placeholder="Örn: 504" 
                  value={transferData.target_brand_id}
                  onChange={e => setTransferData({...transferData, target_brand_id: e.target.value})}
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label">KDV Oranı (%)</label>
                <input 
                  type="number" 
                  className="input-field" 
                  placeholder="20" 
                  value={transferData.vat_rate}
                  onChange={e => setTransferData({...transferData, vat_rate: e.target.value})}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                <button type="submit" className="btn btn-primary" disabled={transferring} style={{ flex: 1 }}>
                  {transferring ? 'Aktarılıyor...' : 'Aktarımı Başlat'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)} disabled={transferring}>
                  Kapat
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
