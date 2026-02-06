import React from 'react';
import './LandingPage.css';

function LandingPage({ onEnter }) {
  return (
    <div className="landing-page">
      <video
        className="landing-video"
        src="/home-main-hero-video-mobile-2025.mp4"
        autoPlay
        muted
        loop
        playsInline
        aria-hidden
      />
      <div className="landing-overlay" />
      <div className="landing-content">
        <div className="landing-logo-wrap">
          <img src="/download.svg" alt="Document Translator" className="landing-logo" />
        </div>
        <button
          type="button"
          className="landing-cta"
          onClick={onEnter}
        >
          The STARK Future of translation begins here
        </button>
      </div>
    </div>
  );
}

export default LandingPage;
