import './KnowledgeCard.css';
import { Snackbar, Alert } from '@mui/material';
import { useState, useEffect, useCallback, useRef } from 'react'; // Added useRef
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import CreatableSelect from 'react-select/creatable';
import Base from '../../components/Base/Base';
import CommonButton from '../../components/CommonButton/CommonButton';
import LoadingModal from '../../components/LoadingModal/LoadingModal';
import ConfirmationModal from '../../components/ConfirmationModal/ConfirmationModal';
import AlertModal from '../../components/AlertModal/AlertModal';
import ProgressModal from '../../components/ProgressModal/ProgressModal';
import KnowledgeCardHistory from '../../components/KnowledgeCardHistory/KnowledgeCardHistory';
import KnowledgeCardReferences from '../../components/KnowledgeCardReferences/KnowledgeCardReferences';
import UploadReferenceModal from '../../components/UploadReferenceModal/UploadReferenceModal';
import { setupSse } from '../../utils/sse';
import Markdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
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
    const [allKnowledgeCards, setAllKnowledgeCards] = useState([]);
    const [selectedGeoCoverage, setSelectedGeoCoverage] = useState('');
    const [linkOptions, setLinkOptions] = useState([]);
    const [newDonors, setNewDonors] = useState([]);
    const [newOutcomes, setNewOutcomes] = useState([]);
    const [newFieldContexts, setNewFieldContexts] = useState([]);
    const [proposal_template, setProposalTemplate] = useState(null);
    const [editingReferenceIndex, setEditingReferenceIndex] = useState(null);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [currentReference, setCurrentReference] = useState(null);
    const [isConfirmationModalOpen, setIsConfirmationModalOpen] = useState(false);
    const [existingCard, setExistingCard] = useState(null);
    const [initialDataLoaded, setInitialDataLoaded] = useState(false);
    const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
    const [alertModalMessage, setAlertModalMessage] = useState('');
    const [currentUser, setCurrentUser] = useState(null);

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
            // Get profile for ownership check
            const profRes = await authenticatedFetch(`${API_BASE_URL}/profile`, { credentials: 'include' });
            let curUser = null;
            if (profRes.ok) {
                const profData = await profRes.json();
                curUser = profData.user;
                setCurrentUser(curUser);
            }

            if (id) {
                const cardRes = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${id}`, { credentials: 'include' });
                if (cardRes.ok) {
                    const data = await cardRes.json();
                    const card = data.knowledge_card;

                    if (curUser) {
                        const isOwner = curUser.id === card.created_by || curUser.user_id === card.created_by;
                        if (!isOwner) {
                            navigate(`/review/knowledge-card/${id}`);
                            return;
                        }
                    }

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

            const [donorsRes, outcomesRes, allFieldContextsRes, allKnowledgeCardsRes] = await Promise.all([
                authenticatedFetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
                authenticatedFetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
                authenticatedFetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' }),
                authenticatedFetch(`${API_BASE_URL}/knowledge-cards`, { credentials: 'include' })
            ]);
            if (donorsRes.ok) setDonors((await donorsRes.json()).donors);
            if (outcomesRes.ok) setOutcomes((await outcomesRes.json()).outcomes);
            if (allKnowledgeCardsRes.ok) setAllKnowledgeCards((await allKnowledgeCardsRes.json()).knowledge_cards);
            if (allFieldContextsRes.ok) {
                const allContexts = (await allFieldContextsRes.json()).field_contexts;
                const uniqueGeos = [...new Set(allContexts.map(fc => fc.geographic_coverage))];
                setGeographicCoverages(uniqueGeos);
            }
        } catch (error) {
            console.error("Error fetching data for KC form:", error);
        } finally {
            setInitialDataLoaded(true);
        }
    }, [id, navigate, authenticatedFetch]);

    useEffect(() => {
        fetchDataRef.current = fetchData;
    }, [fetchData]);

    // --- Progress + Notification State ---
    const [notif, setNotif] = useState({ open: false, message: '', severity: 'info' }); // info/success/error
    const [generatedCardId, setGeneratedCardId] = useState(null);
    const activeCardId = id || generatedCardId;

    // --- Streaming polling logic for populate ---
    useEffect(() => {
        if (pollingFor !== 'populate' || !activeCardId) return;
        setNotif({ open: true, message: 'Generating knowledge card…', severity: 'info' });

        // Start progress modal
        setGenerationProgress(0);
        setGenerationMessage("Starting knowledge card generation...");
        setIsProgressModalOpen(true);

        let isActive = true;
        const pollInterval = setInterval(async () => {
            if (!isActive) return;
            try {
                const response = await fetch(`${API_BASE_URL}/knowledge-cards/${activeCardId}`, { credentials: 'include' });
                if (response.ok) {
                    const data = await response.json();
                    // Populate streamed sections as soon as backend sends them
                    const generated = data.knowledge_card?.generated_sections || {};
                    setGeneratedSections(generated);
                    const totalSections = proposal_template && proposal_template.sections ? proposal_template.sections.length : 0;
                    const currSections = Object.keys(generated).length;

                    if (totalSections > 0 && currSections > 0) {
                        setGenerationProgress(Math.round(100 * currSections / totalSections));
                    } else {
                        setGenerationProgress(10 + Math.min(85, currSections * 15));
                    }

                    // Update message to show the NEXT section being generated
                    if (proposal_template && proposal_template.sections) {
                        const generatedKeys = Object.keys(generated);
                        const nextSection = proposal_template.sections.find(s => !generatedKeys.includes(s.section_name));
                        if (nextSection) {
                            setGenerationMessage(`Generating section: ${nextSection.section_name}...`);
                        } else {
                            // All done or unknown, maybe keep the last one or generic
                            const lastSection = generatedKeys.pop();
                            if (lastSection) setGenerationMessage(`Finalizing: ${lastSection}...`);
                        }
                    } else {
                        // Fallback if template not loaded yet
                        const lastSection = Object.keys(generated).pop();
                        if (lastSection) {
                            setGenerationMessage(`Generated section: ${lastSection}...`);
                        }
                    }

                    // Complete?
                    if (proposal_template && proposal_template.sections && proposal_template.sections.every(sectionInfo => Object.keys(generated).includes(sectionInfo.section_name))) {
                        setLoading(false);
                        setGenerationProgress(100);
                        setNotif({ open: true, message: "Knowledge card generation completed!", severity: 'success' });
                        clearInterval(pollInterval);
                        setPollingFor(null);
                        setIsProgressModalOpen(false); // Close progress modal on completion
                        // fetchData for full freshness (if required)
                        if (fetchDataRef.current) fetchDataRef.current();
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
                setNotif({ open: true, message: 'Error streaming knowledge card content. Try again.', severity: 'error' });
                setLoading(false);
                setIsProgressModalOpen(false); // Close modal on error
                clearInterval(pollInterval);
                setPollingFor(null);
            }
        }, 1000);
        return () => { isActive = false; clearInterval(pollInterval); };
    }, [pollingFor, activeCardId, proposal_template]);


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

    useEffect(() => {
        if (!id && linkedId && linkType && initialDataLoaded) {
            console.log(`Checking for duplicates. ID: ${id}, Linked ID: ${linkedId}, Link Type: ${linkType}, Loaded: ${initialDataLoaded}`);
            const existing = allKnowledgeCards.find(card => {
                if (linkType === 'donor') return card.donor_id === linkedId;
                if (linkType === 'outcome') return card.outcome_id === linkedId;
                if (linkType === 'field_context') return card.field_context_id === linkedId;
                return false;
            });
            console.log('Existing card found:', existing);

            if (existing) {
                setExistingCard(existing);
                setIsConfirmationModalOpen(true);
            }
        }
    }, [id, linkedId, linkType, allKnowledgeCards, initialDataLoaded]);

    const proceedWithSave = useCallback(async (navigateOnSuccess = true) => {
        // This function contains the original logic of handleSave
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
    }, [id, navigate, authenticatedFetch, newDonors, newOutcomes, newFieldContexts]);

    const handleSave = useCallback(async (navigateOnSuccess = true) => {
        return proceedWithSave(navigateOnSuccess);
    }, [proceedWithSave]);

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

    const handleIngestReferences = useCallback(async (referenceId = null) => {
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
        setLoadingMessage("Ingesting references... This may take a while.");

        const uningestedReferences = references.filter(ref => !ref.ingested_at).map(ref => ref.id);
        const isSingleReingest = typeof referenceId === 'string';
        const endpoint = isSingleReingest ? `${API_BASE_URL}/knowledge-cards/${cardId}/references/${referenceId}/reingest` : `${API_BASE_URL}/knowledge-cards/${cardId}/ingest-references`;
        const body = isSingleReingest ? null : JSON.stringify({ reference_ids: uningestedReferences });
        const headers = isSingleReingest ? {} : { 'Content-Type': 'application/json' };

        try {
            const response = await authenticatedFetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: body,
                credentials: 'include'
            });

            if (response.ok) {
                setLoadingMessage("Reference ingestion started... This may take a while, the screen will refresh automatically when it is done.");

                // Start polling immediately, like the 'populate' function does.
                setPollingFor('ingest');
                pollingRef.current.attempts = 0;
                pollingRef.current.intervalId = setInterval(() => {
                    pollingRef.current.attempts += 1;
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
        if (editingReferenceIndex !== null && references[editingReferenceIndex]?.isNew) {
            setReferences(references.filter((_, index) => index !== editingReferenceIndex));
        }
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
            const response = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${id}/references/${refId}`, {
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
            setGeneratedCardId(cardId);
            setPollingFor('populate');
            setIsProgressModalOpen(true);
            setGenerationProgress(0);
            setGenerationMessage("Requesting content generation...");

            try {
                const genResponse = await authenticatedFetch(`${API_BASE_URL}/knowledge-cards/${cardId}/generate`, {
                    method: 'POST',
                    credentials: 'include'
                });

                if (genResponse.ok) {
                    setGenerationMessage("Starting content generation...");
                } else {
                    const error = await genResponse.json();
                    alert(`Error starting content generation: ${error.detail}`);
                    setPollingFor(null);
                    setIsProgressModalOpen(false);
                }
            } catch (error) {
                console.error("Error starting content generation:", error);
                alert("Failed to start content generation.");
                setPollingFor(null);
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
        setLoadingMessage('Uploading and processing file...');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const uploadResponse = await authenticatedFetch(
                `${API_BASE_URL}/knowledge-cards/references/${referenceId}/upload`,
                { method: 'POST', body: formData, credentials: 'include' }
            );

            if (uploadResponse.ok) {
                setIsUploadModalOpen(false);
                //  The backend now clears the error, so we just need to refresh.
                await fetchData();
            } else {
                const error = await uploadResponse.json();
                alert(`Upload failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('An error occurred during the upload process:', error);
            alert('An unexpected error occurred during the file upload.');
        } finally {
            setLoading(false);
            setLoadingMessage('');
        }
    };

    async function handleExport(format) {


        const cardId = id;

        if (!cardId || cardId === "undefined") {
            setAlertModalMessage("No draft available to export. Please create or load a draft first.");
            setIsAlertModalOpen(true);
            return;
        }

        const response = await fetch(`${API_BASE_URL}/knowledge-cards/${id}/generate-document/?format=${format}`, {
            method: "GET",
            headers: { 'Content-Type': 'application/json' },
            credentials: "include"
        })

        if (response.ok) {
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = "knowledge-card.docx"; // Default filename
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }

            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();

            setTimeout(() => URL.revokeObjectURL(link.href), 1000);
        }
        else if (response.status === 401) {
            sessionStorage.setItem("session_expired", "Session expired. Please login again.")
            navigate("/login")
        }
        else
            throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    return (
        <Base>
            {/* Modals */}
            <Snackbar
                open={notif.open}
                autoHideDuration={notif.severity === "info" ? 1400 : 5000}
                onClose={() => setNotif(v => ({ ...v, open: false }))}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity={notif.severity} onClose={() => setNotif(v => ({ ...v, open: false }))} sx={{ width: '100%' }}>
                    {notif.message}
                </Alert>
            </Snackbar>
            <AlertModal
                isOpen={isAlertModalOpen}
                message={alertModalMessage}
                onClose={() => setIsAlertModalOpen(false)}
            />
            <ConfirmationModal
                isOpen={isConfirmationModalOpen}
                message="A knowledge card with this selection already exists. Ad-hoc knowledge cards with specific references and content can be added to offer flexibility. Do you want to create another one?"
                link={existingCard ? `/knowledge-card/${existingCard.id}` : ''}
                onConfirm={() => {
                    setIsConfirmationModalOpen(false);
                }}
                onCancel={() => {
                    setIsConfirmationModalOpen(false);
                    setLinkedId('');
                }}
            />
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
                        <div className="kc-form-header" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '10px' }}>
                            <div style={{ width: '100%' }}>
                                <h1 data-testid="kc-form-header-title" style={{ marginBottom: '5px' }}>
                                    {id ? (
                                        `${linkType === 'donor' ? 'Donor' : linkType === 'outcome' ? 'Outcome' : 'Field Context'} Knowledge Card: ${linkOptions.find(o => o.id === linkedId)?.name || linkedId}`
                                    ) : 'Create New Knowledge Card'}
                                </h1>
                                {id && <p style={{ fontSize: '14px', color: '#666', marginTop: '0', marginBottom: '15px' }}>{summary}</p>}
                            </div>

                            {/* Action Buttons - Moved to Top */}
                            <div className="kc-form-actions-box" style={{ marginTop: '0', marginBottom: '10px', width: '100%' }}>
                                <div className="kc-form-actions" style={{ justifyContent: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                                    <CommonButton
                                        type="button"
                                        onClick={handleIdentifyReferences}
                                        label="1. Identify References"
                                        className="squared-btn small-btn"
                                        style={{ padding: '6px 12px', fontSize: '13px' }}
                                        data-testid="identify-references-button"
                                        disabled={!linkType || !linkedId}
                                    />
                                    <CommonButton
                                        type="button"
                                        onClick={() => handleIngestReferences()}
                                        label="2. Ingest References"
                                        className="squared-btn small-btn"
                                        style={{ padding: '6px 12px', fontSize: '13px' }}
                                        data-testid="ingest-references-button"
                                        disabled={references.length === 0}
                                    />
                                    <CommonButton
                                        type="submit"
                                        label="3. Populate Card Content"
                                        className="squared-btn small-btn"
                                        style={{ padding: '6px 12px', fontSize: '13px' }}
                                        data-testid="populate-card-button"
                                        disabled={!linkType || !linkedId}
                                    />
                                </div>
                            </div>

                            {/* History Button - Moved Below Action Buttons */}
                            {id && (
                                <div style={{ marginBottom: '20px' }}>
                                    <CommonButton
                                        type="button"
                                        onClick={fetchHistory}
                                        label="View Content History"
                                        className="squared-btn"
                                        style={{ padding: '4px 10px', fontSize: '12px' }}
                                        data-testid="view-history-button"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Form Fields - Conditionally Read-Only (Only for New Cards) */}
                        {!id && (
                            <>
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
                                            inputId="kc-linked-id"
                                            classNamePrefix="kc-linked-item-select"
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
                            </>
                        )}

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
                            onReingestClick={handleIngestReferences}
                        />

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
                                            <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{content}</Markdown>
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