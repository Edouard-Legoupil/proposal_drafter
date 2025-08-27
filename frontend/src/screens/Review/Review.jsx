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
                const response = await fetch(`${API_BASE_URL}/load-draft/${proposal_id}`, {
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
                                initialComments[section] = ""
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

        function handleCommentChange(section, text) {
                setReviewComments(prev => ({
                        ...prev,
                        [section]: text
                }))
        }

        async function handleSubmitReview() {
                const response = await fetch(`${API_BASE_URL}/proposals/${proposal_id}/review`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ review_data: reviewComments }),
                        credentials: "include"
                })

                if(response.ok)
                {
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

        return <Base>
                <div className="Review">
                        <div className="Review_header">
                                <h1>Reviewing: {proposal.form_data['Project Draft Short name']}</h1>
                                <CommonButton label="Review Completed" onClick={handleSubmitReview} />
                        </div>
                        <div className="Review_proposal">
                                {Object.entries(proposal.generated_sections).map(([section, content]) => (
                                        <div key={section} className="Review_section">
                                                <h2>{section}</h2>
                                                <div className="Review_section_content">
                                                        <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                                                </div>
                                                <textarea
                                                        className="Review_comment_textarea"
                                                        placeholder={`Your comments for ${section}...`}
                                                        value={reviewComments[section] || ""}
                                                        onChange={e => handleCommentChange(section, e.target.value)}
                                                />
                                        </div>
                                ))}
                        </div>
                        <div className="Review_footer">
                                <CommonButton label="Review Completed" onClick={handleSubmitReview} />
                        </div>
                </div>
        </Base>
}
