import './LoadingModal.css'

export default function LoadingModal({ isOpen, message }) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay" data-testid="loading-modal-overlay">
      <div className="modal-content" data-testid="loading-modal-content">
        <div className="loading-spinner" data-testid="loading-spinner" />
        <p data-testid="loading-message">{message}</p>
      </div>
    </div>
  );
}
