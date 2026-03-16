import Base from '../../components/Base/Base'
import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import './DonorTemplateDetail.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faThumbsUp, faThumbsDown, faComments, faListCheck, faRobot, faList, faArrowLeft, faFileLines, faFileContract } from '@fortawesome/free-solid-svg-icons'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function DonorTemplateDetail() {
    const { id } = useParams()
    const [searchParams] = useSearchParams()
    const type = searchParams.get('type') // 'file' or 'db'
    const navigate = useNavigate()

    const [template, setTemplate] = useState(null)
    const [commentText, setCommentText] = useState('')
    const [commentSection, setCommentSection] = useState('')
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
                    <div className="section-review-actions">
                        <button 
                            className={`thumb-btn up ${rating === 'up' ? 'active' : ''}`}
                            onClick={() => handleAddQuickComment(hliName, 'up')}
                            title="Looks good"
                        >
                            <FontAwesomeIcon icon={faThumbsUp} />
                            <span style={{ fontSize: '0.65rem', marginLeft: '4px' }}>Good</span>
                        </button>
                        <button 
                            className={`thumb-btn down ${rating === 'down' ? 'active' : ''}`}
                            onClick={() => {
                                setCommentSection(hliName)
                                setCommentText(comment)
                            }}
                            title="Needs changes"
                        >
                            <FontAwesomeIcon icon={faThumbsDown} />
                            <span style={{ fontSize: '0.65rem', marginLeft: '4px' }}>Fix</span>
                        </button>
                    </div>
                </div>

                <ol className="hli-list">
                    {instructions.map((instr, idx) => (
                        <li key={idx}>{instr}</li>
                    ))}
                </ol>

                {/* HLI Comments History */}
                {template.comments?.filter(c => c.section_name === hliName).length > 0 && (
                    <div className="section-comments-history" style={{ borderTop: 'none', marginTop: '0.5rem', paddingTop: 0 }}>
                        <div className="shared-history-label">Previous Feedback:</div>
                        {template.comments.filter(c => c.section_name === hliName).map(c => (
                            <div key={c.id} className={`mini-comment ${c.rating === 'up' ? 'positive' : 'negative'}`}>
                                <div className="mini-comment-header">
                                    <strong>{c.user}</strong>
                                    <span className="mini-comment-date">{new Date(c.created_at).toLocaleDateString()}</span>
                                </div>
                                <div className="mini-comment-body">
                                    <FontAwesomeIcon icon={c.rating === 'up' ? faThumbsUp : faThumbsDown} style={{ marginRight: '6px', opacity: 0.6 }} />
                                    {c.text}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* HLI Inline Comment Form */}
                {commentSection === hliName && (
                    <div className="inline-comment-form">
                        <textarea
                            value={commentText}
                            onChange={(e) => setCommentText(e.target.value)}
                            placeholder="Feedback for High-level Instructions..."
                        />
                        <div className="inline-comment-actions">
                            <button className="btn btn--primary btn--small" onClick={handleAddComment}>Save Comment</button>
                            <button className="btn btn--link btn--small" onClick={() => { setCommentSection(''); setCommentText(''); }}>Cancel</button>
                        </div>
                    </div>
                )}
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

                                {/* Enable feedback for all templates */}
                                <div className="section-review-actions">
                                        <button 
                                            className={`thumb-btn up ${sectionRating === 'up' ? 'active' : ''}`}
                                            onClick={() => handleAddQuickComment(name, 'up')}
                                            title="Looks good"
                                        >
                                            <FontAwesomeIcon icon={faThumbsUp} />
                                            <span style={{ fontSize: '0.65rem', marginLeft: '4px' }}>Good</span>
                                        </button>
                                    <button 
                                        className={`thumb-btn down ${sectionRating === 'down' ? 'active' : ''}`}
                                        onClick={() => {
                                            setCommentSection(name)
                                            setCommentText(sectionComment)
                                            // Focus the local textarea
                                            setTimeout(() => {
                                                const el = document.getElementById(`comment-textarea-${idx}`);
                                                if (el) el.focus();
                                            }, 10);
                                        }}
                                        title="Needs changes"
                                    >
                                        <FontAwesomeIcon icon={faThumbsDown} />
                                        <span style={{ fontSize: '0.65rem', marginLeft: '4px' }}>Fix</span>
                                    </button>
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

                            {/* Section Comments History (Visible to all users) */}
                            {template.comments?.filter(c => c.section_name === name).length > 0 && (
                                <div className="section-comments-history">
                                    <div className="shared-history-label">Previous Feedback:</div>
                                    {template.comments.filter(c => c.section_name === name).map(c => (
                                        <div key={c.id} className={`mini-comment ${c.rating === 'up' ? 'positive' : 'negative'}`}>
                                            <div className="mini-comment-header">
                                                <strong>{c.user}</strong>
                                                <span className="mini-comment-date">{new Date(c.created_at).toLocaleDateString()}</span>
                                            </div>
                                            <div className="mini-comment-body">
                                                <FontAwesomeIcon 
                                                    icon={c.rating === 'up' ? faThumbsUp : faThumbsDown} 
                                                    style={{ marginRight: '6px', opacity: 0.6 }} 
                                                />
                                                {c.text}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Inline Comment Form (when thumb-down or active) */}
                            {(sectionRating === 'down' || commentSection === name) && (
                                <div className="inline-comment-form">
                                    <textarea
                                        id={`comment-textarea-${idx}`}
                                        value={commentSection === name ? commentText : ''}
                                        onChange={(e) => {
                                            setCommentSection(name)
                                            setCommentText(e.target.value)
                                        }}
                                        placeholder={`Feedback for ${name}...`}
                                    />
                                    <div className="inline-comment-actions">
                                        <button 
                                            className="btn btn--primary btn--small" 
                                            onClick={handleAddComment}
                                            disabled={isSubmittingComment || (commentSection === name && !commentText.trim())}
                                        >
                                            {isSubmittingComment && commentSection === name ? 'Saving...' : 'Save Comment'}
                                        </button>
                                        <button 
                                            className="btn btn--link btn--small" 
                                            onClick={() => {
                                                setCommentSection('')
                                                setCommentText('')
                                            }}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}

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

    const handleAddQuickComment = async (sectionName, rating) => {
        try {
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    comment_text: rating === 'up' ? 'Approved' : 'Needs review',
                    section_name: sectionName,
                    rating: rating
                }),
                credentials: 'include'
            })
            if (res.ok) {
                await fetchTemplate()
            }
        } catch (err) {
            console.error("Error adding quick comment", err)
        }
    }

    // ── Comment handlers ───────────────────────────────────────────────────
    const handleAddComment = async (e) => {
        e.preventDefault()
        if (!commentText.trim()) return
        setIsSubmittingComment(true)

        try {
            const res = await fetch(`${API_BASE_URL}/templates/request/${id}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    comment_text: commentText,
                    section_name: commentSection || null,
                    rating: 'down' // Manual comments are usually for improvements/rejections
                }),
                credentials: 'include'
            })

            if (res.ok) {
                setCommentText('')
                setCommentSection('')
                await fetchTemplate()
            }
        } catch (err) {
            console.error("Error adding comment", err)
        } finally {
            setIsSubmittingComment(false)
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
