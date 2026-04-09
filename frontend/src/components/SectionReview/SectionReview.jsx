import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThumbsDown, faTrash } from '@fortawesome/free-solid-svg-icons';
import './SectionReview.css';

const SEVERITY_OPTIONS = {
    proposal: [
        { value: 'P0', label: 'P0 – Critical: Output unsafe or unacceptable', description: 'Unsupported claims, fabricated numbers, wrong donor/country content, non-compliant with mandatory requirements, or evidence base is fundamentally wrong.' },
        { value: 'P1', label: 'P1 – High: Major quality or compliance risk', description: 'Misses major required content, major logic gaps, excessive editing effort, or consistent reviewer approval failure.' },
        { value: 'P2', label: 'P2 – Medium: Weakens reliability (manageable)', description: 'Acceptable in principle but requires noticeable rewrite for specificity, completeness, or tone; too generic to be efficient.' },
        { value: 'P3', label: 'P3 – Low: Minor issue, no material impact', description: 'Minor formatting or polish issue; small editorial improvement needed with no factual or compliance impact.' },
    ],
    knowledge_card: [
        { value: 'P0', label: 'P0 – Critical: Output unsafe or unacceptable', description: 'Wrong source type admitted as authoritative, corpus so incomplete grounded outputs are impossible, hallucinated statistic/requirement, or missing critical mandatory card.' },
        { value: 'P1', label: 'P1 – High: Major quality or compliance risk', description: 'Outdated donor guidance, major metadata error (wrong donor/country/tag), near-duplicate/conflicting documents, major card omission, or retrieval returns regional generalities for specific ask.' },
        { value: 'P2', label: 'P2 – Medium: Weakens reliability (manageable)', description: 'Context mostly relevant but incomplete, extra irrelevant information retrieved, card broadly correct but too generic, or partial traceability gaps for non-critical details.' },
        { value: 'P3', label: 'P3 – Low: Minor issue, no material impact', description: 'Stylistic or wording issues in the card with no factual impact; minor formatting issues in the source record.' },
    ],
};

export default function SectionReview({
    section,
    type,
    reviewComment,
    status,
    isReviewEditable,
    onCommentChange,
    onStatusChange,
    onDeleteComment,
    isOwnerOfComment,
    isAdmin
}) {
    const severityOptions = SEVERITY_OPTIONS[type] || SEVERITY_OPTIONS.proposal;
    const selectedSeverity = reviewComment?.type_of_comment || 'P2';

    return (
        <div className="SectionReview_container">
            <div className="SectionReview_header">
                <h3>Review this Section</h3>
                <div className="SectionReview_thumbs">
                    {/* Thumb Down button only (for reporting!) */}
                    <button
                        className={`thumb-btn down ${status === 'down' ? 'active' : ''}`}
                        onClick={() => isReviewEditable && onStatusChange(section, 'down')}
                        title="Report Issue"
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: status === 'down' ? 'red' : '#555', fontSize: '1.3rem', display: 'flex', alignItems: 'center' }}
                        type="button"
                    >
                        <FontAwesomeIcon icon={faThumbsDown} />
                        <span style={{ fontSize: '0.65rem', marginLeft: 4 }}>Report</span>
                    </button>
                </div>
            </div>

            {(status === 'down' || (reviewComment && reviewComment.review_text)) && (
                <div className="SectionReview_comment_section">
                    {/* Main author comment textarea (no reply field) */}
                    <textarea
                        className="SectionReview_comment_textarea"
                        placeholder={isReviewEditable ? `Your comments for ${section}...` : "No comments provided."}
                        value={reviewComment?.review_text || ""}
                        onChange={e => onCommentChange(section, 'review_text', e.target.value)}
                        disabled={!isReviewEditable}
                        id={`section-review-textarea-${section}`}
                    />
                    <div className="SectionReview_comment_controls">
                        <div className="SectionReview_severity-selector">
                            <label className="SectionReview_severity-label">Incident Severity</label>
                            <div className="SectionReview_severity-options">
                                {severityOptions.map(opt => (
                                    <label
                                        key={opt.value}
                                        className={`SectionReview_severity-option ${selectedSeverity === opt.value ? 'selected' : ''} severity-${opt.value}`}
                                        title={opt.description}
                                    >
                                        <input
                                            type="radio"
                                            name={`severity-${section}`}
                                            value={opt.value}
                                            checked={selectedSeverity === opt.value}
                                            onChange={() => {
                                                onCommentChange(section, 'type_of_comment', opt.value);
                                                onCommentChange(section, 'severity', opt.value);
                                            }}
                                            disabled={!isReviewEditable}
                                        />
                                        <span className="SectionReview_severity-badge">{opt.value}</span>
                                        <span className="SectionReview_severity-text">{opt.label.replace(`${opt.value} – `, '')}</span>
                                    </label>
                                ))}
                            </div>
                            {(() => {
                                const sel = severityOptions.find(o => o.value === selectedSeverity);
                                return sel ? <p className="SectionReview_severity-description">{sel.description}</p> : null;
                            })()}
                        </div>
                    </div>

                    {/* Save/Delete - only for owner or admin, and only if there's text */}
                    {isReviewEditable && (isOwnerOfComment || isAdmin) && reviewComment?.review_text && (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.5rem' }}>
                            {/* Save button (identical style to DonorTemplateDetail) */}
                            <button
                                className="btn btn--primary btn--small"
                                onClick={() => onCommentChange(section, 'save', reviewComment.review_text)}
                                title="Save comment"
                                type="button"
                            >
                                Save
                            </button>
                            {/* Delete comment */}
                            <button
                                className="SectionReview_delete_comment_btn"
                                onClick={() => onDeleteComment(section)}
                                title="Delete comment"
                                type="button"
                            >
                                <FontAwesomeIcon icon={faTrash} /> Delete
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

