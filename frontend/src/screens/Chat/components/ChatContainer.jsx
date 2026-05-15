import '../Chat.css';
import { Snackbar, Alert } from '@mui/material';

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import Base from '../../../components/Base/Base';
import MultiSelectModal from '../../../components/MultiSelectModal/MultiSelectModal';
import AssociateKnowledgeModal from '../../../components/AssociateKnowledgeModal/AssociateKnowledgeModal';
import PdfUploadModal from '../../../components/PdfUploadModal/PdfUploadModal';
import SingleSelectUserModal from '../../../components/SingleSelectUserModal/SingleSelectUserModal';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

import fileIcon from "../../../assets/images/chat-titleIcon.svg";
import arrow from "../../../assets/images/expanderArrow.svg";
import generateIcon from "../../../assets/images/generateIcon.svg";
import edit from "../../../assets/images/Chat_edit.svg";
import save from "../../../assets/images/Chat_save.svg";
import cancel from "../../../assets/images/Chat_editCancel.svg";
import copy from "../../../assets/images/Chat_copy.svg";
import tick from "../../../assets/images/Chat_copiedTick.svg";
import regenerate from "../../../assets/images/Chat_regenerate.svg";
import regenerateClose from "../../../assets/images/Chat_regenerateClose.svg";
import excel_icon from "../../../assets/images/excel.svg";
import { FollowUpModal, ValidationModal, ProgressModal, RegenerateModal } from './index';
import ChatHeader from './ChatHeader';
import ChatControls from './ChatControls';
import ChatMain from './ChatMain';
import ChatSidebar from './ChatSidebar';
import { toKebabCase } from '../utils';
import { useFormData } from '../hooks/useFormData';
import { useChatApi } from '../hooks/useChatApi';
import { useProposal } from '../hooks/useProposal';

const ChatContainer = (props) => {
        // Initialize custom hooks
	const {
		formData,
		setFormData,
		formExpanded,
		setFormExpanded,
		handleFormInput,
		getMissingFields,
		renderFormField
	} = useFormData();

	const {
		donors,
		outcomes,
		fieldContexts,
		filteredFieldContexts,
		newBudgetRanges,
		newDurations,
		geographicCoverages,
		setDonors,
		setOutcomes,
		setFieldContexts,
		setFilteredFieldContexts,
		setNewBudgetRanges,
		setNewDurations: setNewDurationsFromApi,
		setGeographicCoverages,
		users,
		transferUsers,
		currentUser,
		setCurrentUser,
		isReviewer,
		setIsReviewer,
		isAdmin,
		setIsAdmin,
		fetchData,
		getUsers,
		getTransferUsers,
		getProfile
	} = useChatApi();

	const {
		proposal,
		setProposal,
		proposalTemplate,
		setProposalTemplate,
		proposalStatus,
		setProposalStatus,
		generateLoading,
		setGenerateLoading,
		generateLabel,
		setGenerateLabel,
		contributionId,
		setContributionId,
		statusHistory,
		isEdit,
                setIsEdit,
                editorContent,
                setEditorContent,
		selectedSectionName,
		isCopied,
                fromFollowUpModalRef,
                topRef,
                proposalRef,
                associatedKnowledgeCards,
                setAssociatedKnowledgeCards,
		reviews,
                reviewComments,
                setReviewComments,
                reviewStatus,
                setReviewStatus,
                getPeerReviews,
                getStatusHistory,
                handleCopyClick,
                handleExpanderToggle,
                handleEditClick,
                handleRegenerateIconClick,
                handleCommentChange,
                handleStatusChange,
                handleDeleteComment,
                handleSaveResponse,
                handleSidebarSectionClick
        } = useProposal({ setCurrentUser, setIsAdmin, setIsReviewer });
        const navigate = useNavigate()
        const { id } = useParams()

        const [documentType, setDocumentType] = useState("proposal")

	// Local state (not in hooks yet)
	const [titleName, setTitleName] = useState(props?.title ?? "Generate Draft Proposal")
	const [userPrompt, setUserPrompt] = useState("")
	const [buttonEnable, setButtonEnable] = useState(false)

        // Modal state (could be in useModalState but needs local for now)
        const [sidebarOpen, setSidebarOpen] = useState(false);
        const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
        const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
        const [isPeerReviewModalOpen, setIsPeerReviewModalOpen] = useState(false)
        const [isAssociateKnowledgeModalOpen, setIsAssociateKnowledgeModalOpen] = useState(false)
	const [isPdfUploadModalOpen, setIsPdfUploadModalOpen] = useState(false)
	const [selectedUsers, setSelectedUsers] = useState([])
	const [validationMissingFields, setValidationMissingFields] = useState([])
	const [isValidationModalOpen, setIsValidationModalOpen] = useState(false)
	const [isTransferModalOpen, setIsTransferModalOpen] = useState(false)
	const [showFollowUpModal, setShowFollowUpModal] = useState(false)
	const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
	const [followUpInstruction, setFollowUpInstruction] = useState("");
	const [generationProgress, setGenerationProgress] = useState(0);
	const [generationMessage, setGenerationMessage] = useState("");
	const [isRegenerateModalOpen, setIsRegenerateModalOpen] = useState(false)
	const [regenerateInput, setRegenerateInput] = useState("");
	const [regenerateSectionLoading, setRegenerateSectionLoading] = useState(false);
	const [notif, setNotif] = useState({ open: false, message: '', severity: 'info' });
	const [isSubmittedProposalLoaded, setIsSubmittedProposalLoaded] = useState(false);

	const renderFormFieldWithContext = useCallback((label, disabled) => {
		return renderFormField(
			label,
			disabled,
			formData,
			handleFormInput,
			outcomes,
			donors,
			filteredFieldContexts,
			geographicCoverages,
			newDurations,
			newBudgetRanges,
			setNewDurationsFromApi,
			setNewBudgetRanges
		);
	}, [renderFormField, formData, handleFormInput, outcomes, donors, filteredFieldContexts, geographicCoverages, newDurations, newBudgetRanges, setNewDurationsFromApi, setNewBudgetRanges]);

	useEffect(() => {
		function handleResize() {
			setIsMobile(window.innerWidth < 768);
		}

		window.addEventListener('resize', handleResize);
		return () => window.removeEventListener('resize', handleResize);
	}, []);

	useEffect(() => {
		const missingFields = getMissingFields(userPrompt);
		const hasPrompt = userPrompt.trim().length > 0;
		setButtonEnable(proposalStatus === 'draft' && hasPrompt && missingFields.length === 0);
	}, [getMissingFields, userPrompt, proposalStatus]);

        // Use hook functions
	const fetchFormData = useCallback(async () => {
		try {
			const [donorsRes, outcomesRes, fieldContextsRes, geoCoveragesRes] = await Promise.all([
				fetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
				fetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
				fetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' }),
				fetch(`${API_BASE_URL}/geographic-coverages`, { credentials: 'include' })
			]);

			if (donorsRes.ok) {
				const data = await donorsRes.json();
				setDonors(data.donors);
			}
			if (outcomesRes.ok) {
				const data = await outcomesRes.json();
				setOutcomes(data.outcomes);
			}
			if (fieldContextsRes.ok) {
				const data = await fieldContextsRes.json();
				const sortedFieldContexts = data.field_contexts.sort((a, b) => a.name.localeCompare(b.name));
				setFieldContexts(sortedFieldContexts);
				setFilteredFieldContexts(sortedFieldContexts);
			}
			if (geoCoveragesRes.ok) {
				const data = await geoCoveragesRes.json();
				setGeographicCoverages(data.geographic_coverages || []);
			}
		} catch (error) {
			console.error("Error fetching form data:", error);
		}
	}, [setDonors, setOutcomes, setFieldContexts, setFilteredFieldContexts, setGeographicCoverages]);

	useEffect(() => {
		if (id) {
			sessionStorage.setItem("proposal_id", id);
		}
		fetchData().then(() => {
			if (sessionStorage.getItem("proposal_id")) {
				fetchFormData();
			}
		});
	}, [id, fetchData, fetchFormData]);

        // getUsers and getTransferUsers are imported from useChatApi hook



        useEffect(() => {
                if (isPeerReviewModalOpen && users.length > 0) {
                        const proposalDonors = Array.isArray(formData["Targeted Donor"].value) ? formData["Targeted Donor"].value : (formData["Targeted Donor"].value ? [formData["Targeted Donor"].value] : []);
                        const proposalOutcomes = formData["Main Outcome"].value || [];
                        const proposalFieldContexts = Array.isArray(formData["Country / Location(s)"].value) ? formData["Country / Location(s)"].value : (formData["Country / Location(s)"].value ? [formData["Country / Location(s)"].value] : []);

                        const matchedUsers = users.filter(user => {
                                const donorMatch = (user.donor_ids || []).some(id => proposalDonors.includes(id));
                                const outcomeMatch = (user.outcomes || []).some(id => proposalOutcomes.includes(id));
                                const contextMatch = (user.field_contexts || []).some(id => proposalFieldContexts.includes(id));
                                return donorMatch || outcomeMatch || contextMatch;
                        });

                        if (matchedUsers.length > 0) {
                                setSelectedUsers(matchedUsers);
                        }
                }
        }, [isPeerReviewModalOpen, users, formData]);

	useEffect(() => {
		getUsers()
		getTransferUsers()
		getProfile()
	}, [getUsers, getTransferUsers, getProfile])

	const geographicalScopeValue = formData['Geographical Scope'].value;
	const locationFieldValue = formData['Country / Location(s)'].value;

	useEffect(() => {
		const scope = geographicalScopeValue;
		const filtered = scope
			? fieldContexts.filter(fc => fc.geographic_coverage === scope)
			: fieldContexts;
		setFilteredFieldContexts(filtered);

		const locationValue = locationFieldValue;
		if (locationValue) {
			if (Array.isArray(locationValue)) {
				const validLocations = locationValue.filter(id => filtered.some(fc => fc.id === id));
				if (validLocations.length !== locationValue.length) {
					handleFormInput({ target: { value: validLocations } }, "Country / Location(s)");
				}
			} else {
				const isLocationStillValid = filtered.some(fc => fc.id === locationValue);
				if (fieldContexts.length > 0 && !isLocationStillValid) {
					handleFormInput({ target: { value: "" } }, "Country / Location(s)");
				}
			}
		}
	}, [geographicalScopeValue, locationFieldValue, fieldContexts, handleFormInput, setFilteredFieldContexts]);

        // Set label to Regenerate if there's an existing proposal
	useEffect(() => {
		if (sessionStorage.getItem("proposal_id")) {
			setGenerateLabel("Regenerate");
		}
	}, [setGenerateLabel]);

	useEffect(() => {
		if (titleName === "Generate Draft Proposal" || titleName === "Generate Concept Note") {
			if (documentType === "concept note") {
				setTitleName("Generate Concept Note");
			} else {
				setTitleName("Generate Draft Proposal");
			}
		}
	}, [documentType, titleName, setTitleName]);

	useEffect(() => {
		if (!generateLoading && proposal && Object.values(proposal).every(section => section.content)) {
			topRef.current?.scrollIntoView({ behavior: "smooth" });
		}
	}, [generateLoading, proposal, topRef]);

        // --- Streaming polling logic for proposal generation ---
        useEffect(() => {
                if (!generateLoading) return;

                setNotif({ open: true, message: 'Generating proposal…', severity: 'info' });
                setGenerationProgress(0);
                setGenerationMessage("Starting proposal generation...");
                setIsProgressModalOpen(true);

                let pollingActive = true;
                const pollInterval = setInterval(async () => {
                        if (!pollingActive) return;
                        const proposalId = sessionStorage.getItem("proposal_id");
                        if (!proposalId) return; // Wait for ID to be available

                        try {
                                const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/status`, { credentials: 'include' });
                                if (response.ok) {
                                        const data = await response.json();
                                        if (data.generated_sections) {
                                                // Progress: show % by sections present, if known total
                                                let total = Object.keys(data.generated_sections).length;
                                                if (data.expected_sections && data.expected_sections > 0) {
                                                        setGenerationProgress(Math.round(100 * total / data.expected_sections));
                                                } else {
                                                        setGenerationProgress(10 + Math.min(85, total * 15));
                                                }

                                                // Update message based on sections
                                                const lastSection = Object.keys(data.generated_sections).pop();
                                                if (lastSection) {
                                                        setGenerationMessage(`Generating section: ${lastSection}...`);
                                                }

                                                // Show each section live
                                                const sectionState = {};
                                                Object.entries(data.generated_sections).forEach(([key, value]) => {
                                                        sectionState[key] = {
                                                                content: value,
                                                                open: true
                                                        };
                                                });
                                                setProposal(sectionState);
                                        }
                                        // Check if generation is truly complete: status is not 'generating_sections' AND we have all expected sections
                                        // Also handle edge case where expected_sections is 0 (template not loaded yet)
                                        const generatedCount = Object.keys(data.generated_sections || {}).length;
                                        const hasAllSections = data.expected_sections > 0 ?
                                                generatedCount >= data.expected_sections :
                                                generatedCount > 0;
                                        const isFailed = data.status === 'failed';

                                        if ((data.status !== 'generating_sections' && hasAllSections) || isFailed) {
                                                setGenerateLoading(false);
                                                setGenerationProgress(100);
                                                setGenerationMessage(isFailed ? "Generation failed!" : "Generation completed!");
                                                setNotif({ open: true, message: isFailed ? 'Proposal generation failed!' : 'Proposal generation completed!', severity: isFailed ? 'error' : 'success' });
                                                pollingActive = false;
                                                clearInterval(pollInterval);
                                                setTimeout(() => setIsProgressModalOpen(false), 1000); // Small delay to show 100%

                                                // Change button label to Regenerate after successful generation
                                                if (!isFailed && hasAllSections) {
                                                        setGenerateLabel("Regenerate");
                                                }
                                        }
                                } else throw new Error('Non-200 response');
				} catch {
                                setGenerateLoading(false);
                                setGenerationProgress(0);
                                setNotif({ open: true, message: 'Error streaming proposal content. Try again.', severity: 'error' });
                                setIsProgressModalOpen(false);
                                pollingActive = false;
                                clearInterval(pollInterval);
                        }
                }, 1000);
                return () => { pollingActive = false; clearInterval(pollInterval); };
	}, [generateLoading, setGenerateLabel, setGenerateLoading, setProposal, setGenerationProgress, setGenerationMessage, setNotif, setIsProgressModalOpen]);


        async function fetchAndAssociateKnowledgeCards() {
                if (associatedKnowledgeCards.length > 0) {
                        return associatedKnowledgeCards;
                }
                const donorIds = Array.isArray(formData["Targeted Donor"].value) ? formData["Targeted Donor"].value : (formData["Targeted Donor"].value ? [formData["Targeted Donor"].value] : []);
                const outcomeIds = formData["Main Outcome"].value;
                const fieldIconsIds = Array.isArray(formData["Country / Location(s)"].value) ? formData["Country / Location(s)"].value : (formData["Country / Location(s)"].value ? [formData["Country / Location(s)"].value] : []);

                const fetchPromises = [];

                if (donorIds.length > 0) {
                        donorIds.forEach(donorId => {
                                if (donorId && !donorId.startsWith("new_")) {
                                        fetchPromises.push(
                                                fetch(`${API_BASE_URL}/knowledge-cards?donor_id=${donorId}`, { credentials: 'include' })
                                                        .then(res => res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] }))
                                                        .then(data => data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null)
                                        );
                                }
                        });
                }

                if (fieldIconsIds.length > 0) {
                        fieldIconsIds.forEach(fieldContextId => {
                                if (fieldContextId && !fieldContextId.startsWith("new_")) {
                                        fetchPromises.push(
                                                fetch(`${API_BASE_URL}/knowledge-cards?field_context_id=${fieldContextId}`, { credentials: 'include' })
                                                        .then(res => res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] }))
                                                        .then(data => data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null)
                                        );
                                }
                        });
                }

                if (outcomeIds && outcomeIds.length > 0) {
                        const validOutcomeIds = outcomeIds.filter(id => !id.startsWith("new_"));
                        if (validOutcomeIds.length > 0) {
                                const queryParams = new URLSearchParams();
                                validOutcomeIds.forEach(id => queryParams.append('outcome_id', id));
                                fetchPromises.push(
                                        fetch(`${API_BASE_URL}/knowledge-cards?${queryParams.toString()}`, { credentials: 'include' })
                                                .then(res => res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] }))
                                                .then(data => data.knowledge_cards) // This will be an array of cards
                                );
                        }
                }

                try {
                        const results = await Promise.all(fetchPromises);
                        const newAssociatedCards = results.flat().filter(Boolean);

                        const combinedCards = [...associatedKnowledgeCards, ...newAssociatedCards];
                        const uniqueAssociatedCards = Array.from(new Map(combinedCards.map(card => [card.id, card])).values());

                        setAssociatedKnowledgeCards(uniqueAssociatedCards);
                        return uniqueAssociatedCards;
                } catch (error) {
                        console.error("Error auto-associating knowledge cards:", error);
                        return associatedKnowledgeCards;
                }
        }

        async function handleRegenerateWithFollowUp() {
                // Regenerate entire proposal with follow-up instruction
                if (!followUpInstruction) return;

                setShowFollowUpModal(false);
                fromFollowUpModalRef.current = true;
                // Trigger the main generate/regenerate flow
                await handleGenerateClick();
                fromFollowUpModalRef.current = false;
        }

	async function handleGenerateClick() {
		setIsSubmittedProposalLoaded(false);
		// Check if this is a regeneration (proposal already exists)
                const existingProposalId = sessionStorage.getItem("proposal_id");
                const existingSessionId = sessionStorage.getItem("session_id");

                // For regeneration, skip missing fields check (fields should already be filled)
                // For initial generation, check for missing fields
                if (!existingProposalId || !existingSessionId) {
                        const missing = getMissingFields(userPrompt);
                        if (missing.length > 0) {
                                setValidationMissingFields(missing);
                                setIsValidationModalOpen(true);
                                return;
                        }
                }

                // Show follow-up modal for regeneration unless coming from the modal itself
                if (existingProposalId && existingSessionId) {
                        if (!fromFollowUpModalRef.current) {
                                setShowFollowUpModal(true);
                                return;
                        }
                        fromFollowUpModalRef.current = false;
                        // If we're coming from the modal with follow-up instruction, proceed with regeneration
                        if (followUpInstruction) {
                                // This is a regeneration with follow-up instruction
                                setGenerateLoading(true);
                                setFormExpanded(false);

                                try {
                                        // Get all current sections to pass as context
                                        const currentSections = proposal;

                                        // Call backend to regenerate with follow-up instruction
                                        const response = await fetch(`${API_BASE_URL}/regenerate-full-proposal/${existingSessionId}`, {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({
                                                        proposal_id: existingProposalId,
                                                        follow_up_instruction: followUpInstruction,
                                                        current_sections: currentSections,
                                                        form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
                                                        project_description: userPrompt
                                                }),
                                                credentials: 'include'
                                        });

                                        if (!response.ok) {
                                                throw new Error('Failed to start proposal regeneration.');
                                        }

                                        const data = await response.json();
                                        // Update session with new IDs if needed
                                        if (data.session_id) {
                                                sessionStorage.setItem("session_id", data.session_id);
                                        }

                                        // Reset state for polling
                                        setGenerationProgress(0);
                                        setGenerationMessage("Starting proposal regeneration...");
                                        setIsProgressModalOpen(true);

                                        // Keep generateLoading true so polling continues
                                        // The polling will be handled by the existing useEffect
                                        return;

                                } catch (error) {
                                        console.error("Error during proposal regeneration:", error);
                                        setGenerateLoading(false);
                                        setNotif({ open: true, message: 'Failed to start proposal regeneration. Try again.', severity: 'error' });
                                        return;
                                }
                        }
                        // If we're coming from modal but no followUpInstruction, just return (shouldn't happen)
                        return;
                }

                // Initial generation flow
                setGenerateLoading(true);
                setFormExpanded(false);
                sessionStorage.removeItem("proposal_id"); // Clear old ID to prevent polling it

                try {
                        const finalAssociatedCards = (await fetchAndAssociateKnowledgeCards()).filter(card => card.generated_section != null);
                        const updatedFormData = { ...Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])) };

                        // Call the new, streamlined endpoint to create the session and initial draft.
                        const response = await fetch(`${API_BASE_URL}/create-session`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        project_description: userPrompt,
                                        form_data: updatedFormData,
                                        associated_knowledge_cards: finalAssociatedCards,
                                        document_type: documentType
                                }),
                                credentials: 'include'
                        });

                        if (!response.ok) {
                                throw new Error("Failed to create a new session.");
                        }

                        const data = await response.json();

                        // Store the new session and proposal IDs received from the backend.
                        sessionStorage.setItem("session_id", data.session_id);
                        sessionStorage.setItem("proposal_id", data.proposal_id);
                        if (data.proposal_template) {
                                setProposalTemplate(data.proposal_template);
                                sessionStorage.setItem("proposal_template", JSON.stringify(data.proposal_template));
                        }

                        // Initialize the proposal sections based on the template received from the backend.
                        const sectionState = {};
                        if (data.proposal_template && data.proposal_template.sections) {
                                data.proposal_template.sections.forEach(section => {
                                        sectionState[section.section_name] = {
                                                content: "", // Content will be populated by the getSections call.
                                                open: true
                                        };
                                });
                        }

                        setProposal(sectionState);
                        setSidebarOpen(true);

                        // Trigger the background generation
                        const generateResponse = await fetch(`${API_BASE_URL}/generate-proposal-sections/${data.session_id}`, {
                                method: 'POST',
                                credentials: 'include'
                        });

                        if (!generateResponse.ok) {
                                throw new Error("Failed to start proposal generation.");
                        }

                } catch (error) {
                        console.error("Error during proposal generation:", error);
                        setGenerateLoading(false);
                        setGenerateLabel("Generate"); // Reset button label on error.
                }
        }

	const [selectedSection] = useState(-1)
        async function handleRegenerateButtonClick(ip = regenerateInput) {
                setRegenerateSectionLoading(true)
                const sectionName = selectedSectionName;

                const response = await fetch(`${API_BASE_URL}/regenerate_section/${sessionStorage.getItem("proposal_id")}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                session_id: sessionStorage.getItem("session_id"),
                                section: sectionName,
                                concise_input: ip,
                                form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
                                project_description: userPrompt
                        }),
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setProposal(p => ({
                                ...p,
                                [sectionName]: {
                                        open: p[sectionName].open,
                                        content: data.generated_text
                                }
                        }))
                }
                else if (response.status === 401) {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
                else
                        console.log("Error: ", response)

                setRegenerateInput("")
                setIsRegenerateModalOpen(false)
                setRegenerateSectionLoading(false)

                if (isEdit)
                        setIsEdit(false)
        }

        async function handleSaveContributionId() {
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/save-contribution-id`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ contribution_id: contributionId }),
                        credentials: 'include'
                });

                if (response.ok) {
                        alert("Contribution ID saved!");
                } else {
                        console.error("Failed to save Contribution ID");
                        alert("Failed to save Contribution ID.");
                }
	}

        useEffect(() => {
                if (sessionStorage.getItem("proposal_id")) {
                        getContent();
                }
        }, [id]);

	// getPeerReviews and getStatusHistory are imported from useProposal hook

        // getProfile is imported from useChatApi hook

        async function getContent() {

                if (sessionStorage.getItem("proposal_id")) {
                        const response = await fetch(`${API_BASE_URL}/load-draft/${sessionStorage.getItem("proposal_id")}`, {
                                method: "GET",
                                headers: { 'Content-Type': 'application/json' },
                                credentials: "include"
                        })

                        if (response.ok) {
                                const data = await response.json()

                                // Ownership check
                                const profileRes = await fetch(`${API_BASE_URL}/profile`, { credentials: 'include' });
                                if (profileRes.ok) {
                                        const profileData = await profileRes.json();
                                        const curUser = profileData.user;
                                        setCurrentUser(curUser);
                                        const ownerId = data.user_id;
                                        const isOwner = curUser.id === ownerId || curUser.user_id === ownerId;
                                        const _isAdmin = curUser.is_admin || (curUser.roles || []).some(r => r === 'admin' || (r && r.name === 'admin'));
                                        setIsAdmin(_isAdmin);

                                        if (!isOwner) {
                                                setIsReviewer(true);
	}
                                }

                                sessionStorage.setItem("proposal_id", data.proposal_id)
                                sessionStorage.setItem("session_id", data.session_id)

                                setUserPrompt(data.project_description)

                                setFormData(p => {
                                        const next = { ...p };
                                        Object.entries(data.form_data).forEach(([key, val]) => {
                                                next[key] = {
                                                        ...(p[key] || { mandatory: false }),
                                                        value: val
                                                };
                                        });
                                        return next;
                                });

                                const sectionState = {};
                                Object.entries(data.generated_sections).forEach(([key, value]) => {
                                        sectionState[key] = {
                                                content: value,
                                                open: true
                                        };
                                });
                                setProposal(sectionState);

                                if (data.associated_knowledge_cards) {
                                        setAssociatedKnowledgeCards(data.associated_knowledge_cards);
                                }

                                if (data.template_name && data.template_name.startsWith("concept_note_")) {
                                        setDocumentType("concept note");
                                } else {
                                        setDocumentType("proposal");
                                }

				setProposalStatus(data.status)
				setIsSubmittedProposalLoaded(data.status === 'submitted')
                                setContributionId(data.contribution_id || "")
                                setSidebarOpen(true)
                                getStatusHistory()
                                // Always fetch peer reviews for all users
                                getPeerReviews()

                                const storedTemplate = sessionStorage.getItem("proposal_template");
                                if (storedTemplate) {
                                        setProposalTemplate(JSON.parse(storedTemplate));
                                }
                        } else if (response.status === 401) {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        } else if (response.status === 400 || response.status === 403 || response.status === 404) {
                                // May be a reviewer: try loading via the review endpoint
                                const profileRes2 = await fetch(`${API_BASE_URL}/profile`, { credentials: 'include' });
                                if (profileRes2.ok) {
                                        const profileData2 = await profileRes2.json();
                                        const curUser2 = profileData2.user;
                                        setCurrentUser(curUser2);
                                        const _isAdmin2 = curUser2.is_admin || (curUser2.roles || []).some(r => r === 'admin' || (r && r.name === 'admin'));
                                        setIsAdmin(_isAdmin2);
                                        setIsReviewer(true);
                                }
                                const proposalIdFromParam = id || sessionStorage.getItem('proposal_id');
                                if (!proposalIdFromParam) return;
                                const reviewRes = await fetch(`${API_BASE_URL}/review-proposal/${proposalIdFromParam}`, { credentials: 'include' });
                                if (reviewRes.ok) {
                                        const reviewData = await reviewRes.json();
                                        sessionStorage.setItem('proposal_id', proposalIdFromParam);

                                        setUserPrompt(reviewData.project_description || '');

                                        const sectionState = {};
                                        Object.entries(reviewData.generated_sections || {}).forEach(([key, value]) => {
                                                sectionState[key] = { content: value, open: true };
                                        });
                                        setProposal(sectionState);
				setProposalStatus(reviewData.status);
				setIsSubmittedProposalLoaded(reviewData.status === 'submitted');

                                        const initialComments = {};
                                        const initialStatus = {};
                                        Object.keys(reviewData.generated_sections || {}).forEach(section => {
                                                const existing = reviewData.draft_comments?.[section] || {};
                                                initialComments[section] = {
                                                        id: existing.id || null,
                                                        review_text: existing.review_text || '',
                                                        type_of_comment: existing.type_of_comment || 'P2',
                                                        severity: existing.severity || 'P2',
                                                        author_response: existing.author_response || '',
                                                        rating: existing.rating || null
                                                };
                                                initialStatus[section] = existing.rating || null;
                                        });
                                        setReviewComments(initialComments);
                                        setReviewStatus(initialStatus);
                                        setSidebarOpen(true);

                                        // Load template so section list renders correctly
			try {
				const tplRes = await fetch(`${API_BASE_URL}/templates/proposal_template_unhcr.json/sections`, { credentials: 'include' });
				if (tplRes.ok) {
					const tplData = await tplRes.json();
					// tplData is { sections: [...] }
					setProposalTemplate(tplData);
				} else {
					// Fallback: build template from section keys
					const syntheticSections = Object.keys(reviewData.generated_sections || {}).map(name => ({ section_name: name }));
					setProposalTemplate({ sections: syntheticSections });
				}
			} catch {
                                                // Fallback: build template from section keys
                                                const syntheticSections = Object.keys(reviewData.generated_sections || {}).map(name => ({ section_name: name }));
                                                setProposalTemplate({ sections: syntheticSections });
                                        }
                                } else if (reviewRes.status === 401) {
                                        sessionStorage.setItem('session_expired', 'Session expired. Please login again.');
                                        navigate('/login');
                                } else {
                                        // Final fallback: truly not found or no access
                                        console.warn("Draft not found or no access after trying review endpoint.");
                                        sessionStorage.removeItem("proposal_id");
                                        sessionStorage.removeItem("session_id");
                                }
                        }
                }
        }

	// ── Review handler functions ────────────────────────────────────────
	const handleReplyToFeedback = async (feedbackId, replyText, replyStatus) => {
		const proposalId = sessionStorage.getItem('proposal_id');
		if (!proposalId) return;
		try {
			const res = await fetch(`${API_BASE_URL}/proposals/${proposalId}/reply-to-feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					feedback_id: feedbackId,
					author_response: replyText,
					status: replyStatus
				}),
				credentials: 'include'
			});
			if (res.ok) getPeerReviews();
		} catch (error) { console.error('Error replying to feedback:', error); }
	};
	// ───────────────────────────────────────────────────────────────────
        // SharePoint Link State Management
        // ───────────────────────────────────────────────────────────────────

	// State for tracking SharePoint upload status
	const [, setSharepointStatus] = useState(null); // null, 'uploading', 'failed', 'uploaded'
	const [, setSharepointLink] = useState(null);
	const [, setSharepointError] = useState(null);
	const [, setIsCheckingLink] = useState(false);

        // Check for existing SharePoint link
        async function checkSharepointLink(proposalId) {
                if (!proposalId || proposalId === "undefined") {
                        return null;
                }

                try {
                        setIsCheckingLink(true);
                        const response = await fetch(`${API_BASE_URL}/sharepoint-link-status/proposal/${proposalId}`, {
                                method: "GET",
                                headers: { 'Content-Type': 'application/json' },
                                credentials: "include"
                        });

                        if (response.ok) {
                                const data = await response.json();
                                return data;
                        }
                        return null;
                } catch (error) {
                        console.error("Error checking SharePoint link status:", error);
                        return null;
                } finally {
                        setIsCheckingLink(false);
                }
        }

        // Retry SharePoint upload
        async function handleRetryUpload(proposalId) {
                if (!proposalId || proposalId === "undefined") {
                        setNotif({ open: true, message: "No draft available. Please create or load a draft first.", severity: 'error' });
                        return;
                }

                try {
                        setSharepointStatus('uploading');
                        setSharepointError(null);

                        const response = await fetch(`${API_BASE_URL}/retry-sharepoint-upload/proposal/${proposalId}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                credentials: "include"
                        });

                        if (response.ok) {
                                const data = await response.json();
                                if (data.success && data.url) {
                                        setSharepointStatus('uploaded');
                                        setSharepointLink(data);
                                        window.open(data.url, '_blank');
                                        setNotif({ open: true, message: "Document opened in Word Online", severity: 'success' });
                                } else {
                                        throw new Error(data.message || "Failed to get SharePoint URL");
                                }
                        }
                        else if (response.status === 401) {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                        else if (response.status === 429) {
                                const errorData = await response.json();
                                setSharepointStatus('failed');
                                setSharepointError(errorData.detail || "Max retry attempts exceeded");
                                setNotif({ open: true, message: errorData.detail || "Max retry attempts exceeded", severity: 'error' });
                        }
                        else {
                                const errorData = await response.json();
                                throw new Error(errorData.detail || `Retry failed: ${response.status} ${response.statusText}`);
                        }
                } catch (error) {
                        setSharepointStatus('failed');
                        setSharepointError(error.message);
                        setNotif({ open: true, message: `Error: ${error.message}`, severity: 'error' });
                        console.error("SharePoint retry error:", error);
                }
        }

        // Handle export with SharePoint caching and retry logic
	async function handleExport(format) {
		const proposalId = sessionStorage.getItem("proposal_id");

                if (!proposalId || proposalId === "undefined") {
                        setNotif({ open: true, message: "No draft available to export. Please create or load a draft first.", severity: 'error' });
                        return;
                }

                // Check for existing link first
                const linkStatus = await checkSharepointLink(proposalId);

                if (linkStatus && linkStatus.has_link) {
                        if (linkStatus.status === 'uploaded' && !linkStatus.is_expired) {
                                // Use cached link
                                setSharepointStatus('uploaded');
                                setSharepointLink(linkStatus);
                                window.open(linkStatus.url, '_blank');
                                setNotif({ open: true, message: "Document opened in Word Online (cached)", severity: 'success' });
                                return;
                        }
                        else if (linkStatus.status === 'uploading') {
                                setSharepointStatus('uploading');
                                setNotif({ open: true, message: "Document is currently being uploaded to SharePoint. Please wait...", severity: 'info' });
                                return;
                        }
                        else if (linkStatus.status === 'failed' && linkStatus.can_retry) {
                                // Auto-retry
                                setSharepointStatus('uploading');
                                setNotif({ open: true, message: "Retrying SharePoint upload...", severity: 'info' });
                                handleRetryUpload(proposalId);
                                return;
                        }
                        else if (linkStatus.status === 'failed' && !linkStatus.can_retry) {
                                setSharepointStatus('failed');
                                setSharepointError(linkStatus.error_message || "Max retry attempts exceeded");
                                setNotif({ open: true, message: linkStatus.error_message || "Max retry attempts exceeded. Please contact support.", severity: 'error' });
                                return;
                        }
                }

                // No existing link or needs new upload
                try {
                        setSharepointStatus('uploading');
                        setSharepointError(null);

                        // Call the new SharePoint upload endpoint
                        const response = await fetch(`${API_BASE_URL}/upload-proposal-to-sharepoint/${proposalId}?format=${format}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                credentials: "include"
                        });

                        if (response.ok) {
                                const data = await response.json();
                                if (data.success && data.url) {
                                        setSharepointStatus('uploaded');
                                        setSharepointLink(data);
                                        // Open the document in Word Online in a new tab
                                        window.open(data.url, '_blank');
                                        setNotif({ open: true, message: data.from_cache ? "Document opened in Word Online (cached)" : "Document opened in Word Online", severity: 'success' });
                                } else {
                                        throw new Error(data.message || "Failed to get SharePoint URL");
                                }
                        }
                        else if (response.status === 401) {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                        else if (response.status === 503) {
                                // Service unavailable - upload failed but will retry
                                const errorData = await response.json();
                                setSharepointStatus('failed');
                                setSharepointError(errorData.detail || "Upload failed");
                                setNotif({ open: true, message: errorData.detail || "Upload failed. Will retry automatically.", severity: 'warning' });
                        }
                        else if (response.status === 429) {
                                const errorData = await response.json();
                                setSharepointStatus('failed');
                                setSharepointError(errorData.detail || "Max retry attempts exceeded");
                                setNotif({ open: true, message: errorData.detail || "Max retry attempts exceeded", severity: 'error' });
                        }
                        else {
                                const errorData = await response.json();
                                throw new Error(errorData.detail || `Upload failed: ${response.status} ${response.statusText}`);
                        }
		} catch (error) {
			setSharepointStatus('failed');
			setSharepointError(error.message);
			setNotif({ open: true, message: `Error: ${error.message}`, severity: 'error' });
			console.error("SharePoint upload error:", error);
		}
	}

	async function handleExportTables() {
		const proposalId = sessionStorage.getItem("proposal_id");

		if (!proposalId || proposalId === "undefined") {
			setNotif({ open: true, message: "No draft available to export tables. Please create or load a draft first.", severity: 'error' });
			return;
		}

		try {
			const response = await fetch(`${API_BASE_URL}/generate-tables/${proposalId}`, {
				method: "GET",
				headers: { 'Content-Type': 'application/json' },
				credentials: "include"
			});

			if (response.ok) {
				const contentDisposition = response.headers.get('Content-Disposition');
				let filename = "proposal-tables.xlsx";
				if (contentDisposition) {
					const match = contentDisposition.match(/filename="?([^";]+)"?/);
					if (match && match[1]) {
						filename = match[1];
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
			} else if (response.status === 401) {
				sessionStorage.setItem("session_expired", "Session expired. Please login again.");
				navigate("/login");
			} else {
				throw new Error(`Download failed: ${response.status} ${response.statusText}`);
			}
		} catch (error) {
			setNotif({ open: true, message: `Error: ${error.message}`, severity: 'error' });
			console.error("Table download error:", error);
		}
	}

	async function handleRevert(status) {
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/revert-to-status/${status}`, {
                        method: "PUT",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                });

                if (response.ok) {
                        await getContent();
                } else {
                        console.error("Failed to revert status");
                }
        }

        async function handleSetStatus(status) {
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/status`, {
                        method: "PUT",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: status }),
                        credentials: "include"
                });

                if (response.ok) {
                        await getContent();
                } else {
                        console.error("Failed to update status");
                }
        }

        async function handleSubmit() {
                setIsPdfUploadModalOpen(true);
        }

        async function handlePdfUpload(file) {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/upload-submitted-pdf`, {
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                });

                if (response.ok) {
                        await getContent();
                } else {
                        console.error("Failed to upload PDF");
                }
                setIsPdfUploadModalOpen(false);
        }

        async function handleSubmitForPeerReview({ selectedUsers, deadline }) {
                const reviewers = selectedUsers.map(user_id => ({ user_id, deadline }));
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/submit-for-review`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ reviewers }),
                        credentials: "include"
                })

                if (response.ok) {
                        setProposalStatus('in_review');
                        await getContent()
                        setIsPeerReviewModalOpen(false)
                }
                else if (response.status === 401) {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        async function confirmTransfer(new_owner_id) {
                const proposalId = sessionStorage.getItem("proposal_id");
                if (!proposalId) return;

                const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/transfer`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ new_owner_id }),
                        credentials: 'include'
                })

                if (response.ok) {
                        setNotif({ open: true, message: 'Proposal ownership transferred successfully!', severity: 'success' });
                        setIsTransferModalOpen(false);
                        // Redirect to dashboard or refresh profile check
                        navigate('/dashboard');
                } else {
                        setNotif({ open: true, message: 'Failed to transfer proposal ownership.', severity: 'error' });
                }
        }

        function handleAssociateKnowledgeConfirm(selectedCards) {
                setAssociatedKnowledgeCards(selectedCards);
        }

        return (
                <Base>
                        <div className={`Chat ${isMobile && isMobileMenuOpen ? 'mobile-menu-open' : ''}`} data-testid="chat-container">
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
                                <ProgressModal
                                        isOpen={isProgressModalOpen}
                                        onClose={() => setIsProgressModalOpen(false)}
                                        progress={generationProgress}
                                        message={generationMessage}
                                />

                                <MultiSelectModal
                                        isOpen={isPeerReviewModalOpen}
                                        onClose={() => setIsPeerReviewModalOpen(false)}
                                        options={users}
                                        selectedOptions={selectedUsers}
                                        onSelectionChange={setSelectedUsers}
                                        onConfirm={handleSubmitForPeerReview}
                                        title="Select Users for Peer Review"
                                        showDeadline={true}
                                />
                                <SingleSelectUserModal
                                        isOpen={isTransferModalOpen}
                                        onClose={() => setIsTransferModalOpen(false)}
                                        options={transferUsers}
                                        title="Transfer Proposal Ownership to another Focal Point"
                                        onConfirm={confirmTransfer}
                                />
                                <AssociateKnowledgeModal
                                        isOpen={isAssociateKnowledgeModalOpen}
                                        onClose={() => setIsAssociateKnowledgeModalOpen(false)}
                                        onConfirm={handleAssociateKnowledgeConfirm}
                                        donorId={formData["Targeted Donor"]?.value}
                                        outcomeId={formData["Main Outcome"]?.value}
                                        fieldContextId={formData["Country / Location(s)"]?.value}
                                        initialSelection={associatedKnowledgeCards}
                                />
                                <PdfUploadModal
                                        isOpen={isPdfUploadModalOpen}
                                        onClose={() => setIsPdfUploadModalOpen(false)}
                                        onConfirm={handlePdfUpload}
                                />

                                {/* Validation Modal */}
                                <ValidationModal
                                        isOpen={isValidationModalOpen}
                                        onClose={() => setIsValidationModalOpen(false)}
                                        missingFields={validationMissingFields}
                                />

                                {/* Follow-up Instruction Modal - Shown when regenerating a proposal */}
                                <FollowUpModal
                                        isOpen={showFollowUpModal}
                                        onClose={() => setShowFollowUpModal(false)}
                                        onSkip={() => {
                                                setShowFollowUpModal(false);
                                                setGenerateLabel("Regenerate");
                                        }}
                                        onSaveForLater={() => {
                                                setShowFollowUpModal(false);
                                                setGenerateLabel("Regenerate");
                                        }}
                                        onRegenerate={handleRegenerateWithFollowUp}
                                        instruction={followUpInstruction}
                                        setInstruction={setFollowUpInstruction}
                                        regenerateCloseIcon={regenerateClose}
                                        generateIcon={generateIcon}
                                />

			<ChatSidebar
				isMobile={isMobile}
				isMobileMenuOpen={isMobileMenuOpen}
				sidebarOpen={sidebarOpen}
				selectedSection={selectedSection}
				proposalTemplate={proposalTemplate}
				proposal={proposal}
				handleSidebarSectionClick={handleSidebarSectionClick}
				toKebabCase={toKebabCase}
			/>

			<main className="Chat_right" ref={topRef} data-testid="chat-main">
				<button className="Chat_menuButton" onClick={() => setIsMobileMenuOpen(p => !p)} data-testid="mobile-menu-button">
					<i className="fa-solid fa-bars"></i>
				</button>

			{!isSubmittedProposalLoaded && proposalStatus !== 'submitted' && (
					<>
						<ChatHeader
							titleName={titleName}
							documentType={documentType}
							setDocumentType={setDocumentType}
							proposalStatus={proposalStatus}
							fileIcon={fileIcon}
							userPrompt={userPrompt}
							setUserPrompt={setUserPrompt}
							formExpanded={formExpanded}
							setFormExpanded={setFormExpanded}
							renderFormField={renderFormFieldWithContext}
							formData={formData}
							setFormData={setFormData}
						/>
						<ChatControls
							proposal={proposal}
							proposalStatus={proposalStatus}
							buttonEnable={buttonEnable}
							getMissingFields={getMissingFields}
							setValidationMissingFields={setValidationMissingFields}
							setIsValidationModalOpen={setIsValidationModalOpen}
							setIsAssociateKnowledgeModalOpen={setIsAssociateKnowledgeModalOpen}
							associatedKnowledgeCards={associatedKnowledgeCards}
							handleGenerateClick={handleGenerateClick}
							generateLabel={generateLabel}
							generateLoading={generateLoading}
							userPrompt={userPrompt}
						/>
					</>
				)}

				<ChatMain
					sidebarOpen={sidebarOpen}
					proposalStatus={proposalStatus}
					proposal={proposal}
					proposalTemplate={proposalTemplate}
					proposalRef={proposalRef}
					generateLoading={generateLoading}
					selectedSectionName={selectedSectionName}
					isEdit={isEdit}
					isReviewer={isReviewer}
					isAdmin={isAdmin}
					currentUser={currentUser}
					reviews={reviews}
					reviewComments={reviewComments}
					reviewStatus={reviewStatus}
					editorContent={editorContent}
					setEditorContent={setEditorContent}
					isCopied={isCopied}
					setIsEdit={setIsEdit}
					regenerateSectionLoading={regenerateSectionLoading}
					edit={edit}
					save={save}
					copy={copy}
					tick={tick}
					cancel={cancel}
					regenerate={regenerate}
					arrow={arrow}
					toKebabCase={toKebabCase}
					handleEditClick={handleEditClick}
					handleCopyClick={handleCopyClick}
					handleExpanderToggle={handleExpanderToggle}
					handleRegenerateIconClick={handleRegenerateIconClick}
					handleCommentChange={handleCommentChange}
					handleStatusChange={handleStatusChange}
					handleDeleteComment={handleDeleteComment}
					handleReplyToFeedback={handleReplyToFeedback}
					handleSaveResponse={handleSaveResponse}
					handleExport={handleExport}
					handleExportTables={handleExportTables}
					setIsTransferModalOpen={setIsTransferModalOpen}
					handleSetStatus={handleSetStatus}
					handleSubmit={handleSubmit}
					handleRevert={handleRevert}
					statusHistory={statusHistory}
					setIsPeerReviewModalOpen={setIsPeerReviewModalOpen}
					handleSaveContributionId={handleSaveContributionId}
					contributionId={contributionId}
					setContributionId={setContributionId}
				/>
			</main>


                                <RegenerateModal
                                        isOpen={isRegenerateModalOpen}
                                        onClose={() => {
                                                setRegenerateSectionLoading(false)
                                                setRegenerateInput("")
                                                setIsRegenerateModalOpen(false)
                                        }}
                                        onRegenerate={() => handleRegenerateButtonClick()}
                                        sectionName={selectedSectionName}
                                        inputValue={regenerateInput}
                                        setInputValue={setRegenerateInput}
                                        loading={regenerateSectionLoading}
                                        generateIcon={generateIcon}
                                        regenerateCloseIcon={regenerateClose}
                                />
                        </div>
                </Base>
        );
};

export default ChatContainer;
