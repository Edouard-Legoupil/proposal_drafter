import './KnowledgeCard.css';
import { useState, useEffect, useCallback, useRef } from 'react'; // Added useRef
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import CreatableSelect from 'react-select/creatable';
import Base from '../../components/Base/Base';
import CommonButton from '../../components/CommonButton/CommonButton';
import LoadingModal from '../../components/LoadingModal/LoadingModal';
import ProgressModal from '../../components/ProgressModal/ProgressModal';
import KnowledgeCardHistory from '../../components/KnowledgeCardHistory/KnowledgeCardHistory';
import KnowledgeCardReferences from '../../components/KnowledgeCardReferences/KnowledgeCardReferences';
import UploadReferenceModal from '../../components/UploadReferenceModal/UploadReferenceModal';
import { setupSse } from '../../utils/sse';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import word_icon from '../../assets/images/word.svg';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function KnowledgeCard() {
    const navigate = useNavigate();
    const { id } = useParams();
    const location = useLocation();

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
    const [proposal_template, setProposalTemplate] = useState(null);
    const [editingReferenceIndex, setEditingReferenceIndex] = useState(null);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [currentReference, setCurrentReference] = useState(null);

    // Use refs to track current state without stale closures
    const summaryRef = useRef(summary);
    useEffect(() => { summaryRef.current = summary; }, [summary]);
    const linkTypeRef = useRef(linkType);
    useEffect(() => { linkTypeRef.current = linkType; }, [linkType]);
    const linkedIdRef = useRef(linkedId);
    useEffect(() => { linkedIdRef.current = linkedId; }, [linkedId]);
    const referencesRef = useRef(references);
    const eventSourceRef = useRef(eventSource);
    const pollingRef = useRef({ intervalId: null, attempts: 0 });
    const [pollingFor, setPollingFor] = useState(null); // 'ingest' or 'populate'
    const fetchDataRef = useRef(null);

    // Sync refs with state
    useEffect(() => {
        referencesRef.current = references;
    }, [references]);

    useEffect(() => {
        eventSourceRef.current = eventSource;
    }, [eventSource]);

    const getStatus = useCallback((ref) => {
        if (ref.status) return ref.status;
        if (ref.scraping_error) return 'error';
        if (ref.scraped_at) return 'ingested';
        return 'pending';
    }, []);

    const getStatusMessage = useCallback((ref) => {
        if (ref.status_message) return ref.status_message;
        if (ref.scraping_error) return 'Scraping failed';
        if (ref.scraped_at) return 'Ingested successfully';
        return 'Pending ingestion';
    }, []);

    // Cleanup effect for EventSource and other resources
    useEffect(() => {
        return () => {
            // Cleanup EventSource on component unmount
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                console.log('EventSource cleaned up on unmount');
            }
            // Cleanup polling interval on unmount
            if (pollingRef.current.intervalId) {
                clearInterval(pollingRef.current.intervalId);
                console.log('Polling interval cleaned up on unmount');
            }
        };
    }, []);

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
                    setSummary(card.summary || '');
                    let determinedLinkType = '';
                    if (card.donor_id) {
                        determinedLinkType = 'donor';
                        setLinkType('donor');
                        setLinkedId(card.donor_id);
                    } else if (card.outcome_id) {
                        determinedLinkType = 'outcome';
                        setLinkType('outcome');
                        setLinkedId(card.outcome_id);
                    } else if (card.field_context_id) {
                        determinedLinkType = 'field_context';
                        setLinkType('field_context');
                        setLinkedId(card.field_context_id);
                    }
                    setReferences(card.references || []);
                    
                    // Properly handle generated sections
                    if (card.generated_sections && typeof card.generated_sections === 'object') {
                        // Ensure it's a non-empty object
                        const sections = card.generated_sections;
                        if (Object.keys(sections).length > 0) {
                            setGeneratedSections(sections);
                        } else {
                            setGeneratedSections(null);
                        }
                    } else {
                        setGeneratedSections(null);
                    }

                    // Fetch the template using the DERIVED linkType, not from the card data
                    if (determinedLinkType) {
                        const templateName = `knowledge_card_${determinedLinkType}_template.json`;
                        const templateRes = await authenticatedFetch(`${API_BASE_URL}/templates/${templateName}`, { credentials: 'include' });
                        if (templateRes.ok) {
                            const templateData = await templateRes.json();
                            setProposalTemplate(templateData);
                        } else {
                            console.error(`Failed to load template: ${templateName}`);
                            setProposalTemplate(null);
                        }
                    } else {
                        setProposalTemplate(null);
                    }
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
        fetchDataRef.current = fetchData;
    }, [fetchData]);

    useEffect(() => {
        if (!pollingRef.current.intervalId) {
            return; // Not polling, do nothing
        }

        pollingRef.current.attempts += 1;

        if (pollingFor === 'ingest') {
            const maxAttempts = 15; // Poll for 30 seconds
            if (pollingRef.current.attempts >= maxAttempts) {
                console.log("Finished polling for reference ingestion.");
                clearInterval(pollingRef.current.intervalId);
                pollingRef.current.intervalId = null;
                setLoading(false);
                setLoadingMessage('');
                if (fetchDataRef.current) {
                    fetchDataRef.current(); // Final fetch to get the latest data
                }
                alert("Reference ingestion completed successfully!");
            }
        } else if (pollingFor === 'populate') {
            const maxAttempts = 5; // Poll for 10 seconds to allow DB to update
            if (pollingRef.current.attempts >= maxAttempts) {
                console.log("Finished polling for content generation.");
                clearInterval(pollingRef.current.intervalId);
                pollingRef.current.intervalId = null;
                setLoading(false);
                setLoadingMessage('');
                fetchData(); // Final fetch to get the latest data
                alert("Content generation completed successfully!");
            }
        }
    }, [references, getStatus, pollingFor, fetchData]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        const fetchTemplate = async () => {
            if (!id && linkType) { // Only for new cards
                const templateName = `knowledge_card_${linkType}_template.json`;
                try {
                    const response = await authenticatedFetch(`${API_BASE_URL}/templates/${templateName}`, { credentials: 'include' });
                    if (response.ok) {
                        const data = await response.json();
                        setProposalTemplate(data);
                    } else {
                        console.error("Failed to load template");
                    }
                } catch (error) {
                    console.error("Error fetching template:", error);
                }
            }
        };
        fetchTemplate();
    }, [id, linkType, authenticatedFetch]);

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

    const handleSave = useCallback(async (navigateOnSuccess = true) => {
        // Validate required fields
        if (!summaryRef.current.trim()) {
            alert("Description is required.");
            return { ok: false };
        }

        if (!linkTypeRef.current || !linkedIdRef.current) {
            alert("Please select a link type and item.");
            return { ok: false };
        }

        setLoading(true);
        setLoadingMessage("Saving knowledge card...");
        
        let finalLinkedId = linkedIdRef.current;
        if (finalLinkedId && finalLinkedId.startsWith('new_')) {
            const endpointMap = {
                donor: 'donors',
                outcome: 'outcomes',
                field_context: 'field-contexts',
            };
            const endpoint = endpointMap[linkTypeRef.current];
            const value = finalLinkedId.substring(4);
            
            if (!value.trim()) {
                alert("Please enter a valid name for the new item.");
                setLoading(false);
                return { ok: false };
            }

            try {
                const response = await authenticatedFetch(`${API_BASE_URL}/${endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: value }),
                    credentials: 'include'
                });
                if (!response.ok) {
                    const error = await response.json();
                    alert(`Failed to create new ${linkTypeRef.current}: ${error.detail}`);
                    setLoading(false);
                    return { ok: false };
                }
                const data = await response.json();
                finalLinkedId = data.id;
            } catch (error) {
                console.error("Error creating new item:", error);
                alert("Failed to create new item.");
                setLoading(false);
                return { ok: false };
            }
        }

        const payload = {
            summary: summaryRef.current.trim(),
            donor_id: linkTypeRef.current === 'donor' ? finalLinkedId : null,
            outcome_id: linkTypeRef.current === 'outcome' ? finalLinkedId : null,
            field_context_id: linkTypeRef.current === 'field_context' ? finalLinkedId : null,
            references: referencesRef.current.filter(r => r.url && r.reference_type)
        };

        const url = id ? `${API_BASE_URL}/knowledge-cards/${id}` : `${API_BASE_URL}/knowledge-cards`;
        const method = id ? 'PUT' : 'POST';

        try {
            const response = await authenticatedFetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                credentials: 'include'
            });

            if (response.ok) {
                if (navigateOnSuccess) {
                    alert(`Knowledge card ${id ? 'updated' : 'created'} successfully!`);
                    sessionStorage.setItem('selectedDashboardTab', 'knowledge');
                    navigate('/dashboard');
                }
                return response;
            } else {
                const error = await response.json();
                alert(`Error ${id ? 'updating' : 'creating'} knowledge card: ${error.detail}`);
                return { ok: false };
            }
        } catch (error) {
            console.error("Error saving knowledge card:", error);
            alert("Failed to save knowledge card.");
            return { ok: false };
        } finally {
            setLoading(false);
            setLoadingMessage('');
        }
    }, [id, navigate, authenticatedFetch]);

    const handleIdentifyReferences = useCallback(async () => {
        //  Validate required fields before proceeding
        if (!linkType || !linkedId) {
            alert("Please select a link type and item before identifying references.");
            return;
        }

        let cardId = id;

        // Use proper async/await for navigation
        if (!cardId) {
            const saveResponse = await handleSave(false);
            if (!saveResponse.ok) {
                return;
            }
            const data = await saveResponse.json();
            cardId = data.knowledge_card_id;
            
            navigate(`/knowledge-card/${cardId}`, {
                replace: true,
                state: { fromAction: 'identify' }
            });
            return;
        }

        setLoading(true);
        setLoadingMessage("Let me search the web for you and identify the relevant references. Just a minute...");
        
        try {
            // Build title from linked elements only (not summary)
            const selectedItem = linkOptions.find(o => o.id === linkedId);
            let title = '';
            
            if (selectedItem) {
                title = `${linkType.replace('_', ' ').toUpperCase()}: ${selectedItem.name}`;
                if (linkType === 'field_context' && selectedGeoCoverage) {
                    title += ` (${selectedGeoCoverage})`;
                }
            }

            const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${cardId}/identify-references`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    linked_element: linkType,
                    // Remove summary field or set to empty
                    summary: ''
                }),
                credentials: 'include'
            });

            if (response.ok) {
                await fetchData(); // Wait for data refresh
                alert("Good News! References were successfully identified !");
            } else {
                const error = await response.json();
                alert(`Aie.. Error identifying references: ${error.detail}`);
            }
        } catch (error) {
            console.error("Sorry - I failed to identify references:", error);
            alert("An error occurred while identifying references.");
        } finally {
            setLoading(false);
            setLoadingMessage('');
        }
    }, [id, linkType, linkedId, handleSave, navigate, linkOptions, selectedGeoCoverage, authenticatedFetch, fetchData]);

    const handleIngestReferences = useCallback(async () => {
        let cardId = id;
    
        if (!cardId) {
            const saveResponse = await handleSave(false);
            if (!saveResponse.ok) return;
            const data = await saveResponse.json();
            cardId = data.knowledge_card_id;
            
            navigate(`/knowledge-card/${cardId}`, { replace: true, state: { fromAction: 'ingest' } });
            return;
        }
    
        setLoading(true);
        setLoadingMessage("Ingesting all references... This may take a while.");
    
        try {
            const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${cardId}/ingest-references`, {
                method: 'POST',
                credentials: 'include'
            });
    
            if (response.ok) {
                setLoadingMessage("Reference ingestion started... This may take a while, the screen will refresh automatically when it is done.");
    
                // Start polling immediately, like the 'populate' function does.
                setPollingFor('ingest');
                pollingRef.current.attempts = 0;
                pollingRef.current.intervalId = setInterval(() => {
                    console.log(`Polling for ingestion updates... Attempt: ${pollingRef.current.attempts + 1}`);
                    if (fetchDataRef.current) {
                        fetchDataRef.current();
                    }
                }, 2000);
    
                // The SSE events will now only update the UI with statuses, but not control the polling.
                const onMessage = (data) => {
                    setReferences(prev => 
                        prev.map(ref => ref.id === data.reference_id ? { ...ref, status: data.status, status_message: data.message } : ref)
                    );
                };
    
                const onError = (error) => {
                    console.error("Ingestion SSE error:", error);
                    if (eventSourceRef.current) {
                        eventSourceRef.current.close();
                        eventSourceRef.current = null;
                    }
                };
                
                const onTimeout = () => {
                    console.warn("Ingestion SSE timeout.");
                    if (eventSourceRef.current) {
                        eventSourceRef.current.close();
                        eventSourceRef.current = null;
                    }
                };
    
                const closeSse = setupSse(`${API_BASE_URL}/knowledge-cards/${cardId}/ingest-status`, onMessage, onError, onTimeout);
                eventSourceRef.current = { close: closeSse };
    
            } else {
                const error = await response.json();
                console.error(`Error starting ingestion: ${error.detail}`);
                setLoading(false);
                setLoadingMessage('');
            }
        } catch (error) {
            console.error("Error starting reference ingestion:", error);
            setLoading(false);
            setLoadingMessage('');
        }
    }, [id, handleSave, navigate, authenticatedFetch, fetchData, getStatus]);

    useEffect(() => {
        const fromAction = location.state?.fromAction;
        if (id && fromAction) {
            // Clean the state from location to prevent re-triggering
            navigate(location.pathname, { replace: true });

            if (fromAction === 'identify') {
                handleIdentifyReferences();
            } else if (fromAction === 'ingest') {
                handleIngestReferences();
            }
        }
    }, [id, location.state, navigate, handleIdentifyReferences, handleIngestReferences]);

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

        try {
            let cardId = id;
            let isNewCard = false;

            // If it's a new card, save it first to get an ID
            if (!cardId) {
                isNewCard = true;
                const saveResponse = await handleSave(false); // Don't navigate
                if (!saveResponse.ok) {
                    alert("Could not save the new knowledge card. Please fill in all required fields.");
                    return;
                }
                const data = await saveResponse.json();
                cardId = data.knowledge_card_id;
            }

            // Now we are sure we have a cardId
            const isNewReference = reference.isNew;
            const url = isNewReference ? `${API_BASE_URL}/knowledge-cards/${cardId}/references` : `${API_BASE_URL}/knowledge-cards/references/${reference.id}`;
            const method = isNewReference ? 'POST' : 'PUT';

            const response = await authenticatedFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reference),
                credentials: 'include'
            });

            if (response.ok) {
                if (isNewCard) {
                    // If it was a new card, we navigate to the new URL.
                    // This will cause a re-render and fetchData will be called with the correct new ID.
                    navigate(`/knowledge-card/${cardId}`, { replace: true });
                } else {
                    // If it was an existing card, just refetch the data.
                    await fetchData();
                    setEditingReferenceIndex(null);
                }
            } else {
                const error = await response.json();
                const errorMessage = error.detail || JSON.stringify(error);
                alert(`Failed to save reference: ${errorMessage}`);
            }
        } catch (error) {
            console.error("Error saving reference:", error);
            alert("An unexpected error occurred while saving the reference.");
        }
    };

    const handleRemoveReference = async (refId) => {
        if (!window.confirm("Are you sure you want to delete this reference?")) {
            return;
        }

        setLoading(true);
        setLoadingMessage("Deleting this reference as requested...");

        try {
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
        } catch (error) {
            console.error("Error deleting reference:", error);
            alert("Failed to delete reference.");
        } finally {
            setLoading(false);
            setLoadingMessage('');
        }
    };

    const handlePopulate = async (e) => {
        e.preventDefault();

        if (!linkType || !linkedId) {
            alert("Please select a link type and item before generating content.");
            return;
        }
    
        const saveResponse = await handleSave(false);
        if (saveResponse.ok) {
            const cardId = id || (await saveResponse.json()).knowledge_card_id;
            setIsProgressModalOpen(true);
            setGenerationProgress(0);
            setGenerationMessage("Starting content generation for the different sections of the card...");
    
            try {
                const genResponse = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${cardId}/generate`, {
                    method: 'POST',
                    credentials: 'include'
                });
    
                if (genResponse.ok) {
                    const es = new EventSource(`${API_BASE_URL}/knowledge-cards/${cardId}/status`);
                    setEventSource(es);
                    eventSourceRef.current = es;
    
                    es.onmessage = (event) => {
                        try {
                            const statusData = JSON.parse(event.data);
                            setGenerationProgress(statusData.progress);
                            setGenerationMessage(statusData.message);

                            if (statusData.section_name && statusData.section_content) {
                                //  Use functional update to properly build sections
                                setGeneratedSections(prev => {
                                    const newSections = {
                                        ...prev,
                                        [statusData.section_name]: statusData.section_content
                                    };
                                    return newSections;
                                });
                            }

                            if (statusData.progress >= 100 || statusData.progress === -1) {
                                es.close();
                                setEventSource(null);
                                eventSourceRef.current = null;
                                setIsProgressModalOpen(false);

                                if (statusData.progress >= 100) {
                                    // Start polling to ensure DB is updated before showing success
                                    setLoading(true);
                                    setLoadingMessage("Finalizing content generation... This might take a moment.");
                                    setPollingFor('populate');
                                    pollingRef.current.attempts = 0; // Reset attempts
                                    pollingRef.current.intervalId = setInterval(() => {
                                        console.log(`Polling for content updates... Attempt: ${pollingRef.current.attempts + 1}`);
                                        if (fetchDataRef.current) {
                                            fetchDataRef.current();
                                        }
                                    }, 2000); // Poll every 2 seconds
                                } else {
                                    alert("Content generation failed. Please try again.");
                                }
                            }
                        } catch (error) {
                            console.error("Error processing generation status:", error);
                        }
                    };
    
                    es.onerror = (error) => {
                        console.error("EventSource error:", error);
                        es.close();
                        setEventSource(null);
                        eventSourceRef.current = null;
                        setIsProgressModalOpen(false);
                        alert("Content generation encountered an error.");
                    };
    
                    setTimeout(() => {
                        if (es.readyState !== EventSource.CLOSED) {
                            es.close();
                            setEventSource(null);
                            eventSourceRef.current = null;
                            setIsProgressModalOpen(false);
                            alert("Content generation timeout. Please check back later.");
                        }
                    }, 600000);
    
                } else {
                    const error = await genResponse.json();
                    alert(`Error starting content generation: ${error.detail}`);
                    setIsProgressModalOpen(false);
                }
            } catch (error) {
                console.error("Error starting content generation:", error);
                alert("Failed to start content generation.");
                setIsProgressModalOpen(false);
            }
        }
    };

    const handleEditClick = (section, content) => {
        setEditingSection(section);
        setEditedContent(content);
    };

    const handleSaveClick = async (section) => {
        setLoading(true);
        setLoadingMessage("Saving section...");
        
        try {
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
                alert("Section saved successfully!");
            } else {
                const error = await response.json();
                alert(`Failed to save section: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error saving section:", error);
            alert("Failed to save section.");
        } finally {
            setLoading(false);
            setLoadingMessage('');
        }
    };

    const handleCancelClick = () => {
        setEditingSection(null);
    };

    const fetchHistory = async () => {
        if (id) {
            setLoading(true);
            setLoadingMessage("Loading history...");
            
            try {
                const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${id}/history`, { credentials: 'include' });
                if (response.ok) {
                    const data = await response.json();
                    setHistory(data.history);
                    setIsHistoryModalOpen(true);
                } else {
                    const error = await response.json();
                    alert(`Failed to fetch history: ${error.detail}`);
                }
            } catch (error) {
                console.error("Error fetching history:", error);
                alert("Failed to fetch history.");
            } finally {
                setLoading(false);
                setLoadingMessage('');
            }
        }
    };

    const handleReferenceFieldChange = (index, field, value) => {
        const newReferences = [...references];
        newReferences[index][field] = value;
        setReferences(newReferences);
    };


    const handleOpenUploadModal = (reference) => {
        setCurrentReference(reference);
        setIsUploadModalOpen(true);
    };

    const handleUploadReference = async (referenceId, file) => {
        setLoading(true);
        setLoadingMessage('Uploading file...');
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Step 1: Upload the file
            const uploadResponse = await authenticatedFetch(
                `${API_BASE_URL}/knowledge-cards/references/${referenceId}/upload`,
                { method: 'POST', body: formData, credentials: 'include' }
            );

            if (!uploadResponse.ok) {
                const error = await uploadResponse.json();
                console.error(`Upload failed: ${error.detail}`);
                setLoading(false);
                setLoadingMessage('');
                return;
            }

            // Step 2: Close modal and trigger re-ingestion of the single reference
            setIsUploadModalOpen(false);
            setLoadingMessage('File uploaded. Re-ingesting reference...');

            const reingestResponse = await authenticatedFetch(
                `${API_BASE_URL}/knowledge-cards/${id}/references/${referenceId}/reingest`,
                { method: 'POST', credentials: 'include' }
            );

            if (!reingestResponse.ok) {
                const error = await reingestResponse.json();
                console.error(`Failed to start re-ingestion: ${error.detail}`);
                setLoading(false);
                setLoadingMessage('');
                return;
            }

            // Step 3: Listen for SSE updates for the single reference
            const onMessage = (data) => {
                if (data.reference_id === referenceId) {
                    setReferences(prev => prev.map(ref =>
                        ref.id === referenceId ? { ...ref, status: data.status, status_message: data.message } : ref
                    ));

                    if (['ingested', 'error', 'skipped'].includes(data.status)) {
                        if (eventSourceRef.current) eventSourceRef.current.close();
                        setLoading(false);
                        setLoadingMessage('');
                    }
                }
            };

            const onError = (error) => {
                console.error('Re-ingestion SSE error:', error);
                setLoading(false);
                setLoadingMessage('');
            };

            const onTimeout = () => {
                console.warn('Re-ingestion timed out.');
                setLoading(false);
                setLoadingMessage('');
            };

            const closeSse = setupSse(`${API_BASE_URL}/knowledge-cards/${id}/ingest-status`, onMessage, onError, onTimeout);
            eventSourceRef.current = { close: closeSse };

        } catch (error) {
            console.error('An error occurred during the upload/re-ingest process:', error);
            setLoading(false);
            setLoadingMessage('');
        }
    };

    async function handleExport (format)
    {


            const cardId = id;

            if (!cardId || cardId === "undefined") {
                    setErrorMessage("No draft available to export. Please create or load a draft first.");
                    return;
            }

            const response = await fetch(`${API_BASE_URL}/knowledge-cards/${id}/generate-document/?format=${format}`, {
                    method: "GET",
                    headers: { 'Content-Type': 'application/json' },
                    credentials: "include"
            })

            if(response.ok)
            {
                    const blob = await response.blob();
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    const selectedItem = linkOptions.find(o => o.id === linkedId);
                    link.download = selectedItem ? selectedItem.name : "knowledge-card" + "." + format;
                    document.body.appendChild(link);
                    link.click();
                    link.remove();

                    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
            }
            else if(response.status === 401)
            {
                    sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                    navigate("/login")
            }
            else
                    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    return (
        <Base>
            {/* Modals */}
            <ProgressModal
                isOpen={isProgressModalOpen}
                onClose={() => {
                    // Close EventSource when modal closes
                    if (eventSourceRef.current) {
                        eventSourceRef.current.close();
                        setEventSource(null);
                        eventSourceRef.current = null;
                    }
                    setIsProgressModalOpen(false);
                }}
                progress={generationProgress}
                message={generationMessage}
            />

            {isHistoryModalOpen && (
                <KnowledgeCardHistory
                    history={history}
                    onClose={() => setIsHistoryModalOpen(false)}
                />
            )}

            <UploadReferenceModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                onUpload={handleUploadReference}
                reference={currentReference}
            />

            <LoadingModal isOpen={loading} message={loadingMessage} />

            <div className="kc-container" data-testid="knowledge-card-container">
                <div className="kc-form-container">
                    <form onSubmit={handlePopulate} className="kc-form" data-testid="knowledge-card-form">
                        {/* Header */}
                        <div className="kc-form-header">
                            <h2 data-testid="kc-form-header-title">{id ? 'View/Edit Knowledge Card' : 'Create New Knowledge Card'}</h2>
                            {id && (
                                <CommonButton
                                    type="button"
                                    onClick={fetchHistory}
                                    label="View Content History"
                                    data-testid="view-history-button"
                                />
                            )}
                        </div>

                        {/* Form Fields */}
                        <label htmlFor="kc-link-type">Link To</label>
                        <select
                            id="kc-link-type"
                            value={linkType}
                            onChange={e => setLinkType(e.target.value)}
                            data-testid="link-type-select"
                            required
                        >
                            <option value="">Select Type...</option>
                            <option value="donor">Donor</option>
                            <option value="outcome">Outcome</option>
                            <option value="field_context">Field Context</option>
                        </select>

                        {linkType === 'field_context' && (
                            <>
                                <label htmlFor="kc-geo-coverage">Geographic Coverage</label>
                                <select
                                    id="kc-geo-coverage"
                                    value={selectedGeoCoverage}
                                    onChange={e => setSelectedGeoCoverage(e.target.value)}
                                    data-testid="geo-coverage-select"
                                >
                                    <option value="">All</option>
                                    {geographicCoverages.map(geo => (
                                        <option key={geo} value={geo}>{geo}</option>
                                    ))}
                                </select>
                            </>
                        )}

                        {linkType && (
                            <>
                                <label htmlFor="kc-linked-id">Select Item*</label>
                                <CreatableSelect
                                    isClearable
                                    id="kc-linked-id"
                                    name="kc-linked-id"
                                    value={linkOptions.find(o => o.id === linkedId) ?
                                        { value: linkedId, label: linkOptions.find(o => o.id === linkedId).name } : null}
                                    onChange={option => setLinkedId(option ? option.value : '')}
                                    onCreateOption={inputValue => {
                                        const newOption = { id: `new_${inputValue}`, name: inputValue };
                                        if (linkType === 'donor') setNewDonors(prev => [...prev, newOption]);
                                        if (linkType === 'outcome') setNewOutcomes(prev => [...prev, newOption]);
                                        if (linkType === 'field_context') setNewFieldContexts(prev => [...prev, newOption]);
                                        setLinkedId(newOption.id);
                                    }}
                                    options={linkOptions.map(o => ({ ...o, value: o.id, label: o.name }))}
                                    data-testid="linked-item-select"
                                    required
                                />
                            </>
                        )}

                        <label htmlFor="kc-summary">Description*</label>
                        <textarea
                            id="kc-summary"
                            value={summary}
                            onChange={e => setSummary(e.target.value)}
                            required
                            data-testid="summary-textarea"
                            placeholder="Enter a description for this knowledge card..."
                        />

                        <KnowledgeCardReferences
                            references={references}
                            editingReferenceIndex={editingReferenceIndex}
                            handleReferenceFieldChange={handleReferenceFieldChange}
                            handleSaveReference={handleSaveReference}
                            handleCancelEditReference={handleCancelEditReference}
                            handleEditReference={handleEditReference}
                            handleRemoveReference={handleRemoveReference}
                            handleAddReference={handleAddReference}
                            getStatus={getStatus}
                            getStatusMessage={getStatusMessage}
                            onUploadClick={handleOpenUploadModal}
                        />

                        {/* Form Actions */}
                        <div className="kc-form-actions-box">
                            <div className="kc-form-actions">
                                <CommonButton
                                    type="button"
                                    onClick={handleIdentifyReferences}
                                    label="1. Identify References"
                                    className="squared-btn"
                                    data-testid="identify-references-button"
                                    disabled={!linkType || !linkedId}
                                />
                                <CommonButton
                                    type="button"
                                    onClick={handleIngestReferences}
                                    label="2. Ingest References"
                                    className="squared-btn"
                                    data-testid="ingest-references-button"
                                    disabled={references.length === 0}
                                />
                                <CommonButton
                                    type="submit"
                                    label="3. Populate Card Content"
                                    className="squared-btn"
                                    data-testid="populate-card-button"
                                    disabled={!linkType || !linkedId}
                                />
                                <CommonButton
                                    type="button"
                                    onClick={() => handleSave()}
                                    label="Save & Close"
                                    className="squared-btn"
                                    data-testid="close-card-button"
                                />
                            </div>
                        </div>
                    </form>
                </div>

                {/* Generated Content Section - Automatically shows when content exists */}
                {generatedSections && proposal_template && proposal_template.sections && (
                    <div className="kc-content-container" data-testid="generated-content-container">
                        <div className="kc-content-header">
                            <h2>Generated Content</h2>
                            <button type="button" onClick={() => handleExport("docx")} className="download-word-btn" data-testid="export-word-button">
                                <img src={word_icon} alt="Download as Word" />
                                Download as Word
                            </button>
                        </div>
                        {proposal_template.sections.map(sectionInfo => {
                            const section = sectionInfo.section_name;
                            const content = generatedSections[section];
                            // Only show sections that have content
                            if (!content) return null;

                            return (
                                <div key={section} className={`kc-section ${editingSection === section ? 'kc-section-editing' : ''}`} data-testid={`generated-section-${section}`}>
                                    <h3>{section}</h3>
                                    {editingSection === section ? (
                                        <textarea
                                            className="kc-edit-textarea"
                                            value={editedContent}
                                            onChange={(e) => setEditedContent(e.target.value)}
                                            rows={10}
                                            data-testid={`edit-section-textarea-${section}`}
                                        />
                                    ) : (
                                        <div className="kc-section-content" data-testid={`section-content-${section}`}>
                                            <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                                        </div>
                                    )}
                                    <div className="kc-section-actions">
                                        {editingSection === section ? (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={() => handleSaveClick(section)}
                                                    data-testid={`save-section-button-${section}`}
                                                >
                                                    Save
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={handleCancelClick}
                                                    data-testid={`cancel-edit-button-${section}`}
                                                >
                                                    Cancel
                                                </button>
                                            </>
                                        ) : (
                                            <button
                                                type="button"
                                                onClick={() => handleEditClick(section, content)}
                                                data-testid={`edit-section-button-${section}`}
                                            >
                                                Edit
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}


            </div>
        </Base>
    );
}