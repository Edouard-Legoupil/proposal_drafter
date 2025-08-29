import './KnowledgeCard.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Base from '../../components/Base/Base';
import CommonButton from '../../components/CommonButton/CommonButton';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function KnowledgeCard() {
    const navigate = useNavigate();

    const [title, setTitle] = useState('');
    const [summary, setSummary] = useState('');
    const [linkType, setLinkType] = useState(''); // 'donor', 'outcome', 'field_context'
    const [linkedId, setLinkedId] = useState('');
    const [references, setReferences] = useState([{ url: '', reference_type: '' }]);
    const [loading, setLoading] = useState(false);

    const [donors, setDonors] = useState([]);
    const [outcomes, setOutcomes] = useState([]);
    const [fieldContexts, setFieldContexts] = useState([]);
    const [linkOptions, setLinkOptions] = useState([]);

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
            } catch (error) {
                console.error("Error fetching data for KC form:", error);
            }
        }
        fetchData();
    }, []);

    useEffect(() => {
        if (linkType === 'donor') setLinkOptions(donors);
        else if (linkType === 'outcome') setLinkOptions(outcomes);
        else if (linkType === 'field_context') setLinkOptions(fieldContexts);
        else setLinkOptions([]);
        setLinkedId(''); // Reset linked ID when type changes
    }, [linkType, donors, outcomes, fieldContexts]);

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

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const payload = {
            title,
            summary,
            donor_id: linkType === 'donor' ? linkedId : null,
            outcome_id: linkType === 'outcome' ? linkedId : null,
            field_context_id: linkType === 'field_context' ? linkedId : null,
            references: references.filter(r => r.url && r.reference_type)
        };

        const response = await fetch(`${API_BASE_URL}/knowledge-cards`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });
        setLoading(false);

        if (response.ok) {
            alert('Knowledge card created successfully!');
            navigate('/dashboard');
        } else {
            const error = await response.json();
            alert(`Error creating knowledge card: ${error.detail}`);
        }
    };

    return (
        <Base>
            <div className="kc-form-container">
                <form onSubmit={handleSubmit} className="kc-form">
                    <h2>Create New Knowledge Card</h2>

                    <label htmlFor="kc-title">Title*</label>
                    <input id="kc-title" type="text" value={title} onChange={e => setTitle(e.target.value)} required />

                    <label htmlFor="kc-summary">Summary</label>
                    <textarea id="kc-summary" value={summary} onChange={e => setSummary(e.target.value)} />

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
                            <select id="kc-linked-id" value={linkedId} onChange={e => setLinkedId(e.target.value)} required>
                                <option value="">Select Item...</option>
                                {linkOptions.map(option => (
                                    <option key={option.id} value={option.id}>{option.name}</option>
                                ))}
                            </select>
                        </>
                    )}

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
                        <CommonButton type="submit" label="Create Card" loading={loading} disabled={loading || !title} />
                    </div>
                </form>
            </div>
        </Base>
    );
}
