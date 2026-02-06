import React, { useState, useEffect } from 'react';
import './TranslationHistory.css';
import { useLanguage } from '../../contexts/LanguageContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function TranslationHistory({ onPreview, onClose }) {
  const { t } = useLanguage();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_URL}/api/history?limit=50`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load history');
        return res.json();
      })
      .then((data) => setHistory(data.history || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const formatDate = (ts) => {
    if (!ts) return '';
    const d = new Date(ts * 1000);
    return d.toLocaleString();
  };

  if (loading) return <div className="translation-history loading">{t('translation.loading')}...</div>;
  if (error) return <div className="translation-history error">{error}</div>;

  return (
    <div className="translation-history">
      <div className="history-header">
        <h3>{t('translation.historyTitle')}</h3>
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          {t('translation.closePreview')}
        </button>
      </div>
      {history.length === 0 ? (
        <p className="history-empty">{t('translation.historyEmpty')}</p>
      ) : (
        <ul className="history-list">
          {history.map((entry) => (
            <li key={entry.id} className="history-item">
              <span className="history-filename">{entry.filename || entry.original_file_id}</span>
              <span className="history-meta">
                {entry.target_language} • {formatDate(entry.timestamp)}
              </span>
              <div className="history-actions">
                <a
                  href={`${API_URL}/api/download/${entry.translated_file_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-small"
                >
                  {t('translation.download')}
                </a>
                {onPreview && (
                  <button
                    type="button"
                    className="btn btn-small btn-secondary"
                    onClick={() => onPreview(entry.original_file_id, entry.translated_file_id)}
                  >
                    {t('translation.preview')}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default TranslationHistory;
