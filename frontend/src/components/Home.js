// import React from 'react';
// import { useNavigate } from 'react-router-dom';
// import './Home.css';

// const Home = () => {
//   const navigate = useNavigate();

//   return (
//     <div className="home">
//       <header className="home-header layout-constrain">
//         <div className="brand">
//           <div className="brand-mark">BA</div>
//           <div className="brand-name">BankAssist<span> AI</span></div>
//         </div>
//         <nav className="home-nav">
//           <button className="btn btn-outline" onClick={() => navigate('/register')}>Open Account</button>
//           <button className="btn" onClick={() => navigate('/login')}>Login</button>
//         </nav>
//       </header>

//       <main className="home-hero layout-constrain">
//         <div className="hero-copy">
//           <h1>Modern banking, secured by you</h1>
//           <p>Face, voice and OTP authentication for seamless and secure access. Transfer money, manage beneficiaries and get instant support — all in one place.</p>
//           <div className="hero-cta">
//             <button className="btn" onClick={() => navigate('/register')}>Get Started</button>
//             <button className="btn btn-outline" onClick={() => navigate('/otp-login')}>Try OTP Login</button>
//           </div>
//           <div className="hero-highlights">
//             <span>Zero-fee transfers</span>
//             <span>AI-powered support</span>
//             <span>Bank-grade security</span>
//           </div>
//         </div>
//         <div className="hero-card u-card">
//           <div className="hero-card-header">
//             <div className="badge">Preview</div>
//             <div className="card-title">Quick Access</div>
//           </div>
//           <div className="hero-actions">
//             <button className="hero-action" onClick={() => navigate('/beneficiaries')}>Manage Beneficiaries</button>
//             <button className="hero-action" onClick={() => navigate('/transfer')}>Make a Transfer</button>
//             <button className="hero-action" onClick={() => navigate('/history')}>View Transactions</button>
//             <button className="hero-action" onClick={() => navigate('/sign-recognition')}>Customer Support</button>
//           </div>
//         </div>
//       </main>

//       <section className="home-features layout-constrain">
//         <div className="features-grid">
//           <div className="feature u-card">
//             <h3>Face Authentication</h3>
//             <p>Sign in with a glance. Fast and secure facial verification protects your account.</p>
//           </div>
//           <div className="feature u-card">
//             <h3>Voice Authentication</h3>
//             <p>Your voice is your key. Convenient access with industry-standard audio verification.</p>
//           </div>
//           <div className="feature u-card">
//             <h3>Real-time Transfers</h3>
//             <p>Send money in seconds with robust beneficiary management and instant confirmation.</p>
//           </div>
//           <div className="feature u-card">
//             <h3>AI Support</h3>
//             <p>Get help instantly with our integrated sign recognition and guided assistance.</p>
//           </div>
//         </div>
//       </section>

//       <footer className="home-footer layout-constrain">
//         <p className="u-text-soft">© {new Date().getFullYear()} BankAssist AI. All rights reserved.</p>
//       </footer>
//     </div>
//   );
// };

// export default Home;




import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home">
      {/* Enhanced Header */}
      <header className="home-header layout-constrain">
        <div className="brand">
          <div className="brand-mark">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <path d="M18 0C8.058 0 0 8.058 0 18C0 27.942 8.058 36 18 36C27.942 36 36 27.942 36 18C36 8.058 27.942 0 18 0Z" fill="url(#gradient-primary)"/>
              <path d="M24 12H12V24H24V12Z" fill="white"/>
              <path d="M15 15H21V21H15V15Z" fill="url(#gradient-primary)"/>
              <defs>
                <linearGradient id="gradient-primary" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#4361ee"/>
                  <stop offset="100%" stopColor="#3a0ca3"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="brand-name">
            BankAssist<span> AI</span>
          </div>
        </div>
        <nav className="home-nav">
        </nav>
      </header>

      {/* Enhanced Hero Section */}
      <section className="home-hero">
        <div className="hero-background">
          <div className="hero-shape shape-1"></div>
          <div className="hero-shape shape-2"></div>
          <div className="hero-shape shape-3"></div>
        </div>
        <div className="layout-constrain hero-content">
          <div className="hero-copy">
            <div className="hero-badge">
              <span>Next-Gen Banking</span>
            </div>
            <h1>Modern banking, secured by <span className="text-gradient">you</span></h1>
            <p>Face, voice and OTP authentication for seamless and secure access. Transfer money, manage beneficiaries and get instant support — all in one place.</p>
            <div className="hero-cta">
              <button className="btn btn-primary" onClick={() => navigate('/register')}>
                <span>Create an Account</span>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 0L6.59 1.41L12.17 7H0V9H12.17L6.59 14.59L8 16L16 8L8 0Z" fill="currentColor"/>
                </svg>
              </button>
              <button className="btn btn-outline" onClick={() => navigate('/login')}>
                Login to Your Account
              </button>
            </div>
            <div className="hero-highlights">
              <div className="highlight-item">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#10b981"/>
                </svg>
                <span>Zero-fee transfers</span>
              </div>
              <div className="highlight-item">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#10b981"/>
                </svg>
                <span>AI-powered support</span>
              </div>
              <div className="highlight-item">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#10b981"/>
                </svg>
                <span>Bank-grade security</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Features Section */}
      <section className="home-features">
        <div className="layout-constrain">
          <div className="section-header">
            <h2>Why Choose BankAssist AI?</h2>
            <p>Experience the future of banking with our cutting-edge features</p>
          </div>
          <div className="features-grid">
            <div className="feature u-card">
              <div className="feature-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M24 4C13 4 4 13 4 24C4 35 13 44 24 44C35 44 44 35 44 24C44 13 35 4 24 4ZM24 8C32.84 8 40 15.16 40 24C40 32.84 32.84 40 24 40C15.16 40 8 32.84 8 24C8 15.16 15.16 8 24 8ZM24 12C18.48 12 14 16.48 14 22C14 27.52 18.48 32 24 32C29.52 32 34 27.52 34 22C34 16.48 29.52 12 24 12ZM24 16C27.32 16 30 18.68 30 22C30 25.32 27.32 28 24 28C20.68 28 18 25.32 18 22C18 18.68 20.68 16 24 16Z" fill="url(#gradient-primary)"/>
                </svg>
              </div>
              <h3>Face Authentication</h3>
              <p>Sign in with a glance. Fast and secure facial verification protects your account.</p>
            </div>
            <div className="feature u-card">
              <div className="feature-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M24 4C13 4 4 13 4 24C4 35 13 44 24 44C35 44 44 35 44 24C44 13 35 4 24 4ZM24 8C32.84 8 40 15.16 40 24C40 32.84 32.84 40 24 40C15.16 40 8 32.84 8 24C8 15.16 15.16 8 24 8ZM16 18H32V22H16V18ZM16 24H32V28H16V24Z" fill="url(#gradient-primary)"/>
                </svg>
              </div>
              <h3>Voice Authentication</h3>
              <p>Your voice is your key. Convenient access with industry-standard audio verification.</p>
            </div>
            <div className="feature u-card">
              <div className="feature-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M40 8H8C6.9 8 6 8.9 6 10V38C6 39.1 6.9 40 8 40H40C41.1 40 42 39.1 42 38V10C42 8.9 41.1 8 40 8ZM40 38H8V20H40V38ZM40 14H8V10H40V14ZM22 32H34V26H22V32ZM14 32H18V26H14V32Z" fill="url(#gradient-primary)"/>
                </svg>
              </div>
              <h3>Real-time Transfers</h3>
              <p>Send money in seconds with robust beneficiary management and instant confirmation.</p>
            </div>
            <div className="feature u-card">
              <div className="feature-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M38 8H10C8.9 8 8 8.9 8 10V38C8 39.1 8.9 40 10 40H38C39.1 40 40 39.1 40 38V10C40 8.9 39.1 8 38 8ZM38 38H10V10H38V38ZM18 32H30V28H18V32ZM18 26H30V22H18V26ZM14 32H16V28H14V32ZM14 26H16V22H14V26Z" fill="url(#gradient-primary)"/>
                </svg>
              </div>
              <h3>AI Support</h3>
              <p>Get help instantly with our integrated sign recognition and guided assistance.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Footer */}
      <footer className="home-footer">
        <div className="layout-constrain">
          <div className="footer-content">
            <div className="footer-brand">
              <div className="brand">
                <div className="brand-mark">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 0C5.373 0 0 5.373 0 12C0 18.627 5.373 24 12 24C18.627 24 24 18.627 24 12C24 5.373 18.627 0 12 0Z" fill="url(#gradient-primary)"/>
                    <path d="M16 8H8V16H16V8Z" fill="white"/>
                    <path d="M10 10H14V14H10V10Z" fill="url(#gradient-primary)"/>
                  </svg>
                </div>
                <div className="brand-name">BankAssist<span> AI</span></div>
              </div>
              <p className="footer-description">Modern banking solutions for the digital age.</p>
            </div>
            <div className="footer-links">
              <div className="footer-column">
                <h4>Products</h4>
                <ul>
                  <li><a href="#personal">Personal Banking</a></li>
                  <li><a href="#business">Business Banking</a></li>
                  <li><a href="#investments">Investments</a></li>
                  <li><a href="#loans">Loans</a></li>
                </ul>
              </div>
              <div className="footer-column">
                <h4>Company</h4>
                <ul>
                  <li><a href="#about">About Us</a></li>
                  <li><a href="#careers">Careers</a></li>
                  <li><a href="#press">Press</a></li>
                  <li><a href="#blog">Blog</a></li>
                </ul>
              </div>
              <div className="footer-column">
                <h4>Support</h4>
                <ul>
                  <li><a href="#help">Help Center</a></li>
                  <li><a href="#contact">Contact Us</a></li>
                  <li><a href="#security">Security</a></li>
                  <li><a href="#status">System Status</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© {new Date().getFullYear()} BankAssist AI. All rights reserved.</p>
            <div className="footer-legal">
              <a href="#privacy">Privacy Policy</a>
              <a href="#terms">Terms of Service</a>
              <a href="#cookies">Cookie Policy</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;