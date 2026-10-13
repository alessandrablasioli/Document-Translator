import React, { useState } from 'react';
import './App.css';
import LandingPage from './components/landing/LandingPage';
import FileUpload from './components/upload/FileUpload';
import TranslationForm from './components/translation/TranslationForm';
import ProgressIndicator from './components/translation/ProgressIndicator';
import ResultDisplay from './components/translation/ResultDisplay';
import BatchResultDisplay from './components/translation/BatchResultDisplay';
import TranslationHistory from './components/history/TranslationHistory';
import SideBySidePreview from './components/preview/SideBySidePreview';
import Chatbot from './components/layout/Chatbot';
import LanguageSelector from './components/layout/LanguageSelector';
import { useLanguage } from './contexts/LanguageContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const { t } = useLanguage();
  const [showLanding, setShowLanding] = useState(true);
  const [fileId, setFileId] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, translating, completed, batch_completed, error
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [messageKey, setMessageKey] = useState('');
  const [translatedFileId, setTranslatedFileId] = useState(null);
  const [detectedSourceLanguage, setDetectedSourceLanguage] = useState(null);
  const [error, setError] = useState(null);
  const [documentText, setDocumentText] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyPreviewIds, setHistoryPreviewIds] = useState(null); // { originalFileId, translatedFileId }
  const [batchUploads, setBatchUploads] = useState([]); // [{ fileId, fileName }]
  const [batchResults, setBatchResults] = useState(null); // { results: [...], total }
  const [batchPreviewIds, setBatchPreviewIds] = useState(null); // { originalFileId, translatedFileId }

  const handleFileUpload = async (file) => {
    try {
      setStatus('uploading');
      setProgress(20);
      setMessageKey('status.uploadingFile');
      setMessage('');
      setError(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setFileId(data.file_id);
      setFileName(data.filename);
      setBatchUploads([]);
      setStatus('idle');
      setProgress(0);
      setMessage('');
      setMessageKey('');

      // Extract text for chatbot document search
      try {
        const extractResponse = await fetch(`${API_URL}/api/extract-text/${data.file_id}`, {
          method: 'GET',
        });
        if (extractResponse.ok) {
          const extractData = await extractResponse.json();
          setDocumentText(extractData.text);
        }
      } catch (err) {
        // Silently fail - document search is optional
        console.log('Could not extract text for search:', err);
      }
    } catch (err) {
      setStatus('error');
      setError(err.message);
      setMessage('');
      setMessageKey('');
    }
  };

  const handleFilesUpload = async (files) => {
    if (!files || files.length === 0) return;
    try {
      setStatus('uploading');
      setProgress(10);
      setMessageKey('status.uploadingFile');
      setMessage('');
      setError(null);
      const uploads = [];
      const step = 80 / Math.max(files.length, 1);
      for (let i = 0; i < files.length; i++) {
        setProgress(10 + Math.round(step * i));
        setMessageKey('');
        setMessage(`${t('status.uploadingFile')} (${i + 1}/${files.length})`);
        const formData = new FormData();
        formData.append('file', files[i]);
        const response = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: formData });
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || `Upload failed for ${files[i].name}`);
        }
        const data = await response.json();
        uploads.push({ fileId: data.file_id, fileName: data.filename });
      }
      setFileId(null);
      setFileName(null);
      setBatchUploads(uploads);
      setStatus('idle');
      setProgress(0);
      setMessage('');
      setMessageKey('');
    } catch (err) {
      setStatus('error');
      setError(err.message);
      setBatchUploads([]);
      setMessage('');
      setMessageKey('');
    }
  };

  const handleTranslate = async (targetLanguage, sourceLanguage = null) => {
    if (!fileId) {
      setError(t('error.uploadFirst') || 'Please upload a file first');
      return;
    }

    try {
      setStatus('translating');
      setProgress(30);
      setMessageKey('translation.extracting');
      setMessage('');
      setError(null);
      setDetectedSourceLanguage(null);

      const body = {
        file_id: fileId,
        target_language: targetLanguage,
        filename: fileName || undefined,
      };
      if (sourceLanguage) {
        body.source_language = sourceLanguage;
      }

      const response = await fetch(`${API_URL}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Translation failed');
      }

      setProgress(60);
      setMessageKey('translation.translatingContent');
      setMessage('');

      const data = await response.json();
      setProgress(90);
      setMessageKey('translation.generating');
      setMessage('');
      await new Promise(resolve => setTimeout(resolve, 500));

      setTranslatedFileId(data.file_id);
      if (data.detected_source_language) setDetectedSourceLanguage(data.detected_source_language);
      setStatus('completed');
      setProgress(100);
      setMessageKey('translation.completedMessage');
      setMessage('');
    } catch (err) {
      setStatus('error');
      setError(err.message);
      setMessage('');
      setMessageKey('');
      setProgress(0);
    }
  };

  const handleBatchTranslate = async (targetLanguage, sourceLanguage = null) => {
    if (!batchUploads.length) {
      setError(t('error.uploadFirst'));
      return;
    }
    try {
      setStatus('translating');
      setProgress(30);
      setMessageKey('translation.extracting');
      setMessage('');
      setError(null);
      const body = {
        file_ids: batchUploads.map((u) => u.fileId),
        filenames: batchUploads.map((u) => u.fileName),
        target_language: targetLanguage,
      };
      if (sourceLanguage) body.source_language = sourceLanguage;
      const response = await fetch(`${API_URL}/api/translate-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Batch translation failed');
      }
      const data = await response.json();
      setProgress(100);
      setMessageKey('translation.completedMessage');
      setMessage('');
      setBatchResults(data);
      setStatus('batch_completed');
    } catch (err) {
      setStatus('error');
      setError(err.message);
      setProgress(0);
      setMessageKey('');
    }
  };

  const handleReset = () => {
    setFileId(null);
    setFileName(null);
    setStatus('idle');
    setProgress(0);
    setMessage('');
    setMessageKey('');
    setTranslatedFileId(null);
    setDetectedSourceLanguage(null);
    setError(null);
    setDocumentText(null);
    setBatchUploads([]);
    setBatchResults(null);
  };

  const handleDownload = async (fileIdToDownload = null) => {
    const id = fileIdToDownload ?? translatedFileId;
    if (!id) return;
    const url = `${API_URL}/api/download/${id}`;
    try {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition');
      const filenameMatch = disposition && disposition.match(/filename="?([^";\n]+)"?/);
      const filename = filenameMatch ? filenameMatch[1].trim() : `translated_${id}`;
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(err.message || t('translation.error'));
    }
  };

  const handleBatchPreview = (originalFileId, translatedFileId) => {
    setBatchPreviewIds({ originalFileId, translatedFileId });
  };

  const handleBatchDownload = (translatedFileId) => {
    handleDownload(translatedFileId);
  };

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />;
  }

  return (
    <div className="App">
      <div className="app-lang-bar">
        <LanguageSelector />
      </div>
      <div className="container">
        <div className="top-bar">
          <button type="button" className="btn btn-secondary btn-history" onClick={() => setShowHistory(!showHistory)}>
            {t('translation.historyTitle')}
          </button>
        </div>
        <header className="header">
          <div className="logo">
            <div className="logo-text">
              <h1>{t('app.title')}</h1>
              <p>{t('app.subtitle')}</p>
            </div>
          </div>
        </header>

        <main className="main-content">
          {status === 'idle' && !fileId && !batchUploads.length && (
            <FileUpload onFileUpload={handleFileUpload} onFilesUpload={handleFilesUpload} />
          )}

          {batchUploads.length > 0 && status === 'idle' && (
            <div className="upload-success">
              <div className="success-icon">✓</div>
              <p>{t('status.fileUploaded')} {batchUploads.length} {batchUploads.length === 1 ? 'file' : 'files'}</p>
              <ul className="batch-file-list">
                {batchUploads.map((u, i) => (
                  <li key={u.fileId}>{u.fileName || u.fileId}</li>
                ))}
              </ul>
              <TranslationForm
                onTranslate={handleBatchTranslate}
                onReset={handleReset}
                isBatch
              />
            </div>
          )}

          {fileId && status === 'idle' && (
            <div className="upload-success">
              <div className="success-icon">✓</div>
              <p>{t('status.fileUploaded')} {fileName}</p>
              <TranslationForm onTranslate={handleTranslate} onReset={handleReset} />
            </div>
          )}

          {(status === 'uploading' || status === 'translating') && (
            <ProgressIndicator 
              status={status} 
              progress={progress} 
              message={message} 
              messageKey={messageKey}
            />
          )}

          {status === 'completed' && (
            <ResultDisplay 
              onDownload={handleDownload}
              onReset={handleReset}
              detectedSourceLanguage={detectedSourceLanguage}
              originalFileId={fileId}
              translatedFileId={translatedFileId}
            />
          )}

          {status === 'batch_completed' && batchResults && (
            <BatchResultDisplay
              results={batchResults.results}
              filenames={batchUploads.map((u) => u.fileName)}
              onReset={handleReset}
              onPreview={handleBatchPreview}
              onDownload={handleBatchDownload}
            />
          )}

          {status === 'error' && (
            <div className="error-display">
              <div className="error-icon">✗</div>
              <h2>{t('error.title')}</h2>
              <p>{error}</p>
              <button onClick={handleReset} className="btn btn-primary">
                {t('error.tryAgain')}
              </button>
            </div>
          )}

          {showHistory && (
            <TranslationHistory
              onClose={() => setShowHistory(false)}
              onPreview={(origId, transId) => setHistoryPreviewIds({ originalFileId: origId, translatedFileId: transId })}
            />
          )}

          {historyPreviewIds && (
            <div className="history-preview-overlay">
              <SideBySidePreview
                originalFileId={historyPreviewIds.originalFileId}
                translatedFileId={historyPreviewIds.translatedFileId}
                onClose={() => setHistoryPreviewIds(null)}
              />
            </div>
          )}

          {batchPreviewIds && (
            <div className="history-preview-overlay">
              <SideBySidePreview
                originalFileId={batchPreviewIds.originalFileId}
                translatedFileId={batchPreviewIds.translatedFileId}
                onClose={() => setBatchPreviewIds(null)}
              />
            </div>
          )}
        </main>

        <footer className="footer">
          <p>{t('footer.poweredBy')}</p>
        </footer>
      </div>
      <Chatbot uploadedDocumentText={documentText} />
    </div>
  );
}

export default App;

