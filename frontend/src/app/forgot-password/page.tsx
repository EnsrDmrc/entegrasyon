"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        throw new Error('Bir hata oluştu. Lütfen tekrar deneyin.');
      }

      const data = await response.json();
      setSuccessMsg(data.message || 'Şifre sıfırlama kodu gönderildi.');
      setStep(2);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code, new_password: newPassword })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Şifre sıfırlama başarısız.');
      }

      const data = await response.json();
      setSuccessMsg(data.message || 'Şifreniz başarıyla güncellendi. Giriş sayfasına yönlendiriliyorsunuz...');
      setStep(3); // Success step
      
      setTimeout(() => {
        router.push('/login');
      }, 3000);
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container animate-fade-in">
      <div className="login-box">
        <h1 className="login-title">Şifremi Unuttum</h1>
        <p className="login-subtitle">
          {step === 1 && "E-posta adresinizi girin, size şifre sıfırlama kodu gönderelim."}
          {step === 2 && "E-postanıza gelen kodu ve yeni şifrenizi girin."}
          {step === 3 && "İşlem tamamlandı!"}
        </p>

        {error && <div className="badge badge-red" style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>{error}</div>}
        {successMsg && <div className="badge badge-green" style={{ marginBottom: '1rem', display: 'block', padding: '0.75rem' }}>{successMsg}</div>}

        {step === 1 && (
          <form onSubmit={handleRequestCode}>
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

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Kod Gönderiliyor...' : 'Sıfırlama Kodu Gönder'}
            </button>
            
            <div style={{ marginTop: '1.5rem', fontSize: '0.875rem', textAlign: 'center' }}>
              <Link href="/login" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600 }}>← Giriş Sayfasına Dön</Link>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleResetPassword}>
            <div className="input-group">
              <label className="input-label">Doğrulama Kodu</label>
              <input 
                type="text" 
                className="input-field" 
                placeholder="123456"
                value={code}
                onChange={e => setCode(e.target.value)}
                maxLength={6}
                style={{ textAlign: 'center', letterSpacing: '10px', fontSize: '1.25rem', fontWeight: 'bold' }}
                required
              />
            </div>
            
            <div className="input-group">
              <label className="input-label">Yeni Şifre</label>
              <input 
                type="password" 
                className="input-field" 
                placeholder="••••••••"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Şifre Güncelleniyor...' : 'Şifreyi Güncelle'}
            </button>
            
            <div style={{ marginTop: '1rem', textAlign: 'center', cursor: 'pointer' }} onClick={() => {setStep(1); setSuccessMsg('');}}>
              <span style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600, fontSize: '0.875rem' }}>← E-posta adresini değiştir</span>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
