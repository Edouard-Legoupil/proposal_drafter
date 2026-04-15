import Base from '../../components/Base/Base'
import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import './DonorTemplateDetail.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faThumbsDown, faComments, faListCheck, faRobot, faList, faArrowLeft, faFileLines, faFileContract, faTrash, faCircleInfo } from '@fortawesome/free-solid-svg-icons'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"
import SectionReview from '../../components/SectionReview/SectionReview'

export default function DonorTemplateDetail() {
    const { id } = useParams()
    const [searchParams] = useSearchParams()
    const type = searchParams.get('type') // 'file' or 'db'
    const navigate = useNavigate()

    const [template, setTemplate] = useState(null)
    const [reviewComments, setReviewComments] = useState({})
    const [reviewStatus, setReviewStatus] = useState({})
    const [isSubmittingComment, setIsSubmittingComment] = useState(false)
    const [error, setError] = useState(null)
    const [currentUser, setCurrentUser] = useState(null)

    const fetchTemplate = useCallback(async () => {
        try {
            const profileRes = await fetch(`${API_BASE_URL}/profile`, { credentials: 'include' })
            if (profileRes.ok) {
                const profileData = await profileRes.json()
                setCurrentUser(profileData.user)
            }

            if (type === 'db') {
                const res = await fetch(`${API_BASE_URL}/templates/request/${id}`, { credentials: 'include' })
                if (res.ok) {
                    const data = await res.json()
                    setTemplate({ ...data, type: 'db' })
                } else {
                    setError("Failed to fetch template details")
                }
            } else {
                const res = await fetch(`${API_BASE_URL}/templates/published/${id}`, { credentials: 'include' })
                if (res.ok) {
                    const data = await res.json()
                    setTemplate({
                        ...data,
                        id: id,
                        name: data.template_name || id,
                        status: 'published',
                        type: 'file',
                        template_type: data.template_type || 'Proposal',
                        configuration: {
                            instructions: data.special_requirements?.instructions || [],
                            sections: data.sections || [],
                        }
                    })
                } else {
                    setError("Failed to fetch published template details")
                }
            }
        } catch (error) {
            console.error("Fetch error:", error)
            setError("Error connecting to server")
        }
    }, [id, type])

    useEffect(() => { fetchTemplate() }, [fetchTemplate])

    // ── Helpers ────────────────────────────────────────────────────────────
    const getSectionsSortedByReading = (sections) => {
        if (!sections || sections.length === 0) return []
        return [...sections].sort((a, b) => {
            const ra = typeof a === 'object' ? (a.reading_sequence ?? 999) : 999
            const rb = typeof b === 'object' ? (b.reading_sequence ?? 999) : 999
            return ra - rb
        })
    }

    const getSectionsSortedByGeneration = (sections) => {
        if (!sections || sections.length === 0) return []
        return [...sections].sort((a, b) => {
            const ga = typeof a === 'object' ? (a.generation_sequence ?? 999) : 999
            const gb = typeof b === 'object' ? (b.generation_sequence ?? 999) : 999
            return ga - gb
        })
    }

    // ── Rendering helpers ──────────────────────────────────────────────────
    const renderHighLevelInstructions = () => {
        const instructions = template.configuration?.instructions || []
        if (instructions.length === 0) return null

        const hliName = "High-level Instructions"
        const rating = template.comments?.find(c => c.section_name === hliName && c.user === currentUser?.name)?.rating || null
        const comment = template.comments?.find(c => c.section_name === hliName && c.user === currentUser?.name)?.text || ''

        return (
            <div className="hli-panel">
                <div className="hli-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h4 style={{ margin: 0 }}><FontAwesomeIcon icon={faListCheck} style={{ marginRight: '8px' }} /> High-level Instructions</h4>
                </div>

                <ol className="hli-list">
                    {instructions.map((instr, idx) => (
                        <li key={idx}>{instr}</li>
                    ))}
                </ol>

                {/* HLI Inline Comment Form wrapped in SectionReview */}
                {(() => {
                    const existingSelf = template.comments?.find(c => c.section_name === hliName && (c.user_id === currentUser?.id || c.user_id === currentUser?.user_id));
                    
                    return (
                        <SectionReview
                            section={hliName}
                            type="template"
                            status={reviewStatus[hliName]}
                            reviewComment={reviewComments[hliName]}
                            isReviewEditable={true}
                            isAuthorizedToReply={false}
                            onSaveReply={handleSaveResponse}
                            onStatusChange={(sec, stat) => {
                                setReviewStatus(prev => ({ ...prev, [sec]: stat }));
                                if (stat === 'down' && !reviewComments[sec] && existingSelf) {
                                    setReviewComments(prev => ({ 
                                        ...prev, 
                                        [sec]: { 
                                            id: existingSelf.id,
                                            review_text: existingSelf.text,
                                            severity: existingSelf.severity || 'P2',
                                            type_of_comment: existingSelf.type_of_comment || ''
                                        } 
                                    }));
                                }
                            }}
                            onCommentChange={(sec, field, val) => {
                                if (field === 'save') {
                                    handleSaveComment(sec, val);
                                } else {
                                    setReviewComments(prev => ({
                                        ...prev,
                                        [sec]: { ...prev[sec], [field]: val }
                                    }));
                                }
                            }}
                            onDeleteComment={(sec) => {
                                const commentId = reviewComments[sec]?.id || existingSelf?.id;
                                if (commentId) handleDeleteTemplateComment(commentId);
                                setReviewComments(prev => {
                                    const next = { ...prev };
                                    delete next[sec];
                                    return next;
                                });
                                setReviewStatus(prev => ({ ...prev, [sec]: null }));
                            }}
                            isOwnerOfComment={true}
                            isAdmin={currentUser?.is_admin}
                            previousFeedback={template.comments?.filter(c => c.section_name === hliName && c.status !== 'removed').map(c => ({
                                id: c.id,
                                author: c.user,
                                review_text: c.text,
                                severity: c.severity || 'P2',
                                type_of_comment: c.type_of_comment,
                                status: c.status,
                                isOwnedByCurrentUser: c.user_id === (currentUser?.id || currentUser?.user_id),
                                replies: c.author_response ? [{
                                    author: 'Author',
                                    text: c.author_response,
                                    status: c.status
                                }] : []
                            })) || []}
                            onReplyToFeedback={handleReplyToFeedback}
                            isExpanded={reviewStatus[hliName] === 'down'}
                        />
                    );
                })()}
            </div>
        )
    }

    const renderGenerationSequence = (sections) => {
        const sorted = getSectionsSortedByGeneration(sections)
        const hasSeq = sorted.some(s => typeof s === 'object' && s.generation_sequence != null)
        if (!hasSeq) return null
        return (
            <div className="gen-seq-panel">
                <h4><FontAwesomeIcon icon={faRobot} style={{ marginRight: '8px' }} /> AI Generation Order</h4>
                <ol className="gen-seq-list">
                    {sorted.map((s, idx) => {
                        const label = typeof s === 'object' ? (s.section_label || s.section_name) : s
                        const seq = typeof s === 'object' ? s.generation_sequence : idx + 1
                        return (
                            <li key={idx}>
                                <span className="gen-seq-num">{seq}</span>
                                <span>{label}</span>
                            </li>
                        )
                    })}
                </ol>
            </div>
        )
    }

    const renderGlobalComments = () => {
        const globalComments = template.comments?.filter(c => !c.section_name) || []
        if (globalComments.length === 0) return null
        return (
            <div className="global-comments-history">
                <h4 className="shared-history-title">
                    <FontAwesomeIcon icon={faComments} style={{ marginRight: '8px' }} />
                    Shared Template Feedback
                </h4>
                <div className="comments-list">
                    {globalComments.map(c => (
                        <div key={c.id} className="comment-item">
                            <div className="comment-header">
                                <strong>{c.user}</strong>
                                <span className="comment-date">{new Date(c.created_at).toLocaleString()}</span>
                            </div>
                            <div className="comment-body">{c.text}</div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    const renderSections = () => {
        const raw = template.configuration?.sections || []
        if (raw.length === 0) return <p className="no-data">No sections defined.</p>

        const sections = getSectionsSortedByReading(raw)

        return (
            <div className="template-sections">
                {sections.map((section, idx) => {
                    const isObject = typeof section === 'object' && section !== null
                    const name = isObject ? (section.section_label || section.section_name) : section
                    const instructions = isObject ? section.instructions : null
                    const format = isObject ? (section.format_type || 'text') : 'text'
                    const wordLimit = isObject ? section.word_limit : null
                    const charLimit = isObject ? section.char_limit : null
                    const readSeq = isObject ? (section.reading_sequence ?? idx + 1) : idx + 1
                    const genSeq = isObject ? section.generation_sequence : null
                    const mandatory = isObject ? section.mandatory : null
                    const parent = isObject ? section.section_parent : null
                    const columns = isObject ? section.columns : null
                    const rows = isObject ? section.rows : null
                    const fixedText = isObject ? section.fixed_text : null

                    // Thumbs up/down state for this section
                    const sectionRating = template.comments?.find(c => c.section_name === name && c.user === currentUser?.name)?.rating || null
                    const sectionComment = template.comments?.find(c => c.section_name === name && c.user === currentUser?.name)?.text || ''

                    return (
                        <div key={idx} className="section-detail-card">
                            <div className="section-header">
                                <div className="section-title-group">
                                    <span className="section-read-seq">#{readSeq}</span>
                                    <h5>{name}</h5>
                                    {parent && <span className="section-parent-badge">↳ {parent}</span>}
                                </div>
                                <div className="section-meta">
                                    <span className="badge-format">{format}</span>
                                    {wordLimit && <span className="badge-limit">{wordLimit}w</span>}
                                    {charLimit && <span className="badge-limit">{charLimit}c</span>}
                                    {mandatory != null && (
                                        <span className={`badge-mandatory ${mandatory ? 'yes' : 'no'}`}>
                                            {mandatory ? 'Required' : 'Optional'}
                                        </span>
                                    )}
                                    {genSeq != null && (
                                        <span className="badge-gen" title={`AI Generation Order: ${genSeq}`}>
                                            <FontAwesomeIcon icon={faRobot} style={{ marginRight: '4px' }} />
                                            #{genSeq}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {instructions && (
                                <div className="section-instructions">
                                    <strong>Instructions:</strong> {instructions}
                                </div>
                            )}

                            {fixedText && (
                                <div className="section-fixed-text" style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#f0f4f8', borderRadius: '4px', borderLeft: '4px solid #3498db' }}>
                                    <strong>Fixed Text:</strong>
                                    <div style={{ marginTop: '4px', fontStyle: 'italic', color: '#444' }}>{fixedText}</div>
                                </div>
                            )}

                            {/* SectionReview Integrated - Single component per section */}
                            {(() => {
                                const existingSelf = template.comments?.find(c => c.section_name === name && (c.user_id === currentUser?.id || c.user_id === currentUser?.user_id));
                                
                                return (
                                    <SectionReview
                                        section={name}
                                        type="template"
                                        status={reviewStatus[name]}
                                        reviewComment={reviewComments[name]}
                                        isReviewEditable={true}
                                        onStatusChange={(sec, stat) => {
                                            setReviewStatus(prev => ({ ...prev, [sec]: stat }));
                                            if (stat === 'down' && !reviewComments[sec] && existingSelf) {
                                                setReviewComments(prev => ({ 
                                                    ...prev, 
                                                    [sec]: { 
                                                        id: existingSelf.id,
                                                        review_text: existingSelf.text,
                                                        severity: existingSelf.severity || 'P2',
                                                        type_of_comment: existingSelf.type_of_comment || ''
                                                    } 
                                                }));
                                            }
                                        }}
                                        onCommentChange={(sec, field, val) => {
                                            if (field === 'save') {
                                                handleSaveComment(sec, val);
                                            } else {
                                                setReviewComments(prev => ({
                                                    ...prev,
                                                    [sec]: { ...prev[sec], [field]: val }
                                                }));
                                            }
                                        }}
                                        onDeleteComment={(sec) => {
                                            const commentId = reviewComments[sec]?.id || existingSelf?.id;
                                            if (commentId) handleDeleteTemplateComment(commentId);
                                            setReviewComments(prev => {
                                                const next = { ...prev };
                                                delete next[sec];
                                                return next;
                                            });
                                            setReviewStatus(prev => ({ ...prev, [sec]: null }));
                                        }}
                                        isOwnerOfComment={true}
                                        isAdmin={currentUser?.is_admin}
                                        isAuthorizedToReply={isAdmin}
                                        onSaveReply={handleSaveResponse}
                                        previousFeedback={template.comments?.filter(c => c.section_name === name && c.user_id !== currentUser?.id && c.user_id !== currentUser?.user_id).map(c => ({
                                            id: c.id,
                                            author: c.user,
                                            review_text: c.text,
                                            severity: c.severity || 'P2',
                                            type_of_comment: c.type_of_comment,
                                            status: c.status,
                                            isOwnedByCurrentUser: false,
                                            replies: c.author_response ? [{
                                                author: 'Author',
                                                text: c.author_response,
                                                status: c.status
                                            }] : []
                                        })) || []}
                                        onReplyToFeedback={handleReplyToFeedback}
                                        isExpanded={reviewStatus[name] === 'down'}
                                    />
                                );
                            })()}

                            {format === 'table' && columns && (
                                <div className="table-preview-container">
                                    <h6>Table Structure</h6>
                                    <table className="preview-table">
                                        <thead>
                                            <tr>
                                                <th>Row / Column</th>
                                                {columns.map((col, cidx) => (
                                                    <th key={cidx}>{col.name}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rows ? rows.map((row, ridx) => (
                                                <tr key={ridx}>
                                                    <td className="row-title">{row.row_title}</td>
                                                    {columns.map((_, cidx) => (
                                                        <td key={cidx} className="placeholder-cell">…</td>
                                                    ))}
                                                </tr>
                                            )) : (
                                                <tr>
                                                    <td className="row-title">Generic Row</td>
                                                    {columns.map((_, cidx) => (
                                                        <td key={cidx} className="placeholder-cell">…</td>
                                                    ))}
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        )
    }

    // ── Comment handlers ───────────────────────────────────────────────────
    const handleSaveComment = async (section, textContent) => {
        if (!textContent.trim()) return
        setIsSubmittingComment(true)

        const reviewData = reviewComments[section] || {}

        try {
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    comment_text: textContent,
                    section_name: section || null,
                    severity: reviewData.severity || 'P2',
                    type_of_comment: reviewData.type_of_comment || '',
                    status: 'submitted'
                }),
                credentials: 'include'
            })

            if (res.ok) {
                await fetchTemplate()
                setReviewStatus(prev => ({ ...prev, [section]: null }))
                setReviewComments(prev => {
                    const next = { ...prev }
                    delete next[section]
                    return next
                })
            }
        } catch (err) {
            console.error("Error adding comment", err)
        } finally {
            setIsSubmittingComment(false)
        }
    }

    const handleDeleteTemplateComment = async (commentId) => {
        if (!window.confirm('Remove this comment?')) return
        try {
            // Change status to 'removed' instead of deleting
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/comment/${commentId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'removed' }),
                credentials: 'include'
            })
            
            if (res.ok) {
                await fetchTemplate()
            } else {
                alert('Failed to remove comment. The comment may have already been removed.')
            }
        } catch (err) {
            console.error('Error removing comment', err)
            alert('Error connecting to server. Please try again.')
        }
    }

    const handleSaveResponse = async (section, responseText) => {
        try {
            const existing = template.comments?.find(c => c.section_name === section && c.user === currentUser?.name);
            if (!existing?.id) {
                console.error('No comment ID found for author response');
                return;
            }
            
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/comment/${existing.id}/response`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ author_response: responseText }),
                credentials: 'include'
            })
            
            if (res.ok) {
                await fetchTemplate()
            } else {
                alert('Failed to save response. Please try again.')
            }
        } catch (err) {
            console.error('Error saving author response', err)
            alert('Error connecting to server. Please try again.')
        }
    }

    const handleReplyToFeedback = async (feedbackId, replyText, replyStatus) => {
        try {
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/reply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    author_response: replyText,
                    feedback_id: feedbackId,
                    status: replyStatus
                }),
                credentials: 'include'
            })
            
            if (res.ok) {
                await fetchTemplate()
            } else {
                alert('Failed to save reply. Please try again.')
            }
        } catch (err) {
            console.error('Error saving reply', err)
            alert('Error connecting to server. Please try again.')
        }
    }

    const handleUpdateStatus = async (newStatus) => {
        try {
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus }),
                credentials: 'include'
            })
            if (res.ok) {
                setTemplate({ ...template, status: newStatus })
            }
        } catch (err) {
            console.error("Error updating status", err)
        }
    }

    const handleDownloadJson = () => {
        if (!template?.initial_file_content) return
        const blob = new Blob([JSON.stringify(template.initial_file_content, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${template.name.toLowerCase().replace(/\s+/g, '_')}_template.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    if (error) return <Base><div className="error-container">{error}</div></Base>
    if (!template) return <Base><div className="loading">Loading...</div></Base>

    const isAdmin = currentUser?.is_admin || currentUser?.roles?.some(r => r.name === 'admin' || r.name === 'knowledge manager donors')
    const sections = template.configuration?.sections || []
    const sectionsCount = sections.length

    return (
        <Base>
            <div className="DonorTemplateDetail">
                <header className="detail-header">
                    <button className="btn-back" onClick={() => navigate(-1)}>
                        <FontAwesomeIcon icon={faArrowLeft} style={{ marginRight: '8px' }} /> Back
                    </button>
                    <div className="header-main">
                        <div className="header-title-group">
                            <h1>{template.name}</h1>
                            <span className="template-type-badge">
                                <FontAwesomeIcon
                                    icon={template.template_type === 'concept_note' || template.template_type === 'Concept Note' ? faFileLines : faFileContract}
                                    style={{ marginRight: '6px' }}
                                />
                                {template.template_type === 'concept_note' ? 'Concept Note' : template.template_type || 'Proposal'}
                            </span>
                        </div>
                        <span className={`status-badge ${template.status}`}>{template.status}</span>
                    </div>
                </header>

                <div className="detail-body">
                    {/* ── Left column: config ── */}
                    <div className="detail-main">
                        <section className="info-section">
                            <h3>Configuration</h3>
                            <div className="info-grid">
                                {template.donor && <div className="info-item"><strong>Donor:</strong> {template.donor}</div>}
                                {template.creator && <div className="info-item"><strong>Created by:</strong> {template.creator}</div>}
                                {template.created_at && (
                                    <div className="info-item"><strong>Date:</strong> {new Date(template.created_at).toLocaleDateString()}</div>
                                )}
                            </div>

                            {renderHighLevelInstructions()}
                            {renderGenerationSequence(sections)}

                            <h4><FontAwesomeIcon icon={faList} style={{ marginRight: '8px' }} /> Template Sections <span className="section-count">{sectionsCount}</span></h4>
                            {renderSections()}

                            {renderGlobalComments()}

                            {isAdmin && template.type !== 'file' && (
                                <div className="admin-actions">
                                    <h4>Admin Actions</h4>
                                    <div className="btn-group">
                                        <button className="btn btn--secondary" onClick={handleDownloadJson}>
                                            <i className="fa-solid fa-download"></i> Download JSON
                                        </button>
                                        {template.status === 'pending' && (
                                            <>
                                                <button className="btn btn--primary" onClick={() => handleUpdateStatus('approved')}>Approve</button>
                                                <button className="btn btn--danger" onClick={() => handleUpdateStatus('rejected')}>Reject</button>
                                            </>
                                        )}
                                        {template.status === 'approved' && (
                                            <button className="btn btn--primary" onClick={() => handleUpdateStatus('published')}>Mark as Published</button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </section>
                    </div>

                </div>
            </div>
        </Base>
    )
}
