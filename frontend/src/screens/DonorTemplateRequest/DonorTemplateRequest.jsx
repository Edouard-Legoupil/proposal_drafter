import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Select from 'react-select'
import Base from '../../components/Base/Base'
import './DonorTemplateRequest.css'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

// Default high-level instructions pre-populated from existing templates
const DEFAULT_INSTRUCTIONS = [
    "Strictly base all content on the provided inputs and knowledge base.",
    "Do not invent or hallucinate facts, figures, or dates.",
    "If information is missing, explicitly state that it is not available in the context.",
    "Ensure tone, style, and formatting match a professional humanitarian document.",
    "When referencing donor, use donor name and never donor_id.",
    "When referencing outcomes, use outcome name and never outcome_id.",
]

const DEFAULT_SECTION = () => ({
    section_label: '',
    section_name: '',
    section_parent: '',
    reading_sequence: 1,
    generation_sequence: 1,
    format_type: 'text',
    limit_type: 'word', // 'word' or 'char'
    limit_value: '',
    word_limit: '',
    char_limit: '',
    instructions: '',
    mandatory: true,
    fixed_text: '',
})

const FORMAT_TYPES = ['text', 'table', 'number', 'fixed_text']

function slugify(str) {
    return str.trim()
        .replace(/[^a-zA-Z0-9 ]/g, '')
        .replace(/\s+/g, ' ')
}

export default function DonorTemplateRequest() {
    const navigate = useNavigate()
    const [donors, setDonors] = useState([])
    const [formData, setFormData] = useState({
        name: '',
        template_type: 'proposal',
        donor_ids: [],
        instructions: [...DEFAULT_INSTRUCTIONS],
        sections: [{ ...DEFAULT_SECTION(), reading_sequence: 1, generation_sequence: 1 }],
    })
    const [openSections, setOpenSections] = useState({ 0: true })
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function fetchDonors() {
            try {
                const response = await fetch(`${API_BASE_URL}/donors`)
                if (response.ok) {
                    const data = await response.json()
                    setDonors(data.donors || [])
                }
            } catch (err) {
                console.error("Error fetching donors", err)
            }
        }
        fetchDonors()
    }, [])

    // ── Global instructions ──────────────────────────────────────────────────
    const handleInstructionChange = (index, value) => {
        const updated = [...formData.instructions]
        updated[index] = value
        setFormData(prev => ({ ...prev, instructions: updated }))
    }
    const handleAddInstruction = () =>
        setFormData(prev => ({ ...prev, instructions: [...prev.instructions, ''] }))
    const handleRemoveInstruction = (index) =>
        setFormData(prev => ({
            ...prev,
            instructions: prev.instructions.filter((_, i) => i !== index)
        }))

    // ── Sections ─────────────────────────────────────────────────────────────
    const handleSectionFieldChange = (index, field, value) => {
        const updated = [...formData.sections]
        updated[index] = { ...updated[index], [field]: value }
        // Auto-derive section_name from section_label
        if (field === 'section_label') {
            updated[index].section_name = slugify(value)
        }
        setFormData(prev => ({ ...prev, sections: updated }))
    }

    const handleAddSection = () => {
        const newIdx = formData.sections.length
        const newSection = {
            ...DEFAULT_SECTION(),
            reading_sequence: newIdx + 1,
            generation_sequence: newIdx + 1,
        }
        setFormData(prev => ({ ...prev, sections: [...prev.sections, newSection] }))
        setOpenSections(prev => ({ ...prev, [newIdx]: true }))
    }

    const handleRemoveSection = (index) => {
        setFormData(prev => ({
            ...prev,
            sections: prev.sections.filter((_, i) => i !== index)
        }))
        setOpenSections(prev => {
            const updated = {}
            Object.keys(prev).forEach(k => {
                const ki = parseInt(k)
                if (ki < index) updated[ki] = prev[k]
                else if (ki > index) updated[ki - 1] = prev[k]
            })
            return updated
        })
    }

    const toggleSection = (index) =>
        setOpenSections(prev => ({ ...prev, [index]: !prev[index] }))

    const moveSectionUp = (index) => {
        if (index === 0) return
        const updated = [...formData.sections]
        ;[updated[index - 1], updated[index]] = [updated[index], updated[index - 1]]
        setFormData(prev => ({ ...prev, sections: updated }))
    }

    const moveSectionDown = (index) => {
        if (index === formData.sections.length - 1) return
        const updated = [...formData.sections]
        ;[updated[index], updated[index + 1]] = [updated[index + 1], updated[index]]
        setFormData(prev => ({ ...prev, sections: updated }))
    }

    // ── Submit ────────────────────────────────────────────────────────────────
    const handleSubmit = async (e) => {
        e.preventDefault()
        setIsSubmitting(true)
        setError(null)

        const validSections = formData.sections.filter(s => s.section_label.trim() !== '')

        const payload = {
            name: formData.name,
            donor_ids: formData.donor_ids,
            template_type: formData.template_type,
            configuration: {
                limit_type: formData.limit_type,
                limit_value: formData.limit_value ? parseInt(formData.limit_value) : null,
                instructions: formData.instructions.filter(i => i.trim() !== ''),
                sections: validSections.map(s => ({
                    section_name: s.section_name || slugify(s.section_label),
                    section_label: s.section_label,
                    section_parent: s.section_parent || null,
                    reading_sequence: parseInt(s.reading_sequence) || 1,
                    generation_sequence: parseInt(s.generation_sequence) || 1,
                    format_type: s.format_type || 'text',
                    word_limit: s.limit_type === 'word' ? (s.limit_value ? parseInt(s.limit_value) : null) : null,
                    char_limit: s.limit_type === 'char' ? (s.limit_value ? parseInt(s.limit_value) : null) : null,
                    instructions: s.instructions || '',
                    mandatory: s.mandatory,
                    fixed_text: s.format_type === 'fixed_text' ? s.fixed_text : null,
                }))
            }
        }

        try {
            const response = await fetch(`${API_BASE_URL}/templates/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                credentials: 'include'
            })

            if (response.ok) {
                navigate("/dashboard/templates/all")
            } else {
                const data = await response.json()
                setError(data.detail || "Failed to submit request")
            }
        } catch (err) {
            console.error(err)
            setError("Network error. Please try again.")
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <Base>
            <div className="DonorTemplateRequest">
                <header className="page-header">
                    <h1>Request New Donor Template</h1>
                    <p>Configure the structure for a new donor proposal or concept note template.</p>
                </header>

                <form className="request-form" onSubmit={handleSubmit}>

                    {/* ── 1. General Information ─────────────────────────── */}
                    <section className="form-section">
                        <h3>1. General Information</h3>

                        {/* Template type */}
                        <div className="form-group">
                            <label>Template Type *</label>
                            <div className="type-toggle">
                                {['proposal', 'concept_note'].map(t => (
                                    <button
                                        key={t}
                                        type="button"
                                        className={`type-btn${formData.template_type === t ? ' active' : ''}`}
                                        onClick={() => setFormData(prev => ({ ...prev, template_type: t }))}
                                    >
                                        <i className={`fa-solid ${t === 'proposal' ? 'fa-file-contract' : 'fa-file-lines'}`}></i>
                                        {t === 'proposal' ? 'Proposal' : 'Concept Note'}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Name */}
                        <div className="form-group">
                            <label htmlFor="template-name">Template Name *</label>
                            <input
                                id="template-name"
                                type="text"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                required
                                placeholder="e.g. UNHCR Proposal 2026"
                            />
                        </div>

                        {/* Donor(s) */}
                        <div className="form-group">
                            <label htmlFor="donor-select">Associated Donor(s)</label>
                            <Select
                                isMulti
                                options={donors.map(d => ({ value: d.id, label: d.name }))}
                                value={donors.filter(d => formData.donor_ids.includes(d.id)).map(d => ({ value: d.id, label: d.name }))}
                                onChange={(selected) => setFormData({ ...formData, donor_ids: (selected || []).map(s => s.value) })}
                                className="multi-select"
                                placeholder="Select one or more donors..."
                            />
                        </div>
                    </section>

                    {/* ── 2. High-level instructions ────────────────────── */}
                    <section className="form-section">
                        <h3>2. High-level Instructions</h3>
                        <p className="section-help">
                            Global generation rules applied to every section. Pre-populated with standard requirements — edit or add to them.
                        </p>
                        <ul className="instructions-list">
                            {formData.instructions.map((instr, idx) => (
                                <li key={idx} className="instruction-item">
                                    <span className="instruction-num">{idx + 1}</span>
                                    <input
                                        type="text"
                                        value={instr}
                                        onChange={(e) => handleInstructionChange(idx, e.target.value)}
                                        placeholder={`Instruction ${idx + 1}`}
                                    />
                                    <button
                                        type="button"
                                        className="btn-icon delete"
                                        onClick={() => handleRemoveInstruction(idx)}
                                        title="Remove instruction"
                                    >
                                        <i className="fa-solid fa-xmark"></i>
                                    </button>
                                </li>
                            ))}
                        </ul>
                        <button type="button" className="btn btn--secondary" onClick={handleAddInstruction}>
                            <i className="fa-solid fa-plus"></i> Add Instruction
                        </button>
                    </section>

                    {/* ── 3. Sections ──────────────────────────────────── */}
                    <section className="form-section">
                        <h3>3. Template Sections</h3>
                        <p className="section-help">
                            Define each section. Use <strong>Reading Sequence</strong> for document order and <strong>Generation Sequence</strong> for AI generation order.
                        </p>

                        <div className="sections-editor">
                            {formData.sections.map((section, idx) => (
                                <div key={idx} className={`section-card${openSections[idx] ? ' open' : ''}`}>
                                    <div className="section-card-header" onClick={() => toggleSection(idx)}>
                                        <div className="section-card-title">
                                            <span className="section-num">#{idx + 1}</span>
                                            <span className="section-name-preview">
                                                {section.section_label || <em>Untitled Section</em>}
                                            </span>
                                            <span className="section-badges">
                                                <span className="badge-fmt">{section.format_type}</span>
                                                {section.mandatory && <span className="badge-req">Required</span>}
                                            </span>
                                        </div>
                                        <div className="section-card-actions" onClick={e => e.stopPropagation()}>
                                            <button type="button" className="btn-icon" onClick={() => moveSectionUp(idx)} disabled={idx === 0} title="Move up">
                                                <i className="fa-solid fa-chevron-up"></i>
                                            </button>
                                            <button type="button" className="btn-icon" onClick={() => moveSectionDown(idx)} disabled={idx === formData.sections.length - 1} title="Move down">
                                                <i className="fa-solid fa-chevron-down"></i>
                                            </button>
                                            <button type="button" className="btn-icon delete" onClick={() => handleRemoveSection(idx)} disabled={formData.sections.length <= 1} title="Remove section">
                                                <i className="fa-solid fa-trash-can"></i>
                                            </button>
                                            <i className={`fa-solid fa-chevron-${openSections[idx] ? 'up' : 'down'} toggle-icon`}></i>
                                        </div>
                                    </div>

                                    {openSections[idx] && (
                                        <div className="section-card-body">
                                            <div className="fields-grid-2">
                                                <div className="form-group">
                                                    <label>Section Label *</label>
                                                    <input
                                                        type="text"
                                                        value={section.section_label}
                                                        onChange={e => handleSectionFieldChange(idx, 'section_label', e.target.value)}
                                                        placeholder="e.g. Project Rationale"
                                                        required
                                                    />
                                                </div>
                                                <div className="form-group">
                                                    <label>Section Name (slug)</label>
                                                    <input
                                                        type="text"
                                                        value={section.section_name}
                                                        onChange={e => handleSectionFieldChange(idx, 'section_name', e.target.value)}
                                                        placeholder="Auto-derived from label"
                                                    />
                                                </div>
                                            </div>

                                            <div className="fields-grid-2">
                                                <div className="form-group">
                                                    <label>Parent Section</label>
                                                    <input
                                                        type="text"
                                                        value={section.section_parent}
                                                        onChange={e => handleSectionFieldChange(idx, 'section_parent', e.target.value)}
                                                        placeholder="Parent section name (optional)"
                                                    />
                                                </div>
                                                <div className="form-group">
                                                    <label>Format Type</label>
                                                    <select
                                                        value={section.format_type}
                                                        onChange={e => handleSectionFieldChange(idx, 'format_type', e.target.value)}
                                                    >
                                                        {FORMAT_TYPES.map(f => (
                                                            <option key={f} value={f}>{f}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>

                                            {section.format_type === 'fixed_text' && (
                                                <div className="form-group" style={{ marginTop: '1rem' }}>
                                                    <label>Fixed Text Content</label>
                                                    <textarea
                                                        value={section.fixed_text}
                                                        onChange={e => handleSectionFieldChange(idx, 'fixed_text', e.target.value)}
                                                        placeholder="Enter the static text that should always appear in this section..."
                                                        rows={3}
                                                    />
                                                </div>
                                            )}

                                            <div className="fields-grid-4">
                                                <div className="form-group">
                                                    <label>Reading Sequence</label>
                                                    <input
                                                        type="number"
                                                        min="1"
                                                        value={section.reading_sequence}
                                                        onChange={e => handleSectionFieldChange(idx, 'reading_sequence', e.target.value)}
                                                    />
                                                </div>
                                                <div className="form-group">
                                                    <label>Generation Sequence</label>
                                                    <input
                                                        type="number"
                                                        min="1"
                                                        value={section.generation_sequence}
                                                        onChange={e => handleSectionFieldChange(idx, 'generation_sequence', e.target.value)}
                                                    />
                                                </div>
                                                <div className="form-group">
                                                    <label>Length Limit</label>
                                                    <div className="limit-row">
                                                        <div className="limit-toggle">
                                                            <label className="radio-label">
                                                                <input
                                                                    type="radio"
                                                                    name={`limit_type_${idx}`}
                                                                    value="word"
                                                                    checked={section.limit_type === 'word'}
                                                                    onChange={() => handleSectionFieldChange(idx, 'limit_type', 'word')}
                                                                />
                                                                <span>Words</span>
                                                            </label>
                                                            <label className="radio-label">
                                                                <input
                                                                    type="radio"
                                                                    name={`limit_type_${idx}`}
                                                                    value="char"
                                                                    checked={section.limit_type === 'char'}
                                                                    onChange={() => handleSectionFieldChange(idx, 'limit_type', 'char')}
                                                                />
                                                                <span>Chars</span>
                                                            </label>
                                                        </div>
                                                        <input
                                                            type="number"
                                                            min="1"
                                                            value={section.limit_value}
                                                            onChange={e => handleSectionFieldChange(idx, 'limit_value', e.target.value)}
                                                            placeholder="Limit"
                                                            className="limit-input"
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="form-group">
                                                <label>Instructions for AI</label>
                                                <textarea
                                                    rows="3"
                                                    value={section.instructions}
                                                    onChange={e => handleSectionFieldChange(idx, 'instructions', e.target.value)}
                                                    placeholder="Specific generation instructions for this section..."
                                                />
                                            </div>

                                            <div className="form-group mandatory-row">
                                                <label className="checkbox-label">
                                                    <input
                                                        type="checkbox"
                                                        checked={section.mandatory}
                                                        onChange={e => handleSectionFieldChange(idx, 'mandatory', e.target.checked)}
                                                    />
                                                    <span>Mandatory section</span>
                                                </label>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        <button type="button" className="btn btn--secondary add-section-btn" onClick={handleAddSection}>
                            <i className="fa-solid fa-plus"></i> Add Section
                        </button>
                    </section>

                    {error && <div className="error-message">{error}</div>}

                    <div className="form-actions">
                        <button type="button" className="btn btn--secondary" onClick={() => navigate(-1)}>Cancel</button>
                        <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
                            {isSubmitting ? "Submitting..." : "Submit Request"}
                        </button>
                    </div>
                </form>
            </div>
        </Base>
    )
}
