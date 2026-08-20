export default function Home() {
  return (
    <div className="layout-container">
      <header className="glass header animate-fade-in">
        <h1 className="logo text-gradient">Nexus Integrations</h1>
        <div className="header-actions">
          <button className="btn btn-secondary">Documentation</button>
          <a href="/login" className="btn btn-primary">Dashboard</a>
        </div>
      </header>

      <main className="main-content animate-fade-in" style={{ animationDelay: '0.2s' }}>
        <h2 className="hero-title">
          Sync Your Marketplaces <br /><span className="text-gradient">in Real-Time</span>
        </h2>
        <p className="hero-subtitle">
          Centralize your inventory and orders across Shopify, n11, Trendyol, and more.
          Prevent overselling with our millisecond-accurate distributed lock system.
        </p>

        <div className="features-grid">
          <div className="glass feature-card">
            <h3>Shopify Ready</h3>
            <p>Instant webhooks and seamless inventory deduction directly connected to your Shopify store.</p>
          </div>
          <div className="glass feature-card">
            <h3>n11 Integration</h3>
            <p>Fully compliant with n11 APIs to ensure your prices and stock are always accurate.</p>
          </div>
          <div className="glass feature-card">
            <h3>Concurrency Control</h3>
            <p>Redis-backed distributed locks guarantee that the last item is never sold twice.</p>
          </div>
        </div>

        <div className="cta-container">
          <button className="btn btn-primary btn-large">
            Get Started
          </button>
        </div>
      </main>
    </div>
  );
}
