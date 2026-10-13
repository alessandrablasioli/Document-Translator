import React from 'react';
import './LandingPage.css';

function Paper({ tilted }) {
  return (
    <div className={`doc-card${tilted ? ' doc-card-back' : ' doc-card-front'}`}>
      <span className="line" />
      <span className="line short" />
      <span className="line" />
      <span className="line short" />
    </div>
  );
}

function LandingPage({ onEnter }) {
  return (
    <div className="landing-page">
      <div className="landing-glow landing-glow-a" aria-hidden="true" />
      <div className="landing-glow landing-glow-b" aria-hidden="true" />
      <div className="landing-content">
        <div className="landing-visual" aria-hidden="true">
          <span className="spark spark-a">✦</span>
          <Paper tilted />
          <div className="doc-bridge">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path
                d="M12 19s-7-4.4-7-9a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 4.6-7 9-7 9z"
                fill="currentColor"
              />
            </svg>
          </div>
          <Paper />
          <span className="spark spark-b">✦</span>
        </div>
        <p className="landing-kicker">AI document translation</p>
        <h1 className="landing-title">Document Translator</h1>
        <p className="landing-lead">
          Upload a file, choose a language, and download a translation that keeps the original structure.
        </p>
        <button type="button" className="landing-cta" onClick={onEnter}>
          Start translating
        </button>
      </div>
    </div>
  );
}

export default LandingPage;
