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
    template: [
        { value: 'P0', label: 'P0 – Critical', description: 'Mandatory donor section omitted (non-compliant) or unsupported/fabricated content introduced despite available source cards.' },
        { value: 'P1', label: 'P1 – High', description: 'Prompt fails to enforce required donor structure or tone in a material way; placeholder text remains in output.' },
        { value: 'P2', label: 'P2 – Medium', description: 'Draft structurally acceptable but too generic; style mismatch that increases editing effort; minor completeness gap in non-mandatory section.' },
        { value: 'P3', label: 'P3 – Low', description: 'Tone slightly off but easily corrected; minor formatting issue with no material donor-compliance impact.' },
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
    const selectedSeverity = reviewComment?.severity || reviewComment?.type_of_comment || 'P2';

    return (
        <div className="SectionReview_container">
            <div className="SectionReview_header">
                <h3>{isReviewEditable ? "Review Feedback" : "Previous Feedback:"}</h3>
                <div className="SectionReview_thumbs">
                    <button
                        className={`thumb-btn down ${status === 'down' ? 'active' : ''}`}
                        onClick={() => isReviewEditable && onStatusChange(section, 'down')}
                        title="Report Issue"
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: status === 'down' ? '#d32f2f' : '#555', fontSize: '1.2rem', display: 'flex', alignItems: 'center', transition: 'color 0.2s' }}
                        type="button"
                    >
                        <FontAwesomeIcon icon={faThumbsDown} />
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, marginLeft: 6 }}>Report Issue</span>
                    </button>
                </div>
            </div>

            {(status === 'down' || (reviewComment && reviewComment.review_text)) && (
                <div className="SectionReview_comment_section">
                    <textarea
                        className="SectionReview_comment_textarea"
                        placeholder={isReviewEditable ? `Enter your detailed feedback for ${section}...` : "No comments provided."}
                        value={reviewComment?.review_text || ""}
                        onChange={e => onCommentChange(section, 'review_text', e.target.value)}
                        disabled={!isReviewEditable}
                        id={`section-review-textarea-${section}`}
                    />
                    
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
                                            onCommentChange(section, 'severity', opt.value);
                                            onCommentChange(section, 'type_of_comment', opt.value);
                                        }}
                                        disabled={!isReviewEditable}
                                    />
                                    <span className="SectionReview_severity-badge">{opt.value}</span>
                                    <span className="SectionReview_severity-text">{opt.label.replace(`${opt.value} – `, '')}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {isReviewEditable && (isOwnerOfComment || isAdmin) && (
                        <div className="SectionReview_actions_footer">
                            <button
                                className="btn btn--primary btn--small"
                                onClick={() => onCommentChange(section, 'save', reviewComment?.review_text || '')}
                                title="Save comment"
                                type="button"
                                disabled={!reviewComment?.review_text?.trim()}
                            >
                                Save Comment
                            </button>
                            {reviewComment?.id && (
                                <button
                                    className="SectionReview_delete_comment_btn"
                                    onClick={() => onDeleteComment(section)}
                                    title="Delete comment"
                                    type="button"
                                >
                                    <FontAwesomeIcon icon={faTrash} /> Remove
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

