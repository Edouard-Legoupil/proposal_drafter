import './AlertModal.css';

export default function AlertModal({ isOpen, message, onClose }) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay" data-testid="alert-modal-overlay">
      <div className="modal-content" data-testid="alert-modal-content">
        <p data-testid="alert-message">{message}</p>
        <div className="modal-actions">
          <button onClick={onClose} className="confirm-btn" data-testid="alert-ok-button">
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
