"use client";

import React, { useEffect, useState } from 'react';
import { apiFetch } from '@/utils/api';
import { Trophy, TrendingUp, AlertTriangle, ChevronDown, ChevronUp, Save, Search, RefreshCw } from 'lucide-react';
import { useScrollRestoration } from '@/hooks/useScrollRestoration';

export default function RepricingReportPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  const [activeTab, setActiveTab] = useState<'rakipsiz' | 'ucuz' | 'pahali'>('pahali');
  const [expandedProduct, setExpandedProduct] = useState<number | null>(null);
  const [updateProduct, setUpdateProduct] = useState<number | null>(null);

  // Manual update states
  const [editPrice, setEditPrice] = useState<{ [id: number]: string }>({});
  const [editStock, setEditStock] = useState<{ [id: number]: string }>({});
  const [syncing, setSyncing] = useState<{ [id: number]: boolean }>({});

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const navEntries = window.performance.getEntriesByType('navigation');
      const isReload = navEntries.length > 0 && (navEntries[0] as PerformanceNavigationTiming).type === 'reload';
      
      if (isReload) {
        const savedTab = sessionStorage.getItem('repricingActiveTab');
        if (savedTab && ['rakipsiz', 'ucuz', 'pahali'].includes(savedTab)) {
          setActiveTab(savedTab as any);
        }
      } else {
        sessionStorage.removeItem('repricingActiveTab');
      }
    }
    fetchProducts();
  }, []);

  const handleTabChange = (tab: 'rakipsiz' | 'ucuz' | 'pahali') => {
    setActiveTab(tab);
    sessionStorage.setItem('repricingActiveTab', tab);
  };

  useScrollRestoration('repricingScrollPos', [loading, products.length]);

  const triggerRepricing = async () => {
    try {
      alert("Ürün analizleri arka planda başlatıldı. İşlem ürün sayısına göre birkaç dakika sürebilir. Lütfen daha sonra sayfayı yenileyin.");
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/repricing/n11/trigger`, {
        method: 'POST'
      });
    } catch (err) {
      console.error(err);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data || []);
      } else {
        setError('Ürünler alınırken bir hata oluştu.');
      }
    } catch (err) {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  const parseCompetitors = (jsonStr: string) => {
    try {
      if (!jsonStr) return [];
      return JSON.parse(jsonStr);
    } catch (e) {
      return [];
    }
  };

  const getStockFromInventories = (product: any) => {
    if (product.inventories && product.inventories.length > 0) {
      return product.inventories[0].quantity;
    }
    return 0;
  };

  const handleUpdate = async (product: any, actionType: 'manual' | 'auto_minus_10') => {
    let targetBasePrice = 0;
    let targetStock = getStockFromInventories(product);
    const myBasePrice = product.price;
    const currentStock = getStockFromInventories(product);
    
    if (actionType === 'auto_minus_10') {
      if (!product.cheapest_competitor_price) return;
      const targetCartPrice = product.cheapest_competitor_price - 10;
      
      let discountMultiplier = 1;
      let discountPercentage = 0;
      if (product.our_cart_price && product.price && product.our_cart_price < product.price) {
        discountMultiplier = product.our_cart_price / product.price;
        discountPercentage = Math.round((1 - discountMultiplier) * 100);
      }
      
      targetBasePrice = targetCartPrice;
      if (discountMultiplier < 1) {
        targetBasePrice = targetCartPrice / discountMultiplier;
      }
      targetBasePrice = Number(targetBasePrice.toFixed(2));
      
      let confirmMessage = `${product.name} ürününün SEPET FİYATI rakibinizden 10 TL ucuz (${targetCartPrice.toFixed(2)} TL) olacak şekilde ayarlanacaktır.`;
      if (discountMultiplier < 1) {
        confirmMessage += `\n\nN11 %${discountPercentage} indirimi tespit edildi! Liste fiyatınız ${targetBasePrice} TL olarak gönderilecektir.`;
      }
      confirmMessage += `\nOnaylıyor musunuz?`;
      
      if (!window.confirm(confirmMessage)) return;
      
    } else {
      // Manual edit
      const rawPrice = editPrice[product.id] !== undefined && editPrice[product.id] !== '' ? editPrice[product.id] : myBasePrice.toString();
      const p = parseFloat(rawPrice);
      if (isNaN(p) || p <= 0) {
        alert('Geçerli bir fiyat giriniz.'); return;
      }
      targetBasePrice = p;
      
      const rawStock = editStock[product.id] !== undefined && editStock[product.id] !== '' ? editStock[product.id] : currentStock.toString();
      const s = parseInt(rawStock);
      if (!isNaN(s)) {
        targetStock = s;
      }
    }

    setSyncing(prev => ({ ...prev, [product.id]: true }));
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products/${product.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: targetBasePrice, quantity: targetStock })
      });
      
      if (res.ok) {
        alert('Fiyat ve stok başarıyla güncellendi! Tüm platformlara senkronize ediliyor...');
      } else {
        alert('Güncelleme sırasında bir hata oluştu.');
      }
    } catch (err) {
      alert('Sunucuya bağlanırken bir hata oluştu.');
    } finally {
      setSyncing(prev => ({ ...prev, [product.id]: false }));
      fetchProducts();
    }
  };

  const handlePriceChange = (id: number, val: string) => setEditPrice(prev => ({ ...prev, [id]: val }));
  const handleStockChange = (id: number, val: string) => setEditStock(prev => ({ ...prev, [id]: val }));

  // Categorize products
  const rakipsiz: any[] = [];
  const ucuz: any[] = [];
  const pahali: any[] = [];

  const searchedProducts = products.filter(p => 
    p.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  searchedProducts.forEach(p => {
    // Only categorize if it has been repriced (last_repricing_check exists)
    if (!p.last_repricing_check) return;

    const comps = parseCompetitors(p.competitors_json);
    if (!comps || comps.length === 0 || !p.cheapest_competitor_price || p.cheapest_competitor_price === 0) {
      rakipsiz.push(p);
    } else {
      const myPrice = p.our_cart_price || p.price;
      if (myPrice <= p.cheapest_competitor_price) {
        ucuz.push(p);
      } else {
        pahali.push(p);
      }
    }
  });

  const getActiveList = () => {
    if (activeTab === 'rakipsiz') return rakipsiz;
    
    if (activeTab === 'ucuz') {
      return [...ucuz].sort((a, b) => {
        const aMyPrice = a.our_cart_price || a.price;
        const bMyPrice = b.our_cart_price || b.price;
        const aDiff = a.cheapest_competitor_price - aMyPrice;
        const bDiff = b.cheapest_competitor_price - bMyPrice;
        
        const aActive = aDiff > 10.05;
        const bActive = bDiff > 10.05;
        
        if (aActive && !bActive) return -1;
        if (!aActive && bActive) return 1;
        
        return bDiff - aDiff;
      });
    }
    
    if (activeTab === 'pahali') {
      return [...pahali].sort((a, b) => {
        const aMyPrice = a.our_cart_price || a.price;
        const bMyPrice = b.our_cart_price || b.price;
        const aDiff = aMyPrice - a.cheapest_competitor_price;
        const bDiff = bMyPrice - b.cheapest_competitor_price;
        
        return aDiff - bDiff;
      });
    }
    
    return [];
  };

  const activeList = getActiveList();

  return (
    <div style={{ padding: '2rem', background: '#f8fafc', minHeight: '100vh', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>Fırsat ve Rakip Analizi</h1>
          <p style={{ color: '#64748b', marginTop: '0.5rem' }}>Rakiplerinizin fiyat ve stoklarını anlık izleyin, manuel aksiyon alın.</p>
        </div>
        <div style={{ position: 'relative', display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button
            onClick={triggerRepricing}
            style={{
              background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1',
              padding: '0.75rem 1.5rem', borderRadius: '999px', cursor: 'pointer',
              fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}
          >
            <RefreshCw size={18} />
            Verileri Yenile
          </button>
          
          <div style={{ position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            <input 
              type="text" 
              placeholder="Ürün veya SKU ara..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{ padding: '0.75rem 1.5rem 0.75rem 2.5rem', borderRadius: '999px', border: '1px solid #e2e8f0', width: '300px', outline: 'none' }}
            />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '2px solid #e2e8f0' }}>
        <button 
          onClick={() => handleTabChange('pahali')}
          style={{ 
            padding: '1rem 2rem', border: 'none', background: 'transparent', cursor: 'pointer',
            fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem',
            color: activeTab === 'pahali' ? '#ef4444' : '#64748b',
            borderBottom: activeTab === 'pahali' ? '3px solid #ef4444' : '3px solid transparent',
            marginBottom: '-2px'
          }}
        >
          <AlertTriangle size={20} />
          Pahalı Kaldıklarımız ({pahali.length})
        </button>
        <button 
          onClick={() => handleTabChange('ucuz')}
          style={{ 
            padding: '1rem 2rem', border: 'none', background: 'transparent', cursor: 'pointer',
            fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem',
            color: activeTab === 'ucuz' ? '#10b981' : '#64748b',
            borderBottom: activeTab === 'ucuz' ? '3px solid #10b981' : '3px solid transparent',
            marginBottom: '-2px'
          }}
        >
          <TrendingUp size={20} />
          En Ucuz Biziz ({ucuz.length})
        </button>
        <button 
          onClick={() => handleTabChange('rakipsiz')}
          style={{ 
            padding: '1rem 2rem', border: 'none', background: 'transparent', cursor: 'pointer',
            fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem',
            color: activeTab === 'rakipsiz' ? '#3b82f6' : '#64748b',
            borderBottom: activeTab === 'rakipsiz' ? '3px solid #3b82f6' : '3px solid transparent',
            marginBottom: '-2px'
          }}
        >
          <Trophy size={20} />
          Rakipsiz (Tek Satıcı) ({rakipsiz.length})
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>Yükleniyor...</div>
      ) : activeList.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', background: 'white', borderRadius: '12px', color: '#64748b' }}>
          Bu kategoride ürün bulunamadı.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {activeList.map(product => {
            const comps = parseCompetitors(product.competitors_json);
            const myCartPrice = product.our_cart_price || product.price;
            const myBasePrice = product.price;
            const diff = activeTab === 'pahali' ? (myCartPrice - (product.cheapest_competitor_price || 0)) : 0;
            const isExpanded = expandedProduct === product.id;
            const currentStock = getStockFromInventories(product);
            const hasDiscount = myCartPrice < myBasePrice;

            return (
              <div key={product.id} style={{ background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
                {/* Main Row */}
                <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '2rem' }}>
                  
                  <div style={{ flex: '2', minWidth: '200px' }}>
                    <div style={{ fontWeight: 700, marginBottom: '0.5rem' }}>
                      {product.n11_url ? (
                        <a href={product.n11_url} target="_blank" rel="noopener noreferrer" style={{ color: '#0f172a', textDecoration: 'none' }} onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'} onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}>
                          {product.name}
                        </a>
                      ) : (
                        <span style={{ color: '#0f172a' }}>{product.name}</span>
                      )}
                    </div>
                    <span style={{ background: '#f1f5f9', padding: '4px 8px', borderRadius: '6px', fontSize: '0.8rem', fontFamily: 'monospace', color: '#475569' }}>{product.sku}</span>
                  </div>

                  <div style={{ flex: '1' }}>
                    <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '0.2rem' }}>Sepet Fiyatımız</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#334155' }}>
                      {myCartPrice.toLocaleString('tr-TR')} TL
                    </div>
                    {hasDiscount && (
                      <div style={{ fontSize: '0.75rem', color: '#8b5cf6', fontWeight: 600, marginTop: '0.2rem' }}>
                        *N11 İndirimi Var (Liste: {myBasePrice} TL)
                      </div>
                    )}
                  </div>

                  {activeTab !== 'rakipsiz' && (
                    <div style={{ flex: '1' }}>
                      <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '0.2rem' }}>En Ucuz Rakip</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: activeTab === 'pahali' ? '#ef4444' : '#10b981' }}>
                        {product.cheapest_competitor_price?.toLocaleString('tr-TR')} TL
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>{product.cheapest_competitor_name}</div>
                    </div>
                  )}
                  
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <button 
                      onClick={() => setUpdateProduct(updateProduct === product.id ? null : product.id)}
                      style={{ background: '#10b981', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
                    >
                      Fiyat ve Stok Güncelle
                    </button>
                    
                    {(activeTab === 'pahali' || activeTab === 'ucuz') && (
                      <button 
                        onClick={() => handleUpdate(product, 'auto_minus_10')}
                        disabled={activeTab === 'ucuz' && (product.cheapest_competitor_price - product.our_cart_price) <= 10.05}
                        style={{ 
                          background: (activeTab === 'ucuz' && (product.cheapest_competitor_price - product.our_cart_price) <= 10.05) ? '#94a3b8' : '#ef4444', 
                          color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '8px', cursor: (activeTab === 'ucuz' && (product.cheapest_competitor_price - product.our_cart_price) <= 10.05) ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: '0.85rem' 
                        }}
                      >
                        Rakibe Göre Fiyatı Ayarla
                      </button>
                    )}
                    
                    <button 
                      onClick={() => setExpandedProduct(expandedProduct === product.id ? null : product.id)}
                      style={{ background: 'transparent', border: '1px solid #e2e8f0', padding: '0.5rem', borderRadius: '8px', cursor: 'pointer', color: '#64748b' }}
                    >
                      {expandedProduct === product.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </button>
                  </div>
                </div>

                {/* Update Panel */}
                {updateProduct === product.id && (
                  <div style={{ borderTop: '1px solid #e2e8f0', background: '#f8fafc', padding: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.85rem', color: '#475569', fontWeight: 600 }}>Manuel Fiyat:</span>
                      <input 
                        type="number" 
                        value={editPrice[product.id] !== undefined ? editPrice[product.id] : myBasePrice}
                        onChange={e => handlePriceChange(product.id, e.target.value)}
                        style={{ width: '90px', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                      />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.85rem', color: '#475569', fontWeight: 600 }}>Stok:</span>
                      <input 
                        type="number" 
                        value={editStock[product.id] !== undefined ? editStock[product.id] : currentStock}
                        onChange={e => handleStockChange(product.id, e.target.value)}
                        style={{ width: '70px', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                      />
                    </div>
                    <button 
                      onClick={() => { handleUpdate(product, 'manual'); setUpdateProduct(null); }}
                      disabled={syncing[product.id]}
                      style={{ background: '#10b981', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                    >
                      {syncing[product.id] ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
                      Kaydet ve Senkronize Et
                    </button>
                  </div>
                )}

                {/* Expanded Accordion for Competitors */}
                {expandedProduct === product.id && (
                  <div style={{ borderTop: '1px solid #e2e8f0', background: '#f8fafc', padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                      <h4 style={{ margin: 0, color: '#334155', fontSize: '1rem' }}>Rakip Analizi</h4>
                    </div>
                    
                    <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                      <thead>
                        <tr style={{ background: '#f1f5f9', borderBottom: '2px solid #e2e8f0' }}>
                          <th style={{ padding: '0.75rem', textAlign: 'left', color: '#475569', fontSize: '0.85rem' }}>Satıcı Adı</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', color: '#475569', fontSize: '0.85rem' }}>Sepet Fiyatı</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', color: '#475569', fontSize: '0.85rem' }}>Liste Fiyatı</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', color: '#475569', fontSize: '0.85rem' }}>Stok</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comps.map((c: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '0.75rem', fontSize: '0.9rem', fontWeight: 600, color: '#0f172a' }}>{c.seller_name}</td>
                            <td style={{ padding: '0.75rem', fontSize: '0.9rem', color: '#16a34a', fontWeight: 700 }}>{c.price.toLocaleString('tr-TR')} TL</td>
                            <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: '#64748b' }}>{c.base_price ? c.base_price.toLocaleString('tr-TR') + ' TL' : '-'}</td>
                            <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: '#ef4444', fontWeight: 700 }}>{c.stock ? c.stock + ' Adet' : 'Bilinmiyor'}</td>
                          </tr>
                        ))}
                        {comps.length === 0 && (
                          <tr><td colSpan={4} style={{ padding: '1rem', textAlign: 'center', color: '#64748b' }}>Rakip bilgisi bulunamadı.</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
