import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThumbsDown, faTrash, faInfoCircle, faReply, faTimes } from '@fortawesome/free-solid-svg-icons';
import { Chip } from '@mui/material';
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

// I have a system generating proposals based on requirements and knowledge cards and aliging with templates. I have a process to collect user feedback based on predifine incident types.
// desing an agentic system that will turn them into 1. suggestions made to the user to quickly correct the proposal. 2. analysis of root cause of the issue. 3. suggested fix to the issue. 
// here are the type of incident par criticality level.     
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

// Helper functions for severity styling (consistent with QualityGate)
const getSeverityColor = (sev) => {
    switch (sev) {
        case 'P0': return '#c0392b' // Red
        case 'P1': return '#e67e22' // Orange  
        case 'P2': return '#2980b9' // Blue
        case 'P3': return '#27ae60' // Green
        default: return '#7f8c8d' // Gray
    }
};

const getSeverityIcon = (sev) => {
    switch (sev) {
        case 'P0': return faThumbsDown;
        case 'P1': return faThumbsDown;
        case 'P2': return faInfoCircle;
        case 'P3': return faThumbsDown;
        default: return faInfoCircle;
    }
};

const formatDateTime = (value) => {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
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
    onSaveReply,
    previousFeedback = [], // Add previous feedback prop
    onReplyToFeedback, // Function to handle replies to previous feedback
    isExpanded = false // Control whether the comment section is expanded
}) {
    
    // Debug logging
    console.log(`SectionReview[${section}] - Props:`, {
        section,
        type,
        reviewComment,
        status,
        isReviewEditable,
        previousFeedback,
        isExpanded
    });
    const severityOptions = SEVERITY_OPTIONS[type] || SEVERITY_OPTIONS.proposal;
    const selectedSeverity = reviewComment?.severity || reviewComment?.type_of_comment || 'P2';
    const selectedTypeOfComment = reviewComment?.type_of_comment || '';
    const [hoveredSeverity, setHoveredSeverity] = useState(null);
    const [replyModalOpen, setReplyModalOpen] = useState(null);
    const [replyText, setReplyText] = useState('');
    const [replyStatus, setReplyStatus] = useState('pending');
    const [localExpanded, setLocalExpanded] = useState(isExpanded);

    // Get available type_of_comment options based on selected severity
    const typeOfCommentOptions = TYPE_OF_COMMENT_OPTIONS[type]?.[selectedSeverity] || [];

    // Validation: check if all required fields are filled
    const isSaveEnabled = reviewComment?.review_text?.trim() && selectedSeverity && selectedTypeOfComment;

    const handleReplySubmit = (feedbackId) => {
        if (replyText.trim() && onReplyToFeedback) {
            onReplyToFeedback(feedbackId, replyText, replyStatus);
            setReplyModalOpen(null);
            setReplyText('');
            setReplyStatus('pending');
        }
    };

    const toggleExpand = () => {
        const newExpanded = !localExpanded;
        setLocalExpanded(newExpanded);
        if (onStatusChange) {
            onStatusChange(section, newExpanded ? 'down' : null);
        }
    };

    return (
        <div className="SectionReview_container">
            <div className="SectionReview_header">
                <h3>{isReviewEditable ? "Review Feedback" : "Previous Feedback:"}</h3>
                <div className="SectionReview_thumbs">
                    <button
                        className={`thumb-btn down ${(status === 'down' || localExpanded) ? 'active' : ''}`}
                        onClick={toggleExpand}
                        title={localExpanded ? "Collapse" : "Report Issue"}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: (status === 'down' || localExpanded) ? '#d32f2f' : '#555', fontSize: '1.2rem', display: 'flex', alignItems: 'center', transition: 'color 0.2s' }}
                        type="button"
                    >
                        <FontAwesomeIcon icon={faThumbsDown} />
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, marginLeft: 6 }}>
                            {localExpanded ? 'Collapse' : 'Report Issue'}
                        </span>
                    </button>
                </div>
            </div>

            {/* Always show previous feedback first, at the top */}
            {console.log('SectionReview previousFeedback:', previousFeedback)}
            {previousFeedback.length > 0 && (
                <div className="SectionReview_previous_feedback_container">
                    <h4>Previous Feedback:</h4>
                    <div className="SectionReview_previous_feedback">
                        {previousFeedback.map((feedback, index) => (
                            <div key={index} className="SectionReview_previous_feedback_item">
                                <div className="SectionReview_previous_feedback_header">
                                    <div className="SectionReview_previous_feedback_info">
                                        <span className="SectionReview_previous_feedback_author">{feedback.author || 'Anonymous'}</span>
                                        {formatDateTime(feedback.created_at) && (
                                            <span className="SectionReview_previous_feedback_date">
                                                {formatDateTime(feedback.created_at)}
                                            </span>
                                        )}
                                    </div>
                                    <div className="SectionReview_previous_feedback_badges">
                                        {/* Severity Chip - consistent with QualityGate */}
                                        <Chip 
                                            icon={<FontAwesomeIcon icon={getSeverityIcon(feedback.severity)} style={{ color: '#fff', fontSize: '0.8rem' }} />}
                                            label={feedback.severity}
                                            size="small"
                                            sx={{
                                                bgcolor: getSeverityColor(feedback.severity), 
                                                color: '#fff',
                                                fontWeight: 'bold',
                                                marginRight: '8px'
                                            }}
                                        />
                                        {/* Comment Type Chip */}
                                        {feedback.type_of_comment && (
                                            <Chip 
                                                label={feedback.type_of_comment}
                                                variant="outlined"
                                                size="small"
                                                sx={{
                                                    borderColor: getSeverityColor(feedback.severity),
                                                    color: getSeverityColor(feedback.severity),
                                                    fontWeight: 'bold'
                                                }}
                                            />
                                        )}
                                        {/* Status Chip */}
                                        {feedback.status && (
                                            <Chip 
                                                label={feedback.status}
                                                size="small"
                                                sx={{
                                                    bgcolor: feedback.status === 'resolved' ? '#4caf50' : 
                                                           feedback.status === 'acknowledged' ? '#2196f3' :
                                                           feedback.status === 'needs-more-info' ? '#ff9800' :
                                                           '#9e9e9e',
                                                    color: '#fff',
                                                    fontWeight: 'bold'
                                                }}
                                            />
                                        )}
                                    </div>
                                    <div className="SectionReview_previous_feedback_actions">
                                        {feedback.isOwnedByCurrentUser && (
                                            <button
                                                className="SectionReview_previous_feedback_remove"
                                                onClick={() => onDeleteComment(feedback.id)}
                                                title="Remove feedback"
                                            >
                                                <FontAwesomeIcon icon={faTrash} />
                                            </button>
                                        )}
                                        <button
                                            className="SectionReview_previous_feedback_reply"
                                            onClick={() => setReplyModalOpen(feedback.id)}
                                            title="Reply to feedback"
                                        >
                                            <FontAwesomeIcon icon={faReply} />
                                        </button>
                                    </div>
                                </div>
                                <div className="SectionReview_previous_feedback_content">
                                    {feedback.review_text}
                                </div>
                                {/* Display replies in compact chat style */}
                                {feedback.replies && feedback.replies.length > 0 && (
                                    <div className="SectionReview_previous_feedback_replies">
                                        {feedback.replies.map((reply, replyIndex) => {
                                            const replyDate = formatDateTime(reply.created_at);
                                            return (
                                                <div key={replyIndex} className="SectionReview_previous_feedback_reply_item">
                                                    <div className="SectionReview_previous_feedback_reply_header">
                                                        <div className="SectionReview_previous_feedback_reply_meta">
                                                            <span className="SectionReview_previous_feedback_reply_author">
                                                                {reply.author || 'Author'}
                                                            </span>
                                                            {replyDate && (
                                                                <span className="SectionReview_previous_feedback_reply_date">
                                                                    {replyDate}
                                                                </span>
                                                            )}
                                                        </div>
                                                        {reply.status && (
                                                            <div className={`SectionReview_previous_feedback_reply_status status-${reply.status}`}>
                                                                {reply.status}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="SectionReview_previous_feedback_reply_content">
                                                        {reply.text}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Current feedback section - only visible when editable and expanded */}
            {(localExpanded || (isReviewEditable && status === 'down')) && (
                <div
                    className="SectionReview_comment_section"
                    onClick={(e) => {
                        // Don't trigger when clicking on buttons or inputs
                        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT' && e.target.tagName !== 'TEXTAREA') {
                            if (reviewComment?.review_text && status !== 'down' && isReviewEditable) {
                                onStatusChange(section, 'down');
                            }
                        }
                    }}
                >
                    {/* Comment input */}
                    <textarea
                        className="SectionReview_comment_textarea"
                        placeholder={`Enter your detailed feedback for ${section}...`}
                        value={reviewComment?.review_text || ""}
                        onChange={e => onCommentChange(section, 'review_text', e.target.value)}
                        disabled={!isReviewEditable}
                        id={`section-review-textarea-${section}`}
                    />

                    {/* Quick type-selector grid mapped by severity */}
                    <div className="SectionReview_type-grid">
                        <table>
                            <thead>
                                <tr>
                                    {severityOptions.map(opt => {
                                        const [, shortLabel] = opt.label.split('–').map(s => s.trim())
                                        const headerText = shortLabel.split(':')[0]?.trim() || opt.value
                                        return (
                                            <th
                                                key={opt.value}
                                                title={opt.description}
                                                className={`severity-${opt.value}`}
                                            >
                                                <FontAwesomeIcon
                                                    icon={getSeverityIcon(opt.value)}
                                                    style={{ marginRight: '4px' }}
                                                />
                                                {`${opt.value}-${headerText}`}
                                            </th>
                                        )
                                    })}
                                </tr>
                            </thead>
                            <tbody>
                                {Array.from({ length: Math.max(...severityOptions.map(o => TYPE_OF_COMMENT_OPTIONS[type]?.[o.value]?.length || 0)) }).map((_, rowIndex) => (
                                    <tr key={rowIndex}>
                                        {severityOptions.map(opt => {
                                            const choices = TYPE_OF_COMMENT_OPTIONS[type]?.[opt.value] || [];
                                            const choice = choices[rowIndex];
                                            return (
                                                <td key={opt.value + rowIndex}>
                                                    {choice && (
                                                        <label className="SectionReview_grid-option">
                                                            <input
                                                                type="radio"
                                                                name={`type-${section}`}
                                                                value={choice}
                                                                checked={selectedTypeOfComment === choice}
                                                                onChange={() => {
                                                                    onCommentChange(section, 'type_of_comment', choice);
                                                                    onCommentChange(section, 'severity', opt.value);
                                                                }}
                                                                disabled={!isReviewEditable}
                                                            />
                                                            <span>{choice}</span>
                                                        </label>
                                                    )}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {/* Other type free-form input */}
                        <div className="SectionReview_other-field">
                            <label>Other:</label>
                            <input
                                type="text"
                                className="SectionReview_other-input"
                                placeholder="Custom comment type"
                                value={reviewComment?.type_of_comment === 'Other' ? '' : reviewComment?.type_of_comment || ''}
                                onChange={e => onCommentChange(section, 'type_of_comment', e.target.value)}
                                disabled={!isReviewEditable}
                            />
                        </div>
                        </div>
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
                    </div>
                </div>
            )}

            {/* Reply Modal */}
            {replyModalOpen !== null && (
                <div className="SectionReview_reply_modal_overlay">
                    <div className="SectionReview_reply_modal">
                        <div className="SectionReview_reply_modal_header">
                            <h4>Reply to Feedback</h4>
                            <button
                                className="SectionReview_reply_modal_close"
                                onClick={() => setReplyModalOpen(null)}
                            >
                                <FontAwesomeIcon icon={faTimes} />
                            </button>
                        </div>
                        <div className="SectionReview_reply_modal_body">
                            <textarea
                                className="SectionReview_reply_modal_textarea"
                                placeholder="Write your reply..."
                                value={replyText}
                                onChange={(e) => setReplyText(e.target.value)}
                            />
                            <div className="SectionReview_reply_modal_status">
                                <label>Status:</label>
                                <select
                                    value={replyStatus}
                                    onChange={(e) => setReplyStatus(e.target.value)}
                                >
                                    <option value="pending">Pending</option>
                                    <option value="resolved">Resolved</option>
                                    <option value="acknowledged">Acknowledged</option>
                                    <option value="needs-more-info">Needs More Info</option>
                                </select>
                            </div>
                        </div>
                        <div className="SectionReview_reply_modal_footer">
                            <button
                                className="btn btn--secondary btn--small"
                                onClick={() => setReplyModalOpen(null)}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn btn--primary btn--small"
                                onClick={() => handleReplySubmit(replyModalOpen)}
                                disabled={!replyText.trim()}
                            >
                                Save Reply
                            </button>
                        </div>
                    </div>
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
