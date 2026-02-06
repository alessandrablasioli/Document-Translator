import React, { useState } from 'react';
import './ResultDisplay.css';
import { useLanguage } from '../../contexts/LanguageContext';
import SideBySidePreview from '../preview/SideBySidePreview';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ResultDisplay({ onDownload, onReset, detectedSourceLanguage, originalFileId, translatedFileId }) {
  const { t } = useLanguage();
  const [showPreview, setShowPreview] = useState(false);
  const downloadUrl = translatedFileId ? `${API_URL}/api/download/${translatedFileId}` : null;

  return (
    <div className="result-display">
      <div className="success-icon">✓</div>
      <h2>{t('translation.completed')}</h2>
      <p>{t('translation.completedMessage')}</p>
      <p className="formatting-notice">{t('translation.formattingNotice')}</p>
      {detectedSourceLanguage && (
        <p className="detected-source">{t('translation.detectedSource')}: {detectedSourceLanguage}</p>
      )}
      <div className="result-actions">
        {downloadUrl ? (
          <a href={downloadUrl} download className="btn btn-primary" rel="noopener noreferrer" target="_blank">
            {t('translation.download')}
          </a>
        ) : (
          <button onClick={() => onDownload()} className="btn btn-primary" disabled>
            {t('translation.download')}
          </button>
        )}
        {originalFileId && translatedFileId && (
          <button type="button" onClick={() => setShowPreview(true)} className="btn btn-secondary">
            {t('translation.preview')}
          </button>
        )}
        <button onClick={onReset} className="btn btn-secondary">
          {t('translation.translateAnother')}
        </button>
      </div>
      {showPreview && originalFileId && translatedFileId && (
        <SideBySidePreview
          originalFileId={originalFileId}
          translatedFileId={translatedFileId}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
}

export default ResultDisplay;
