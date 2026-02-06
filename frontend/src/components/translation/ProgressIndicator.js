import React from 'react';
import './ProgressIndicator.css';
import { useLanguage } from '../../contexts/LanguageContext';

function ProgressIndicator({ status, progress, message, messageKey }) {
  const { t } = useLanguage();
  const displayMessage = messageKey ? t(messageKey) : (message || t('translation.loading'));
  return (
    <div className="progress-indicator">
      <div className="progress-icon">
        {status === 'uploading' ? '📤' : '🔄'}
      </div>
      <h2>{status === 'uploading' ? t('status.uploading') : t('translation.translating')}</h2>
      <div className="progress-bar-container">
        <div 
          className="progress-bar" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <p className="progress-message">{displayMessage}</p>
      <p className="progress-percentage">{Math.round(progress)}%</p>
    </div>
  );
}

export default ProgressIndicator;
