import './KnowledgeCard.css';
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import CreatableSelect from 'react-select/creatable';
import Base from '../../components/Base/Base';
import CommonButton from '../../components/CommonButton/CommonButton';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function KnowledgeCard() {
    const navigate = useNavigate();
    const { id } = useParams();

    const [title, setTitle] = useState('');
    const [summary, setSummary] = useState('');
    const [linkType, setLinkType] = useState(''); // 'donor', 'outcome', 'field_context'
    const [linkedId, setLinkedId] = useState('');
    const [references, setReferences] = useState([{ url: '', reference_type: '' }]);
    const [loading, setLoading] = useState(false);
    const [generatedSections, setGeneratedSections] = useState(null);

    const [donors, setDonors] = useState([]);
    const [outcomes, setOutcomes] = useState([]);
    const [fieldContexts, setFieldContexts] = useState([]);
    const [linkOptions, setLinkOptions] = useState([]);
    const [newDonors, setNewDonors] = useState([]);
    const [newOutcomes, setNewOutcomes] = useState([]);
    const [newFieldContexts, setNewFieldContexts] = useState([]);

    useEffect(() => {
        async function fetchData() {
            try {
                const [donorsRes, outcomesRes, fieldContextsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
                    fetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
                    fetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' })
                ]);
                if (donorsRes.ok) setDonors((await donorsRes.json()).donors);
                if (outcomesRes.ok) setOutcomes((await outcomesRes.json()).outcomes);
                if (fieldContextsRes.ok) setFieldContexts((await fieldContextsRes.json()).field_contexts);

                if (id) {
                    const cardRes = await fetch(`${API_BASE_URL}/knowledge-cards/${id}`, { credentials: 'include' });
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
                        setReferences(card.references && card.references.length > 0 ? card.references : [{ url: '', reference_type: '' }]);
                    } else {
                        console.error("Failed to load knowledge card");
                        navigate('/dashboard');
                    }
                }
            } catch (error) {
                console.error("Error fetching data for KC form:", error);
            }
        }
        fetchData();
    }, [id, navigate]);

    useEffect(() => {
        if (linkType === 'donor') setLinkOptions([...donors, ...newDonors]);
        else if (linkType === 'outcome') setLinkOptions([...outcomes, ...newOutcomes]);
        else if (linkType === 'field_context') setLinkOptions([...fieldContexts, ...newFieldContexts]);
        else setLinkOptions([]);

        if (!id) { // Only reset linkedId in create mode
            setLinkedId('');
        }
    }, [linkType, donors, outcomes, fieldContexts, newDonors, newOutcomes, newFieldContexts, id]);

    const handleReferenceChange = (index, field, value) => {
        const newReferences = [...references];
        newReferences[index][field] = value;
        setReferences(newReferences);
    };

    const addReference = () => {
        setReferences([...references, { url: '', reference_type: '' }]);
    };

    const removeReference = (index) => {
        const newReferences = references.filter((_, i) => i !== index);
        setReferences(newReferences);
    };

    const handleSave = async () => {
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
            const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
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

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });
        setLoading(false);

        if (response.ok) {
            alert(`Knowledge card ${id ? 'updated' : 'created'} successfully!`);
            if (!id) {
                const data = await response.json();
                navigate(`/knowledge-card/${data.knowledge_card_id}`);
            }
        } else {
            const error = await response.json();
            alert(`Error ${id ? 'updating' : 'creating'} knowledge card: ${error.detail}`);
        }
        return response;
    };

    const handlePopulate = async (e) => {
        e.preventDefault();
        const saveResponse = await handleSave();
        if (saveResponse.ok) {
            const cardId = id || (await saveResponse.json()).knowledge_card_id;
            setLoading(true);
            const genResponse = await fetch(`${API_BASE_URL}/knowledge-cards/${cardId}/generate`, {
                method: 'POST',
                credentials: 'include'
            });
            setLoading(false);
            if (genResponse.ok) {
                const genData = await genResponse.json();
                setGeneratedSections(genData.generated_sections);
                alert('Knowledge card content populated successfully!');
            } else {
                const error = await genResponse.json();
                alert(`Error populating card content: ${error.detail}`);
            }
        }
    }

    return (
        <Base>
            <div className="kc-container">
                <div className="kc-form-container">
                    <form onSubmit={handlePopulate} className="kc-form">
                        <h2>{id ? 'View/Edit Knowledge Card' : 'Create New Knowledge Card'}</h2>

                        <label htmlFor="kc-link-type">Link To</label>
                        <select id="kc-link-type" value={linkType} onChange={e => setLinkType(e.target.value)}>
                            <option value="">Select Type...</option>
                            <option value="donor">Donor</option>
                            <option value="outcome">Outcome</option>
                            <option value="field_context">Field Context</option>
                        </select>

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
                                />
                            </>
                        )}

                        <label htmlFor="kc-title">Title*</label>
                        <input id="kc-title" type="text" value={title} onChange={e => setTitle(e.target.value)} required />

                    <label htmlFor="kc-summary">Description</label>
                        <textarea id="kc-summary" value={summary} onChange={e => setSummary(e.target.value)} />

                        <div className="kc-form-actions">
                            <CommonButton type="button" label="Identify References" />
                        </div>

                        <h3>References</h3>
                        {references.map((ref, index) => (
                            <div key={index} className="kc-reference-item">
                                <input type="url" placeholder="https://example.com" value={ref.url} onChange={e => handleReferenceChange(index, 'url', e.target.value)} />
                                <input type="text" placeholder="Reference Type" value={ref.reference_type} onChange={e => handleReferenceChange(index, 'reference_type', e.target.value)} />
                                <button type="button" onClick={() => removeReference(index)}>Remove</button>
                            </div>
                        ))}
                        <button type="button" onClick={addReference}>Add Reference</button>

                        <div className="kc-form-actions">
                            <CommonButton type="button" onClick={() => handleSave()} label="Save Card" loading={loading} disabled={loading || !title} />
                            <CommonButton type="submit" label="Populate Card Content" loading={loading} disabled={loading || !title} />
                        </div>
                    </form>
                </div>
                {generatedSections && (
                    <div className="kc-content-container">
                        <h2>Generated Content</h2>
                        {Object.entries(generatedSections).map(([section, content]) => (
                            <div key={section} className="kc-section">
                                <h3>{section}</h3>
                                <p>{content}</p>
                                <div className="kc-section-actions">
                                    <button>Edit</button>
                                    <button>Regenerate</button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Base>
    );
}
