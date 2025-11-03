import React from 'react';
import './ConfirmationModal.css';

const ConfirmationModal = ({ isOpen, message, link, onConfirm, onCancel }) => {
    if (!isOpen) {
        return null;
    }

    return (
        <div className="confirmation-modal-overlay" data-testid="confirmation-modal">
            <div className="confirmation-modal-content">
                <p>{message}</p>
                {link && (
                    <p>
                        <a href={link} target="_blank" rel="noopener noreferrer">
                            View Existing Card
                        </a>
                    </p>
                )}
                <div className="confirmation-modal-actions">
                    <button onClick={onConfirm} data-testid="confirm-button">Confirm</button>
                    <button onClick={onCancel} data-testid="cancel-button">Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;
