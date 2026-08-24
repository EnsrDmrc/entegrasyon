"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [step, setStep] = useState(1);
  const [verificationCode, setVerificationCode] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Otomatik Giriş Kontrolü
  useEffect(() => {
    const token = localStorage.getItem('token');
    const refreshToken = localStorage.getItem('refresh_token');
    if (token || refreshToken) {
      router.push('/dashboard');
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 403) {
          // Doğrulanmamış hesap
          setSuccessMsg(data.detail || 'Lütfen e-postanıza gönderilen doğrulama kodunu girin.');
          setStep(2);
          return;
        }
        throw new Error(data.detail || 'E-posta veya şifre hatalı');
      }

      localStorage.setItem('token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      router.push('/dashboard');
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
        body: JSON.stringify({ email: email, code: verificationCode })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Doğrulama başarısız');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
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
        <h1 className="login-title">Yönetim Paneli</h1>
        <p className="login-subtitle">Envanterinizi yönetmek için giriş yapın</p>

        {error && <div className="badge badge-red" style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>{error}</div>}
        {successMsg && <div className="badge badge-green" style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>{successMsg}</div>}

        {step === 1 ? (
          <form onSubmit={handleLogin}>
            <div className="input-group">
              <label className="input-label" htmlFor="email">E-posta Adresi</label>
              <input 
                id="email" 
                type="email" 
                className="input-field" 
                placeholder="admin@magaza.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
              />
            </div>

            <div className="input-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="input-label" htmlFor="password" style={{ marginBottom: 0 }}>Şifre</label>
                <Link href="/forgot-password" style={{ fontSize: '0.875rem', color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>
                  Şifremi Unuttum
                </Link>
              </div>
              <input 
                id="password" 
                type="password" 
                className="input-field" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
                style={{ marginTop: '0.5rem' }}
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Giriş Yapılıyor...' : 'Giriş Yap'}
            </button>
            
            <div style={{ marginTop: '1.5rem', fontSize: '0.875rem', textAlign: 'center' }}>
              Henüz hesabınız yok mu? <Link href="/register" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>Kayıt Ol</Link>
            </div>
          </form>
        ) : (
          <form onSubmit={handleVerify}>
            <div className="input-group">
              <label className="input-label">Doğrulama Kodu</label>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                <b>{email}</b> adresine gönderilen 6 haneli doğrulama kodunu girin.
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
            <div style={{ marginTop: '1rem', textAlign: 'center', cursor: 'pointer' }} onClick={() => {setStep(1); setSuccessMsg('');}}>
              <span style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600, fontSize: '0.875rem' }}>← Geri Dön</span>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
