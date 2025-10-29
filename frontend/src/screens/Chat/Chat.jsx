import './Chat.css'

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import MultiSelectModal from '../../components/MultiSelectModal/MultiSelectModal'
import AssociateKnowledgeModal from '../../components/AssociateKnowledgeModal/AssociateKnowledgeModal'
import CreatableSelect from 'react-select/creatable';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import fileIcon from "../../assets/images/chat-titleIcon.svg"
import arrow from "../../assets/images/expanderArrow.svg"
import generateIcon from "../../assets/images/generateIcon.svg"
import knowIcon from "../../assets/images/knowIcon.svg"
import resultsIcon from "../../assets/images/Chat_resultsIcon.svg"
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

export default function Chat (props)
{
        const navigate = useNavigate()

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
        const [users, setUsers] = useState([])
        const [selectedUsers, setSelectedUsers] = useState([])
        const [associatedKnowledgeCards, setAssociatedKnowledgeCards] = useState([]);

        const [donors, setDonors] = useState([]);
        const [outcomes, setOutcomes] = useState([]);
        const [fieldContexts, setFieldContexts] = useState([]);
        const [filteredFieldContexts, setFilteredFieldContexts] = useState([]);
        const [newDonors, setNewDonors] = useState([]);
        const [newOutcomes, setNewOutcomes] = useState([]);
        const [newFieldContexts, setNewFieldContexts] = useState([]);
        const [newBudgetRanges, setNewBudgetRanges] = useState([]);
        const [newDurations, setNewDurations] = useState([]);

        useEffect(() => {
                async function fetchData() {
                        try {
                                const [donorsRes, outcomesRes, fieldContextsRes] = await Promise.all([
                                        fetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
                                        fetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
                                        fetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' })
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
                        } catch (error) {
                                console.error("Error fetching form data:", error);
                        }
                }
                fetchData().then(() => {
                        if (sessionStorage.getItem("proposal_id")) {
                                getContent();
                        }
                });
        }, []);

        async function getUsers () {
                const response = await fetch(`${API_BASE_URL}/users`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if(response.ok)
                {
                        const data = await response.json()
                        setUsers(data.users.map(user => ({id: user.id, name: user.name})))
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
        function handleFormInput (e, label) {
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
                if(userPrompt) {
                        setButtonEnable(true)

                        for (const property in formData) {
                                const field = formData[property];
                                if (field.mandatory) {
                                        if (Array.isArray(field.value) && field.value.length === 0) {
                                                setButtonEnable(false);
                                                return;
                                        } else if (!field.value) {
                                                setButtonEnable(false);
                                                return;
                                        }
                                }
                        }
                }
                else
                        setButtonEnable(false)
        }, [userPrompt, formData])

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
                                        return [ "One Country Operation", "Multiple Country","One Region","Route-Based-Approach", "Area-Based-Approach","Global Coverage"].map(gc => ({ value: gc, label: gc }));
                                case "Duration":
                                        const durationOptions = ["1 month", "3 months", "6 months", "12 months", "18 months", "24 months", "30 months", "36 months"];
                                        return [...durationOptions.map(d => ({ value: d, label: d })), ...newDurations.map(d => ({ value: d.id, label: d.name }))];
                                case "Budget Range":
                                        const budgetOptions = ["50k$", "100k$","250k$","500k$","1M$","2M$","5M$","10M$","15M$","25M$"];
                                        return [...budgetOptions.map(b => ({ value: b, label: b })), ...newBudgetRanges.map(b => ({ value: b.id, label: b.name }))];
                                default:
                                        return [];
                        }
                };

                const handleCreate = (inputValue, label) => {
                        const newOption = { id: `new_${inputValue}`, name: inputValue };
                        switch (label) {
                                case "Main Outcome":
                                        setNewOutcomes(prev => [...prev, newOption]);
                                        handleFormInput({ target: { value: [...field.value, newOption.id] } }, label);
                                        break;
                                case "Targeted Donor":
                                        setNewDonors(prev => [...prev, newOption]);
                                        handleFormInput({ target: { value: newOption.id } }, label);
                                        break;
                                case "Country / Location(s)":
                                        setNewFieldContexts(prev => [...prev, newOption]);
                                        handleFormInput({ target: { value: newOption.id } }, label);
                                        break;
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

                const isCreatableSelect = ["Targeted Donor", "Country / Location(s)", "Duration", "Budget Range"].includes(label);
                const isCreatableMultiSelect = label === "Main Outcome";
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
                                ) : isCreatableMultiSelect ? (
                                        <div data-testid={`creatable-multiselect-container-${toKebabCase(label)}`}>
                                                <CreatableSelect
                                                        isMulti
                                                        aria-label={label}
                                                        classNamePrefix={toKebabCase(label)}
                                                        onChange={options => handleFormInput({ target: { value: options ? options.map(o => o.value) : [] } }, label)}
                                                        onCreateOption={inputValue => handleCreate(inputValue, label)}
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
                if(sidebarOpen)
                {
                        if(titleName === "Generate Draft Proposal")
                                setTitleName("Generate Draft Proposal")
                }
        // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [sidebarOpen])

        useEffect(() => {
                if (!generateLoading && proposal && Object.values(proposal).every(section => section.content)) {
                        topRef.current?.scrollIntoView({ behavior: "smooth" });
                }
        }, [generateLoading, proposal]);

        useEffect(() => {
                const pollStatus = async () => {
                        const proposalId = sessionStorage.getItem("proposal_id");
                        if (!proposalId || !generateLoading) return;

                        try {
                                const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/status`, { credentials: 'include' });
                                if (response.ok) {
                                        const data = await response.json();
                                        if (data.status !== 'generating_sections') {
                                                setGenerateLoading(false);
                                                setGenerateLabel("Regenerate");
                                                const sectionState = {};
                                                Object.entries(data.generated_sections).forEach(([key, value]) => {
                                                        sectionState[key] = {
                                                                content: value,
                                                                open: true
                                                        };
                                                });
                                                setProposal(sectionState);
                                        }
                                }
                        } catch (error) {
                                console.error("Error polling for status:", error);
                                setGenerateLoading(false);
                        }
                };

                const intervalId = setInterval(pollStatus, 5000); // Poll every 5 seconds

                return () => clearInterval(intervalId);
        }, [generateLoading]);

        async function fetchAndAssociateKnowledgeCards() {
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
                        outcomeIds.forEach(outcomeId => {
                                if (!outcomeId.startsWith("new_")) {
                                        fetchPromises.push(
                                                fetch(`${API_BASE_URL}/knowledge-cards?outcome_id=${outcomeId}`, { credentials: 'include' })
                                                        .then(res => res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] }))
                                                        .then(data => data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null)
                                        );
                                }
                        });
                }

                try {
                        const results = await Promise.all(fetchPromises);
                        const newAssociatedCards = results.filter(Boolean); // Filter out any nulls
                        
                        // Combine with already associated cards, ensuring uniqueness
                        const combinedCards = [...associatedKnowledgeCards, ...newAssociatedCards];
                        const uniqueAssociatedCards = Array.from(new Map(combinedCards.map(card => [card.id, card])).values());

                        setAssociatedKnowledgeCards(uniqueAssociatedCards);
                        return uniqueAssociatedCards;
                } catch (error) {
                        console.error("Error auto-associating knowledge cards:", error);
                        return associatedKnowledgeCards; // Return original cards on error
                }
        }

        async function handleGenerateClick ()
        {
                setGenerateLoading(true);
                setFormExpanded(false);

                try {
                        const finalAssociatedCards = await fetchAndAssociateKnowledgeCards();
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

                        if (updatedFormData["Targeted Donor"] && updatedFormData["Targeted Donor"].startsWith("new_")) {
                                updatedFormData["Targeted Donor"] = await createNewOption("donors", updatedFormData["Targeted Donor"]);
                        }
                        if (updatedFormData["Country / Location(s)"] && updatedFormData["Country / Location(s)"].startsWith("new_")) {
                                updatedFormData["Country / Location(s)"] = await createNewOption("field-contexts", updatedFormData["Country / Location(s)"]);
                        }
                        if (updatedFormData["Main Outcome"]) {
                                updatedFormData["Main Outcome"] = await Promise.all(
                                        updatedFormData["Main Outcome"].map(o => o.startsWith("new_") ? createNewOption("outcomes", o) : o)
                                );
                        }

                        // Call the new, streamlined endpoint to create the session and initial draft.
                        const response = await fetch(`${API_BASE_URL}/create-session`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        project_description: userPrompt,
                                        form_data: updatedFormData,
                                        associated_knowledge_cards: finalAssociatedCards
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
        function handleSidebarSectionClick (sectionIndex)
        {
                setSelectedSection(sectionIndex)

                if(sectionIndex === -1 && topRef?.current)
                        topRef?.current?.scroll({top: 0, behavior: "smooth"})
                else if(proposalRef.current)
                        proposalRef?.current?.children[sectionIndex]?.scrollIntoView({behavior: "smooth"})
        }

        const [isCopied, setIsCopied] = useState(false)
        async function handleCopyClick (section, content) {
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
        async function handleRegenerateButtonClick (ip = regenerateInput)
        {
                setRegenerateSectionLoading(true)
                const sectionName = proposalTemplate ? proposalTemplate.sections[selectedSection].section_name : Object.keys(proposal)[selectedSection];

                const response = await fetch(`${API_BASE_URL}/regenerate_section/${sessionStorage.getItem("session_id")}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                section: sectionName,
                                concise_input: ip,
                                proposal_id: sessionStorage.getItem("proposal_id"),
                                form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
                                project_description: userPrompt
                        }),
                        credentials: 'include'
                })

                if(response.ok) {
                        const data = await response.json()
                        setProposal(p => ({
                                ...p,
                                [sectionName]: {
                                        open: p[sectionName].open,
                                        content: data.generated_text
                                }
                        }))
                }
                else if(response.status === 401)
                {
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

        function handleExpanderToggle (section)
        {
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
        async function handleEditClick (section)
        {
                if(!isEdit)
                {
                        // Entering edit mode
                        setSelectedSection(section);
                        setIsEdit(true);
                        setEditorContent(Object.values(proposal)[section].content);
                }
                else
                {
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

        const [isApproved, setIsApproved] = useState(false)
        const [proposalStatus, setProposalStatus] = useState("draft")
        const [statusHistory, setStatusHistory] = useState([])
        const [reviews, setReviews] = useState([])

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
                        }
                }
        }

        async function getStatusHistory() {
                // if (sessionStorage.getItem("proposal_id")) {
                //      const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/status-history`, {
                //              method: "GET",
                //              headers: { 'Content-Type': 'application/json' },
                //              credentials: "include"
                //      });
                //      if (response.ok) {
                //              const data = await response.json();
                //              setStatusHistory(data.statuses);
                //      } else if (response.status === 403) {
                //              // If forbidden, user doesn't have rights, so we don't show history.
                //              setStatusHistory([]);
                //      }
                // }
        }

        async function getContent()         {

                if(sessionStorage.getItem("proposal_id"))
                {
                        const response = await fetch(`${API_BASE_URL}/load-draft/${sessionStorage.getItem("proposal_id")}`, {
                                method: "GET",
                                headers: { 'Content-Type': 'application/json' },
                                credentials: "include"
                        })

                        if(response.ok)
                        {
                                const data = await response.json()

                                sessionStorage.setItem("proposal_id", data.proposal_id)
                                sessionStorage.setItem("session_id", data.session_id)

                                setUserPrompt(data.project_description)

                                setFormData(p => Object.fromEntries(Object.entries(data.form_data).map(field =>
                                        [field[0], {
                                                value: field[1],
                                                mandatory: p[field[0]].mandatory
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

                                setIsApproved(data.is_accepted)
                                setProposalStatus(data.status)
                                setSidebarOpen(true)
                                getStatusHistory()
                                if(data.status === 'submission') {
                                    getPeerReviews()
                                }

                                const storedTemplate = sessionStorage.getItem("proposal_template");
                                if (storedTemplate) {
                                        setProposalTemplate(JSON.parse(storedTemplate));
                                }
                        }
                        else if(response.status === 401)
                        {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                }
        }
        
        async function handleExport (format)
        {
                
                
                const proposalId = sessionStorage.getItem("proposal_id");

                if (!proposalId || proposalId === "undefined") {
                        setErrorMessage("No draft available to export. Please create or load a draft first.");
                        return;
                }
                
                const response = await fetch(`${API_BASE_URL}/generate-document/${sessionStorage.getItem("proposal_id")}?format=${format}`, {
                        method: "GET",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if(response.ok)
                {
                        const blob = await response.blob();
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                link.download = formData["Project Draft Short name"].value ?? "proposal" + "." + format;
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

        async function handleExportTables ()
        {
                const proposalId = sessionStorage.getItem("proposal_id");

                if (!proposalId || proposalId === "undefined") {
                        setErrorMessage("No draft available to export. Please create or load a draft first.");
                        return;
                }

                const response = await fetch(`${API_BASE_URL}/generate-tables/${sessionStorage.getItem("proposal_id")}`, {
                        method: "GET",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if(response.ok)
                {
                        const blob = await response.blob();
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = formData["Project Draft Short name"].value ?? "proposal" + "_tables.xlsx";
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

        async function handleRequestSubmission ()
        {
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/request-submission`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if(response.ok)
                {
                        await getContent()
                }
                else if(response.status === 401)
                {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        async function handleRevert (status)
        {
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

        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) {
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/upload-approved-document`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            if (response.ok) {
                alert('File uploaded successfully');
            } else {
                alert('File upload failed');
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

        async function handleSubmit ()
        {
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/submit`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        credentials: "include"
                })

                if(response.ok)
                {
                        await getContent()
                }
                else if(response.status === 401)
                {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        async function handleApprove ()
        {
                const response = await fetch(`${API_BASE_URL}/finalize-proposal`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ proposal_id: sessionStorage.getItem("proposal_id")}),
                        credentials: "include"
                })

                if(response.ok)
                {
                        await getContent()
                }
                else if(response.status === 401)
                {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        async function handleSubmitForPeerReview ({ selectedUsers, deadline })
        {
                const reviewers = selectedUsers.map(user_id => ({ user_id, deadline }));
                const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/submit-for-review`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ reviewers }),
                        credentials: "include"
                })

                if(response.ok)
                {
                        setProposalStatus('in_review');
                        await getContent()
                        setIsPeerReviewModalOpen(false)
                }
                else if(response.status === 401)
                {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
        }

        function handleAssociateKnowledgeConfirm(selectedCards) {
                setAssociatedKnowledgeCards(selectedCards);
        }

        return  <Base>
                <div className={`Chat ${isMobile && isMobileMenuOpen ? 'mobile-menu-open' : ''}`}>
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
                        {((!isMobile && sidebarOpen) || (isMobile && isMobileMenuOpen)) && <aside>
                                <ul className='Chat_sidebar'>
                                        <li
                                                className={`Chat_sidebarOption ${selectedSection === -1 ? "selectedSection" : ""}`}
                                                onClick={() => handleSidebarSectionClick(-1)}
                                        >
                                                Proposal Prompt
                                        </li>

                                        {proposalTemplate ? proposalTemplate.sections.map((section, i) =>
                                                <li
                                                        key={i}
                                                        className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
                                                        onClick={() => handleSidebarSectionClick(i)}
                                                >
                                                        {section.section_name}
                                                </li>
                                        ) : Object.keys(proposal).map((section, i) =>
                                                <li
                                                        key={i}
                                                        className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
                                                        onClick={() => handleSidebarSectionClick(i)}
                                                >
                                                        {section}
                                                </li>
                                        )}
                                </ul>
                        </aside>}

                        <main className="Chat_right" ref={topRef}>
                                <button className="Chat_menuButton" onClick={() => setIsMobileMenuOpen(p => !p)}>
                                        <i className="fa-solid fa-bars"></i>
                                </button>
                                {!isApproved ?
                                        <>
                                                <div className='Dashboard_top'>
                                                        <div className='Dashboard_label'>
                                                                <img className='Dashboard_label_fileIcon' src={fileIcon} />
                                                                {titleName}
                                                        </div>
                                                </div>

                                                <div className="Chat_inputArea">
                                                        {renderFormField("Project Draft Short name", proposalStatus !== 'draft')}
                                                        <textarea id="main-prompt" name="main-prompt" value={userPrompt} onChange={e => setUserPrompt(e.target.value)} placeholder='Provide as much details as possible on your initial project idea!' className='Chat_inputArea_prompt' disabled={proposalStatus !== 'draft'} />

                                                        <span
                                                            onClick={() => proposalStatus === 'draft' && setFormExpanded(p => !p)}
                                                            className={`Chat_inputArea_additionalDetails ${form_expanded && "expanded"} ${proposalStatus !== 'draft' ? 'disabled' : ''}`}
                                                        >
                                                            Specify Parameters
                                                            <img src={arrow} alt="Arrow" />
                                                        </span>

                                                        {form_expanded ?
                                                                <form className='Chat_form'>
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
                                                                        <CommonButton onClick={() => setIsAssociateKnowledgeModalOpen(true)} label="Manage Knowledge" disabled={proposalStatus !== 'draft'} icon={knowIcon}/>
                                                                        {associatedKnowledgeCards.length > 0 && (
                                                                                <div className="associated-knowledge-display">
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
                                                                        <CommonButton onClick={handleGenerateClick} icon={generateIcon} label={generateLabel} loading={generateLoading} loadingLabel={generateLabel === "Generate" ? "Generating (~ 2 mins) " : "Regenerating (~ 2 mins)"} disabled={!buttonEnable || proposalStatus !== 'draft'}/>
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
                                                        <img className='Dashboard_label_fileIcon' src={resultsIcon} />
                                                        Results
                                                </div>

                                                {Object.keys(proposal).length > 0 ? <div className='Chat_exportButtons'>
                                                        <button type="button" onClick={() => handleExport("docx")}>
                                                                <img src={word_icon} />
                                                                Download Document
                                                        </button>
                                                        <button type="button" onClick={() => handleExportTables()}>
                                                                <img src={excel_icon} />
                                                                Download Tables
                                                        </button>
                                                        <div className="Chat_workflow_status_container">
                                                            <div className="workflow-stage-box">
                                                                <span className="workflow-stage-label">Workflow Stage</span>
                                                                <div className="workflow-badges">
                                                                    {['draft', 'in_review', 'submission', 'submitted', 'approved'].map(status => {
                                                                            const statusDetails = {
                                                                                    draft: { text: 'Drafting', className: 'status-draft', message: "Initial drafting stage - Author + AI" },
                                                                                    in_review: { text: 'Peer Review', className: 'status-review', message: "Wait while proposal sent for quality review to other users" },
                                                                                    submission: { text: 'Pre-Submission', className: 'status-submission', message: "Edit to address the comments from all your reviewers" },
                                                                                    submitted: { text: 'Submitted', className: 'status-submitted', message: "Non editable Record of Initial version as submitted to donor" },
                                                                                    approved: { text: 'Approved', className: 'status-approved', message: "Non editable uploaded record of the Final version as approved by donor" }
                                                                            };
                                                                            const isActive = proposalStatus === status;
                                                                            const isClickable = (proposalStatus === 'draft' && status === 'in_review') ||
                                                                                                    (proposalStatus === 'in_review' && status === 'submission') ||
                                                                                                    (proposalStatus === 'in_review' && status === 'draft') ||
                                                                                                    (proposalStatus === 'submission' && status === 'submitted') ||
                                                                                                    (proposalStatus === 'submitted' && status === 'approved');

                                                                            return (
                                                                                <div key={status} className="status-badge-container">
                                                                                    <button
                                                                                            type="button"
                                                                                            title={statusDetails[status].message}
                                                                                            className={`status-badge ${statusDetails[status].className} ${isActive ? 'active' : 'inactive'}`}
                                                                                            onClick={() => {
                                                                                                    if (status === 'in_review' && proposalStatus === 'draft') setIsPeerReviewModalOpen(true);
                                                                                                    if (status === 'draft' && proposalStatus === 'in_review') handleSetStatus('draft');
                                                                                                    if (status === 'submission' && proposalStatus === 'in_review') handleRequestSubmission();
                                                                                                    if (status === 'submitted' && proposalStatus === 'submission') handleSubmit();
                                                                                                    if (status === 'approved' && proposalStatus === 'submitted') handleApprove();
                                                                                            }}
                                                                                            disabled={!isClickable && !isActive}
                                                                                    >
                                                                                            {statusDetails[status].text}
                                                                                    </button>
                                                                                    {statusHistory.includes(status) && !isActive && (
                                                                                        <button className="revert-btn" onClick={() => handleRevert(status)}>
                                                                                            Revert
                                                                                        </button>
                                                                                    )}
                                                                                </div>
                                                                            );
                                                                    })}
                                                                </div>
                                                            </div>
                                                             {proposalStatus === 'approved' && (
                                                                <div className="upload-approved-container">
                                                                    <label htmlFor="approved-doc-upload" className="upload-label">
                                                                        Upload Approved Document
                                                                    </label>
                                                                    <input id="approved-doc-upload" type="file" onChange={handleFileUpload} />
                                                                </div>
                                                             )}
                                                        </div>
                                                </div> : ""}
                                        </div>

                                        <div ref={proposalRef} className="Chat_proposalContainer">
                                                {(proposalTemplate ? proposalTemplate.sections.map(s => s.section_name) : Object.keys(proposal)).map((sectionName, i) => {
                                                        const sectionObj = proposal[sectionName];
                                                        const sectionReviews = reviews.filter(r => r.section_name === sectionName);

                                                        if (!sectionObj) return null;

                                                        return (
                                                                <div key={i} className="Chat_proposalSection">
                                                                        <div className="Chat_sectionHeader">
                                                                                 <div className="Chat_sectionTitle">{sectionName}</div>

                                                                                {!generateLoading && sectionObj.content && sectionObj.open && !isApproved ? <div className="Chat_sectionOptions" data-testid={`section-options-${i}`}>
                                                                                        {!isEdit || (selectedSection === i && isEdit) ? <button type="button" onClick={() => handleEditClick(i)} style={(selectedSection === i && isEdit && regenerateSectionLoading) ? {pointerEvents: "none"} : {}} aria-label={`edit-section-${i}`} disabled={proposalStatus === 'in_review'}>
                                                                                                <img src={(selectedSection === i && isEdit) ? save : edit} />
                                                                                                <span>{(selectedSection === i && isEdit) ? "Save" : "Edit"}</span>
                                                                                        </button> : "" }

                                                                                        {selectedSection === i && isEdit ? <button type="button" onClick={() => setIsEdit(false)}>
                                                                                                <img src={cancel} />
                                                                                                <span>Cancel</span>
                                                                                        </button> : "" }

                                                                                        {!isEdit ?
                                                                                                <>
                                                                                                        <button type="button" onClick={() => handleCopyClick(i, sectionObj.content)}>
                                                                                                                <img src={(selectedSection === i && isCopied) ? tick : copy} />
                                                                                                                <span>{(selectedSection === i && isCopied) ? "Copied" : "Copy"}</span>
                                                                                                        </button>

                                                                                                        <button type="button" className='Chat_sectionOptions_regenerate' onClick={() => handleRegenerateIconClick(i)} disabled={proposalStatus !== 'draft'} >
                                                                                                                <img src={regenerate} />
                                                                                                                <span>Regenerate</span>
                                                                                                        </button>
                                                                                                </>
                                                                                        : "" }
                                                                                </div> : ""}

                                                                                {sectionObj.content && !(isEdit && selectedSection === i) ? <div className={`Chat_expanderArrow ${sectionObj.open ? "" : "closed"}`} onClick={() => handleExpanderToggle(i)}>
                                                                                        <img src={arrow} />
                                                                                </div> : ""}
                                                                        </div>

                                                                        {(sectionObj.open || !sectionObj.content) ? <div className='Chat_sectionContent'>
                                                                                {sectionObj.content ?
                                                                                        (selectedSection === i && isEdit) ?
                                                                                                <textarea value={editorContent} onChange={e => setEditorContent(e.target.value)} aria-label={`editor for ${sectionName}`} />
                                                                                                :
                                                                                                <Markdown remarkPlugins={[remarkGfm]}>{sectionObj.content}</Markdown>
                                                                                        :
                                                                                        <div className='Chat_sectionContent_loading'>
                                                                                                <span className='submitButtonSpinner' />
                                                                                                <span className='Chat_sectionContent_loading'>Loading</span>
                                                                                        </div>
                                                                                }
                                                                        </div> : ""}

                                                                         {proposalStatus === 'submission' && sectionReviews.length > 0 && (
                                                                             <div className="reviews-container">
                                                                                 <h4>Peer Reviews</h4>
                                                                                 {sectionReviews.map(review => (
                                                                                     <div key={review.id} className="review">
                                                                                         <p><strong>{review.reviewer_name}:</strong> {review.review_text}</p>
                                                                                         <div className="author-response">
                                                                                             <textarea
                                                                                                 placeholder="Respond to this review..."
                                                                                                 defaultValue={review.author_response || ''}
                                                                                                 onBlur={(e) => handleSaveResponse(review.id, e.target.value)}
                                                                                             />
                                                                                         </div>
                                                                                     </div>
                                                                                 ))}
                                                                             </div>
                                                                         )}
                                                                </div>
                                                     )
                                                 })}
                                        </div>
                                </> : ""}
                        </main>

                        <dialog ref={dialogRef} className='Chat_regenerate'>
                                <header className='Chat_regenerate_header'>
                                        Regenerate — {proposalTemplate ? proposalTemplate.sections[selectedSection]?.section_name : Object.keys(proposal)[selectedSection]}
                                        <img src={regenerateClose} onClick={() => {setRegenerateSectionLoading(false); setRegenerateInput(""); dialogRef.current.close()}} />
                                </header>

                                <main className='Chat_right'>
                                        <section className='Chat_inputArea'>
                                                <textarea id="regenerate-prompt" name="regenerate-prompt" value={regenerateInput} onChange={e => setRegenerateInput(e.target.value)} className='Chat_inputArea_prompt' />

                                                <div className="Chat_inputArea_buttonContainer" style={{marginTop: "20px"}}>
                                                        <CommonButton icon={generateIcon} onClick={() => handleRegenerateButtonClick()} label="Regenerate" loading={regenerateSectionLoading} loadingLabel="Regenerating" disabled={!regenerateInput} />
                                                </div>
                                        </section>
                                </main>
                        </dialog>
                </div>
        </Base>
}

