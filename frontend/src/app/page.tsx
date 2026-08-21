import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <div className="landing-body">
      {/* Navigation */}
      <nav className="landing-nav animate-fade-in">
        <div className="landing-logo">Nexus Integrations</div>
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
            alt="Nexus Integrations Dashboard" 
            width={1000} 
            height={562}
            className="landing-mockup-img"
            priority
          />
        </div>
      </header>

      {/* Marquee Section */}
      <section className="landing-marquee animate-fade-in" style={{ animationDelay: '0.5s' }}>
        <div className="landing-marquee-content">
          <span>Shopify</span>
          <span>•</span>
          <span>N11</span>
          <span>•</span>
          <span>Trendyol</span>
          <span>•</span>
          <span>Hepsiburada</span>
          <span>•</span>
          <span>WooCommerce</span>
          <span>•</span>
          <span>Amazon</span>
          <span>•</span>
          <span>Shopify</span>
          <span>•</span>
          <span>N11</span>
          <span>•</span>
          <span>Trendyol</span>
          <span>•</span>
          <span>Hepsiburada</span>
          <span>•</span>
          <span>WooCommerce</span>
          <span>•</span>
          <span>Amazon</span>
        </div>
      </section>

      {/* Features Section */}
      <section className="landing-features">
        <h2 className="landing-section-title">Neden Nexus Integrations?</h2>
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
        <p>© {new Date().getFullYear()} Nexus Integrations. Tüm hakları saklıdır.</p>
      </footer>
    </div>
  );
}
