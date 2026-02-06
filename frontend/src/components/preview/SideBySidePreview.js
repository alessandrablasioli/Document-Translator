import React, { useState, useEffect } from 'react';
import './SideBySidePreview.css';
import { useLanguage } from '../../contexts/LanguageContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function SideBySidePreview({ originalFileId, translatedFileId, onClose }) {
  const { t } = useLanguage();
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!originalFileId || !translatedFileId) return;
    setLoading(true);
    setError(null);
    const url = `${API_URL}/api/preview?original_file_id=${encodeURIComponent(originalFileId)}&translated_file_id=${encodeURIComponent(translatedFileId)}`;
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load preview');
        return res.json();
      })
      .then((data) => {
        setOriginalText(data.original_text || '');
        setTranslatedText(data.translated_text || '');
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [originalFileId, translatedFileId]);

  if (loading) return <div className="side-by-side-preview loading">{t('translation.generating')}...</div>;
  if (error) return <div className="side-by-side-preview error">{error}</div>;

  return (
    <div className="side-by-side-preview">
      <div className="preview-header">
        <h3>{t('translation.sideBySidePreview')}</h3>
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          {t('translation.closePreview')}
        </button>
      </div>
      <div className="preview-columns">
        <div className="preview-column">
          <h4>{t('translation.original')}</h4>
          <pre className="preview-text">{originalText}</pre>
        </div>
        <div className="preview-column">
          <h4>{t('translation.translated')}</h4>
          <pre className="preview-text">{translatedText}</pre>
        </div>
      </div>
    </div>
  );
}

export default SideBySidePreview;
