"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    tenant_name: '',
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Kayıt başarısız');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container animate-fade-in">
      <div className="login-box">
        <h1 className="login-title">Yeni Hesap Oluştur</h1>
        <p className="login-subtitle">Sistemi kullanmaya başlamak için mağazanızı kaydedin</p>

        {error && <div className="badge badge-red" style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>{error}</div>}

        <form onSubmit={handleRegister}>
          <div className="input-group">
            <label className="input-label" htmlFor="tenant_name">Mağaza Adı</label>
            <input 
              id="tenant_name" 
              type="text" 
              className="input-field" 
              placeholder="Örn: Teknoloji Dünyası" 
              value={formData.tenant_name}
              onChange={(e) => setFormData({...formData, tenant_name: e.target.value})}
              required 
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="email">E-posta Adresi</label>
            <input 
              id="email" 
              type="email" 
              className="input-field" 
              placeholder="admin@magaza.com" 
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required 
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">Şifre</label>
            <input 
              id="password" 
              type="password" 
              className="input-field" 
              placeholder="••••••••" 
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required 
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
            disabled={loading}
          >
            {loading ? 'Kayıt Yapılıyor...' : 'Kayıt Ol'}
          </button>
        </form>
        
        <div style={{ marginTop: '1.5rem', fontSize: '0.875rem' }}>
          Zaten hesabınız var mı? <Link href="/login" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>Giriş Yap</Link>
        </div>
      </div>
    </div>
  );
}
