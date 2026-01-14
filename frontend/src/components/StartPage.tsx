import { useNavigate } from 'react-router-dom';
import './StartPage.css';
import { POPULAR_GAMES } from '../data/games';
import hardwareSeed from '../data/hardware_seed_frontend.json';

const StartPage = () => {
  const navigate = useNavigate();

  const handleStartAnalysis = () => {
    navigate('/benchmark');
  };

  return (
    <div className="start-page">
      {/* Floating background elements */}
      <div className="floating-element-1"></div>
      <div className="floating-element-2"></div>
      <div className="floating-element-3"></div>

      {/* Navigation Header */}
      <nav className="nav-header">
        <div className="nav-container">
          <div className="nav-logo">
            <span className="nav-logo-text">硬體效能分析平台</span>
          </div>
          <div className="nav-actions">
            <button
              className="nav-cta-button"
              onClick={handleStartAnalysis}
            >
              開始分析
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="badge-text">🔎 基於公開基準資料與自動化分析</span>
            </div>
            <h1 className="hero-title">
              硬體效能分析與組裝平台
            </h1>
            <p className="hero-subtitle">
              結合 FPS 基準測試、系統瓶頸分析與 PC 組裝建議的專業平台，
              幫助您打造最佳遊戲體驗與工作效能的硬體配置。
            </p>
            <div className="hero-actions">
              <button
                className="hero-primary-button"
                onClick={handleStartAnalysis}
              >
                立即開始分析
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-card">
              <div className="card-header">
                <div className="card-icon">🎮</div>
                <span className="card-title">效能分析</span>
              </div>
              <div className="card-content">
                <div className="metric">
                  <span className="metric-value">{hardwareSeed && Array.isArray(hardwareSeed.items) ? hardwareSeed.items.length : '—'}</span>
                  <span className="metric-label">硬體條目（repo）</span>
                </div>
                <div className="metric">
                  <span className="metric-value">{POPULAR_GAMES.length}</span>
                  <span className="metric-label">示例遊戲（repo）</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Consultation / Info Section */}
      <section className="consultation-section">
        <div className="consultation-container">
          <h3 className="consultation-title">諮詢與使用說明</h3>
          <p className="consultation-text">
            本站蒐集並彙整公開的硬體效能基準資料，提供 FPS 基準查詢與常見的 PC 組裝建議作為參考。網站內容以資訊分享為主，並非專業的技術或法律諮詢。
          </p>
          <p className="consultation-text">
            若您需要針對個別系統或商用部署的專業建議，請透過頁尾的「聯絡我們」與我們聯絡，我們會協助轉介或安排進一步的諮詢服務。本站不會偽造或誇大任何效能數據；所有數據來源會儘量標明來源與信心水準。
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="features-container">
          <div className="features-header">
            <h2 className="features-title">完整功能套件</h2>
            <p className="features-subtitle">
              從硬體效能分析到 PC 組裝建議，一站式解決您的硬體升級需求
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
            <div className="feature-icon-wrapper">
                <div className="feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
                    <path d="M6.5 11.5c-.83 0-1.5.67-1.5 1.5S5.67 14.5 6.5 14.5 8 13.83 8 13s-.67-1.5-1.5-1.5zM17.5 11.5c-.83 0-1.5.67-1.5 1.5S16.67 14.5 17.5 14.5 19 13.83 19 13s-.67-1.5-1.5-1.5z" />
                    <path d="M20 8.5c-.2-.6-.8-1-1.5-1h-3.1c-.7 0-1.4-.4-1.7-1L11 2.6C10.6 1.9 9.8 1.5 9 1.5H7C5.9 1.5 5 2.4 5 3.5v2C3.9 6 3 6.9 3 8v6c0 1.1.9 2 2 2h3c.6 0 1.1-.4 1.4-1l.6-1.3c.3-.6.9-1 1.6-1h4.4c.7 0 1.3.4 1.5 1l.7 1.8c.2.6.8 1 1.5 1H21c1.1 0 2-.9 2-2v-6c0-1.1-.9-2-2-2h-1z" fill-opacity="0.0"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">遊戲基準測試</h3>
              <p className="feature-description">
                提供多款熱門遊戲的 FPS 基準示例（見資料檔），
                涵蓋不同解析度與畫質設定以供參考。
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <div className="feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
                    <path d="M10 2a8 8 0 105.29 14.29l4.7 4.7 1.41-1.41-4.7-4.7A8 8 0 0010 2zm0 2a6 6 0 110 12A6 6 0 0110 4z"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">即時資料抓取</h3>
              <p className="feature-description">
                從全球各大基準測試網站即時獲取最新的硬體效能資料，
                確保分析結果的時效性。
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <div className="feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
                    <path d="M12 2a6 6 0 00-6 6v1H5a3 3 0 00-3 3v2a6 6 0 006 6h8a6 6 0 006-6v-2a3 3 0 00-3-3h-1V8a6 6 0 00-6-6z" />
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">AI 瓶頸分析</h3>
              <p className="feature-description">
                智能分析系統瓶頸，提供具體的升級建議，
                幫助您最大化投資回報。
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <div className="feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
                    <path d="M3 5h18v10H3zM2 17h20v2H2z" />
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">PC 組裝建議</h3>
              <p className="feature-description">
                根據您的預算和使用需求，提供完整的 PC 組裝配置建議，
                包含 CPU、GPU、主機板、記憶體等配件的相容性分析。
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <div className="feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
                    <path d="M13 2L3 14h7l-1 8 10-12h-7z" />
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">效能比較</h3>
              <p className="feature-description">
                支援多種硬體配置同時比較，提供直觀的效能差異視覺化圖表，
                讓您輕鬆評估升級效益。
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <div className="feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
                    <path d="M21.7 13.35l-2.05-2.05a1 1 0 00-1.41 0l-1.06 1.06a7 7 0 11-1.41-1.41l1.06-1.06a1 1 0 000-1.41L10.65 2.3 9.3 3.65l6.36 6.36a1 1 0 001.41 0l1.06-1.06a7 7 0 011.41 1.41l-1.06 1.06a1 1 0 000 1.41l2.05 2.05-1.41 1.41z" />
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">硬體相容性檢查</h3>
              <p className="feature-description">
                檢查硬體配件的相容性，包括電源供應、散熱需求、機殼尺寸等，
                避免組裝時的相容性問題。
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-container">
          <div className="stat-item">
            <div className="stat-number">{POPULAR_GAMES.length}</div>
            <div className="stat-label">示例遊戲數（repo）</div>
          </div>
          {hardwareSeed && Array.isArray((hardwareSeed as any).items) && (hardwareSeed as any).items.length > 0 && (
            <div className="stat-item">
              <div className="stat-number">{(hardwareSeed as any).items.length}</div>
              <div className="stat-label">硬體條目數（repo）</div>
            </div>
          )}
          <div className="stat-item">
            <div className="stat-number">來源標註</div>
            <div className="stat-label">資料來源會標明於結果</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">持續更新</div>
            <div className="stat-label">資料與抓取腳本會定期更新</div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <h2 className="cta-title">準備好打造您的夢想 PC 了嗎？</h2>
          <p className="cta-description">
            無論是遊戲玩家還是內容創作者，讓我們幫助您找到最佳的硬體配置方案。
          </p>
          <button
            className="cta-button"
            onClick={handleStartAnalysis}
          >
            開始免費分析
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <div className="footer-content">
            <div className="footer-logo">
              <span className="footer-logo-text">硬體效能分析平台</span>
            </div>
            <div className="footer-links">
              <a href="#" className="footer-link">關於我們</a>
              <a href="#" className="footer-link">隱私政策</a>
              <a href="#" className="footer-link">使用條款</a>
              <a href="#" className="footer-link">聯絡我們</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p className="footer-copyright">
              © 2024 硬體效能分析平台. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default StartPage;