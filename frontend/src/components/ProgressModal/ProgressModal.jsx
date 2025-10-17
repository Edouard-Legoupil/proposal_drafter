import './ProgressModal.css';

export default function ProgressModal({ isOpen, onClose, progress, message }) {
    if (!isOpen) {
        return null;
    }

    return (
        <div className="progress-modal-overlay">
            <div className="progress-modal">
                <div className="progress-modal-header">
                    <h2>Content Generation Progress</h2>
                    <button onClick={onClose} className="progress-modal-close-btn">&times;</button>
                </div>
                <div className="progress-modal-content">
                    <div className="progress-bar-container">
                        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p className="progress-message">{message}</p>
                </div>
            </div>
        </div>
    );
}
