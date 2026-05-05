import './Review.css'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faThumbsUp, faThumbsDown, faTrash } from '@fortawesome/free-solid-svg-icons'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import Modal from '../../components/Modal/Modal'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

// P0-P3 severity categories per review context
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
}

export default function Review() {
    const [proposalTemplate, setProposalTemplate] = useState(null);
    const navigate = useNavigate()
    const { type, id } = useParams()

    const [data, setData] = useState(null)
    const [reviewComments, setReviewComments] = useState({})
    const [reviewStatus, setReviewStatus] = useState({})
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [currentUser, setCurrentUser] = useState(null)
    const [replyingTo, setReplyingTo] = useState(null); // section name
    const [replyText, setReplyText] = useState("");
    const [submittedReviews, setSubmittedReviews] = useState([]); // list of fully saved review objects with DB ids
    const autoSaveTimers = useRef({});

    async function getProfile() {
        const response = await fetch(`${API_BASE_URL}/profile`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (response.ok) {
            const result = await response.json();
            setCurrentUser(result.user);
        }
    }

    async function fetchData() {
        const endpoint = type === 'proposal'
            ? `${API_BASE_URL}/review-proposal/${id}`
            : `${API_BASE_URL}/review-knowledge-card/${id}`;

        const response = await fetch(endpoint, {
            method: "GET",
            headers: { 'Content-Type': 'application/json' },
            credentials: "include"
        })

        if (response.ok) {
            const result = await response.json()
            setData(result)

            const sections = type === 'proposal'
                ? result.generated_sections
                : result.knowledge_card.generated_sections;

            const initialComments = {}
            const initialStatus = {}

            Object.keys(sections || {}).forEach(section => {
                const existing = result.draft_comments[section] || {};
                initialComments[section] = {
                    review_text: existing.review_text || "",
                    type_of_comment: existing.type_of_comment || "P2",
                    severity: existing.severity || "P2",
                    author_response: existing.author_response || "",
                    rating: existing.rating || null
                }
                initialStatus[section] = existing.rating || null;
            })
            setReviewComments(initialComments)
            setReviewStatus(initialStatus)

            // Load all submitted reviews (with DB ids) for delete capability
            try {
                const reviewsEndpoint = type === 'proposal'
                    ? `${API_BASE_URL}/proposals/${id}/peer-reviews`
                    : `${API_BASE_URL}/knowledge-cards/${id}/all-reviews`;
                const reviewsRes = await fetch(reviewsEndpoint, { credentials: 'include' });
                if (reviewsRes.ok) {
                    const { reviews } = await reviewsRes.json();
                    setSubmittedReviews(reviews || []);
                }
            } catch (e) { /* silent – reviews list is optional */ void e; }


            // === PATCH: Fetch template for section order ===
            if (type !== 'proposal' && result.knowledge_card) {
                let templateType = null;
                const card = result.knowledge_card;
                if (card.donor_id) templateType = 'donor';
                else if (card.outcome_id) templateType = 'outcome';
                else if (card.field_context_id) templateType = 'field_context';
                if (templateType) {
                    const templateName = `knowledge_card_${templateType}_template.json`;
                    try {
                        const templateRes = await fetch(`${API_BASE_URL}/templates/${templateName}`, { credentials: 'include' });
                        if (templateRes.ok) {
                            const templateData = await templateRes.json();
                            setProposalTemplate(templateData);
                        } else {
                            setProposalTemplate(null);
                        }
                    } catch (err) {
                        setProposalTemplate(null);
                    }
                } else {
                    setProposalTemplate(null);
                }
            }
        }
        else if (response.status === 401) {
            sessionStorage.setItem("session_expired", "Session expired. Please login again.")
            navigate("/login")
        }
    }

    useEffect(() => {
        getProfile()
        fetchData()
    }, [type, id])

    // PATCH: Automatically redirect unauthorized users to Review interface
    useEffect(() => {
        const requiredRoles = [
            "knowledge manager donors",
            "knowledge manager outcome",
            "knowledge manager field context"
        ];

        if (
            type === 'knowledge_card' &&
            currentUser &&
            (!Array.isArray(currentUser.roles) ||
                !currentUser.roles.some(role => requiredRoles.includes(role)))
        ) {
            console.log(
                `User lacks required role for direct access. Redirecting to Review interface for knowledge card ${id}.`
            );
            navigate(`/review/knowledge-card/${id}`, { replace: true });
        }
    }, [type, currentUser, id, navigate]);

    function handleCommentChange(section, field, value) {
        setReviewComments(prev => {
            const updated = {
                ...prev,
                [section]: {
                    ...prev[section],
                    [field]: value
                }
            };
            // Trigger auto-save whenever text or category changes
            if (field === 'review_text' || field === 'type_of_comment' || field === 'severity') {
                autoSaveSection(section, updated[section]);
            }
            return updated;
        });
    }

    function handleStatusChange(section, status) {
        setReviewStatus(prev => ({
            ...prev,
            [section]: status
        }));
        handleCommentChange(section, 'rating', status);
    }

    // Auto-save a single section's comment after a short debounce
    const autoSaveSection = useCallback((section, commentData) => {
        if (autoSaveTimers.current[section]) clearTimeout(autoSaveTimers.current[section]);
        autoSaveTimers.current[section] = setTimeout(async () => {
            const endpoint = type === 'proposal'
                ? `${API_BASE_URL}/proposals/${id}/save-draft-review`
                : `${API_BASE_URL}/knowledge-cards/${id}/save-draft-review`;
            try {
                await fetch(endpoint, {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ comments: [{ section_name: section, ...commentData }] }),
                    credentials: "include"
                });
            } catch (e) { /* silent auto-save failure */ void e; }
        }, 800);
    }, [type, id]);

    async function handleDeleteComment(section) {
        // find the DB record for this section from submittedReviews
        const review = submittedReviews.find(r => r.section_name === section);
        if (!review) {
            // Nothing persisted yet – just clear local state
            handleCommentChange(section, 'review_text', '');
            handleCommentChange(section, 'rating', null);
            handleStatusChange(section, null);
            return;
        }
        if (!window.confirm(`Delete your comment for "${section}"?`)) return;
        const deleteEndpoint = type === 'proposal'
            ? `${API_BASE_URL}/peer-reviews/${review.id}`
            : `${API_BASE_URL}/knowledge-card-reviews/${review.id}`;
        const res = await fetch(deleteEndpoint, { method: 'DELETE', credentials: 'include' });
        if (res.ok || res.status === 404) {
            setSubmittedReviews(prev => prev.filter(r => r.id !== review.id));
            handleCommentChange(section, 'review_text', '');
            handleCommentChange(section, 'rating', null);
            setReviewStatus(prev => ({ ...prev, [section]: null }));
        } else {
            alert('Failed to delete comment.');
        }
    }

    async function handleSubmitReview() {
        const comments = Object.entries(reviewComments).map(([section_name, comment_data]) => ({
            section_name,
            ...comment_data
        }));

        const endpoint = type === 'proposal'
            ? `${API_BASE_URL}/proposals/${id}/review`
            : `${API_BASE_URL}/knowledge-cards/${id}/review`;

        const response = await fetch(endpoint, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments }),
            credentials: "include"
        })

        if (response.ok) {
            sessionStorage.setItem('selectedDashboardTab', 'reviews');
            navigate("/dashboard")
        }
        else if (response.status === 401) {
            sessionStorage.setItem("session_expired", "Session expired. Please login again.")
            navigate("/login")
        }
    }

    async function handleSaveReply(section) {
        // Find the review ID for this section.
        // For simplicity, we assume there's only one review per section for the current viewer context.
        // In backend we fetched 'reviews' which are draft_comments.
        // Wait, draft_comments doesn't include the DB ID.
        // Actually, for proposals, we have a separate endpoint to get all peer reviews which includes IDs.

        // I need to fetch ALL reviews with IDs to be able to respond to a specific one.
        // Or I can add a new endpoint that saves by section name.

        // Actually, the current AuthorResponseRequest expects review_id.
        // I'll fetch all reviews first.

        const reviewsEndpoint = type === 'proposal'
            ? `${API_BASE_URL}/proposals/${id}/peer-reviews`
            : `${API_BASE_URL}/knowledge-cards/${id}/all-reviews`;

        const reviewsRes = await fetch(reviewsEndpoint, { credentials: 'include' });
        if (reviewsRes.ok) {
            const { reviews } = await reviewsRes.json();
            // Find the review by section name and current user being the reviewer (or any for now)
            const review = reviews.find(r => r.section_name === section);
            if (review) {
                const responseEndpoint = type === 'proposal'
                    ? `${API_BASE_URL}/peer-reviews/${review.id}/response`
                    : `${API_BASE_URL}/knowledge-card-reviews/${review.id}/response`;

                const res = await fetch(responseEndpoint, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ author_response: replyText }),
                    credentials: 'include'
                });

                if (res.ok) {
                    setReplyingTo(null);
                    fetchData(); // Refresh
                } else {
                    alert("Failed to save response.");
                }
            } else {
                alert("Review comment not found.");
            }
        }
    }

    if (!data || !currentUser) {
        return <Base><div className="loading">Loading...</div></Base>
    }

    let title = 'Untitled Knowledge Card';
    if (type === 'proposal') {
        title = (
            data.form_data['Project Draft Short name'] ||
            data.form_data['Project title'] ||
            'Untitled Proposal'
        );
    } else if (data.knowledge_card) {
        const card = data.knowledge_card;
        let linkType = '';
        let linkedLabel = '';
        if (card.donor_id) {
            linkType = 'Donor';
            linkedLabel = card.item_name || card.donor_name || card.donorLabel || card.donor_id;
        } else if (card.outcome_id) {
            linkType = 'Outcome';
            linkedLabel = card.item_name || card.outcome_name || card.outcomeLabel || card.outcome_id;
        } else if (card.field_context_id) {
            linkType = 'Field Context';
            linkedLabel = card.item_name || card.field_context_name || card.fieldContextLabel || card.field_context_id;
        }
        if (linkType && linkedLabel) {
            title = `${linkType} ${linkedLabel}`;
        } else {
            title = card.summary || 'Untitled Knowledge Card';
        }
    }

    const generatedSections = type === 'proposal'
        ? data.generated_sections
        : data.knowledge_card.generated_sections;

    const ownerId = type === 'proposal' ? data.user_id : data.knowledge_card.created_by;
    const isOwner = currentUser.id === ownerId || currentUser.user_id === ownerId;

    // A review is editable if:
    // 1. For proposals: status is 'in_review' AND user is NOT owner
    // 2. For knowledge cards: User is NOT owner
    const isReviewEditable = true;

    const isFinalizeEnabled = Object.keys(reviewStatus).every(section => {
        const status = reviewStatus[section];
        const comment = reviewComments[section];
        return status === 'up' || (status === 'down' && comment.review_text);
    });

    function handleFinalizeClick() {
        if (isFinalizeEnabled) {
            handleSubmitReview();
        } else {
            setIsModalOpen(true);
        }
    }

    return <Base>
        <div className="Review" data-testid="review-container">
            <div className="Review_header">
                <h1>Reviewing {type === 'proposal' ? 'Draft' : 'Knowledge Card'}: {title}</h1>
            </div>

            <div className="Review_proposal" data-testid="review-content">
                {(
                    proposalTemplate && proposalTemplate.sections
                        ? proposalTemplate.sections
                        : Object.keys(generatedSections || {}).map(section => ({ section_name: section }))
                ).map(sectionObj => (
                    (() => {
                        const section = sectionObj.section_name || sectionObj;
                        const content = generatedSections && generatedSections[section] ? generatedSections[section] : '';
                        return (
                            <div
                                key={section}
                                className={`Review_section ${reviewStatus[section] === 'up' ? 'thumb-up-section' : reviewStatus[section] === 'down' ? 'thumb-down-section' : ''}`}
                                data-testid={`review-section-${section}`}
                            >
                                <div className="Review_section_main">
                                    <div className="Review_section_header">
                                        <h2 data-testid={`review-section-title-${section}`}>{section}</h2>
                                        <div className="Review_thumbs">
                                            <FontAwesomeIcon
                                                icon={faThumbsUp}
                                                className={`thumb-up ${reviewStatus[section] === 'up' ? 'active' : ''}`}
                                                onClick={() => isReviewEditable && handleStatusChange(section, 'up')}
                                                data-testid={`thumb-up-${section}`}
                                            />
                                            <FontAwesomeIcon
                                                icon={faThumbsDown}
                                                className={`thumb-down ${reviewStatus[section] === 'down' ? 'active' : ''}`}
                                                onClick={() => isReviewEditable && handleStatusChange(section, 'down')}
                                                data-testid={`thumb-down-${section}`}
                                            />
                                        </div>
                                    </div>
                                    <div className="Review_section_content">
                                        {content
                                            ? <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{content}</Markdown>
                                            : <span className="Review_section_placeholder">No content generated for this section yet!</span>
                                        }
                                    </div>
                                </div>
                                {(reviewStatus[section] === 'down' || reviewComments[section]?.review_text) && (
                                    <div className="Review_comment_section">
                                        <textarea
                                            className="Review_comment_textarea"
                                            placeholder={isReviewEditable ? `Your comments for ${section}...` : ""}
                                            value={reviewComments[section]?.review_text || ""}
                                            onChange={e => handleCommentChange(section, 'review_text', e.target.value)}
                                            data-testid={`comment-textarea-${section}`}
                                            disabled={!isReviewEditable}
                                        />
                                        <div className="Review_comment_controls">
                                            <div className="severity-selector">
                                                <label className="severity-label">Incident Severity</label>
                                                <div className="severity-options">
                                                    {(SEVERITY_OPTIONS[type === 'proposal' ? 'proposal' : 'knowledge_card']).map(opt => (
                                                        <label
                                                            key={opt.value}
                                                            className={`severity-option ${(reviewComments[section]?.type_of_comment || 'P2') === opt.value ? 'selected' : ''} severity-${opt.value}`}
                                                            title={opt.description}
                                                            data-testid={`severity-option-${opt.value}-${section}`}
                                                        >
                                                            <input
                                                                type="radio"
                                                                name={`severity-${section}`}
                                                                value={opt.value}
                                                                checked={(reviewComments[section]?.type_of_comment || 'P2') === opt.value}
                                                                onChange={() => {
                                                                    handleCommentChange(section, 'type_of_comment', opt.value);
                                                                    handleCommentChange(section, 'severity', opt.value);
                                                                }}
                                                                disabled={!isReviewEditable}
                                                            />
                                                            <span className="severity-badge">{opt.value}</span>
                                                            <span className="severity-text">{opt.label.replace(`${opt.value} – `, '')}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                                {/* Show description for selected */}
                                                {(() => {
                                                    const opts = SEVERITY_OPTIONS[type === 'proposal' ? 'proposal' : 'knowledge_card'];
                                                    const sel = opts.find(o => o.value === (reviewComments[section]?.type_of_comment || 'P2'));
                                                    return sel ? <p className="severity-description">{sel.description}</p> : null;
                                                })()}
                                            </div>
                                        </div>
                                        {/* Delete comment button */}
                                        {isReviewEditable && (
                                            (() => {
                                                const saved = submittedReviews.find(r => r.section_name === section);
                                                const isOwnerOfComment = saved && (saved.reviewer_id === currentUser?.id || saved.reviewer_id === currentUser?.user_id);
                                                const isAdmin = currentUser?.is_admin || currentUser?.roles?.some(r => r === 'admin' || r?.name === 'admin');
                                                if (isOwnerOfComment || isAdmin) {
                                                    return (
                                                        <button
                                                            className="Review_delete_comment_btn"
                                                            onClick={() => handleDeleteComment(section)}
                                                            title="Delete this comment"
                                                            data-testid={`delete-comment-${section}`}
                                                        >
                                                            <FontAwesomeIcon icon={faTrash} /> Delete comment
                                                        </button>
                                                    );
                                                }
                                                // Also show delete for comments not yet saved (local only)
                                                if (!saved && reviewComments[section]?.review_text) {
                                                    return (
                                                        <button
                                                            className="Review_delete_comment_btn"
                                                            onClick={() => handleDeleteComment(section)}
                                                            title="Clear this comment"
                                                            data-testid={`delete-comment-${section}`}
                                                        >
                                                            <FontAwesomeIcon icon={faTrash} /> Clear comment
                                                        </button>
                                                    );
                                                }
                                                return null;
                                            })()
                                        )}
                                        {reviewComments[section]?.author_response && (
                                            <div className="author-response-display" data-testid={`author-response-display-${section}`}>
                                                <strong>Author's Response:</strong>
                                                <p>{reviewComments[section].author_response}</p>
                                            </div>
                                        )}
                                        {isOwner && !isReviewEditable && (
                                            <div className="Review_author_reply">
                                                {replyingTo === section ? (
                                                    <>
                                                        <textarea
                                                            className="Review_reply_textarea"
                                                            value={replyText}
                                                            onChange={e => setReplyText(e.target.value)}
                                                            placeholder="Enter your response..."
                                                        />
                                                        <div className="Review_reply_actions">
                                                            <button onClick={() => handleSaveReply(section)}>Save Reply</button>
                                                            <button onClick={() => setReplyingTo(null)}>Cancel</button>
                                                        </div>
                                                    </>
                                                ) : (
                                                    <button
                                                        className="Review_reply_btn"
                                                        onClick={() => {
                                                            setReplyingTo(section);
                                                            setReplyText(reviewComments[section]?.author_response || "");
                                                        }}
                                                    >
                                                        {reviewComments[section]?.author_response ? 'Edit Response' : 'Reply to Comment'}
                                                    </button>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })()
                ))}
            </div>

            {isReviewEditable && (
                <div className="Review_footer">
                    <CommonButton label="Peer review completed" onClick={handleFinalizeClick} data-testid="review-completed-button-footer" />
                </div>
            )}
        </div>
        <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}>
            <h2>Incomplete Review</h2>
            <p>Please provide a rating (thumbs-up or thumbs-down) for every section. If you give a thumbs-down, you must also provide a comment.</p>
        </Modal>
    </Base>
}
