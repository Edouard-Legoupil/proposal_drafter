import './Review.css'

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

export default function Review ()
{
        const navigate = useNavigate()
        const { proposal_id } = useParams()

        const [proposal, setProposal] = useState(null)
        const [reviewComments, setReviewComments] = useState({})

        async function getProposal() {
                const response = await fetch(`${API_BASE_URL}/review-proposal/${proposal_id}`, {
                        method: "GET",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if(response.ok)
                {
                        const data = await response.json()
                        setProposal(data)
                        const initialComments = {}
                        Object.keys(data.generated_sections).forEach(section => {
                            initialComments[section] = {
                                review_text: "",
                                type_of_comment: "General",
                                severity: "Medium"
                            }
                        })
                        setReviewComments(initialComments)
                }
                else if(response.status === 401)
                {
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

                if(response.ok)
                {
                        sessionStorage.setItem('selectedDashboardTab', 'reviews');
                        navigate("/dashboard")
                }
                else if(response.status === 401)
                {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        if (!proposal) {
                return <Base><div className="loading">Loading...</div></Base>
        }

        const isReviewCompleted = proposal.review_status === 'completed';

        return <Base>
                <div className="Review">
                        <div className="Review_header">
                                <h1>Reviewing: {proposal.form_data['Project Draft Short name']}</h1>
                                <CommonButton label="Review Completed" onClick={handleSubmitReview} data-testid="review-completed-button-header" disabled={isReviewCompleted} />
                        </div>
                        <div className="Review_proposal">
                                {Object.entries(proposal.generated_sections).map(([section, content]) => (
                                        <div key={section} className="Review_section">
                                                <h2>{section}</h2>
                                                <div className="Review_section_content">
                                                        <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                                                </div>
                                                <div className="Review_comment_controls">
                                                    <select value={reviewComments[section]?.type_of_comment || 'General'} onChange={e => handleCommentChange(section, 'type_of_comment', e.target.value)} data-testid={`comment-type-select-${section}`} disabled={isReviewCompleted}>
                                                        <option value="General">General</option>
                                                        <option value="Clarity">Clarity</option>
                                                        <option value="Compliance">Compliance</option>
                                                        <option value="Impact">Impact</option>
                                                    </select>
                                                    <select value={reviewComments[section]?.severity || 'Medium'} onChange={e => handleCommentChange(section, 'severity', e.target.value)} data-testid={`severity-select-${section}`} disabled={isReviewCompleted}>
                                                        <option value="Low">Low</option>
                                                        <option value="Medium">Medium</option>
                                                        <option value="High">High</option>
                                                    </select>
                                                </div>
                                                <textarea
                                                        className="Review_comment_textarea"
                                                        placeholder={isReviewCompleted ? "Review completed. No new comments can be added." : `Your comments for ${section}...`}
                                                        value={reviewComments[section]?.review_text || ""}
                                                        onChange={e => handleCommentChange(section, 'review_text', e.target.value)}
                                                        data-testid={`comment-textarea-${section}`}
                                                        disabled={isReviewCompleted}
                                                />
                                        </div>
                                ))}
                        </div>
                        <div className="Review_footer">
                                <CommonButton label="Review Completed" onClick={handleSubmitReview} data-testid="review-completed-button-footer" disabled={isReviewCompleted} />
                        </div>
                </div>
        </Base>
}
