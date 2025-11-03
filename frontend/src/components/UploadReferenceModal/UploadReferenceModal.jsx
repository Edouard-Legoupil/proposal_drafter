import React, { useState } from 'react';
import './UploadReferenceModal.css';

export default function UploadReferenceModal({
  isOpen,
  onClose,
  onUpload,
  reference,
}) {
  const [file, setFile] = useState(null);

  if (!isOpen) {
    return null;
  }

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (file) {
      onUpload(reference.id, file);
    } else {
      alert('Please select a file to upload.');
    }
  };

  return (
    <div className="upload-modal-overlay" data-testid="upload-reference-modal-overlay">
      <div className="upload-modal-content" data-testid="upload-reference-modal-content">
        <h2 data-testid="upload-reference-modal-title">Upload PDF for Reference</h2>
        <p>
          Sorry. We could not automatically ingest the reference from the URL (likely because of bot scrapping prevention policy on that server). Please visit manuualy that page, save it as PDF and upload the PDF here
          manually.
        </p>
        <p>
          <strong>URL:</strong>{' '}
          <a href={reference.url} target="_blank" rel="noopener noreferrer">
            {reference.url}
          </a>
        </p>
        <input type="file" accept=".pdf" onChange={handleFileChange} data-testid="upload-reference-file-input" />
        <div className="upload-modal-actions">
          <button onClick={handleUpload} disabled={!file} data-testid="upload-reference-button">
            Upload
          </button>
          <button onClick={onClose} data-testid="upload-reference-cancel-button">Cancel</button>
        </div>
      </div>
    </div>
  );
}