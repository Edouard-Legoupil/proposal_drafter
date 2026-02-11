import './Chat.css'
import { Snackbar, Alert } from '@mui/material';

import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import MultiSelectModal from '../../components/MultiSelectModal/MultiSelectModal'
import AssociateKnowledgeModal from '../../components/AssociateKnowledgeModal/AssociateKnowledgeModal'
import PdfUploadModal from '../../components/PdfUploadModal/PdfUploadModal'
import ProgressModal from '../../components/ProgressModal/ProgressModal';
import Select from 'react-select';
import CreatableSelect from 'react-select/creatable';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

import fileIcon from "../../assets/images/chat-titleIcon.svg"
import arrow from "../../assets/images/expanderArrow.svg"
import generateIcon from "../../assets/images/generateIcon.svg"
import knowIcon from "../../assets/images/knowIcon.svg"
import resultsIcon from "../../assets/images/Chat_resultsIcon.svg"
import Review from './components/Review/Review'
import edit from "../../assets/images/Chat_edit.svg"
import save from "../../assets/images/Chat_save.svg"
import cancel from "../../assets/images/Chat_editCancel.svg"
import copy from "../../assets/images/Chat_copy.svg"
import tick from "../../assets/images/Chat_copiedTick.svg"
import regenerate from "../../assets/images/Chat_regenerate.svg"
import regenerateClose from "../../assets/images/Chat_regenerateClose.svg"
import word_icon from "../../assets/images/word.svg"
import excel_icon from "../../assets/images/excel.svg"
import pdf_icon from "../../assets/images/pdf.svg"
import approved_icon from "../../assets/images/Chat_approved.svg"

export default function Chat(props) {
        const navigate = useNavigate()
        const { id } = useParams()

        const [documentType, setDocumentType] = useState("proposal")
        const [sidebarOpen, setSidebarOpen] = useState(false);
        const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
        const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

        useEffect(() => {
                function handleResize() {
                        setIsMobile(window.innerWidth < 768);
                }

                window.addEventListener('resize', handleResize);
                return () => window.removeEventListener('resize', handleResize);
        }, []);

        const [titleName, setTitleName] = useState(props?.title ?? "Generate Draft Proposal")

        const [userPrompt, setUserPrompt] = useState("")

        const [isModalOpen, setIsModalOpen] = useState(false)
        const [isPeerReviewModalOpen, setIsPeerReviewModalOpen] = useState(false)
        const [isAssociateKnowledgeModalOpen, setIsAssociateKnowledgeModalOpen] = useState(false)
        const [isPdfUploadModalOpen, setIsPdfUploadModalOpen] = useState(false)
        const [currentUser, setCurrentUser] = useState(null)
        const [users, setUsers] = useState([])
        const [selectedUsers, setSelectedUsers] = useState([])
        const [associatedKnowledgeCards, setAssociatedKnowledgeCards] = useState([]);
        const [validationMissingFields, setValidationMissingFields] = useState([]);
        const [isValidationModalOpen, setIsValidationModalOpen] = useState(false);

        const [donors, setDonors] = useState([]);
        const [outcomes, setOutcomes] = useState([]);
        const [fieldContexts, setFieldContexts] = useState([]);
        const [filteredFieldContexts, setFilteredFieldContexts] = useState([]);
        const [newDonors, setNewDonors] = useState([]);
        const [newOutcomes, setNewOutcomes] = useState([]);
        const [newFieldContexts, setNewFieldContexts] = useState([]);
        const [newBudgetRanges, setNewBudgetRanges] = useState([]);
        const [newDurations, setNewDurations] = useState([]);
        const [geographicCoverages, setGeographicCoverages] = useState([]);

        async function fetchData() {
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
        }

        useEffect(() => {
                if (id) {
                        sessionStorage.setItem("proposal_id", id);
                }
                fetchData().then(() => {
                        if (sessionStorage.getItem("proposal_id")) {
                                getContent();
                        }
                });
        }, [id]);

        async function getUsers() {
                const response = await fetch(`${API_BASE_URL}/users`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setUsers((data.users || []).map(user => ({ id: user.id, name: user.name, team: user.team_name || 'Unassigned' })))
                }
        }

        useEffect(() => {
                getUsers()
        }, [])

        const [form_expanded, setFormExpanded] = useState(true)
        const [formData, setFormData] = useState({
                "Project Draft Short name": {
                        mandatory: true,
                        value: ""
                },
                "Main Outcome": {
                        mandatory: true,
                        value: [],
                        type: 'multiselect'
                },
                "Beneficiaries Profile": {
                        mandatory: true,
                        value: ""
                },
                "Potential Implementing Partner": {
                        mandatory: false,
                        value: ""
                },
                "Geographical Scope": {
                        mandatory: true,
                        value: ""
                },
                "Country / Location(s)": {
                        mandatory: true,
                        value: ""
                },
                "Budget Range": {
                        mandatory: true,
                        value: ""
                },
                "Duration": {
                        mandatory: true,
                        value: ""
                },
                "Targeted Donor": {
                        mandatory: true,
                        value: ""
                }
        })

        useEffect(() => {
                const scope = formData['Geographical Scope'].value;
                const filtered = scope
                        ? fieldContexts.filter(fc => fc.geographic_coverage === scope)
                        : fieldContexts;
                setFilteredFieldContexts(filtered);

                const locationValue = formData['Country / Location(s)'].value;
                if (locationValue) {
                        const isLocationStillValid = filtered.some(fc => fc.id === locationValue);
                        if (fieldContexts.length > 0 && !isLocationStillValid) {
                                handleFormInput({ target: { value: "" } }, "Country / Location(s)");
                        }
                }
        }, [formData['Geographical Scope'].value, fieldContexts]);
        function handleFormInput(e, label) {
                setFormData(p => ({
                        ...p,
                        [label]: {
                                ...formData[label],
                                value: e.target.value
                        }
                }))
        }

        const [buttonEnable, setButtonEnable] = useState(false)
        useEffect(() => {
                const missing = getMissingFields();
                setButtonEnable(missing.length === 0);
        }, [userPrompt, formData])

        const getMissingFields = () => {
                const missing = [];
                if (!userPrompt.trim()) missing.push("Proposal Prompt Details");
                for (const label in formData) {
                        const field = formData[label];
                        if (field.mandatory) {
                                if (Array.isArray(field.value) && field.value.length === 0) {
                                        missing.push(label);
                                } else if (!field.value || (typeof field.value === 'string' && !field.value.trim())) {
                                        missing.push(label);
                                }
                        }
                }
                return missing;
        };

        const toKebabCase = (str) => {
                return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
        };

        const renderFormField = (label, disabled) => {
                const field = formData[label];
                if (!field) return null;

                const fieldId = toKebabCase(label);

                const getOptions = (label) => {
                        switch (label) {
                                case "Main Outcome":
                                        return [...outcomes, ...newOutcomes].map(o => ({ value: o.id, label: o.name }));
                                case "Targeted Donor":
                                        return [...donors, ...newDonors].map(d => ({ value: d.id, label: d.name }));
                                case "Country / Location(s)":
                                        return [...filteredFieldContexts, ...newFieldContexts].map(fc => ({ value: fc.id, label: fc.name }));
                                case "Geographical Scope":
                                        return geographicCoverages.map(gc => ({ value: gc, label: gc }));
                                case "Duration":
                                        const durationOptions = ["1 month", "3 months", "6 months", "12 months", "18 months", "24 months", "30 months", "36 months"];
                                        return [...durationOptions.map(d => ({ value: d, label: d })), ...newDurations.map(d => ({ value: d.id, label: d.name }))];
                                case "Budget Range":
                                        const budgetOptions = ["50k$", "100k$", "250k$", "500k$", "1M$", "2M$", "5M$", "10M$", "15M$", "25M$"];
                                        return [...budgetOptions.map(b => ({ value: b, label: b })), ...newBudgetRanges.map(b => ({ value: b.id, label: b.name }))];
                                default:
                                        return [];
                        }
                };

                const handleCreate = (inputValue, label) => {
                        const newOption = { id: `new_${inputValue}`, name: inputValue };
                        switch (label) {
                                case "Duration":
                                        setNewDurations(prev => [...prev, newOption]);
                                        handleFormInput({ target: { value: newOption.id } }, label);
                                        break;
                                case "Budget Range":
                                        setNewBudgetRanges(prev => [...prev, newOption]);
                                        handleFormInput({ target: { value: newOption.id } }, label);
                                        break;
                        }
                };

                const isCreatableSelect = ["Duration", "Budget Range"].includes(label);
                const isSelect = ["Targeted Donor", "Country / Location(s)"].includes(label);
                const isMultiSelect = label === "Main Outcome";
                const isNormalSelect = label === "Geographical Scope";

                return (
                        <div key={label} className='Chat_form_inputContainer'>
                                <label className='Chat_form_inputLabel' htmlFor={fieldId}>
                                        <div className="tooltip-container">
                                                {label}
                                                <span className={`Chat_form_input_mandatoryAsterisk ${!field.mandatory ? "hidden" : ""}`}>*</span>
                                                {label === "Project Draft Short name" && <span className="tooltip-text">This will be the name used to story your draft on this system</span>}
                                        </div>
                                </label>

                                {isCreatableSelect ? (
                                        <div data-testid={`creatable-select-container-${toKebabCase(label)}`}>
                                                <CreatableSelect
                                                        isClearable
                                                        aria-label={label}
                                                        classNamePrefix={toKebabCase(label)}
                                                        onChange={option => handleFormInput({ target: { value: option ? option.value : "" } }, label)}
                                                        onCreateOption={inputValue => handleCreate(inputValue, label)}
                                                        options={getOptions(label)}
                                                        value={getOptions(label).find(o => o.value === field.value)}
                                                        isDisabled={disabled}
                                                        inputId={fieldId}
                                                />
                                        </div>
                                ) : isSelect ? (
                                        <div data-testid={`select-container-${toKebabCase(label)}`}>
                                                <Select
                                                        isClearable
                                                        aria-label={label}
                                                        classNamePrefix={toKebabCase(label)}
                                                        onChange={option => handleFormInput({ target: { value: option ? option.value : "" } }, label)}
                                                        options={getOptions(label)}
                                                        value={getOptions(label).find(o => o.value === field.value)}
                                                        isDisabled={disabled}
                                                        inputId={fieldId}
                                                />
                                        </div>
                                ) : isMultiSelect ? (
                                        <div data-testid={`multiselect-container-${toKebabCase(label)}`}>
                                                <Select
                                                        isMulti
                                                        aria-label={label}
                                                        classNamePrefix={toKebabCase(label)}
                                                        onChange={options => handleFormInput({ target: { value: options ? options.map(o => o.value) : [] } }, label)}
                                                        options={getOptions(label)}
                                                        value={field.value.map(v => getOptions(label).find(o => o.value === v)).filter(Boolean)}
                                                        isDisabled={disabled}
                                                        inputId={fieldId}
                                                />
                                        </div>
                                ) : isNormalSelect ? (
                                        <select
                                                className='Chat_form_input'
                                                id={fieldId}
                                                name={fieldId}
                                                value={field.value}
                                                onChange={e => handleFormInput(e, label)}
                                                disabled={disabled}
                                                data-testid={fieldId}
                                        >
                                                <option value="" disabled>Select {label}</option>
                                                {getOptions(label).map(option => (
                                                        <option key={option.value} value={option.value}>{option.label}</option>
                                                ))}
                                        </select>
                                ) : (
                                        <input
                                                type="text"
                                                className='Chat_form_input'
                                                id={fieldId}
                                                name={fieldId}
                                                placeholder={`Enter ${label}`}
                                                value={field.value}
                                                onChange={e => handleFormInput(e, label)}
                                                disabled={disabled}
                                                data-testid={fieldId}
                                        />
                                )}
                        </div>
                );
        };

        const [proposal, setProposal] = useState({})
        const [generateLoading, setGenerateLoading] = useState(false)
        const [generateLabel, setGenerateLabel] = useState("Generate")
        const isGenerating = useRef(false);

        useEffect(() => {
                if (titleName === "Generate Draft Proposal" || titleName === "Generate Concept Note") {
                        if (documentType === "concept note") {
                                setTitleName("Generate Concept Note");
                        } else {
                                setTitleName("Generate Draft Proposal");
                        }
                }
        }, [documentType]);

        useEffect(() => {
                if (!generateLoading && proposal && Object.values(proposal).every(section => section.content)) {
                        topRef.current?.scrollIntoView({ behavior: "smooth" });
                }
        }, [generateLoading, proposal]);

        // --- Progress + Notification State ---
        const [generationProgress, setGenerationProgress] = useState(0); // percent [0-100]
        const [generationMessage, setGenerationMessage] = useState("");
        const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
        const [notif, setNotif] = useState({ open: false, message: '', severity: 'info' }); // info/success/error

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
                                        if (data.status !== 'generating_sections') {
                                                setGenerateLoading(false);
                                                setGenerateLabel("Regenerate");
                                                setGenerationProgress(100);
                                                setGenerationMessage("Generation completed!");
                                                setNotif({ open: true, message: 'Proposal generation completed!', severity: 'success' });
                                                pollingActive = false;
                                                clearInterval(pollInterval);
                                                setTimeout(() => setIsProgressModalOpen(false), 1000); // Small delay to show 100%
                                        }
                                } else throw new Error('Non-200 response');
                        } catch (err) {
                                setGenerateLoading(false);
                                setGenerationProgress(0);
                                setNotif({ open: true, message: 'Error streaming proposal content. Try again.', severity: 'error' });
                                setIsProgressModalOpen(false);
                                pollingActive = false;
                                clearInterval(pollInterval);
                        }
                }, 1000);
                return () => { pollingActive = false; clearInterval(pollInterval); };
        }, [generateLoading]);


        async function fetchAndAssociateKnowledgeCards() {
                if (associatedKnowledgeCards.length > 0) {
                        return associatedKnowledgeCards;
                }
                const donorId = formData["Targeted Donor"].value;
                const outcomeIds = formData["Main Outcome"].value;
                const fieldContextId = formData["Country / Location(s)"].value;

                const fetchPromises = [];

                if (donorId && !donorId.startsWith("new_")) {
                        fetchPromises.push(
                                fetch(`${API_BASE_URL}/knowledge-cards?donor_id=${donorId}`, { credentials: 'include' })
                                        .then(res => res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] }))
                                        .then(data => data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null)
                        );
                }

                if (fieldContextId && !fieldContextId.startsWith("new_")) {
                        fetchPromises.push(
                                fetch(`${API_BASE_URL}/knowledge-cards?field_context_id=${fieldContextId}`, { credentials: 'include' })
                                        .then(res => res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] }))
                                        .then(data => data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null)
                        );
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

        async function handleGenerateClick() {
                const missing = getMissingFields();
                if (missing.length > 0) {
                        setValidationMissingFields(missing);
                        setIsValidationModalOpen(true);
                        return;
                }
                setGenerateLoading(true);
                setFormExpanded(false);
                sessionStorage.removeItem("proposal_id"); // Clear old ID to prevent polling it

                try {
                        const finalAssociatedCards = (await fetchAndAssociateKnowledgeCards()).filter(card => card.generated_section != null);
                        const updatedFormData = { ...Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])) };

                        const createNewOption = async (endpoint, value) => {
                                let body = { name: value.substring(4) };
                                if (endpoint === 'field-contexts') {
                                        body.geographic_coverage = formData['Geographical Scope'].value;
                                        body.category = 'Country'; // Default category
                                }

                                const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify(body),
                                        credentials: 'include'
                                });

                                if (!response.ok) {
                                        const errorData = await response.json();
                                        console.error("Failed to create new option:", errorData);
                                        throw new Error(`Failed to create new ${endpoint}`);
                                }

                                const data = await response.json();
                                return data.id;
                        };

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

        const [selectedSection, setSelectedSection] = useState(-1)
        const topRef = useRef()
        const proposalRef = useRef()
        function handleSidebarSectionClick(sectionIndex) {
                setSelectedSection(sectionIndex)

                if (sectionIndex === -1 && topRef?.current)
                        topRef?.current?.scroll({ top: 0, behavior: "smooth" })
                else if (proposalRef.current)
                        proposalRef?.current?.children[sectionIndex]?.scrollIntoView({ behavior: "smooth" })
        }

        const [isCopied, setIsCopied] = useState(false)
        async function handleCopyClick(section, content) {
                setSelectedSection(section)
                setIsCopied(true)
                // await navigator.clipboard.writeText(content)

                const timeoutId = setTimeout(() => {
                        setIsCopied(false)
                }, [3000])

                return () => clearTimeout(timeoutId)
        }

        const dialogRef = useRef()
        const [regenerateInput, setRegenerateInput] = useState("")
        const handleRegenerateIconClick = sectionIndex => {
                setSelectedSection(sectionIndex)
                dialogRef.current.showModal()
        }
        const [regenerateSectionLoading, setRegenerateSectionLoading] = useState(false)
        async function handleRegenerateButtonClick(ip = regenerateInput) {
                setRegenerateSectionLoading(true)
                const sectionName = proposalTemplate ? proposalTemplate.sections[selectedSection].section_name : Object.keys(proposal)[selectedSection];

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
                if (typeof dialogRef.current?.close === 'function') {
                        dialogRef.current.close()
                }
                setRegenerateSectionLoading(false)

                if (isEdit)
                        setIsEdit(false)
        }

        function handleExpanderToggle(section) {
                const sectionName = proposalTemplate ? proposalTemplate.sections[section].section_name : Object.keys(proposal)[section];
                setProposal(p => {
                        return ({
                                ...p,
                                [sectionName]: {
                                        content: p[sectionName].content,
                                        open: !p[sectionName].open
                                }
                        })
                })
        }

        const [isEdit, setIsEdit] = useState(false)
        const [editorContent, setEditorContent] = useState("")
        const [proposalTemplate, setProposalTemplate] = useState(null)
        async function handleEditClick(section) {
                if (!isEdit) {
                        // Entering edit mode
                        setSelectedSection(section);
                        setIsEdit(true);
                        setEditorContent(Object.values(proposal)[section].content);
                }
                else {
                        // Saving the edit
                        const sectionName = proposalTemplate ? proposalTemplate.sections[selectedSection].section_name : Object.keys(proposal)[selectedSection];

                        try {
                                const response = await fetch(`${API_BASE_URL}/update-section-content`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                                proposal_id: sessionStorage.getItem("proposal_id"),
                                                section: sectionName,
                                                content: editorContent
                                        }),
                                        credentials: 'include'
                                });

                                if (!response.ok) {
                                        throw new Error('Failed to save the section content.');
                                }

                                // On successful save, update the local state to reflect the change.
                                setProposal(p => ({
                                        ...p,
                                        [sectionName]: {
                                                ...p[sectionName],
                                                content: editorContent
                                        }
                                }));

                        } catch (error) {
                                console.error("Error saving section:", error);
                                // Optionally, show an error message to the user.
                        } finally {
                                // Exit edit mode regardless of success or failure.
                                setIsEdit(false);
                        }
                }
        }

        const [proposalStatus, setProposalStatus] = useState("draft")
        const [contributionId, setContributionId] = useState("")
        const [statusHistory, setStatusHistory] = useState([])
        const [reviews, setReviews] = useState([])

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

        async function getPeerReviews() {
                if (sessionStorage.getItem("proposal_id")) {
                        const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/peer-reviews`, {
                                method: "GET",
                                headers: { 'Content-Type': 'application/json' },
                                credentials: "include"
                        });
                        if (response.ok) {
                                const data = await response.json();
                                setReviews(data.reviews);
                        } else if (response.status === 403) {
                                setReviews([]);
                        }
                }
        }

        async function getStatusHistory() {
        }

        async function getProfile() {
                const response = await fetch(`${API_BASE_URL}/profile`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                });
                if (response.ok) {
                        const result = await response.json();
                        setCurrentUser(result.user);
                }
        }

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
                                        const ownerId = data.user_id;
                                        const isOwner = curUser.id === ownerId || curUser.user_id === ownerId;

                                        if (!isOwner) {
                                                navigate(`/review/proposal/${data.proposal_id}`);
                                                return;
                                        }
                                }

                                sessionStorage.setItem("proposal_id", data.proposal_id)
                                sessionStorage.setItem("session_id", data.session_id)

                                setUserPrompt(data.project_description)

                                setFormData(p => Object.fromEntries(Object.entries(data.form_data).map(field =>
                                        [field[0], {
                                                value: field[1],
                                                mandatory: p[field[0]]?.mandatory || false
                                        }]
                                )))

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
                                setContributionId(data.contribution_id || "")
                                setSidebarOpen(true)
                                getStatusHistory()
                                if (data.status === 'pre_submission' || data.status === 'in_review') {
                                        getPeerReviews()
                                }

                                const storedTemplate = sessionStorage.getItem("proposal_template");
                                if (storedTemplate) {
                                        setProposalTemplate(JSON.parse(storedTemplate));
                                }
                        }
                        else if (response.status === 401) {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                }
        }

        async function handleExport(format) {


                const proposalId = sessionStorage.getItem("proposal_id");

                if (!proposalId || proposalId === "undefined") {
                        setNotif({ open: true, message: "No draft available to export. Please create or load a draft first.", severity: 'error' });
                        return;
                }

                const response = await fetch(`${API_BASE_URL}/generate-document/${sessionStorage.getItem("proposal_id")}?format=${format}`, {
                        method: "GET",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if (response.ok) {
                        const contentDisposition = response.headers.get('Content-Disposition');
                        let filename = "proposal.docx"; // Default filename
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

        async function handleExportTables() {
                const proposalId = sessionStorage.getItem("proposal_id");

                if (!proposalId || proposalId === "undefined") {
                        setNotif({ open: true, message: "No draft available to export. Please create or load a draft first.", severity: 'error' });
                        return;
                }

                const response = await fetch(`${API_BASE_URL}/generate-tables/${sessionStorage.getItem("proposal_id")}`, {
                        method: "GET",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if (response.ok) {
                        const contentDisposition = response.headers.get('Content-Disposition');
                        let filename = "proposal-tables.xlsx"; // Default filename
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

        async function handleSaveResponse(reviewId, responseText) {
                const response = await fetch(`${API_BASE_URL}/peer-reviews/${reviewId}/response`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ author_response: responseText }),
                        credentials: 'include'
                });

                if (response.ok) {
                        getPeerReviews(); // Refresh reviews to show the new response
                } else {
                        console.error("Failed to save response");
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

        function handleAssociateKnowledgeConfirm(selectedCards) {
                setAssociatedKnowledgeCards(selectedCards);
        }

        return <Base>
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
                        <AssociateKnowledgeModal
                                isOpen={isAssociateKnowledgeModalOpen}
                                onClose={() => setIsAssociateKnowledgeModalOpen(false)}
                                onConfirm={handleAssociateKnowledgeConfirm}
                                donorId={formData["Targeted Donor"].value}
                                outcomeId={formData["Main Outcome"].value}
                                fieldContextId={formData["Country / Location(s)"].value}
                                initialSelection={associatedKnowledgeCards}
                        />
                        <PdfUploadModal
                                isOpen={isPdfUploadModalOpen}
                                onClose={() => setIsPdfUploadModalOpen(false)}
                                onConfirm={handlePdfUpload}
                        />

                        {/* Validation Modal */}
                        <dialog open={isValidationModalOpen} className="Chat_regenerate" style={{ height: 'auto', maxHeight: '80vh', top: '10%' }}>
                                <header className="Chat_regenerate_header">
                                        Data Missing
                                        <img src={regenerateClose} alt="" onClick={() => setIsValidationModalOpen(false)} style={{ cursor: 'pointer' }} />
                                </header>
                                <main className="Chat_right" style={{ padding: '20px' }}>
                                        <p style={{ marginBottom: '15px' }}>The following mandatory parameters are missing:</p>
                                        <ul style={{ listStyleType: 'disc', paddingLeft: '20px', marginBottom: '20px', color: '#141419' }}>
                                                {validationMissingFields.map((field, index) => (
                                                        <li key={index} style={{ marginBottom: '5px' }}>{field}</li>
                                                ))}
                                        </ul>
                                        <div className="Chat_inputArea_buttonContainer">
                                                <CommonButton onClick={() => setIsValidationModalOpen(false)} label="Close" />
                                        </div>
                                </main>
                        </dialog>
                        {((!isMobile && sidebarOpen) || (isMobile && isMobileMenuOpen)) && <aside>
                                <ul className='Chat_sidebar' data-testid="chat-sidebar">
                                        <li
                                                className={`Chat_sidebarOption ${selectedSection === -1 ? "selectedSection" : ""}`}
                                                onClick={() => handleSidebarSectionClick(-1)}
                                                data-testid="sidebar-option-proposal-prompt"
                                        >
                                                Proposal Prompt
                                        </li>

                                        {proposalTemplate ? proposalTemplate.sections.map((section, i) =>
                                                <li
                                                        key={i}
                                                        className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
                                                        onClick={() => handleSidebarSectionClick(i)}
                                                        data-testid={`sidebar-option-${toKebabCase(section.section_name)}`}
                                                >
                                                        {section.section_name}
                                                </li>
                                        ) : Object.keys(proposal).map((section, i) =>
                                                <li
                                                        key={i}
                                                        className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
                                                        onClick={() => handleSidebarSectionClick(i)}
                                                        data-testid={`sidebar-option-${toKebabCase(section)}`}
                                                >
                                                        {section}
                                                </li>
                                        )}
                                </ul>
                        </aside>}

                        <main className="Chat_right" ref={topRef} data-testid="chat-main">
                                <button className="Chat_menuButton" onClick={() => setIsMobileMenuOpen(p => !p)} data-testid="mobile-menu-button">
                                        <i className="fa-solid fa-bars"></i>
                                </button>
                                {proposalStatus !== 'submitted' ?
                                        <>
                                                <div className='Dashboard_top'>
                                                        <div className='Dashboard_label' data-testid="chat-title">
                                                                <img className='Dashboard_label_fileIcon' src={fileIcon} alt="" />
                                                                {titleName}
                                                        </div>
                                                </div>

                                                <div className="Chat_inputArea">
                                                        <div className="Chat_docTypeSwitcher" data-testid="doc-type-switcher">
                                                                <button
                                                                        type="button"
                                                                        className={`Chat_docTypeButton ${documentType === 'proposal' ? 'active' : ''}`}
                                                                        onClick={() => proposalStatus === 'draft' && setDocumentType('proposal')}
                                                                        disabled={proposalStatus !== 'draft'}
                                                                        data-testid="doc-type-proposal-button"
                                                                >
                                                                        Proposal
                                                                </button>
                                                                <button
                                                                        type="button"
                                                                        className={`Chat_docTypeButton ${documentType === 'concept note' ? 'active' : ''}`}
                                                                        onClick={() => proposalStatus === 'draft' && setDocumentType('concept note')}
                                                                        disabled={proposalStatus !== 'draft'}
                                                                        data-testid="doc-type-concept-note-button"
                                                                >
                                                                        Concept Note
                                                                </button>
                                                        </div>
                                                        {renderFormField("Project Draft Short name", proposalStatus !== 'draft')}
                                                        <textarea id="main-prompt" name="main-prompt" value={userPrompt} onChange={e => setUserPrompt(e.target.value)} placeholder='Provide as much details as possible on your initial project idea!' className='Chat_inputArea_prompt' disabled={proposalStatus !== 'draft'} data-testid="main-prompt" />

                                                        <span
                                                                onClick={() => proposalStatus === 'draft' && setFormExpanded(p => !p)}
                                                                className={`Chat_inputArea_additionalDetails ${form_expanded && "expanded"} ${proposalStatus !== 'draft' ? 'disabled' : ''}`}
                                                                data-testid="specify-parameters-expander"
                                                        >
                                                                Specify Parameters
                                                                <img src={arrow} alt="Arrow" />
                                                        </span>

                                                        {form_expanded ?
                                                                <form className='Chat_form' data-testid="chat-form">
                                                                        <div className='Chat_form_group'>
                                                                                <div className="tooltip-container">
                                                                                        <h3 className='Chat_form_group_title'>Identify Potential Interventions</h3>
                                                                                        <span className="tooltip-text">surface Relevant Policies, Strategies and past Evaluation Recommendations</span>
                                                                                </div>
                                                                                {renderFormField("Main Outcome", proposalStatus !== 'draft')}
                                                                                {renderFormField("Beneficiaries Profile", proposalStatus !== 'draft')}
                                                                                {renderFormField("Potential Implementing Partner", proposalStatus !== 'draft')}
                                                                        </div>
                                                                        <div className='Chat_form_group'>
                                                                                <div className="tooltip-container">
                                                                                        <h3 className='Chat_form_group_title'>Define Field Context</h3>
                                                                                        <span className="tooltip-text">surface Situation Analysis and Needs Assessment</span>
                                                                                </div>
                                                                                {renderFormField("Geographical Scope", proposalStatus !== 'draft')}
                                                                                {renderFormField("Country / Location(s)", proposalStatus !== 'draft')}
                                                                        </div>
                                                                        <div className='Chat_form_group'>
                                                                                <div className="tooltip-container">
                                                                                        <h3 className='Chat_form_group_title'>Tailor Funding Request</h3>
                                                                                        <span className="tooltip-text">surface Donor profile and apply Formal Requirement for Submission</span>
                                                                                </div>
                                                                                {renderFormField("Budget Range", proposalStatus !== 'draft')}
                                                                                {renderFormField("Duration", proposalStatus !== 'draft')}
                                                                                {renderFormField("Targeted Donor", proposalStatus !== 'draft')}
                                                                        </div>
                                                                </form> : ""
                                                        }

                                                        <div className="Chat_inputArea_buttonContainer">
                                                                <div style={{ position: 'relative' }}>
                                                                        <CommonButton
                                                                                onClick={() => {
                                                                                        const missing = getMissingFields();
                                                                                        if (missing.length > 0) {
                                                                                                setValidationMissingFields(missing);
                                                                                                setIsValidationModalOpen(true);
                                                                                        } else {
                                                                                                setIsAssociateKnowledgeModalOpen(true);
                                                                                        }
                                                                                }}
                                                                                label="Manage Knowledge"
                                                                                disabled={proposalStatus !== 'draft' || !buttonEnable}
                                                                                className={!buttonEnable ? "inactive" : ""}
                                                                                icon={knowIcon}
                                                                                data-testid="manage-knowledge-button"
                                                                        />
                                                                        {associatedKnowledgeCards.length > 0 && (
                                                                                <div className="associated-knowledge-display" data-testid="associated-knowledge-cards">
                                                                                        <h4>Associated Knowledge Cards:</h4>
                                                                                        <ul>
                                                                                                {associatedKnowledgeCards.map(card => {
                                                                                                        const title = [
                                                                                                                card.title,
                                                                                                                card.donor_name,
                                                                                                                card.outcome_name,
                                                                                                                card.field_context_name,
                                                                                                        ].filter(Boolean).join(' - ');
                                                                                                        return (
                                                                                                                <li key={card.id}>
                                                                                                                        <a href={`/knowledge-card/${card.id}`} target="_blank" rel="noopener noreferrer">
                                                                                                                                {title}
                                                                                                                        </a>
                                                                                                                </li>
                                                                                                        );
                                                                                                })}
                                                                                        </ul>
                                                                                </div>
                                                                        )}
                                                                </div>

                                                                <div style={{ marginLeft: 'auto' }}>
                                                                        <CommonButton
                                                                                onClick={handleGenerateClick}
                                                                                icon={generateIcon}
                                                                                label={generateLabel}
                                                                                loading={generateLoading}
                                                                                loadingLabel={generateLabel === "Generate" ? "Generating (~ 2 mins of patience...) " : "Regenerating (~ 2 mins of patience...)"}
                                                                                disabled={proposalStatus !== 'draft' || !buttonEnable}
                                                                                className={!buttonEnable ? "inactive" : ""}
                                                                                data-testid="generate-button"
                                                                        />
                                                                </div>
                                                        </div>
                                                </div>
                                        </>
                                        :
                                        ""
                                }

                                {sidebarOpen ? <>
                                        <div className='Dashboard_top'>
                                                <div className='Dashboard_label'>
                                                        <img className='Dashboard_label_fileIcon' src={resultsIcon} alt="" />
                                                        Results
                                                </div>

                                                {Object.keys(proposal).length > 0 ? <div className='Chat_exportButtons'>
                                                        <button type="button" onClick={() => handleExport("docx")} data-testid="export-word-button">
                                                                <img src={word_icon} alt="" />
                                                                Download Document
                                                        </button>

                                                        <button type="button" onClick={() => handleExportTables()} data-testid="export-excel-button">
                                                                <img src={excel_icon} alt="" />
                                                                Download Tables
                                                        </button>
                                                        <div className="Chat_workflow_status_container">
                                                                <div className="workflow-stage-box">
                                                                        <span className="workflow-stage-label">Workflow Stage</span>
                                                                        <div className="workflow-badges">
                                                                                {['draft', 'in_review', 'pre_submission', 'submitted'].map(status => {
                                                                                        const statusDetails = {
                                                                                                draft: { text: 'Drafting', className: 'status-draft', message: "Initial drafting stage - Author + AI" },
                                                                                                in_review: { text: 'Peer Review', className: 'status-review', message: "Wait while proposal sent for quality review to other users" },
                                                                                                pre_submission: { text: 'Pre-Submission', className: 'status-submission', message: "Edit to address the comments from all your reviewers" },
                                                                                                submitted: { text: 'Submitted', className: 'status-submitted', message: "Non editable Record of Initial version as submitted to donor" }
                                                                                        };
                                                                                        const isActive = proposalStatus === status;
                                                                                        const isClickable = (proposalStatus === 'draft' && (status === 'in_review' || status === 'submitted')) ||
                                                                                                (proposalStatus === 'in_review' && (status === 'pre_submission' || status === 'draft')) ||
                                                                                                (proposalStatus === 'pre_submission' && status === 'submitted');

                                                                                        return (
                                                                                                <div key={status} className="status-badge-container">
                                                                                                        <button
                                                                                                                type="button"
                                                                                                                title={statusDetails[status].message}
                                                                                                                className={`status-badge ${statusDetails[status].className} ${isActive ? 'active' : 'inactive'}`}
                                                                                                                onClick={() => {
                                                                                                                        if (status === 'in_review' && proposalStatus === 'draft') setIsPeerReviewModalOpen(true);
                                                                                                                        if (status === 'draft' && proposalStatus === 'in_review') handleSetStatus('draft');
                                                                                                                        if (status === 'submitted' && (proposalStatus === 'pre_submission' || proposalStatus === 'draft')) handleSubmit();
                                                                                                                }}
                                                                                                                disabled={!isClickable && !isActive}
                                                                                                                data-testid={`workflow-status-badge-${status}`}
                                                                                                        >
                                                                                                                {statusDetails[status].text}
                                                                                                        </button>
                                                                                                        {statusHistory.includes(status) && !isActive && (
                                                                                                                <button className="revert-btn" onClick={() => handleRevert(status)} data-testid={`revert-button-${status}`}>
                                                                                                                        Revert
                                                                                                                </button>
                                                                                                        )}
                                                                                                </div>
                                                                                        );
                                                                                })}
                                                                        </div>
                                                                        {proposalStatus === 'pre_submission' && (
                                                                                <button className="revert-btn" onClick={() => handleRevert('draft')} data-testid="revert-to-draft-button">
                                                                                        Revert to Draft
                                                                                </button>
                                                                        )}
                                                                </div>
                                                        </div>
                                                </div> : ""}
                                        </div>

                                        {proposalStatus === 'submitted' && (
                                                <div className="contribution-id-container">
                                                        <label htmlFor="contribution-id">Contribution ID:</label>
                                                        <p>Only submitted proposal with a confirmed ContributionID are counted as approved</p>
                                                        <input
                                                                type="text"
                                                                id="contribution-id"
                                                                value={contributionId}
                                                                onChange={(e) => setContributionId(e.target.value)}
                                                                data-testid="contribution-id-input"
                                                        />
                                                        <CommonButton onClick={handleSaveContributionId} label="Save ID" data-testid="save-contribution-id-button" />
                                                </div>
                                        )}

                                        <div ref={proposalRef} className="Chat_proposalContainer" data-testid="proposal-container">
                                                {(proposalTemplate ? proposalTemplate.sections.map(s => s.section_name) : Object.keys(proposal)).map((sectionName, i) => {
                                                        const sectionObj = proposal[sectionName];
                                                        const sectionReviews = reviews.filter(r => r.section_name === sectionName);

                                                        if (!sectionObj) return null;
                                                        const kebabSectionName = toKebabCase(sectionName);

                                                        return (
                                                                <div key={i} className="Chat_proposalSection" data-testid={`proposal-section-${kebabSectionName}`}>
                                                                        <div className="Chat_sectionHeader" data-testid={`section-header-${kebabSectionName}`}>
                                                                                <div className="Chat_sectionTitle" data-testid={`section-title-${kebabSectionName}`}>{sectionName}</div>

                                                                                {!generateLoading && sectionObj.content && sectionObj.open && proposalStatus !== 'submitted' ? <div className="Chat_sectionOptions" data-testid={`section-options-${kebabSectionName}`}>
                                                                                        {!isEdit || (selectedSection === i && isEdit) ? <button type="button" onClick={() => handleEditClick(i)} style={(selectedSection === i && isEdit && regenerateSectionLoading) ? { pointerEvents: "none" } : {}} aria-label={`edit-section-${i}`} disabled={proposalStatus === 'in_review'} data-testid={`edit-save-button-${kebabSectionName}`}>
                                                                                                <img src={(selectedSection === i && isEdit) ? save : edit} alt="" />
                                                                                                <span>{(selectedSection === i && isEdit) ? "Save" : "Edit"}</span>
                                                                                        </button> : ""}

                                                                                        {selectedSection === i && isEdit ? <button type="button" onClick={() => setIsEdit(false)} data-testid={`cancel-edit-button-${kebabSectionName}`}>
                                                                                                <img src={cancel} alt="" />
                                                                                                <span>Cancel</span>
                                                                                        </button> : ""}

                                                                                        {!isEdit ?
                                                                                                <>
                                                                                                        <button type="button" onClick={() => handleCopyClick(i, sectionObj.content)} data-testid={`copy-button-${kebabSectionName}`}>
                                                                                                                <img src={(selectedSection === i && isCopied) ? tick : copy} alt="" />
                                                                                                                <span>{(selectedSection === i && isCopied) ? "Copied" : "Copy"}</span>
                                                                                                        </button>

                                                                                                        <button type="button" className='Chat_sectionOptions_regenerate' onClick={() => handleRegenerateIconClick(i)} disabled={proposalStatus !== 'draft'} data-testid={`regenerate-button-${kebabSectionName}`} >
                                                                                                                <img src={regenerate} alt="" />
                                                                                                                <span>Regenerate</span>
                                                                                                        </button>
                                                                                                </>
                                                                                                : ""}
                                                                                </div> : ""}

                                                                                {sectionObj.content && !(isEdit && selectedSection === i) ? <div className={`Chat_expanderArrow ${sectionObj.open ? "" : "closed"}`} onClick={() => handleExpanderToggle(i)} data-testid={`section-expander-${kebabSectionName}`}>
                                                                                        <img src={arrow} alt="" />
                                                                                </div> : ""}
                                                                        </div>

                                                                        {(sectionObj.open || !sectionObj.content) ? <div className='Chat_sectionContent' data-testid={`section-content-${kebabSectionName}`}>
                                                                                {sectionObj.content ?
                                                                                        (selectedSection === i && isEdit) ?
                                                                                                <textarea value={editorContent} onChange={e => setEditorContent(e.target.value)} aria-label={`editor for ${sectionName}`} data-testid={`section-editor-${kebabSectionName}`} />
                                                                                                :
                                                                                                <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{sectionObj.content}</Markdown>
                                                                                        :
                                                                                        <div className='Chat_sectionContent_loading'>
                                                                                                <span className='submitButtonSpinner' />
                                                                                                <span className='Chat_sectionContent_loading'>Loading</span>
                                                                                        </div>
                                                                                }
                                                                        </div> : ""}

                                                                        {(proposalStatus === 'pre_submission' || proposalStatus === 'submission') && reviews.length > 0 && (
                                                                                <div className="reviews-container" data-testid={`reviews-container-${kebabSectionName}`}>
                                                                                        <h4>Peer Reviews</h4>
                                                                                        {reviews.filter(r => r.section_name === sectionName).map(review => (
                                                                                                <Review
                                                                                                        key={review.id}
                                                                                                        review={review}
                                                                                                        onSaveResponse={handleSaveResponse}
                                                                                                />
                                                                                        ))}
                                                                                </div>
                                                                        )}
                                                                </div>
                                                        )
                                                })}
                                        </div>
                                </> : ""}
                        </main>

                        <dialog ref={dialogRef} className='Chat_regenerate' data-testid="regenerate-dialog">
                                <header className='Chat_regenerate_header'>
                                        Regenerate — {proposalTemplate ? proposalTemplate.sections[selectedSection]?.section_name : Object.keys(proposal)[selectedSection]}
                                        <img src={regenerateClose} alt="" onClick={() => { setRegenerateSectionLoading(false); setRegenerateInput(""); dialogRef.current.close() }} data-testid="regenerate-dialog-close-button" />
                                </header>

                                <main className='Chat_right'>
                                        <section className='Chat_inputArea'>
                                                <textarea id="regenerate-prompt" name="regenerate-prompt" value={regenerateInput} onChange={e => setRegenerateInput(e.target.value)} className='Chat_inputArea_prompt' data-testid="regenerate-dialog-prompt-input" />

                                                <div className="Chat_inputArea_buttonContainer" style={{ marginTop: "20px" }}>
                                                        <CommonButton icon={generateIcon} onClick={() => handleRegenerateButtonClick()} label="Regenerate" loading={regenerateSectionLoading} loadingLabel="Regenerating" disabled={!regenerateInput} data-testid="regenerate-dialog-regenerate-button" />
                                                </div>
                                        </section>
                                </main>
                        </dialog>
                </div>
        </Base>
}
