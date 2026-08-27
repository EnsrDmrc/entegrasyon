"use client";

import React, { useState, useEffect } from 'react';
import { apiFetch } from '@/utils/api';

export default function SettingsPage() {
  const [formData, setFormData] = useState({
    new_password: '',
    confirm_password: '',
    code: ''
  });
  const [passwordStep, setPasswordStep] = useState(1);
  
  const [shopifyData, setShopifyData] = useState({
    store_url: '',
    api_key: ''
  });

  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<{type: 'error' | 'success', text: string} | null>(null);
  const [shopifyMessage, setShopifyMessage] = useState<{type: 'error' | 'success', text: string} | null>(null);

  
  const [amazonData, setAmazonData] = useState({
    seller_id: '',
    client_id: '',
    client_secret: '',
    refresh_token: '',
    region: 'EU'
  });
  const [amazonSyncing, setAmazonSyncing] = useState(false);
  const [amazonOrderSyncing, setAmazonOrderSyncing] = useState(false);
  const [amazonMessage, setAmazonMessage] = useState<{type: 'error' | 'success', text: string} | null>(null);

  
  const [pazaramaData, setPazaramaData] = useState({
    merchant_id: '',
    api_key: '',
    api_secret: ''
  });
  const [pazaramaSyncing, setPazaramaSyncing] = useState(false);
  const [pazaramaOrderSyncing, setPazaramaOrderSyncing] = useState(false);
  const [pazaramaMessage, setPazaramaMessage] = useState<{type: 'error' | 'success', text: string} | null>(null);

  const [n11Data, setN11Data] = useState({
    api_key: '',
    api_secret: ''
  });
  const [n11Syncing, setN11Syncing] = useState(false);
  const [n11OrderSyncing, setN11OrderSyncing] = useState(false);
  const [n11Message, setN11Message] = useState<{type: 'error' | 'success', text: string} | null>(null);

  const [hepsiburadaData, setHepsiburadaData] = useState({
    merchant_id: '',
    api_key: ''
  });
  const [hepsiburadaSyncing, setHepsiburadaSyncing] = useState(false);
  const [hepsiburadaOrderSyncing, setHepsiburadaOrderSyncing] = useState(false);
  const [hepsiburadaMessage, setHepsiburadaMessage] = useState<{type: 'error' | 'success', text: string} | null>(null);

  const [trendyolData, setTrendyolData] = useState({
    supplier_id: '',
    api_key: '',
    api_secret: ''
  });
  const [trendyolSyncing, setTrendyolSyncing] = useState(false);
  const [trendyolOrderSyncing, setTrendyolOrderSyncing] = useState(false);
  const [trendyolMessage, setTrendyolMessage] = useState<{type: 'error' | 'success', text: string} | null>(null);

  useEffect(() => {
    // Mevcut entegrasyonları getir
    const token = localStorage.getItem('token');
    if (token) {
      apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          const shopify = data.find(i => i.marketplace_name === 'shopify');
          if (shopify) {
            setShopifyData({ store_url: shopify.store_url || '', api_key: '********' }); // Şifreyi gizli göster
          }
          
          const amazon = data.find((i: any) => i.marketplace_name === 'amazon');
          if (amazon) {
            let region = 'EU';
            let seller_id = amazon.store_url || '';
            if (seller_id.includes('|')) {
               const parts = seller_id.split('|');
               region = parts[0];
               seller_id = parts[1];
            }
            setAmazonData({ 
              seller_id: seller_id, 
              client_id: amazon.api_key ? '********' : '',
              client_secret: amazon.api_secret ? '********' : '',
              refresh_token: amazon.refresh_token ? '********' : '', 
              region: region 
            });
          }
          
          const pazarama = data.find((i: any) => i.marketplace_name === 'pazarama');
          if (pazarama) {
            setPazaramaData({ merchant_id: pazarama.store_url || '', api_key: '********', api_secret: pazarama.api_secret ? '********' : '' });
          }

          const n11 = data.find(i => i.marketplace_name === 'n11');
          if (n11) {
            setN11Data({ api_key: '********', api_secret: '********' });
          }
          const hepsiburada = data.find(i => i.marketplace_name === 'hepsiburada');
          if (hepsiburada) {
            setHepsiburadaData({ merchant_id: hepsiburada.store_url || '', api_key: '********' });
          }
          const trendyol = data.find(i => i.marketplace_name === 'trendyol');
          if (trendyol) {
            setTrendyolData({ supplier_id: trendyol.store_url || '', api_key: '********', api_secret: '********' });
          }
        }
      })
      .catch(console.error);
    }
  }, []);

  const handleSyncShopify = async () => {
    setSyncing(true);
    setShopifyMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/shopify`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Senkronizasyon başarısız');
      }
      setShopifyMessage({ type: 'success', text: `${data.count} ürün senkronize edildi!` });
    } catch (error: any) {
      setShopifyMessage({ type: 'error', text: error.message });
    } finally {
      setSyncing(false);
      setTimeout(() => setShopifyMessage(null), 5000);
    }
  };

  const handleRequestPasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/request-password-change`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Kod gönderilemedi');
      }

      setMessage({ type: 'success', text: 'E-posta adresinize doğrulama kodu gönderildi.' });
      setPasswordStep(2);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (formData.new_password !== formData.confirm_password) {
      setMessage({ type: 'error', text: 'Yeni şifreler uyuşmuyor!' });
      return;
    }

    setLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          code: formData.code,
          new_password: formData.new_password
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Şifre değiştirilemedi');
      }

      setMessage({ type: 'success', text: 'Şifreniz başarıyla değiştirildi!' });
      setFormData({ new_password: '', confirm_password: '', code: '' });
      setPasswordStep(1);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveShopify = async (e: React.FormEvent) => {
    e.preventDefault();
    setShopifyMessage(null);
    
    // Shopify Token Validation
    if (!shopifyData.api_key.includes('*')) {
      const shopifyKeyRegex = /^shpat_[a-f0-9]{32}$/i;
      if (!shopifyKeyRegex.test(shopifyData.api_key)) {
        setShopifyMessage({ type: 'error', text: 'Geçersiz Shopify Access Token formatı! (shpat_... ile başlamalı ve 38 karakter olmalı)' });
        return;
      }
    }

    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          marketplace_name: 'shopify',
          store_url: shopifyData.store_url,
          api_key: shopifyData.api_key.includes('*') ? undefined : shopifyData.api_key,
          is_active: true
        })
      });

      if (!response.ok) throw new Error('Kaydedilemedi');
      setShopifyMessage({ type: 'success', text: 'Shopify bilgileri kaydedildi!' });
    } catch (err: any) {
      setShopifyMessage({ type: 'error', text: err.message });
    }
  };

  const [activeTab, setActiveTab] = useState<'integrations' | 'ecommerce' | 'account'>('integrations');
  const [selectedMarketplace, setSelectedMarketplace] = useState<'n11' | 'trendyol' | 'hepsiburada' | 'amazon' | 'pazarama' | null>(null);
  const [selectedEcommerce, setSelectedEcommerce] = useState<'shopify' | null>(null);

  const [orderSyncing, setOrderSyncing] = useState(false);

  const handleSyncShopifyOrders = async () => {
    setOrderSyncing(true);
    setShopifyMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/shopify/orders`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sipariş senkronizasyonu başarısız');
      }
      setShopifyMessage({ type: 'success', text: `${data.order_count} sipariş başarıyla çekildi/güncellendi!` });
    } catch (error: any) {
      setShopifyMessage({ type: 'error', text: error.message });
    } finally {
      setOrderSyncing(false);
      setTimeout(() => setShopifyMessage(null), 5000);
    }
  };

  
  const handleSaveAmazon = async (e: React.FormEvent) => {
    e.preventDefault();
    setAmazonMessage(null);

    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          marketplace_name: 'amazon',
          store_url: `${amazonData.region}|${amazonData.seller_id}`,
          api_key: amazonData.client_id.includes('*') ? undefined : amazonData.client_id,
          api_secret: amazonData.client_secret.includes('*') ? undefined : amazonData.client_secret,
          refresh_token: amazonData.refresh_token.includes('*') ? undefined : amazonData.refresh_token,
          is_active: true
        })
      });

      if (!response.ok) throw new Error('Kaydedilemedi');
      setAmazonMessage({ type: 'success', text: 'Amazon bilgileri kaydedildi!' });
    } catch (err: any) {
      setAmazonMessage({ type: 'error', text: err.message });
    }
  };

  const handleSyncAmazon = async () => {
    setAmazonSyncing(true);
    setAmazonMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/amazon`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Senkronizasyon başarısız');
      }
      setAmazonMessage({ type: 'success', text: `${data.message}` });
    } catch (error: any) {
      setAmazonMessage({ type: 'error', text: error.message });
    } finally {
      setAmazonSyncing(false);
      setTimeout(() => setAmazonMessage(null), 5000);
    }
  };

  const handleSyncAmazonOrders = async () => {
    setAmazonOrderSyncing(true);
    setAmazonMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/amazon/orders`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sipariş senkronizasyonu başarısız');
      }
      setAmazonMessage({ type: 'success', text: `${data.order_count} sipariş başarıyla çekildi/güncellendi!` });
    } catch (error: any) {
      setAmazonMessage({ type: 'error', text: error.message });
    } finally {
      setAmazonOrderSyncing(false);
      setTimeout(() => setAmazonMessage(null), 5000);
    }
  };

  
  const handleSavePazarama = async (e: React.FormEvent) => {
    e.preventDefault();
    setPazaramaMessage(null);

    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          marketplace_name: 'pazarama',
          store_url: pazaramaData.merchant_id,
          api_key: pazaramaData.api_key.includes('*') ? undefined : pazaramaData.api_key,
          api_secret: pazaramaData.api_secret.includes('*') ? undefined : pazaramaData.api_secret,
          is_active: true
        })
      });

      if (!response.ok) throw new Error('Kaydedilemedi');
      setPazaramaMessage({ type: 'success', text: 'Pazarama bilgileri kaydedildi!' });
    } catch (err: any) {
      setPazaramaMessage({ type: 'error', text: err.message });
    }
  };

  const handleSyncPazarama = async () => {
    setPazaramaSyncing(true);
    setPazaramaMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/pazarama`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Senkronizasyon başarısız');
      }
      setPazaramaMessage({ type: 'success', text: `${data.message}` });
    } catch (error: any) {
      setPazaramaMessage({ type: 'error', text: error.message });
    } finally {
      setPazaramaSyncing(false);
      setTimeout(() => setPazaramaMessage(null), 5000);
    }
  };

  const handleSyncPazaramaOrders = async () => {
    setPazaramaOrderSyncing(true);
    setPazaramaMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/pazarama/orders`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sipariş senkronizasyonu başarısız');
      }
      setPazaramaMessage({ type: 'success', text: `${data.order_count} sipariş başarıyla çekildi/güncellendi!` });
    } catch (error: any) {
      setPazaramaMessage({ type: 'error', text: error.message });
    } finally {
      setPazaramaOrderSyncing(false);
      setTimeout(() => setPazaramaMessage(null), 5000);
    }
  };

  const handleSaveN11 = async (e: React.FormEvent) => {
    e.preventDefault();
    setN11Message(null);

    // N11 Key Validation (AppKey is usually UUID, AppSecret length varies)
    const n11KeyRegex = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
    
    if (!n11Data.api_key.includes('*') && !n11KeyRegex.test(n11Data.api_key)) {
      setN11Message({ type: 'error', text: 'Geçersiz N11 AppKey formatı! (36 karakterli UUID olmalı)' });
      return;
    }
    
    if (!n11Data.api_secret.includes('*') && n11Data.api_secret.length < 10) {
      setN11Message({ type: 'error', text: 'Geçersiz N11 AppSecret formatı! (Çok kısa)' });
      return;
    }

    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          marketplace_name: 'n11',
          api_key: n11Data.api_key.includes('*') ? undefined : n11Data.api_key,
          api_secret: n11Data.api_secret.includes('*') ? undefined : n11Data.api_secret,
          is_active: true
        })
      });

      if (!response.ok) throw new Error('Kaydedilemedi');
      setN11Message({ type: 'success', text: 'N11 bilgileri kaydedildi!' });
    } catch (err: any) {
      setN11Message({ type: 'error', text: err.message });
    }
  };

  const handleSyncN11 = async () => {
    setN11Syncing(true);
    setN11Message(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/n11`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Senkronizasyon başarısız');
      }
      setN11Message({ type: 'success', text: `${data.count} ürün senkronize edildi!` });
    } catch (error: any) {
      setN11Message({ type: 'error', text: error.message });
    } finally {
      setN11Syncing(false);
      setTimeout(() => setN11Message(null), 5000);
    }
  };

  const handleClearOrders = async () => {
    if (!window.confirm("Tüm sipariş geçmişini silmek istediğinize emin misiniz? Bu işlem geri alınamaz!")) return;
    
    setN11OrderSyncing(true);
    setN11Message(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/me/orders`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Siparişler silinemedi');
      }
      setN11Message({ type: 'success', text: data.message });
    } catch (error: any) {
      setN11Message({ type: 'error', text: error.message });
    } finally {
      setN11OrderSyncing(false);
      setTimeout(() => setN11Message(null), 5000);
    }
  };

  const handleSyncN11Orders = async () => {
    setN11OrderSyncing(true);
    setN11Message(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/n11/orders`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sipariş senkronizasyonu başarısız');
      }
      setN11Message({ type: 'success', text: `${data.order_count} sipariş başarıyla çekildi/güncellendi!` });
    } catch (error: any) {
      setN11Message({ type: 'error', text: error.message });
    } finally {
      setN11OrderSyncing(false);
      setTimeout(() => setN11Message(null), 5000);
    }
  };

  const handleSaveHepsiburada = async (e: React.FormEvent) => {
    e.preventDefault();
    setHepsiburadaMessage(null);

    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          marketplace_name: 'hepsiburada',
          store_url: hepsiburadaData.merchant_id, // Merchant ID'yi store_url'e kaydediyoruz
          api_key: hepsiburadaData.api_key.includes('*') ? undefined : hepsiburadaData.api_key,
          is_active: true
        })
      });

      if (!response.ok) throw new Error('Kaydedilemedi');
      setHepsiburadaMessage({ type: 'success', text: 'Hepsiburada bilgileri kaydedildi!' });
    } catch (err: any) {
      setHepsiburadaMessage({ type: 'error', text: err.message });
    }
  };

  const handleSyncHepsiburada = async () => {
    setHepsiburadaSyncing(true);
    setHepsiburadaMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/hepsiburada`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Senkronizasyon başarısız');
      }
      setHepsiburadaMessage({ type: 'success', text: `${data.count} ürün senkronize edildi!` });
    } catch (error: any) {
      setHepsiburadaMessage({ type: 'error', text: error.message });
    } finally {
      setHepsiburadaSyncing(false);
      setTimeout(() => setHepsiburadaMessage(null), 5000);
    }
  };

  const handleSyncHepsiburadaOrders = async () => {
    setHepsiburadaOrderSyncing(true);
    setHepsiburadaMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/hepsiburada/orders`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sipariş senkronizasyonu başarısız');
      }
      setHepsiburadaMessage({ type: 'success', text: `${data.order_count} sipariş başarıyla çekildi/güncellendi!` });
    } catch (error: any) {
      setHepsiburadaMessage({ type: 'error', text: error.message });
    } finally {
      setHepsiburadaOrderSyncing(false);
      setTimeout(() => setHepsiburadaMessage(null), 5000);
    }
  };

  const handleSaveTrendyol = async (e: React.FormEvent) => {
    e.preventDefault();
    setTrendyolMessage(null);

    const token = localStorage.getItem('token');
    
    try {
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          marketplace_name: 'trendyol',
          store_url: trendyolData.supplier_id,
          api_key: trendyolData.api_key.includes('*') ? undefined : trendyolData.api_key,
          api_secret: trendyolData.api_secret.includes('*') ? undefined : trendyolData.api_secret,
          is_active: true
        })
      });

      if (!response.ok) throw new Error('Kaydedilemedi');
      setTrendyolMessage({ type: 'success', text: 'Trendyol bilgileri kaydedildi!' });
    } catch (err: any) {
      setTrendyolMessage({ type: 'error', text: err.message });
    }
  };

  const handleSyncTrendyol = async () => {
    setTrendyolSyncing(true);
    setTrendyolMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/trendyol`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Senkronizasyon başarısız');
      }
      setTrendyolMessage({ type: 'success', text: `${data.count} ürün senkronize edildi!` });
    } catch (error: any) {
      setTrendyolMessage({ type: 'error', text: error.message });
    } finally {
      setTrendyolSyncing(false);
      setTimeout(() => setTrendyolMessage(null), 5000);
    }
  };

  const handleSyncTrendyolOrders = async () => {
    setTrendyolOrderSyncing(true);
    setTrendyolMessage(null);
    try {
      const token = localStorage.getItem('token');
      const response = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/integrations/sync/trendyol/orders`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sipariş senkronizasyonu başarısız');
      }
      setTrendyolMessage({ type: 'success', text: `${data.order_count} sipariş başarıyla çekildi/güncellendi!` });
    } catch (error: any) {
      setTrendyolMessage({ type: 'error', text: error.message });
    } finally {
      setTrendyolOrderSyncing(false);
      setTimeout(() => setTrendyolMessage(null), 5000);
    }
  };

  return (
    <>
      <h1 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '1.5rem' }}>Ayarlar</h1>

      <div style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
        {/* Kategoriler Menüsü */}
        <div className="card" style={{ width: '260px', padding: '1rem', position: 'sticky', top: '2rem' }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '1rem', paddingLeft: '0.5rem' }}>
            Kategoriler
          </h3>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button 
              className={`btn ${activeTab === 'integrations' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ justifyContent: 'flex-start', border: activeTab === 'integrations' ? 'none' : '1px solid transparent', padding: '0.75rem 1rem' }}
              onClick={() => setActiveTab('integrations')}
            >
              Pazaryeri Entegrasyonları
            </button>
            <button 
              className={`btn ${activeTab === 'ecommerce' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ justifyContent: 'flex-start', border: activeTab === 'ecommerce' ? 'none' : '1px solid transparent', padding: '0.75rem 1rem' }}
              onClick={() => setActiveTab('ecommerce')}
            >
              E-Ticaret Altyapısı
            </button>
            <button 
              className={`btn ${activeTab === 'account' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ justifyContent: 'flex-start', border: activeTab === 'account' ? 'none' : '1px solid transparent', padding: '0.75rem 1rem' }}
              onClick={() => setActiveTab('account')}
            >
              Hesap ve Güvenlik
            </button>
          </nav>
        </div>

        {/* Aktif Kategori İçeriği */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {activeTab === 'account' && (
            <div className="card animate-fade-in">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Şifre Değiştir</h3>
              
              {message && (
                <div className={`badge ${message.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                  {message.text}
                </div>
              )}

              {passwordStep === 1 ? (
                <form onSubmit={handleRequestPasswordChange}>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                    Şifrenizi değiştirmek için kayıtlı e-posta adresinize bir doğrulama kodu gönderilecektir.
                  </p>
                  <button 
                    type="submit" 
                    className="btn btn-primary" 
                    disabled={loading}
                  >
                    {loading ? 'İşleniyor...' : 'Şifre Değiştirme Kodu Gönder'}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleChangePassword}>
                  <div className="input-group">
                    <label className="input-label">Doğrulama Kodu</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="123456"
                      value={formData.code}
                      onChange={(e) => setFormData({...formData, code: e.target.value})}
                      maxLength={6}
                      style={{ letterSpacing: '2px' }}
                      required
                    />
                  </div>
                  
                  <div className="input-group">
                    <label className="input-label">Yeni Şifre</label>
                    <input 
                      type="password" 
                      className="input-field" 
                      value={formData.new_password}
                      onChange={(e) => setFormData({...formData, new_password: e.target.value})}
                      required
                    />
                  </div>

                  <div className="input-group">
                    <label className="input-label">Yeni Şifre (Tekrar)</label>
                    <input 
                      type="password" 
                      className="input-field" 
                      value={formData.confirm_password}
                      onChange={(e) => setFormData({...formData, confirm_password: e.target.value})}
                      required
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                    <button 
                      type="submit" 
                      className="btn btn-primary" 
                      disabled={loading}
                    >
                      {loading ? 'Güncelleniyor...' : 'Şifreyi Güncelle'}
                    </button>
                    <button 
                      type="button" 
                      className="btn btn-secondary" 
                      onClick={() => setPasswordStep(1)}
                      disabled={loading}
                    >
                      İptal
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="card animate-fade-in">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Pazaryeri Entegrasyonları</h3>
              
              {selectedMarketplace === null ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1rem' }}>

                  <div className="card" onClick={() => setSelectedMarketplace('pazarama')} style={{ cursor: 'pointer', padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', backgroundColor: '#f8fafc', transition: 'all 0.2s' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Pazarama</h4>
                       {pazaramaData.merchant_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                     </div>
                     <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>Pazarama Mağaza ID ve API bilgilerinizi girerek entegre olun.</p>
                  </div>

                  
                  <div className="card" onClick={() => setSelectedMarketplace('amazon')} style={{ cursor: 'pointer', padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', backgroundColor: '#f8fafc', transition: 'all 0.2s' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Amazon</h4>
                       {amazonData.seller_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                     </div>
                     <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>Amazon Seller ID ve Refresh Token girerek entegre olun.</p>
                  </div>

                  <div className="card" onClick={() => setSelectedMarketplace('n11')} style={{ cursor: 'pointer', padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', backgroundColor: '#f8fafc', transition: 'all 0.2s' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>N11</h4>
                       {n11Data.api_key ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                     </div>
                     <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>N11 API bilgilerinizi girmek veya güncellemek için tıklayın.</p>
                  </div>

                  <div className="card" onClick={() => setSelectedMarketplace('trendyol')} style={{ cursor: 'pointer', padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', backgroundColor: '#f8fafc', transition: 'all 0.2s' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Trendyol</h4>
                       {trendyolData.supplier_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                     </div>
                     <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>Trendyol API bilgilerinizi girmek veya güncellemek için tıklayın.</p>
                  </div>

                  <div className="card" onClick={() => setSelectedMarketplace('hepsiburada')} style={{ cursor: 'pointer', padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', backgroundColor: '#f8fafc', transition: 'all 0.2s' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Hepsiburada</h4>
                       {hepsiburadaData.merchant_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                     </div>
                     <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>Hepsiburada API bilgilerinizi girmek veya güncellemek için tıklayın.</p>
                  </div>

                </div>
              ) : (
                <div>
                  <button onClick={() => setSelectedMarketplace(null)} className="btn btn-secondary" style={{ marginBottom: '1.5rem' }}>← Geri Dön</button>
                  
                  {selectedMarketplace === 'amazon' && (
              <div style={{ padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', marginBottom: '1rem', backgroundColor: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Amazon Bağlantısı</h4>
                  {amazonData.seller_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  Amazon SP-API yetkilendirme bilgilerinizi girerek ürün ve siparişlerinizi senkronize edebilirsiniz.
                </p>
                
                {amazonMessage && (
                  <div className={`badge ${amazonMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                    {amazonMessage.text}
                  </div>
                )}

                <form onSubmit={handleSaveAmazon}>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Client ID</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="amzn1.application-oa2-client..." 
                      value={amazonData.client_id}
                      onChange={(e) => setAmazonData({...amazonData, client_id: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Client Secret</label>
                    <input 
                      type="password" 
                      className="input-field" 
                      placeholder="Gizli Anahtarınız..." 
                      value={amazonData.client_secret}
                      onChange={(e) => setAmazonData({...amazonData, client_secret: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Seller ID (Merchant ID)</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Örn: A2Q3Y26CGQ..." 
                      value={amazonData.seller_id}
                      onChange={(e) => setAmazonData({...amazonData, seller_id: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Refresh Token</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Atzr|IwEBI..." 
                      value={amazonData.refresh_token}
                      onChange={(e) => setAmazonData({...amazonData, refresh_token: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Amazon Bölgesi (Region)</label>
                    <select 
                      className="input-field" 
                      value={amazonData.region}
                      onChange={(e) => setAmazonData({...amazonData, region: e.target.value})}
                      required
                    >
                      <option value="EU">Avrupa (Türkiye Dahil)</option>
                      <option value="NA">Kuzey Amerika</option>
                      <option value="FE">Uzak Doğu</option>
                    </select>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <button type="submit" className="btn btn-primary">Bilgileri Kaydet</button>
                    {amazonData.seller_id && (
                      <>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncAmazon}
                          disabled={amazonSyncing || amazonOrderSyncing}
                        >
                          {amazonSyncing ? 'Ürünler Çekiliyor...' : 'Tüm Ürünleri Çek'}
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncAmazonOrders}
                          disabled={amazonSyncing || amazonOrderSyncing}
                          style={{ backgroundColor: '#f1f5f9', color: '#334155' }}
                        >
                          {amazonOrderSyncing ? 'Siparişler Çekiliyor...' : 'Tüm Siparişleri Çek'}
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </div>
                  )}

                  
                  {selectedMarketplace === 'pazarama' && (
              <div style={{ padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', marginBottom: '1rem', backgroundColor: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Pazarama Bağlantısı</h4>
                  {pazaramaData.merchant_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  Pazarama mağaza yetkilendirme bilgilerinizi girerek ürün ve siparişlerinizi senkronize edebilirsiniz.
                </p>
                
                {pazaramaMessage && (
                  <div className={`badge ${pazaramaMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                    {pazaramaMessage.text}
                  </div>
                )}

                <form onSubmit={handleSavePazarama}>
                  <div className="input-group">
                    <label className="input-label">Mağaza ID (Merchant ID)</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Örn: 123456" 
                      value={pazaramaData.merchant_id}
                      onChange={(e) => setPazaramaData({...pazaramaData, merchant_id: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1rem' }}>
                    <label className="input-label">Client ID (API Key)</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Client ID (API Key)" 
                      value={pazaramaData.api_key}
                      onChange={(e) => setPazaramaData({...pazaramaData, api_key: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Client Secret</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Client Secret" 
                      value={pazaramaData.api_secret}
                      onChange={(e) => setPazaramaData({...pazaramaData, api_secret: e.target.value})}
                      required
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <button type="submit" className="btn btn-primary">Bilgileri Kaydet</button>
                    {pazaramaData.merchant_id && (
                      <>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncPazarama}
                          disabled={pazaramaSyncing || pazaramaOrderSyncing}
                        >
                          {pazaramaSyncing ? 'Ürünler Çekiliyor...' : 'Tüm Ürünleri Çek'}
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncPazaramaOrders}
                          disabled={pazaramaSyncing || pazaramaOrderSyncing}
                          style={{ backgroundColor: '#f1f5f9', color: '#334155' }}
                        >
                          {pazaramaOrderSyncing ? 'Siparişler Çekiliyor...' : 'Tüm Siparişleri Çek'}
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </div>
                  )}

                  {selectedMarketplace === 'n11' && (
              <div style={{ padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', marginBottom: '1rem', backgroundColor: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>N11 Bağlantısı</h4>
                  {n11Data.api_key ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  N11 API bilgilerinizi (AppKey ve AppSecret) girerek ürünlerinizi senkronize edebilirsiniz.
                </p>
                
                {n11Message && (
                  <div className={`badge ${n11Message.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                    {n11Message.text}
                  </div>
                )}

                <form onSubmit={handleSaveN11}>
                  <div className="input-group">
                    <label className="input-label">AppKey</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="N11 AppKey giriniz" 
                      value={n11Data.api_key}
                      onChange={(e) => setN11Data({...n11Data, api_key: e.target.value})}
                      maxLength={36}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">AppSecret</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="N11 AppSecret giriniz" 
                      value={n11Data.api_secret}
                      onChange={(e) => setN11Data({...n11Data, api_secret: e.target.value})}
                      maxLength={64}
                      required
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <button type="submit" className="btn btn-primary">Bilgileri Kaydet</button>
                    {n11Data.api_key && (
                      <>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncN11}
                          disabled={n11Syncing || n11OrderSyncing}
                        >
                          {n11Syncing ? 'Ürünler Çekiliyor...' : 'Tüm Ürünleri Çek'}
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncN11Orders}
                          disabled={n11Syncing || n11OrderSyncing}
                          style={{ backgroundColor: '#f1f5f9', color: '#334155' }}
                        >
                          {n11OrderSyncing ? 'İşlem yapılıyor...' : 'Tüm Siparişleri Çek'}
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </div>
                  )}
                  {selectedMarketplace === 'trendyol' && (
              <div style={{ padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', marginBottom: '1rem', backgroundColor: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Trendyol Bağlantısı</h4>
                  {trendyolData.supplier_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  Trendyol Satıcı ID (Supplier ID), API Key ve API Secret bilgilerinizi girerek ürünlerinizi senkronize edebilirsiniz.
                </p>
                
                {trendyolMessage && (
                  <div className={`badge ${trendyolMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                    {trendyolMessage.text}
                  </div>
                )}

                <form onSubmit={handleSaveTrendyol}>
                  <div className="input-group">
                    <label className="input-label">Satıcı ID (Supplier ID)</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Trendyol Satıcı ID'nizi giriniz" 
                      value={trendyolData.supplier_id}
                      onChange={(e) => setTrendyolData({...trendyolData, supplier_id: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">API Key</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Trendyol API Key giriniz" 
                      value={trendyolData.api_key}
                      onChange={(e) => setTrendyolData({...trendyolData, api_key: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">API Secret</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Trendyol API Secret giriniz" 
                      value={trendyolData.api_secret}
                      onChange={(e) => setTrendyolData({...trendyolData, api_secret: e.target.value})}
                      required
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <button type="submit" className="btn btn-primary">Bilgileri Kaydet</button>
                    {trendyolData.supplier_id && (
                      <>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncTrendyol}
                          disabled={trendyolSyncing || trendyolOrderSyncing}
                        >
                          {trendyolSyncing ? 'Ürünler Çekiliyor...' : 'Tüm Ürünleri Çek'}
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncTrendyolOrders}
                          disabled={trendyolSyncing || trendyolOrderSyncing}
                          style={{ backgroundColor: '#f1f5f9', color: '#334155' }}
                        >
                          {trendyolOrderSyncing ? 'İşlem yapılıyor...' : 'Tüm Siparişleri Çek'}
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </div>
                  )}
                  {selectedMarketplace === 'hepsiburada' && (
              <div style={{ padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', marginBottom: '1rem', backgroundColor: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Hepsiburada Bağlantısı</h4>
                  {hepsiburadaData.merchant_id ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  Hepsiburada Satıcı ID (Merchant ID) ve API Şifresi (Token) bilgilerinizi girerek ürünlerinizi senkronize edebilirsiniz.
                </p>
                
                {hepsiburadaMessage && (
                  <div className={`badge ${hepsiburadaMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                    {hepsiburadaMessage.text}
                  </div>
                )}

                <form onSubmit={handleSaveHepsiburada}>
                  <div className="input-group">
                    <label className="input-label">Satıcı ID (Merchant ID)</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Hepsiburada Satıcı ID'nizi giriniz" 
                      value={hepsiburadaData.merchant_id}
                      onChange={(e) => setHepsiburadaData({...hepsiburadaData, merchant_id: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">API Şifresi</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="Hepsiburada API Şifrenizi giriniz" 
                      value={hepsiburadaData.api_key}
                      onChange={(e) => setHepsiburadaData({...hepsiburadaData, api_key: e.target.value})}
                      required
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <button type="submit" className="btn btn-primary">Bilgileri Kaydet</button>
                    {hepsiburadaData.merchant_id && (
                      <>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncHepsiburada}
                          disabled={hepsiburadaSyncing || hepsiburadaOrderSyncing}
                        >
                          {hepsiburadaSyncing ? 'Ürünler Çekiliyor...' : 'Tüm Ürünleri Çek'}
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncHepsiburadaOrders}
                          disabled={hepsiburadaSyncing || hepsiburadaOrderSyncing}
                          style={{ backgroundColor: '#f1f5f9', color: '#334155' }}
                        >
                          {hepsiburadaOrderSyncing ? 'İşlem yapılıyor...' : 'Tüm Siparişleri Çek'}
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'ecommerce' && (
            <div className="card animate-fade-in">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>E-Ticaret Altyapısı Entegrasyonları</h3>
              
              {selectedEcommerce === null ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1rem' }}>
                  <div className="card" onClick={() => setSelectedEcommerce('shopify')} style={{ cursor: 'pointer', padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', backgroundColor: '#f8fafc', transition: 'all 0.2s' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Shopify</h4>
                       {shopifyData.store_url ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                     </div>
                     <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>Shopify API bilgilerinizi girmek veya güncellemek için tıklayın.</p>
                  </div>
                </div>
              ) : (
                <div>
                  <button onClick={() => setSelectedEcommerce(null)} className="btn btn-secondary" style={{ marginBottom: '1.5rem' }}>← Geri Dön</button>
                  {selectedEcommerce === 'shopify' && (
              <div style={{ padding: '1.5rem', border: '1px solid var(--border-color)', borderRadius: '0.75rem', marginBottom: '1rem', backgroundColor: '#f8fafc' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Shopify Bağlantısı</h4>
                  {shopifyData.store_url ? <span className="badge badge-green">Aktif</span> : <span className="badge badge-red">Pasif</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  Shopify mağazanıza ait Admin API erişim bilgilerini girerek ürünlerinizi senkronize edebilirsiniz.
                </p>
                
                {shopifyMessage && (
                  <div className={`badge ${shopifyMessage.type === 'error' ? 'badge-red' : 'badge-green'}`} style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>
                    {shopifyMessage.text}
                  </div>
                )}

                <form onSubmit={handleSaveShopify}>
                  <div className="input-group">
                    <label className="input-label">Mağaza Adresi</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="magazaniz.myshopify.com" 
                      value={shopifyData.store_url}
                      onChange={(e) => setShopifyData({...shopifyData, store_url: e.target.value})}
                      required
                    />
                  </div>
                  <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="input-label">Access Token</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="shpat_xxxxxxxxxxxx" 
                      value={shopifyData.api_key}
                      onChange={(e) => setShopifyData({...shopifyData, api_key: e.target.value})}
                      maxLength={38}
                      required
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <button type="submit" className="btn btn-primary">Bilgileri Kaydet</button>
                    {shopifyData.store_url && (
                      <>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncShopify}
                          disabled={syncing || orderSyncing}
                        >
                          {syncing ? 'Ürünler Çekiliyor...' : 'Tüm Ürünleri Çek'}
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary"
                          onClick={handleSyncShopifyOrders}
                          disabled={syncing || orderSyncing}
                          style={{ backgroundColor: '#f1f5f9', color: '#334155' }}
                        >
                          {orderSyncing ? 'Siparişler Çekiliyor...' : 'Tüm Siparişleri Çek'}
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
