import './KnowledgeCardHistory.css';

export default function KnowledgeCardHistory({ history, onClose }) {
    return (
        <div className="kc-history-modal">
            <div className="kc-history-content">
                <button onClick={onClose} className="kc-history-close-btn">
                    &times;
                </button>
                <h2>Knowledge Card History</h2>
                <div className="kc-history-timeline">
                    {history.map((entry, index) => (
                        <div key={index} className="kc-history-entry">
                            <div className="kc-history-entry-header">
                                <span>{new Date(entry.created_at).toLocaleString()}</span>
                                <span>by {entry.created_by_name}</span>
                            </div>
                            <div className="kc-history-entry-body">
                                {Object.entries(entry.generated_sections_snapshot).map(([section, content]) => (
                                    <div key={section} className="kc-history-section">
                                        <h4>{section}</h4>
                                        <p>{content}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
