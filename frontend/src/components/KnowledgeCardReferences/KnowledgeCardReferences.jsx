import './KnowledgeCardReferences.css';

export default function KnowledgeCardReferences({
    references,
    editingReferenceIndex,
    handleReferenceFieldChange,
    handleSaveReference,
    handleCancelEditReference,
    handleEditReference,
    handleRemoveReference,
    handleAddReference,
    getStatus,
    getStatusMessage,
    onUploadClick
}) {
    return (
        <div className="kc-references-section" data-testid="knowledge-card-references">
            <div className="kc-references-header">
                <h3>References</h3>
                <button
                    type="button"
                    onClick={handleAddReference}
                    className="kc-add-reference-btn"
                    data-testid="add-reference-button"
                >
                    <i className="fa-solid fa-plus"></i>
                </button>
            </div>
            <div className="kc-references-grid">
                {references.map((ref, index) => (
                    <div key={ref.id || `new-${index}`} className="kc-reference-card" data-testid={`reference-card-${index}`}>
                        {editingReferenceIndex === index ? (
                            <div className="kc-reference-edit-form" data-testid={`reference-edit-form-${index}`}>
                                <select
                                    value={ref.reference_type}
                                    onChange={e => handleReferenceFieldChange(index, 'reference_type', e.target.value)}
                                    required
                                    data-testid={`reference-type-select-${index}`}
                                >
                                    <option value="">Select Type...</option>
                                    <option value="UNHCR Operation Page">UNHCR Operation Page</option>
                                    <option value="Donor Content">Donor Content</option>
                                    <option value="Humanitarian Partner Content">Humanitarian Partner Content</option>
                                    <option value="Statistics">Statistics</option>
                                    <option value="Needs Assessment">Needs Assessment</option>
                                    <option value="Evaluation Report">Evaluation Report</option>
                                    <option value="Policies">Policies</option>
                                    <option value="Social Media">Social Media</option>
                                </select>
                                <input
                                    type="url"
                                    placeholder="https://example.com"
                                    value={ref.url}
                                    onChange={e => handleReferenceFieldChange(index, 'url', e.target.value)}
                                    required
                                    data-testid={`reference-url-input-${index}`}
                                />
                                <textarea
                                    placeholder="Summary (optional)"
                                    value={ref.summary}
                                    onChange={e => handleReferenceFieldChange(index, 'summary', e.target.value)}
                                    data-testid={`reference-summary-textarea-${index}`}
                                />
                                <div className="kc-reference-edit-actions">
                                    <button
                                        type="button"
                                        onClick={() => handleSaveReference(index)}
                                        disabled={!ref.url || !ref.reference_type}
                                        data-testid={`save-reference-button-${index}`}
                                    >
                                        Save
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleCancelEditReference}
                                        data-testid={`cancel-edit-reference-button-${index}`}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <div className="kc-reference-card-header">
                                    <span className="kc-reference-type" data-testid={`reference-type-${index}`}>{ref.reference_type}</span>

                                    <div className='kc-reference-header-right'>
                                        <div className="kc-reference-status">
                                            <span
                                                className={`kc-reference-status-badge kc-reference-status-${getStatus(ref)} ${getStatus(ref) === 'error' ? 'clickable' : ''}`}
                                                title={getStatusMessage(ref)} // Add tooltip
                                                onClick={() => getStatus(ref) === 'error' && onUploadClick(ref)}
                                                data-testid={`reference-status-badge-${index}`}
                                            >
                                                {getStatus(ref)}
                                            </span>
                                            {ref.status_message && (
                                                <span className="kc-reference-status-message" data-testid={`reference-status-message-${index}`}>
                                                    {ref.status_message}
                                                </span>
                                            )}
                                        </div>
                                        <div className="kc-reference-actions">
                                            <button
                                                type="button"
                                                onClick={() => handleEditReference(index)}
                                                title="Edit reference"
                                                disabled={getStatus(ref) === 'processing'} // Disable during processing
                                                data-testid={`edit-reference-button-${index}`}
                                            >
                                                <i className="fa-solid fa-pen"></i>
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveReference(ref.id)}
                                                title="Delete reference"
                                                disabled={getStatus(ref) === 'processing'} // Disable during processing
                                                data-testid={`remove-reference-button-${index}`}
                                            >
                                                <i className="fa-solid fa-trash"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                <div className="kc-reference-card-body">
                                    <a href={ref.url} target="_blank" rel="noopener noreferrer" data-testid={`reference-url-link-${index}`}>
                                        {ref.url}
                                    </a>
                                    <p data-testid={`reference-summary-${index}`}>{ref.summary || 'No summary provided'}</p>
                                </div>
                            </>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}