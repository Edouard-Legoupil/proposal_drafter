import './LoadingModal.css'

export default function LoadingModal({ isOpen, message }) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="loading-spinner" />
        <p>{message}</p>
      </div>
    </div>
  );
}
