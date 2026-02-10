import './Review.css'

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faThumbsUp, faThumbsDown } from '@fortawesome/free-solid-svg-icons'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import Modal from '../../components/Modal/Modal'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

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
                    type_of_comment: existing.type_of_comment || "General",
                    severity: existing.severity || "Medium",
                    author_response: existing.author_response || "",
                    rating: existing.rating || null
                }
                initialStatus[section] = existing.rating || null;
            })
            setReviewComments(initialComments)
            setReviewStatus(initialStatus)

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
        setReviewComments(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [field]: value
            }
        }))
    }

    function handleStatusChange(section, status) {
        setReviewStatus(prev => ({
            ...prev,
            [section]: status
        }));
        handleCommentChange(section, 'rating', status);

        if (status === 'up') {
            // Reset comment fields when thumbing up, if you want it strict
            // handleCommentChange(section, 'review_text', '');
        }
    }

    async function handleSaveDraft() {
        const comments = Object.entries(reviewComments).map(([section_name, comment_data]) => ({
            section_name,
            ...comment_data
        }));

        const endpoint = type === 'proposal'
            ? `${API_BASE_URL}/proposals/${id}/save-draft-review`
            : `${API_BASE_URL}/knowledge-cards/${id}/save-draft-review`;

        const response = await fetch(endpoint, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments }),
            credentials: "include"
        })

        if (response.ok) {
            alert("Draft saved successfully!")
        }
        else if (response.status === 401) {
            sessionStorage.setItem("session_expired", "Session expired. Please login again.")
            navigate("/login")
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
                                            <select
                                                value={reviewComments[section]?.type_of_comment || 'General'}
                                                onChange={e => handleCommentChange(section, 'type_of_comment', e.target.value)}
                                                data-testid={`comment-type-select-${section}`}
                                                disabled={!isReviewEditable}
                                            >
                                                <option value="General">General</option>
                                                <option value="Clarity">Clarity</option>
                                                <option value="Compliance">Compliance</option>
                                                <option value="Impact">Impact</option>
                                            </select>
                                            <select
                                                value={reviewComments[section]?.severity || 'Medium'}
                                                onChange={e => handleCommentChange(section, 'severity', e.target.value)}
                                                data-testid={`severity-select-${section}`}
                                                disabled={!isReviewEditable}
                                            >
                                                <option value="Low">Low</option>
                                                <option value="Medium">Medium</option>
                                                <option value="High">High</option>
                                            </select>
                                        </div>
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
                    <CommonButton label="Save as draft review" onClick={handleSaveDraft} data-testid="save-draft-button-footer" />
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
