"use client";

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiFetch } from '@/utils/api';

function InventoryContent() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Yeni eklenen filtreleme ve sıralama state'leri
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortType, setSortType] = useState('name_asc');
  
  const searchParams = useSearchParams();
  const router = useRouter();
  const filter = searchParams.get('filter');

  useEffect(() => {
    if (filter === 'low_stock') setStatusFilter('low_stock');
    else if (filter === 'out_of_stock') setStatusFilter('out_of_stock');
  }, [filter]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products`);
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) {
          const mapped = data.map(p => {
            // Stok miktarını pazaryerlerinin toplamı olarak değil, tek bir kayıt olarak al.
            // Çünkü bir ürünün fiziksel stoğu tektir ve tüm pazaryerlerine aynı sayı yansıtılır.
            const totalStock = p.inventories && p.inventories.length > 0 
              ? p.inventories[0].quantity 
              : 0;
            return {
              id: p.id,
              sku: p.sku,
              name: p.name,
              price: p.price,
              stock: totalStock,
              status: totalStock > 0 ? 'Stokta Var' : 'Tükendi'
            };
          });
          setProducts(mapped);
        }
      }
    } catch (error) {
      console.error('Ürünler çekilemedi', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const [editingProduct, setEditingProduct] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ price: 0, stock: 0 });
  const [isUpdating, setIsUpdating] = useState(false);

  const openEditModal = (product: any) => {
    setEditingProduct(product);
    setEditForm({ price: product.price, stock: product.stock });
  };

  const closeEditModal = () => {
    setEditingProduct(null);
  };

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    
    setIsUpdating(true);
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/products/${editingProduct.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          price: editForm.price,
          quantity: editForm.stock 
        })
      });
      
      if (response.ok) {
        const responseData = await response.json();
        let msg = "Ürün başarıyla güncellendi!\n\n";
        if (responseData.sync_results) {
            msg += "Senkronizasyon Sonuçları:\n";
            for (const [marketplace, result] of Object.entries(responseData.sync_results)) {
                msg += `${marketplace.toUpperCase()}: ${(result as any).success ? 'Başarılı (' + (result as any).message + ')' : 'Başarısız (' + (result as any).message + ')'}\n`;
            }
        }
        alert(msg);
        closeEditModal();
        fetchProducts(); // Değişikliği veritabanından çekip UI'a yansıt
      } else {
        alert('Ürün güncellenemedi.');
      }
    } catch(err) {
      alert('Ürün güncellenirken hata oluştu.');
    } finally {
      setIsUpdating(false);
    }
  };

  // Filtreleme mantığı
  const filteredProducts = products.filter(p => {
    const matchesSearch = p.sku.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          p.name.toLowerCase().includes(searchQuery.toLowerCase());
    
    let matchesStatus = true;
    if (statusFilter === 'in_stock') matchesStatus = p.stock > 0;
    else if (statusFilter === 'low_stock') matchesStatus = p.stock > 0 && p.stock < 5;
    else if (statusFilter === 'out_of_stock') matchesStatus = p.stock === 0;

    return matchesSearch && matchesStatus;
  });

  // Sıralama mantığı
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    switch (sortType) {
      case 'price_asc': return a.price - b.price;
      case 'price_desc': return b.price - a.price;
      case 'stock_asc': return a.stock - b.stock;
      case 'stock_desc': return b.stock - a.stock;
      case 'name_desc': return b.name.localeCompare(a.name);
      case 'name_asc': 
      default: return a.name.localeCompare(b.name);
    }
  });

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700 }}>
          Envanter Yönetimi 
        </h1>
        <button className="btn btn-primary" onClick={() => router.push('/dashboard/settings')}>
          Pazaryerinden Ürün Çek
        </button>
      </div>

      {success && (
        <div className="badge badge-green" style={{ marginBottom: '1rem', display: 'block', padding: '1rem' }}>
          {success}
        </div>
      )}
      {error && (
        <div className="badge badge-red" style={{ marginBottom: '1rem', display: 'block', padding: '1rem' }}>
          {error}
        </div>
      )}

      <div className="table-container animate-fade-in">
        <div className="table-header-row" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
          <input 
            type="text" 
            className="input-field" 
            placeholder="SKU veya Ürün Adı Ara..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '300px', marginBottom: 0 }} 
          />
          
          <select 
            className="input-field" 
            style={{ width: '200px', marginBottom: 0 }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Tüm Durumlar</option>
            <option value="in_stock">Stokta Var</option>
            <option value="low_stock">Düşük Stok (1-4)</option>
            <option value="out_of_stock">Tükenenler</option>
          </select>

          <select 
            className="input-field" 
            style={{ width: '200px', marginBottom: 0 }}
            value={sortType}
            onChange={(e) => setSortType(e.target.value)}
          >
            <option value="name_asc">İsim (A-Z)</option>
            <option value="name_desc">İsim (Z-A)</option>
            <option value="price_asc">Fiyat (Düşükten Yükseğe)</option>
            <option value="price_desc">Fiyat (Yüksekten Düşüğe)</option>
            <option value="stock_asc">Stok (En Az)</option>
            <option value="stock_desc">Stok (En Çok)</option>
          </select>

          <div style={{ marginLeft: 'auto', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            {sortedProducts.length} ürün listeleniyor
          </div>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>SKU (Kod)</th>
              <th>Ürün Adı</th>
              <th>Fiyat</th>
              <th>Durum</th>
              <th>Mevcut Stok</th>
              <th style={{ textAlign: 'right' }}>İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}>Yükleniyor...</td></tr>
            ) : sortedProducts.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}>Aramanıza uygun ürün bulunamadı.</td></tr>
            ) : (
              sortedProducts.map((product) => (
                <tr key={product.id}>
                  <td style={{ fontWeight: 500 }}>{product.sku}</td>
                  <td>{product.name}</td>
                  <td>{product.price} ₺</td>
                  <td>
                    <span className={`badge ${product.stock > 0 ? (product.stock < 5 ? 'badge-yellow' : 'badge-green') : 'badge-red'}`}>
                      {product.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{product.stock}</td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <button 
                        className="btn btn-sm btn-secondary" 
                        onClick={() => openEditModal(product)}
                      >
                        Düzenle
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {editingProduct && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <div className="card animate-fade-in" style={{ width: '400px', backgroundColor: '#fff', borderRadius: '0.75rem' }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Ürünü Düzenle</h3>
            <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
              {editingProduct.name} ({editingProduct.sku})
            </p>
            
            <form onSubmit={handleUpdateProduct}>
              <div className="input-group">
                <label className="input-label">Fiyat (₺)</label>
                <input 
                  type="number" 
                  step="0.01"
                  className="input-field" 
                  value={editForm.price}
                  onChange={(e) => setEditForm({...editForm, price: parseFloat(e.target.value)})}
                  required
                />
              </div>
              
              <div className="input-group">
                <label className="input-label">Stok Miktarı</label>
                <input 
                  type="number" 
                  className="input-field" 
                  value={editForm.stock}
                  onChange={(e) => setEditForm({...editForm, stock: parseInt(e.target.value, 10)})}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={closeEditModal} disabled={isUpdating}>
                  İptal
                </button>
                <button type="submit" className="btn btn-primary" disabled={isUpdating}>
                  {isUpdating ? 'Senkronize Ediliyor...' : 'Kaydet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default function InventoryPage() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem' }}>Sayfa Yükleniyor...</div>}>
      <InventoryContent />
    </Suspense>
  );
}
