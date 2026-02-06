import React, { useRef, useState } from 'react';
import './FileUpload.css';
import { useLanguage } from '../../contexts/LanguageContext';

const SUPPORTED_TYPES = ['.pdf', '.md', '.txt', '.json', '.xml', '.docx', '.pptx'];

function FileUpload({ onFileUpload, onFilesUpload }) {
  const { t } = useLanguage();
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const getFileExtension = (filename) => {
    return filename.toLowerCase().substring(filename.lastIndexOf('.'));
  };

  const filterValidFiles = (fileList) => {
    const files = Array.from(fileList || []);
    const valid = [];
    const supportedList = SUPPORTED_TYPES.join(', ');
    for (const file of files) {
      const ext = getFileExtension(file.name);
      if (SUPPORTED_TYPES.includes(ext)) {
        valid.push(file);
      } else {
        alert(`Unsupported file type (${file.name}). Supported formats: ${supportedList}`);
        return null;
      }
    }
    return valid.length ? valid : null;
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    const ext = getFileExtension(file.name);
    if (SUPPORTED_TYPES.includes(ext)) {
      onFileUpload(file);
    } else {
      const supportedList = SUPPORTED_TYPES.join(', ');
      alert(`Unsupported file type. Supported formats: ${supportedList}`);
    }
  };

  const handleMultipleFiles = (fileList) => {
    const valid = filterValidFiles(fileList);
    if (!valid) return;
    if (valid.length === 1 && !onFilesUpload) {
      onFileUpload(valid[0]);
      return;
    }
    if (valid.length > 1 && onFilesUpload) {
      onFilesUpload(valid);
      return;
    }
    if (valid.length === 1) onFileUpload(valid[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length === 1 && !onFilesUpload) {
      handleFileSelect(files[0]);
    } else if (files.length > 0) {
      handleMultipleFiles(files);
    }
  };

  const handleInputChange = (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    if (files.length === 1 && !onFilesUpload) {
      handleFileSelect(files[0]);
    } else {
      handleMultipleFiles(files);
    }
    e.target.value = '';
  };

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-area ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="upload-icon">📄</div>
        <h2>{t('upload.title')}</h2>
        <p>{t('upload.description')}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.txt,.json,.xml,.docx,.pptx"
          multiple
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />
      </div>
      <p className="upload-hint">{t('upload.hint')}</p>
    </div>
  );
}

export default FileUpload;
