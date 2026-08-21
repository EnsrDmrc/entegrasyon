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
            <div className="integration-card">
              <img src="https://cdn.dsmcdn.com/web/logo/ty-web.svg" alt="Trendyol" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://images.hepsiburada.net/assets/sf/mweb/logo.svg" alt="Hepsiburada" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" alt="Amazon" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://upload.wikimedia.org/wikipedia/commons/0/0e/Shopify_logo_2018.svg" alt="Shopify" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://upload.wikimedia.org/wikipedia/commons/2/2a/WooCommerce_logo.svg" alt="WooCommerce" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            
            <div className="integration-card">
              <img src="https://n11scdn.akamaized.net/a1/org/24/07/22/27/98/08/90/13/26/66/83/87/4405908862908846313.svg" alt="N11" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://www.pazarama.com/assets/images/logo.svg" alt="Pazarama" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://cdn.ciceksepeti.com/cicek-resim/xh/ciceksepeti-logo.svg" alt="Çiçeksepeti" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://upload.wikimedia.org/wikipedia/commons/4/42/Opencart_logo.svg" alt="Opencart" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
            <div className="integration-card">
              <img src="https://cdn.pttavm.com/c/m/1722883072.svg" alt="PttAVM" style={{ maxHeight: '30px', maxWidth: '100%' }} />
            </div>
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
