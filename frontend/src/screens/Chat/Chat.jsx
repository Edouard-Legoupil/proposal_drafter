import './Chat.css'

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import MultiSelectModal from '../../components/MultiSelectModal/MultiSelectModal'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import fileIcon from "../../assets/images/chat-titleIcon.svg"
import arrow from "../../assets/images/expanderArrow.svg"
import generateIcon from "../../assets/images/generateIcon.svg"
import resultsIcon from "../../assets/images/Chat_resultsIcon.svg"
import edit from "../../assets/images/Chat_edit.svg"
import save from "../../assets/images/Chat_save.svg"
import cancel from "../../assets/images/Chat_editCancel.svg"
import copy from "../../assets/images/Chat_copy.svg"
import tick from "../../assets/images/Chat_copiedTick.svg"
import regenerate from "../../assets/images/Chat_regenerate.svg"
import regenerateClose from "../../assets/images/Chat_regenerateClose.svg"
import word_icon from "../../assets/images/word.svg"
import pdf_icon from "../../assets/images/pdf.svg"
import approved_icon from "../../assets/images/Chat_approved.svg"

export default function Chat (props)
{
        const navigate = useNavigate()

        const [sidebarOpen, setSidebarOpen] = useState(false)

        const [titleName, setTitleName] = useState(props?.title ?? "Generate Draft Proposal")

        const [userPrompt, setUserPrompt] = useState("")

        const [isModalOpen, setIsModalOpen] = useState(false)
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

        const renderFormField = (label) => {
                const field = formData[label];
                if (!field) return null;
        
                const fieldId = toKebabCase(label);
                const datalistId = `datalist_${fieldId}`;
                const options = {
                        "Main Outcome": ["OA1-Access/Documentation", "OA2-Status", "OA3-Protection Policy", "OA4-GBV", "OA5-Child protection", "OA6-Justice", "OA7-Community", "OA8-Well-Being", "OA9-Housing", "OA10-Health", "OA11-Education", "OA12-WASH", "OA13-Livelihoods", "OA14-Return", "OA15-Resettlement", "OA16-Integrate"],
                        "Duration": ["1 month", "3 months", "6 months", "12 months", "18 months", "24 months", "30 months", "36 months"],
                        "Targeted Donor": Object.keys(templateConfig),
                        "Budget Range": ["50k$", "100k$","250k$","500k$","1M$","2M$","5M$","10M$","15M$","25M$"],
                        "Geographical Scope": ["One Area", "One Country Operation", "Multiple Country","One Region","Route-Based-Approach","Global"],
                }[label] || [];
        
                return (
                        <div key={label} className='Chat_form_inputContainer'>
                                <label className='Chat_form_inputLabel' htmlFor={fieldId}>
                                        <div className="tooltip-container">
                                                {label}
                                                <span className={`Chat_form_input_mandatoryAsterisk ${!field.mandatory ? "hidden" : ""}`}>*</span>
                                                {label === "Project Draft Short name" && <span className="tooltip-text">This will be the name used to story your draft on this system</span>}
                                        </div>
                                </label>
        
                                {field.type === 'multiselect' ? (
                                        <>
                                                <button type="button" className='Chat_form_input' onClick={() => setIsModalOpen(true)}>
                                                        {field.value.length > 0 ? field.value.join(', ') : `Select ${label}`}
                                                </button>
                                                <MultiSelectModal
                                                        isOpen={isModalOpen}
                                                        onClose={() => setIsModalOpen(false)}
                                                        options={options}
                                                        selectedOptions={field.value}
                                                        onSelectionChange={(newSelection) => handleFormInput({ target: { value: newSelection } }, label)}
                                                />
                                        </>
                                ) : options.length > 0 ? (
                                        <>
                                                <input
                                                        list={datalistId}
                                                        className='Chat_form_input'
                                                        id={fieldId}
                                                        name={fieldId}
                                                        placeholder={`Enter or select ${label}`}
                                                        value={field.value}
                                                        onChange={e => handleFormInput(e, label)}
                                                />
                                                <datalist id={datalistId}>
                                                        {options.map((option, idx) => (
                                                                <option key={idx} value={option} />
                                                        ))}
                                                </datalist>
                                        </>
                                ) : (
                                        <input
                                                type="text"
                                                className='Chat_form_input'
                                                id={fieldId}
                                                name={fieldId}
                                                placeholder={`Enter ${label}`}
                                                value={field.value}
                                                onChange={e => handleFormInput(e, label)}
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
                const generateAllSections = async () => {
                        // Use a ref to prevent this function from running again if it's already in progress.
                        if (isGenerating.current) return;
                        isGenerating.current = true;

                        const sectionKeys = Object.keys(proposal);
                        for (let i = 0; i < sectionKeys.length; i++) {
                                const sectionKey = sectionKeys[i];

                                // Check for content again inside the loop, as state might have changed.
                                if (proposal[sectionKey]?.content) {
                                        continue;
                                }
                                
                                try {
                                        setSelectedSection(i);
                                        const el = proposalRef.current?.children[i];
                                        if (typeof el?.scrollIntoView === 'function') {
                                                el.scrollIntoView({ behavior: 'smooth' });
                                        }

                                        const response = await fetch(`${API_BASE_URL}/process_section/${sessionStorage.getItem("session_id")}`, {
                                                method: "POST",
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({
                                                        section: sectionKey,
                                                        proposal_id: sessionStorage.getItem("proposal_id"),
                                                        form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
                                                        project_description: userPrompt
                                                }),
                                                credentials: 'include'
                                        });

                                        if (response.ok) {
                                                const data = await response.json();
                                                setProposal(prev => ({
                                                        ...prev,
                                                        [sectionKey]: { ...prev[sectionKey], content: data.generated_text }
                                                }));
                                        } else {
                                                console.error(`Failed to generate section: ${sectionKey}`);
                                                break; // Exit loop on failure
                                        }
                                } catch (error) {
                                        console.error(`An error occurred while generating section ${sectionKey}:`, error);
                                        break; // Exit loop on error
                                }
                        }

                        // Reset the guard and loading state when the process is complete or has failed.
                        isGenerating.current = false;
                        setGenerateLoading(false);
                        setGenerateLabel("Regenerate");
                };

                // Trigger the generation process only when loading is enabled and sections are present.
                if (generateLoading && proposal && Object.keys(proposal).length > 0) {
                        generateAllSections();
                }
        }, [generateLoading, proposal, formData, userPrompt]); // Dependencies are now correctly listed.

        useEffect(() => {
                if(sidebarOpen)
                {
                        if(titleName === "Generate Draft Proposal")
                                setTitleName("Generate Draft Proposal")
                }
        // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [sidebarOpen])

        const [templateConfig, setTemplateConfig] = useState({});

        // Fetch template configuration from the backend when the component mounts.
        useEffect(() => {
                async function fetchTemplates() {
                        try {
                                const response = await fetch(`${API_BASE_URL}/templates`, {
                                        method: 'GET',
                                        headers: { 'Content-Type': 'application/json' },
                                        credentials: 'include'
                                });
                                if (response.ok) {
                                        const data = await response.json();
                                        setTemplateConfig(data.templates);
                                } else {
                                        console.error("Failed to fetch templates");
                                }
                        } catch (error) {
                                console.error("Error fetching templates:", error);
                        }
                }
                fetchTemplates();
        }, []);

        async function handleGenerateClick ()
        {
                setGenerateLoading(true);
                setFormExpanded(false);

                try {
                        // Call the new, streamlined endpoint to create the session and initial draft.
                        const response = await fetch(`${API_BASE_URL}/create-session`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        project_description: userPrompt,
                                        form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
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
                        // The getSections() call will be triggered by the useEffect that depends on `proposal`.

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

                const response = await fetch(`${API_BASE_URL}/regenerate_section/${sessionStorage.getItem("session_id")}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                section: Object.keys(proposal)[selectedSection],
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
                                [Object.keys(proposal)[selectedSection]]: {
                                        open: Object.values(p)[selectedSection].open,
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
                setProposal(p => {
                        return ({
                                ...p,
                                [Object.keys(p)[section]]: {
                                        content: Object.values(p)[section].content,
                                        open: !Object.values(p)[section].open
                                }
                        })
                })
        }

        const [isEdit, setIsEdit] = useState(false)
        const [editorContent, setEditorContent] = useState("")
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
                        const sectionKey = Object.keys(proposal)[selectedSection];
                        
                        try {
                                const response = await fetch(`${API_BASE_URL}/update-section-content`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                                proposal_id: sessionStorage.getItem("proposal_id"),
                                                section: sectionKey,
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
                                        [sectionKey]: {
                                                ...Object.values(p)[selectedSection],
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
                                setSidebarOpen(true)
                        }
                        else if(response.status === 401)
                        {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                }
        }
        
        useEffect(() => {
                getContent()
        // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [])

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

        return  <Base>
                <div className="Chat">
                        {sidebarOpen ? <aside>
                                <ul className='Chat_sidebar'>
                                        <li
                                                className={`Chat_sidebarOption ${selectedSection === -1 ? "selectedSection" : ""}`}
                                                onClick={() => handleSidebarSectionClick(-1)}
                                        >
                                                Proposal Prompt
                                        </li>

                                        {Object.keys(proposal).map((section, i) =>
                                                <li
                                                        key={i}
                                                        className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
                                                        onClick={() => handleSidebarSectionClick(i)}
                                                >
                                                        {section}
                                                </li>
                                        )}
                                </ul>
                        </aside> : ""}

                        <main className="Chat_right" ref={topRef}>
                                {!isApproved ?
                                        <>
                                                <div className='Dashboard_top'>
                                                        <div className='Dashboard_label'>
                                                                <img className='Dashboard_label_fileIcon' src={fileIcon} />
                                                                {titleName}
                                                        </div>
                                                </div>

                                                <div className="Chat_inputArea">
                                                        {renderFormField("Project Draft Short name")}
                                                        <textarea id="main-prompt" name="main-prompt" value={userPrompt} onChange={e => setUserPrompt(e.target.value)} placeholder='Provide as much details as possible on your initial project idea!' className='Chat_inputArea_prompt' />

                                                        <span onClick={() => setFormExpanded(p => !p)} className={`Chat_inputArea_additionalDetails ${form_expanded && "expanded"}`}>
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
                                                                                {renderFormField("Main Outcome")}
                                                                                {renderFormField("Beneficiaries Profile")}
                                                                                {renderFormField("Potential Implementing Partner")}
                                                                        </div>
                                                                        <div className='Chat_form_group'>
                                                                                <div className="tooltip-container">
                                                                                        <h3 className='Chat_form_group_title'>Define Field Context</h3>
                                                                                        <span className="tooltip-text">surface Situation Analysis and Needs Assessment</span>
                                                                                </div>
                                                                                {renderFormField("Geographical Scope")}
                                                                                {renderFormField("Country / Location(s)")}
                                                                        </div>
                                                                        <div className='Chat_form_group'>
                                                                                <div className="tooltip-container">
                                                                                        <h3 className='Chat_form_group_title'>Tailor Funding Request</h3>
                                                                                        <span className="tooltip-text">surface Donor profile and apply Formal Requirement for Submission</span>
                                                                                </div>
                                                                                {renderFormField("Budget Range")}
                                                                                {renderFormField("Duration")}
                                                                                {renderFormField("Targeted Donor")}
                                                                        </div>
                                                                </form> : ""
                                                        }

                                                        <div className="Chat_inputArea_buttonContainer">
                                                                <CommonButton onClick={handleGenerateClick} icon={generateIcon} label={generateLabel} loading={generateLoading} loadingLabel={generateLabel === "Generate" ? "Generating" : "Regenerating"} disabled={!buttonEnable}/>
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

                                                {Object.values(proposal).some(section => section.content) ? <div className='Chat_exportButtons'>
                                                        <button type="button" onClick={() => handleExport("docx")}>
                                                                <img src={word_icon} />
                                                                Download Document
                                                        </button>
                                                        {!isApproved ? <button type="button" onClick={handleApprove}>
                                                                <img src={approved_icon} />
                                                                Approve
                                                        </button> : ""}
                                                </div> : ""}
                                        </div>

                                        <div ref={proposalRef} className="Chat_proposalContainer">
                                                {Object.entries(proposal).map((sectionObj, i) =>
                                                        <div key={i} className="Chat_proposalSection">
                                                                <div className="Chat_sectionHeader">
                                                                        <div className="Chat_sectionTitle">{sectionObj[0]}</div>

                                                                        {!generateLoading && sectionObj[1].content && sectionObj[1].open && !isApproved ? <div className="Chat_sectionOptions" data-testid={`section-options-${i}`}>
                                                                                {!isEdit || (selectedSection === i && isEdit) ? <button type="button" onClick={() => handleEditClick(i)} style={(selectedSection === i && isEdit && regenerateSectionLoading) ? {pointerEvents: "none"} : {}} aria-label={`edit-section-${i}`}>
                                                                                        <img src={(selectedSection === i && isEdit) ? save : edit} />
                                                                                        <span>{(selectedSection === i && isEdit) ? "Save" : "Edit"}</span>
                                                                                </button> : "" }

                                                                                {selectedSection === i && isEdit ? <button type="button" onClick={() => setIsEdit(false)}>
                                                                                        <img src={cancel} />
                                                                                        <span>Cancel</span>
                                                                                </button> : "" }

                                                                                {!isEdit ?
                                                                                        <>
                                                                                                <button type="button" onClick={() => handleCopyClick(i, sectionObj[1].content)}>
                                                                                                        <img src={(selectedSection === i && isCopied) ? tick : copy} />
                                                                                                        <span>{(selectedSection === i && isCopied) ? "Copied" : "Copy"}</span>
                                                                                                </button>

                                                                                                <button type="button" className='Chat_sectionOptions_regenerate' onClick={() => handleRegenerateIconClick(i)} >
                                                                                                        <img src={regenerate} />
                                                                                                        <span>Regenerate</span>
                                                                                                </button>
                                                                                        </>
                                                                                : "" }
                                                                        </div> : ""}

                                                                        {sectionObj[1].content && !(isEdit && selectedSection === i) ? <div className={`Chat_expanderArrow ${sectionObj[1].open ? "" : "closed"}`} onClick={() => handleExpanderToggle(i)}>
                                                                                <img src={arrow} />
                                                                        </div> : ""}
                                                                </div>

                                                                {sectionObj[1].open || !sectionObj[1].content ? <div className='Chat_sectionContent'>
                                                                        {sectionObj[1].content ?
                                                                                (selectedSection === i && isEdit) ?
                                                                                        <textarea value={editorContent} onChange={e => setEditorContent(e.target.value)} aria-label={`editor for ${sectionObj[0]}`} />
                                                                                        :
                                                                                        <Markdown remarkPlugins={[remarkGfm]}>{sectionObj[1].content}</Markdown>
                                                                                :
                                                                                <div className='Chat_sectionContent_loading'>
                                                                                        <span className='submitButtonSpinner' />
                                                                                        <span className='Chat_sectionContent_loading'>Loading</span>
                                                                                </div>
                                                                        }
                                                                </div> : ""}
                                                        </div>
                                                )}
                                        </div>
                                </> : ""}
                        </main>

                        <dialog ref={dialogRef} className='Chat_regenerate'>
                                <header className='Chat_regenerate_header'>
                                        Regenerate — {Object.keys(proposal)[selectedSection]}
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

