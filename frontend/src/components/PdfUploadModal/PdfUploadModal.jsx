import React, { useState } from 'react';
import './PdfUploadModal.css';

const PdfUploadModal = ({ isOpen, onClose, onConfirm }) => {
    const [selectedFile, setSelectedFile] = useState(null);

    if (!isOpen) {
        return null;
    }

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleConfirm = () => {
        if (selectedFile) {
            onConfirm(selectedFile);
        }
    };

    return (
        <div className="pdf-upload-modal-overlay">
            <div className="pdf-upload-modal">
                <h2>Upload Submitted PDF</h2>
                <input type="file" accept=".pdf" onChange={handleFileChange} />
                <div className="pdf-upload-modal-actions">
                    <button onClick={onClose}>Cancel</button>
                    <button onClick={handleConfirm} disabled={!selectedFile}>Confirm</button>
                </div>
            </div>
        </div>
    );
};

export default PdfUploadModal;
