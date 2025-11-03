import './ProgressModal.css';

export default function ProgressModal({ isOpen, onClose, progress, message }) {
    if (!isOpen) {
        return null;
    }

    return (
        <div className="progress-modal-overlay" data-testid="progress-modal-overlay">
            <div className="progress-modal" data-testid="progress-modal">
                <div className="progress-modal-header">
                    <h2 data-testid="progress-modal-title">Content Generation Progress</h2>
                    <button onClick={onClose} className="progress-modal-close-btn" data-testid="progress-modal-close-button">&times;</button>
                </div>
                <div className="progress-modal-content">
                    <div className="progress-bar-container" data-testid="progress-bar-container">
                        <div className="progress-bar" style={{ width: `${progress}%` }} data-testid="progress-bar"></div>
                    </div>
                    <p className="progress-message" data-testid="progress-message">{message}</p>
                </div>
            </div>
        </div>
    );
}
