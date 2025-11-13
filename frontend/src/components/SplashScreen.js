import React from 'react';
import './SplashScreen.css';

const SplashScreen = () => {
  return (
    <div className="splash-screen">
      <div className="coin-container">
        <div className="coin">
          <div className="coin-face coin-front">BA</div>
          <div className="coin-face coin-back">
            <svg width="32" height="32" viewBox="0 0 36 36" fill="none">
              <path d="M18 0C8.058 0 0 8.058 0 18C0 27.942 8.058 36 18 36C27.942 36 36 27.942 36 18C36 8.058 27.942 0 18 0Z" fill="url(#splash-gradient)"/>
              <path d="M24 12H12V24H24V12Z" fill="white"/>
              <path d="M15 15H21V21H15V15Z" fill="url(#splash-gradient)"/>
              <defs>
                <linearGradient id="splash-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#4361ee"/>
                  <stop offset="100%" stopColor="#3a0ca3"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
      </div>
      <div className="splash-title">
        BankAssist<span> AI</span>
      </div>
    </div>
  );
};

export default SplashScreen;
