import React from 'react';
import './Modal.css';

const Modal = ({ isOpen, onClose, children }) => {
    if (!isOpen) {
        return null;
    }

    return (
        <div className="modal-overlay" data-testid="modal">
            <div className="modal-content">
                <button className="modal-close" onClick={onClose} data-testid="modal-close-button">&times;</button>
                {children}
            </div>
        </div>
    );
};

export default Modal;
