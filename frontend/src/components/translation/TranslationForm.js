import React, { useState } from 'react';
import './TranslationForm.css';
import { useLanguage } from '../../contexts/LanguageContext';

const LANGUAGES = [
  { code: 'English', name: 'English' },
  { code: 'Catalan', name: 'Catalan' },
  { code: 'Spanish', name: 'Spanish' },
  { code: 'French', name: 'French' },
  { code: 'German', name: 'German' },
  { code: 'Italian', name: 'Italian' },
  { code: 'Portuguese', name: 'Portuguese' },
  { code: 'Russian', name: 'Russian' },
  { code: 'Japanese', name: 'Japanese' },
  { code: 'Chinese', name: 'Chinese (Simplified)' },
  { code: 'Korean', name: 'Korean' },
  { code: 'Arabic', name: 'Arabic' },
  { code: 'Dutch', name: 'Dutch' },
  { code: 'Swedish', name: 'Swedish' },
  { code: 'Norwegian', name: 'Norwegian' },
  { code: 'Danish', name: 'Danish' },
  { code: 'Polish', name: 'Polish' },
  { code: 'Turkish', name: 'Turkish' },
  { code: 'Hindi', name: 'Hindi' },
  { code: 'Greek', name: 'Greek' },
];

function TranslationForm({ onTranslate, onReset, isBatch = false }) {
  const { t } = useLanguage();
  const [targetLanguage, setTargetLanguage] = useState('English');
  const [sourceLanguage, setSourceLanguage] = useState(''); // '' = auto-detect
  const [isTranslating, setIsTranslating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (targetLanguage && !isTranslating) {
      setIsTranslating(true);
      await onTranslate(targetLanguage, sourceLanguage || null);
      setIsTranslating(false);
    }
  };

  return (
    <form className="translation-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="source-language">{t('translation.sourceLanguage')}</label>
        <select
          id="source-language"
          value={sourceLanguage}
          onChange={(e) => setSourceLanguage(e.target.value)}
          disabled={isTranslating}
          className="language-select"
        >
          <option value="">{t('translation.autoDetect')}</option>
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.name}>
              {lang.name}
            </option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label htmlFor="target-language">{t('translation.selectLanguage')}</label>
        <select
          id="target-language"
          value={targetLanguage}
          onChange={(e) => setTargetLanguage(e.target.value)}
          disabled={isTranslating}
          className="language-select"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.name}>
              {lang.name}
            </option>
          ))}
        </select>
      </div>

      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isTranslating || !targetLanguage}
        >
          {isTranslating ? t('translation.translating') : (isBatch ? t('translation.batchTranslate') : t('translation.translateButton'))}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onReset}
          disabled={isTranslating}
        >
          {t('translation.uploadNewFile')}
        </button>
      </div>
    </form>
  );
}

export default TranslationForm;
