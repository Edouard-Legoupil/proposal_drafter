import './ProgressModal.css';

export default function ProgressModal({ isOpen, onClose, logs, onFileUpload, onRetry }) {
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
                    <ul>
                        {logs.map((log, index) => (
                            <li key={index} className={`log-entry status-${log.status}`}>
                                <span className="log-timestamp">{new Date(log.timestamp).toLocaleTimeString()}</span>
                                <span className="log-message">{log.message}</span>
                                {log.status === 'requires_action' && (
                                    <div className="log-action">
                                        <input type="file" onChange={(e) => onFileUpload(e, log.reference_id)} accept=".pdf" />
                                        <button onClick={() => onRetry(log.reference_id)}>Retry</button>
                                    </div>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}
