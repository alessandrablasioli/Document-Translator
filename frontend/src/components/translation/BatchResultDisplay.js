import React from 'react';
import './BatchResultDisplay.css';
import { useLanguage } from '../../contexts/LanguageContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function BatchResultDisplay({ results, filenames, onReset, onPreview, onDownload }) {
  const { t } = useLanguage();
  const getFilename = (originalFileId, index) => {
    if (filenames && filenames[index]) return filenames[index];
    return originalFileId;
  };

  return (
    <div className="batch-result-display">
      <div className="success-icon">✓</div>
      <h2>{t('translation.batchResults')}</h2>
      <p className="formatting-notice">{t('translation.formattingNotice')}</p>
      <div className="batch-table-wrap">
        <table className="batch-table">
          <thead>
            <tr>
              <th>{t('translation.batchFile')}</th>
              <th>{t('translation.batchStatus')}</th>
              <th>{t('translation.batchPreview')}</th>
              <th>{t('translation.batchDownload')}</th>
            </tr>
          </thead>
          <tbody>
            {(results || []).map((row, index) => (
              <tr key={row.original_file_id}>
                <td>{getFilename(row.original_file_id, index)}</td>
                <td>
                  <span className={`batch-status batch-status-${row.status}`}>
                    {row.status === 'completed' ? t('translation.completed') : row.error || row.status}
                  </span>
                </td>
                <td>
                  {row.status === 'completed' && row.translated_file_id && onPreview ? (
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => onPreview(row.original_file_id, row.translated_file_id)}
                    >
                      {t('translation.batchPreview')}
                    </button>
                  ) : (
                    '—'
                  )}
                </td>
                <td>
                  {row.status === 'completed' && row.translated_file_id ? (
                    onDownload ? (
                      <button
                        type="button"
                        className="btn btn-small btn-primary"
                        onClick={() => onDownload(row.translated_file_id)}
                      >
                        {t('translation.batchDownload')}
                      </button>
                    ) : (
                      <a
                        href={`${API_URL}/api/download/${row.translated_file_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-small"
                      >
                        {t('translation.batchDownload')}
                      </a>
                    )
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="batch-actions">
        <button type="button" className="btn btn-primary" onClick={onReset}>
          {t('translation.uploadNewFile')}
        </button>
      </div>
    </div>
  );
}

export default BatchResultDisplay;
