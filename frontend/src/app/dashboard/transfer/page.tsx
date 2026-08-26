'use client';

import React, { useState, useEffect } from 'react';

export default function TransferPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Kategori ve Markalar (Backendden çekilen ham liste)
  const [categories, setCategories] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  
  // Arama input değerleri
  const [catSearch, setCatSearch] = useState('');
  const [brandSearch, setBrandSearch] = useState('');

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
    fetchCategoriesAndBrands();
  }, []);

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products`, {
        headers: { 'Authorization': `Bearer ${token}` }
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

  const fetchCategoriesAndBrands = async () => {
    try {
      const token = localStorage.getItem('token');
      const catRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/pazarama/categories`, { headers: { 'Authorization': `Bearer ${token}` } });
      const brandRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/pazarama/brands`, { headers: { 'Authorization': `Bearer ${token}` } });
      
      if (catRes.ok) {
        const cData = await catRes.json();
        setCategories(Array.isArray(cData) ? cData : (cData.data || cData.categories || []));
      }
      if (brandRes.ok) {
        const bData = await brandRes.json();
        setBrands(Array.isArray(bData) ? bData : (bData.data || bData.brands || []));
      }
    } catch (err) {
      console.error("Kategori/Marka çekilemedi", err);
    }
  };

  const openTransferModal = (product: any) => {
    setSelectedProduct(product);
    setTransferMessage(null);
    
    // Son kullanılan ID'leri al
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
    
    localStorage.setItem('lastPazaramaCategoryId', transferData.target_category_id);
    localStorage.setItem('lastPazaramaBrandId', transferData.target_brand_id);
    
    try {
      const token = localStorage.getItem('token');
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

  // Dinamik arama filtrelemesi: İsimde geçenleri bul
  const filteredCategories = categories.filter(c => {
    const name = (c.name || c.Name || c.categoryName || c.displayName || "").toLowerCase();
    return name.includes(catSearch.toLowerCase());
  }).slice(0, 10); // Sadece ilk 10 sonucu göster

  const filteredBrands = brands.filter(b => {
    const name = (b.name || b.Name || b.brandName || "").toLowerCase();
    return name.includes(brandSearch.toLowerCase());
  }).slice(0, 10);

  return (
    <div className="dashboard-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>Akıllı Ürün Aktarımı</h2>
          <p style={{ color: 'var(--text-secondary)' }}>N11 ürünlerinizi Excel kullanmadan kolayca Pazarama'ya aktarın.</p>
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
          <div className="card" style={{ width: '500px', maxWidth: '90%', padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>{selectedProduct.name}</h3>
            
            {transferMessage && (
              <div className={`badge ${transferMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '1rem' }}>
                {transferMessage.text}
              </div>
            )}

            <form onSubmit={handleTransfer}>
              
              <div className="input-group">
                <label className="input-label">Pazarama'da Kategori Ara</label>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Kategori Adı Yazın (Örn: Telefon)..." 
                  value={catSearch}
                  onChange={e => setCatSearch(e.target.value)}
                />
                {catSearch && filteredCategories.length > 0 && (
                  <div style={{ border: '1px solid #ddd', borderRadius: '4px', marginTop: '4px', maxHeight: '150px', overflowY: 'auto' }}>
                    {filteredCategories.map(c => {
                      const cId = c.id || c.Id || c.categoryId;
                      const cName = c.name || c.Name || c.categoryName;
                      return (
                        <div 
                          key={cId}
                          onClick={() => {
                            setTransferData({...transferData, target_category_id: cId});
                            setCatSearch(cName);
                          }}
                          style={{ padding: '8px', cursor: 'pointer', borderBottom: '1px solid #eee' }}
                        >
                          {cName} (ID: {cId})
                        </div>
                      );
                    })}
                  </div>
                )}
                <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: '#666' }}>Seçili Kategori ID:</span>
                  <input 
                    type="text" 
                    value={transferData.target_category_id} 
                    onChange={e => setTransferData({...transferData, target_category_id: e.target.value})}
                    style={{ width: '80px', padding: '4px', border: '1px solid #ccc' }}
                    required 
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Pazarama'da Marka Ara</label>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Marka Adı Yazın (Örn: Apple)..." 
                  value={brandSearch}
                  onChange={e => setBrandSearch(e.target.value)}
                />
                {brandSearch && filteredBrands.length > 0 && (
                  <div style={{ border: '1px solid #ddd', borderRadius: '4px', marginTop: '4px', maxHeight: '150px', overflowY: 'auto' }}>
                    {filteredBrands.map(b => {
                      const bId = b.id || b.Id || b.brandId;
                      const bName = b.name || b.Name || b.brandName;
                      return (
                        <div 
                          key={bId}
                          onClick={() => {
                            setTransferData({...transferData, target_brand_id: bId});
                            setBrandSearch(bName);
                          }}
                          style={{ padding: '8px', cursor: 'pointer', borderBottom: '1px solid #eee' }}
                        >
                          {bName} (ID: {bId})
                        </div>
                      );
                    })}
                  </div>
                )}
                <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: '#666' }}>Seçili Marka ID:</span>
                  <input 
                    type="text" 
                    value={transferData.target_brand_id} 
                    onChange={e => setTransferData({...transferData, target_brand_id: e.target.value})}
                    style={{ width: '80px', padding: '4px', border: '1px solid #ccc' }}
                    required 
                  />
                </div>
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
