import './KnowledgeCard.css';
import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import CreatableSelect from 'react-select/creatable';
import Base from '../../components/Base/Base';
import CommonButton from '../../components/CommonButton/CommonButton';
import LoadingModal from '../../components/LoadingModal/LoadingModal';
import ProgressModal from '../../components/ProgressModal/ProgressModal';
import KnowledgeCardHistory from '../../components/KnowledgeCardHistory/KnowledgeCardHistory';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function KnowledgeCard() {
    const navigate = useNavigate();
    const { id } = useParams();

    const [title, setTitle] = useState('');
    const [summary, setSummary] = useState('');
    const [linkType, setLinkType] = useState('');
    const [linkedId, setLinkedId] = useState('');
    const [references, setReferences] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');
    const [generatedSections, setGeneratedSections] = useState(null);
    const [editingSection, setEditingSection] = useState(null);
    const [editedContent, setEditedContent] = useState('');
    const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
    const [generationProgress, setGenerationProgress] = useState(0);
    const [generationMessage, setGenerationMessage] = useState("");
    const [eventSource, setEventSource] = useState(null);
    const [history, setHistory] = useState([]);
    const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
    const [donors, setDonors] = useState([]);
    const [outcomes, setOutcomes] = useState([]);
    const [fieldContexts, setFieldContexts] = useState([]);
    const [geographicCoverages, setGeographicCoverages] = useState([]);
    const [selectedGeoCoverage, setSelectedGeoCoverage] = useState('');
    const [linkOptions, setLinkOptions] = useState([]);
    const [newDonors, setNewDonors] = useState([]);
    const [newOutcomes, setNewOutcomes] = useState([]);
    const [newFieldContexts, setNewFieldContexts] = useState([]);

    const [editingReferenceIndex, setEditingReferenceIndex] = useState(null);

    const authenticatedFetch = useCallback(async (url, options) => {
        const response = await fetch(url, options);
        if (response.status === 401) {
            sessionStorage.setItem("session_expired", "Session expired. Please login again.");
            navigate("/login");
        }
        return response;
    }, [navigate]);

    const fetchData = useCallback(async () => {
        try {
            if (id) {
                const cardRes = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${id}`, { credentials: 'include' });
                if (cardRes.ok) {
                    const data = await cardRes.json();
                    const card = data.knowledge_card;
                    setTitle(card.title);
                    setSummary(card.summary || '');
                    if (card.donor_id) {
                        setLinkType('donor');
                        setLinkedId(card.donor_id);
                    } else if (card.outcome_id) {
                        setLinkType('outcome');
                        setLinkedId(card.outcome_id);
                    } else if (card.field_context_id) {
                        setLinkType('field_context');
                        setLinkedId(card.field_context_id);
                    }
                    setReferences(card.references || []);
                    setGeneratedSections(card.generated_sections || null);
                } else {
                    console.error("Failed to load knowledge card");
                    navigate('/dashboard');
                }
            }
            const [donorsRes, outcomesRes, allFieldContextsRes] = await Promise.all([
                authenticatedFetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
                authenticatedFetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
                authenticatedFetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' })
            ]);
            if (donorsRes.ok) setDonors((await donorsRes.json()).donors);
            if (outcomesRes.ok) setOutcomes((await outcomesRes.json()).outcomes);
            if (allFieldContextsRes.ok) {
                const allContexts = (await allFieldContextsRes.json()).field_contexts;
                const uniqueGeos = [...new Set(allContexts.map(fc => fc.geographic_coverage))];
                setGeographicCoverages(uniqueGeos);
            }
        } catch (error) {
            console.error("Error fetching data for KC form:", error);
        }
    }, [id, navigate, authenticatedFetch]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        async function fetchFieldContexts() {
            let url = `${API_BASE_URL}/field-contexts`;
            if (selectedGeoCoverage) {
                url += `?geographic_coverage=${encodeURIComponent(selectedGeoCoverage)}`;
            }
            const res = await authenticatedFetch(url, { credentials: 'include' });
            if (res.ok) {
                setFieldContexts((await res.json()).field_contexts);
            }
        }
        if (linkType === 'field_context') {
            fetchFieldContexts();
        }
    }, [selectedGeoCoverage, linkType, authenticatedFetch]);

    useEffect(() => {
        if (linkType === 'donor') setLinkOptions([...donors, ...newDonors]);
        else if (linkType === 'outcome') setLinkOptions([...outcomes, ...newOutcomes]);
        else if (linkType === 'field_context') {
            let filteredContexts = [...fieldContexts, ...newFieldContexts];
            if (selectedGeoCoverage) {
                filteredContexts = filteredContexts.filter(fc => fc.geographic_coverage === selectedGeoCoverage);
            }
            setLinkOptions(filteredContexts);
        } else {
            setLinkOptions([]);
        }
        if (!id) setLinkedId('');
    }, [linkType, donors, outcomes, fieldContexts, newDonors, newOutcomes, newFieldContexts, id, selectedGeoCoverage]);

    const handleAddReference = () => {
        const newReferences = [...references, { url: '', reference_type: '', summary: '', isNew: true }];
        setReferences(newReferences);
        setEditingReferenceIndex(newReferences.length - 1);
    };

    const handleEditReference = (index) => {
        setEditingReferenceIndex(index);
    };

    const handleCancelEditReference = () => {
        setEditingReferenceIndex(null);
    };

    const handleSaveReference = async (index) => {
        const reference = references[index];
        if (!reference || !reference.url || !reference.reference_type) {
            alert("Reference URL and type are required.");
            return;
        }

        const isNew = reference.isNew;
        const url = isNew ? `${API_BASE_URL}/knowledge-cards/${id}/references` : `${API_BASE_URL}/knowledge-cards/references/${reference.id}`;
        const method = isNew ? 'POST' : 'PUT';

        const response = await authenticatedFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reference),
            credentials: 'include'
        });

        if (response.ok) {
            await fetchData();
            setEditingReferenceIndex(null);
        } else {
            const error = await response.json();
            alert(`Failed to save reference: ${error.detail}`);
        }
    };

    const handleRemoveReference = async (refId) => {
        const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/references/${refId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        if (response.ok) {
            await fetchData();
        } else {
            const error = await response.json();
            alert(`Failed to delete reference: ${error.detail}`);
        }
    };

    // The rest of the component remains largely the same...
    // Omitting handleSave, handleIdentifyReferences, handlePopulate, etc. for brevity
    // as they are not the focus of the current fix.

    const handleSave = async (navigateOnSuccess = true) => {
        setLoading(true);
        let finalLinkedId = linkedId;
        if (linkedId && linkedId.startsWith('new_')) {
            const endpointMap = {
                donor: 'donors',
                outcome: 'outcomes',
                field_context: 'field-contexts',
            };
            const endpoint = endpointMap[linkType];
            const value = linkedId.substring(4);
            const response = await authenticatedFetch(`${API_BASE_URL}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: value }),
                credentials: 'include'
            });
            if (!response.ok) {
                alert(`Failed to create new ${linkType}`);
                setLoading(false);
                return;
            }
            const data = await response.json();
            finalLinkedId = data.id;
        }

        const payload = {
            title,
            summary,
            donor_id: linkType === 'donor' ? finalLinkedId : null,
            outcome_id: linkType === 'outcome' ? finalLinkedId : null,
            field_context_id: linkType === 'field_context' ? finalLinkedId : null,
            references: references.filter(r => r.url && r.reference_type)
        };

        const url = id ? `${API_BASE_URL}/knowledge-cards/${id}` : `${API_BASE_URL}/knowledge-cards`;
        const method = id ? 'PUT' : 'POST';

        const response = await authenticatedFetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });
        setLoading(false);

        if (response.ok) {
            if (navigateOnSuccess) {
                alert(`Knowledge card ${id ? 'updated' : 'created'} successfully!`);
                sessionStorage.setItem('selectedDashboardTab', 'knowledge');
                navigate('/dashboard');
            }
        } else {
            const error = await response.json();
            alert(`Error ${id ? 'updating' : 'creating'} knowledge card: ${error.detail}`);
        }
        return response;
    };

    const handleIdentifyReferences = async () => {
        let cardId = id;

        if (!cardId) {
            const saveResponse = await handleSave(false);
            if (!saveResponse.ok) {
                return;
            }
            const data = await saveResponse.json();
            cardId = data.knowledge_card_id;
            navigate(`/knowledge-card/${cardId}`, { replace: true });
        }

        setLoading(true);
        setLoadingMessage("Identifying references...");
        try {
            const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${cardId}/identify-references`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    summary,
                    linked_element: linkType,
                }),
                credentials: 'include'
            });

            if (response.ok) {
                fetchData();
            } else {
                const error = await response.json();
                alert(`Error identifying references: ${error.detail}`);
            }
        } catch (error) {
            console.error("Failed to fetch references:", error);
            alert("An error occurred while identifying references.");
        } finally {
            setLoading(false);
            setLoadingMessage('');
        }
    };

    const handlePopulate = async (e) => {
        e.preventDefault();
        const saveResponse = await handleSave(false);
        if (saveResponse.ok) {
            const cardId = id || (await saveResponse.json()).knowledge_card_id;
            setIsProgressModalOpen(true);
            setGenerationProgress(0);
            setGenerationMessage("Starting content generation...");

            const genResponse = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${cardId}/generate`, {
                method: 'POST',
                credentials: 'include'
            });

            if (genResponse.ok) {
                const es = new EventSource(`${API_BASE_URL}/knowledge-cards/${cardId}/status`);
                setEventSource(es);

                es.onmessage = (event) => {
                    const statusData = JSON.parse(event.data);
                    setGenerationProgress(statusData.progress);
                    setGenerationMessage(statusData.message);
                    if (statusData.progress === 100 || statusData.progress === -1) {
                        if (statusData.progress === 100) {
                            fetchData();
                        }
                        es.close();
                        setEventSource(null);
                    }
                };

                es.onerror = () => {
                    console.error("EventSource failed.");
                    es.close();
                    setEventSource(null);
                };

            } else {
                const error = await genResponse.json();
                alert(`Error starting content generation: ${error.detail}`);
                setIsProgressModalOpen(false);
            }
        }
    }

    const handleEditClick = (section, content) => {
        setEditingSection(section);
        setEditedContent(content);
    };

    const handleSaveClick = async (section) => {
        const url = `${API_BASE_URL}/knowledge-cards/${id}/sections/${section}`;
        const response = await authenticatedFetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: editedContent }),
            credentials: 'include'
        });

        if (response.ok) {
            setGeneratedSections(prev => ({ ...prev, [section]: editedContent }));
            setEditingSection(null);
        } else {
            alert('Failed to save section.');
        }
    };

    const handleCancelClick = () => {
        setEditingSection(null);
    };

    const fetchHistory = async () => {
        if (id) {
            const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${id}/history`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                setHistory(data.history);
                setIsHistoryModalOpen(true);
            } else {
                alert('Failed to fetch history.');
            }
        }
    };

    const handleReferenceFieldChange = (index, field, value) => {
        const newReferences = [...references];
        newReferences[index][field] = value;
        setReferences(newReferences);
    };

    return (
        <Base>
            {/* Modals */}
            <ProgressModal isOpen={isProgressModalOpen} onClose={() => setIsProgressModalOpen(false)} progress={generationProgress} message={generationMessage} />
            {isHistoryModalOpen && <KnowledgeCardHistory history={history} onClose={() => setIsHistoryModalOpen(false)} />}
            <LoadingModal isOpen={loading} message={loadingMessage} />

            <div className="kc-container">
                <div className="kc-form-container">
                    <form onSubmit={handlePopulate} className="kc-form">
                        {/* Header */}
                        <div className="kc-form-header">
                            <h2>{id ? 'View/Edit Knowledge Card' : 'Create New Knowledge Card'}</h2>
                            {id && <CommonButton type="button" onClick={fetchHistory} label="View Content History" />}
                        </div>

                        {/* Form Fields */}
                        <label htmlFor="kc-link-type">Link To</label>
                        <select id="kc-link-type" value={linkType} onChange={e => setLinkType(e.target.value)} data-testid="link-type-select">
                            <option value="">Select Type...</option>
                            <option value="donor">Donor</option>
                            <option value="outcome">Outcome</option>
                            <option value="field_context">Field Context</option>
                        </select>

                        {linkType === 'field_context' && (
                            <>
                                <label htmlFor="kc-geo-coverage">Geographic Coverage</label>
                                <select id="kc-geo-coverage" value={selectedGeoCoverage} onChange={e => setSelectedGeoCoverage(e.target.value)} data-testid="geo-coverage-select">
                                    <option value="">All</option>
                                    {geographicCoverages.map(geo => <option key={geo} value={geo}>{geo}</option>)}
                                </select>
                            </>
                        )}

                        {linkType && (
                            <>
                                <label htmlFor="kc-linked-id">Select Item</label>
                                <CreatableSelect
                                    isClearable
                                    id="kc-linked-id"
                                    name="kc-linked-id"
                                    value={linkOptions.find(o => o.id === linkedId) ? { value: linkedId, label: linkOptions.find(o => o.id === linkedId).name } : null}
                                    onChange={option => setLinkedId(option ? option.id : '')}
                                    onCreateOption={inputValue => {
                                        const newOption = { id: `new_${inputValue}`, name: inputValue };
                                        if (linkType === 'donor') setNewDonors(prev => [...prev, newOption]);
                                        if (linkType === 'outcome') setNewOutcomes(prev => [...prev, newOption]);
                                        if (linkType === 'field_context') setNewFieldContexts(prev => [...prev, newOption]);
                                        setLinkedId(newOption.id);
                                    }}
                                    options={linkOptions.map(o => ({ ...o, value: o.id, label: o.name }))}
                                    data-testid="linked-item-select"
                                />
                            </>
                        )}

                        <label htmlFor="kc-title">Title*</label>
                        <input id="kc-title" type="text" value={title} onChange={e => setTitle(e.target.value)} required data-testid="title-input" />

                        <label htmlFor="kc-summary">Description</label>
                        <textarea id="kc-summary" value={summary} onChange={e => setSummary(e.target.value)} data-testid="summary-textarea" />

                        {/* References Section */}
                        <div className="kc-references-section">
                            <div className="kc-references-header">
                                <h3>References</h3>
                                <button type="button" onClick={handleAddReference} className="kc-add-reference-btn" data-testid="add-reference-button">
                                    <i className="fa-solid fa-plus"></i>
                                </button>
                            </div>
                            <div className="kc-references-grid">
                                {references.map((ref, index) => (
                                    <div key={ref.id || `new-${index}`} className="kc-reference-card">
                                        {editingReferenceIndex === index ? (
                                            <div className="kc-reference-edit-form">
                                                <select
                                                    value={ref.reference_type}
                                                    onChange={e => handleReferenceFieldChange(index, 'reference_type', e.target.value)}
                                                    required
                                                >
                                                    <option value="">Select Type...</option>
                                                    <option value="UNHCR Operation Page">UNHCR Operation Page</option>
                                                    <option value="Donor Content">Donor Content</option>
                                                    <option value="Humanitarian Partner Content">Humanitarian Partner Content</option>
                                                    <option value="Statistics">Statistics</option>
                                                    <option value="Needs Assessment">Needs Assessment</option>
                                                    <option value="Evaluation Report">Evaluation Report</option>
                                                    <option value="Policies">Policies</option>
                                                    <option value="Social Media">Social Media</option>
                                                </select>
                                                <input
                                                    type="url"
                                                    placeholder="https://example.com"
                                                    value={ref.url}
                                                    onChange={e => handleReferenceFieldChange(index, 'url', e.target.value)}
                                                    required
                                                />
                                                <textarea
                                                    placeholder="Summary"
                                                    value={ref.summary}
                                                    onChange={e => handleReferenceFieldChange(index, 'summary', e.target.value)}
                                                />
                                                <div className="kc-reference-edit-actions">
                                                    <button onClick={() => handleSaveReference(index)}>Save</button>
                                                    <button onClick={handleCancelEditReference}>Cancel</button>
                                                </div>
                                            </div>
                                        ) : (
                                            <>
                                                <div className="kc-reference-card-header">
                                                    <span className="kc-reference-type">{ref.reference_type}</span>
                                                    <div className="kc-reference-actions">
                                                        <button onClick={() => handleEditReference(index)}><i className="fa-solid fa-pen"></i></button>
                                                        <button onClick={() => handleRemoveReference(ref.id)}><i className="fa-solid fa-minus"></i></button>
                                                    </div>
                                                </div>
                                                <div className="kc-reference-card-body">
                                                    <a href={ref.url} target="_blank" rel="noopener noreferrer">{ref.url}</a>
                                                    <p>{ref.summary}</p>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Form Actions */}
                        <div className="kc-form-actions-left">
                            <CommonButton type="button" onClick={handleIdentifyReferences} label="Identify References" className="squared-btn" data-testid="identify-references-button" />
                        </div>
                        <div className="kc-form-actions">
                            <div className="kc-form-actions-left">
                                <CommonButton type="submit" label="Populate Card Content" loading={loading} disabled={loading || !title} className="squared-btn" data-testid="populate-card-button" />
                            </div>
                            <div className="kc-form-actions-right">
                                <CommonButton type="button" onClick={() => handleSave(true)} label="Save Card" loading={loading} disabled={loading || !title} data-testid="save-card-button" />
                            </div>
                        </div>
                    </form>
                </div>

                {/* Generated Content */}
                {generatedSections && (
                    <div className="kc-content-container">
                        <h2>Generated Content</h2>
                        {Object.entries(generatedSections).map(([section, content]) => (
                            <div key={section} className={`kc-section ${editingSection === section ? 'kc-section-editing' : ''}`}>
                                <h3>{section}</h3>
                                {editingSection === section ? (
                                    <textarea
                                        className="kc-edit-textarea"
                                        value={editedContent}
                                        onChange={(e) => setEditedContent(e.target.value)}
                                    />
                                ) : (
                                    <p>{content}</p>
                                )}
                                <div className="kc-section-actions">
                                    {editingSection === section ? (
                                        <>
                                            <button onClick={() => handleSaveClick(section)}>Save</button>
                                            <button onClick={handleCancelClick}>Cancel</button>
                                        </>
                                    ) : (
                                        <button onClick={() => handleEditClick(section, content)} data-testid={`edit-section-button-${section}`}>Edit</button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Base>
    );
}
