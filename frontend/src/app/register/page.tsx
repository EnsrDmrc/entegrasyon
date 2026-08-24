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
  const [step, setStep] = useState(1);
  const [verificationCode, setVerificationCode] = useState('');
  const [registeredEmail, setRegisteredEmail] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      
      if (!response.ok) {
        if (response.status === 403 || data.status === 'verification_required') {
          // Zaten kayıtlı ama onaylanmamış
          setRegisteredEmail(data.email || formData.email);
          setSuccessMsg(data.message || 'Lütfen e-postanıza gönderilen 6 haneli kodu girin.');
          setStep(2);
          return;
        }
        throw new Error(data.detail || 'Kayıt başarısız');
      }

      if (data.status === 'verification_required') {
        setRegisteredEmail(data.email || formData.email);
        setSuccessMsg('Kayıt başarılı! Lütfen e-postanıza gönderilen 6 haneli kodu girin.');
        setStep(2);
      } else {
        // Eski sisteme göre anında token dönerse (fallback)
        localStorage.setItem('token', data.access_token);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: registeredEmail, code: verificationCode })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Doğrulama başarısız');
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
        {successMsg && <div className="badge badge-green" style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>{successMsg}</div>}

        {step === 1 ? (
          <form onSubmit={handleRegister}>
            <div className="input-group">
              <label className="input-label">Mağaza Adı</label>
              <input 
                type="text" 
                className="input-field" 
                placeholder="Örn: Benim Mağazam"
                value={formData.tenant_name}
                onChange={e => setFormData({...formData, tenant_name: e.target.value})}
                required
              />
            </div>
            
            <div className="input-group">
              <label className="input-label">E-Posta Adresi</label>
              <input 
                type="email" 
                className="input-field" 
                placeholder="ornek@sirket.com"
                value={formData.email}
                onChange={e => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>

            <div className="input-group">
              <label className="input-label">Şifre</label>
              <input 
                type="password" 
                className="input-field" 
                placeholder="••••••••"
                value={formData.password}
                onChange={e => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Hesap Oluşturuluyor...' : 'Ücretsiz Hesap Oluştur'}
            </button>
            
            <div style={{ marginTop: '1.5rem', fontSize: '0.875rem', textAlign: 'center' }}>
              Zaten bir hesabınız var mı? <Link href="/login" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>Giriş Yap</Link>
            </div>
          </form>
        ) : (
          <form onSubmit={handleVerify}>
            <div className="input-group">
              <label className="input-label">Doğrulama Kodu</label>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                <b>{registeredEmail}</b> adresine gönderilen 6 haneli kodu girin.
              </p>
              <input 
                type="text" 
                className="input-field" 
                placeholder="123456"
                value={verificationCode}
                onChange={e => setVerificationCode(e.target.value)}
                maxLength={6}
                style={{ textAlign: 'center', letterSpacing: '10px', fontSize: '1.25rem', fontWeight: 'bold' }}
                required
              />
            </div>
            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Doğrulanıyor...' : 'Doğrula ve Giriş Yap'}
            </button>
            <div style={{ marginTop: '1rem', textAlign: 'center', cursor: 'pointer' }} onClick={() => setStep(1)}>
              <span style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600, fontSize: '0.875rem' }}>← Geri Dön</span>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
