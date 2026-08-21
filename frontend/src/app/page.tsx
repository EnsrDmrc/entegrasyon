import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <div className="landing-body">
      {/* Navigation */}
      <nav className="landing-nav animate-fade-in">
        <div className="landing-logo">Demircisoft</div>
        <div>
          <Link href="/login" className="landing-btn-login">
            Giriş Yap / Panele Git
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="landing-hero animate-fade-in" style={{ animationDelay: '0.1s' }}>
        <h1 className="landing-title">
          Tüm E-Ticaret Operasyonunuz <br />
          <span>Tek Ekran, Tam Kontrol</span>
        </h1>
        <p className="landing-subtitle">
          N11, Shopify ve daha fazlasını aynı anda yönetin. Stoklarınızı milisaniye hızında senkronize edin, çifte satışı sonsuza dek unutun.
        </p>

        <div className="landing-mockup-wrapper animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <Image 
            src="/dashboard-mockup-light.png" 
            alt="Demircisoft Dashboard" 
            width={1000} 
            height={562}
            className="landing-mockup-img"
            priority
          />
        </div>
      </header>

      {/* Integrations Grid Section */}
      <section className="landing-integrations animate-fade-in" style={{ animationDelay: '0.5s' }}>
        <div className="landing-integrations-container">
          <div className="integrations-grid">
            <div className="integration-card brand-trendyol">trendyol</div>
            <div className="integration-card brand-hepsiburada">hepsiburada</div>
            <div className="integration-card brand-amazon">amazon</div>
            <div className="integration-card brand-shopify">Shopify</div>
            <div className="integration-card brand-woocommerce">WooCommerce</div>
            
            <div className="integration-card brand-n11">n11</div>
            <div className="integration-card brand-pazarama">pazarama</div>
            <div className="integration-card brand-ciceksepeti">ÇiçekSepeti</div>
            <div className="integration-card brand-opencart">opencart</div>
            <div className="integration-card brand-pttavm">PttAVM</div>
          </div>
          <div className="integrations-cta">
            <Link href="/login" className="integrations-cta-btn">
              Tüm Çözüm Ortaklarımızı İnceleyin →
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="landing-features">
        <h2 className="landing-section-title">Neden Demircisoft?</h2>
        <div className="landing-grid">
          <div className="landing-card">
            <div className="landing-card-icon">🚀</div>
            <h3 className="landing-card-title">Işık Hızında Stok Senkronizasyonu</h3>
            <p className="landing-card-text">
              Dağıtık kilit (distributed lock) mimarisi ile ürününüz aynı saniyede iki farklı pazaryerinden alınsa bile stoğunuz asla eksiye düşmez.
            </p>
          </div>
          <div className="landing-card">
            <div className="landing-card-icon">📦</div>
            <h3 className="landing-card-title">Tek Merkezden Sipariş Yönetimi</h3>
            <p className="landing-card-text">
              Hangi platformdan gelirse gelsin, tüm siparişleriniz saniyeler içinde önünüzde. Sipariş devriyesi ile hiçbir satışı kaçırmayın.
            </p>
          </div>
          <div className="landing-card">
            <div className="landing-card-icon">🔄</div>
            <h3 className="landing-card-title">Otomatik Fiyat Güncelleme</h3>
            <p className="landing-card-text">
              Fiyatı ana panelden bir kez değiştirin, REST API teknolojisi ile tüm pazaryerlerine (Shopify, N11 vb.) saniyeler içinde yansısın.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© {new Date().getFullYear()} Demircisoft. Tüm hakları saklıdır.</p>
      </footer>
    </div>
  );
}
