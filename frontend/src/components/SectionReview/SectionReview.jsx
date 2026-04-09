import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThumbsDown, faTrash, faInfoCircle } from '@fortawesome/free-solid-svg-icons';
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

const TYPE_OF_COMMENT_OPTIONS = {
    proposal: {
        P0: ['Factual Error', 'Compliance Violation', 'Security Risk'],
        P1: ['Major Content Gap', 'Structural Issue', 'Quality Concern'],
        P2: ['Clarity Issue', 'Tone Mismatch', 'Minor Gap'],
        P3: ['Formatting Issue', 'Typo', 'Style Suggestion']
    },
    knowledge_card: {
        P0: ['Data Integrity', 'Source Error', 'Critical Omission'],
        P1: ['Metadata Issue', 'Duplicate Content', 'Outdated Information'],
        P2: ['Relevance Issue', 'Traceability Gap', 'Generic Content'],
        P3: ['Formatting Issue', 'Minor Error', 'Style Suggestion']
    },
    template: {
        P0: ['Compliance Issue', 'Structural Problem', 'Critical Error'],
        P1: ['Major Quality Issue', 'Content Gap', 'Format Problem'],
        P2: ['Clarity Issue', 'Tone Mismatch', 'Minor Improvement'],
        P3: ['Formatting Issue', 'Typo', 'Style Suggestion']
    }
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
    isAdmin,
    isAuthorizedToReply,
    onSaveReply
}) {
    const severityOptions = SEVERITY_OPTIONS[type] || SEVERITY_OPTIONS.proposal;
    const selectedSeverity = reviewComment?.severity || reviewComment?.type_of_comment || 'P2';
    const selectedTypeOfComment = reviewComment?.type_of_comment || '';
    const [hoveredSeverity, setHoveredSeverity] = useState(null);
    
    // Get available type_of_comment options based on selected severity
    const typeOfCommentOptions = TYPE_OF_COMMENT_OPTIONS[type]?.[selectedSeverity] || [];
    
    // Validation: check if all required fields are filled
    const isSaveEnabled = reviewComment?.review_text?.trim() && selectedSeverity && selectedTypeOfComment;

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
                                    onMouseEnter={() => setHoveredSeverity(opt.value)}
                                    onMouseLeave={() => setHoveredSeverity(null)}
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
                                    {hoveredSeverity === opt.value && (
                                        <div className="severity-description-tooltip">
                                            <FontAwesomeIcon icon={faInfoCircle} style={{ marginRight: '6px' }} />
                                            {opt.description}
                                        </div>
                                    )}
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Type of Comment Selection */}
                    {typeOfCommentOptions.length > 0 && (
                        <div className="SectionReview_type-selector">
                            <label className="SectionReview_type-label">Type of Comment</label>
                            <select
                                className="SectionReview_type-select"
                                value={selectedTypeOfComment}
                                onChange={e => onCommentChange(section, 'type_of_comment', e.target.value)}
                                disabled={!isReviewEditable}
                            >
                                <option value="">Select comment type...</option>
                                {typeOfCommentOptions.map(option => (
                                    <option key={option} value={option}>{option}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    {isReviewEditable && (isOwnerOfComment || isAdmin) && (
                        <div className="SectionReview_actions_footer">
                            <button
                                className="btn btn--primary btn--small"
                                onClick={() => onCommentChange(section, 'save', reviewComment?.review_text || '')}
                                title="Save comment"
                                type="button"
                                disabled={!isSaveEnabled}
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

            {/* Author Response Section */}
            {!isReviewEditable && isAuthorizedToReply && (
                <div className="SectionReview_authorReply" data-testid={`author-reply-${section}`}>
                    <textarea
                        className="SectionReview_reply_textarea"
                        placeholder={`Your response to ${section}...`}
                        value={reviewComment?.author_response || ''}
                        onChange={e => onSaveReply(section, e.target.value)}
                        data-testid={`author-response-textarea-${section}`}
                    />
                    <div className="SectionReview_reply_actions">
                        <button
                            type="button"
                            className="btn btn--primary btn--small"
                            onClick={() => onSaveReply(section, reviewComment?.author_response || '')}
                            disabled={!reviewComment?.author_response?.trim()}
                            data-testid={`save-reply-button-${section}`}
                        >
                            Save Response
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
