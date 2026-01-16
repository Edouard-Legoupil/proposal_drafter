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

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

export default function Review() {
        const navigate = useNavigate()
        const { proposal_id } = useParams()

        const [proposal, setProposal] = useState(null)
        const [reviewComments, setReviewComments] = useState({})
        const [reviewStatus, setReviewStatus] = useState({})
        const [isModalOpen, setIsModalOpen] = useState(false)

        async function getProposal() {
                const response = await fetch(`${API_BASE_URL}/review-proposal/${proposal_id}`, {
                        method: "GET",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if (response.ok) {
                        const data = await response.json()
                        setProposal(data)
                        const initialComments = {}
                        const initialStatus = {}
                        Object.keys(data.generated_sections).forEach(section => {
                                initialComments[section] = data.draft_comments[section] || {
                                        review_text: "",
                                        type_of_comment: "General",
                                        severity: "Medium",
                                        author_response: ""
                                }
                                initialStatus[section] = null;
                        })
                        setReviewComments(initialComments)
                        setReviewStatus(initialStatus)
                }
                else if (response.status === 401) {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        useEffect(() => {
                getProposal()
        }, [proposal_id])

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

                if (status === 'up') {
                        // Reset comment when thumbing up
                        handleCommentChange(section, 'review_text', '');
                }
        }

        async function handleSaveDraft() {
                const comments = Object.entries(reviewComments).map(([section_name, comment_data]) => ({
                        section_name,
                        ...comment_data
                }));

                const response = await fetch(`${API_BASE_URL}/proposals/${proposal_id}/save-draft-review`, {
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

                const response = await fetch(`${API_BASE_URL}/proposals/${proposal_id}/review`, {
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

        if (!proposal) {
                return <Base><div className="loading">Loading...</div></Base>
        }

        const isReviewEditable = proposal.status === 'in_review';

        const isFinalizeEnabled = Object.keys(reviewStatus).every(section => {
                const status = reviewStatus[section];
                const comment = reviewComments[section];
                return status === 'up' || (status === 'down' && comment.review_text && comment.type_of_comment && comment.severity);
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
                                <h1>Reviewing: {proposal.form_data['Project Draft Short name']}</h1>
                        </div>
                        
<div className="Review_proposal" data-testid="review-proposal-content">
                                {Object.entries(proposal.generated_sections).map(([section, content]) => (
                                        <div key={section} className={`Review_section ${reviewStatus[section] === 'up' ? 'thumb-up-section' : reviewStatus[section] === 'down' ? 'thumb-down-section' : ''}`} data-testid={`review-section-${section}`}>
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
                                                                <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{content}</Markdown>
                                                        </div>
                                                </div>
                                                {reviewStatus[section] === 'down' && (
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
                                                                        <select value={reviewComments[section]?.type_of_comment || 'General'} onChange={e => handleCommentChange(section, 'type_of_comment', e.target.value)} data-testid={`comment-type-select-${section}`} disabled={!isReviewEditable}>
                                                                                <option value="General">General</option>
                                                                                <option value="Clarity">Clarity</option>
                                                                                <option value="Compliance">Compliance</option>
                                                                                <option value="Impact">Impact</option>
                                                                        </select>
                                                                        <select value={reviewComments[section]?.severity || 'Medium'} onChange={e => handleCommentChange(section, 'severity', e.target.value)} data-testid={`severity-select-${section}`} disabled={!isReviewEditable}>
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
                                                        </div>
                                                )}
                                        </div>
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
                        <p>Please provide a rating (thumbs-up or thumbs-down) for every section. If you give a thumbs-down, you must also provide a comment and classify it.</p>
                </Modal>
        </Base>
}
