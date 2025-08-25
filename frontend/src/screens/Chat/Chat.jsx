import './Chat.css'

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'

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

        const [form_expanded, setFormExpanded] = useState(true)
        const [formData, setFormData] = useState({

                "Project title": {
                        mandatory: true,
                        value: ""
                },
                "Main Outcome": {
                        mandatory: true,
                        value: ""
                },
                "Secondary Outcome": {
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
                "Beneficiaries Profile": {
                        mandatory: true,
                        value: ""
                },
                "Duration": {
                        mandatory: true,
                        value: ""
                },            
                "Budget Range": {
                        mandatory: true,
                        value: ""
                },
                "Targeted Donor": {
                        mandatory: true,
                        value: ""
                },
                "Potential Implementing Partner": {
                        mandatory: false,
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

                        for (const property in formData)
                                if(!formData[property].value && !(property === "Secondary Outcome"))
                                        setButtonEnable(false)
                }
                else
                        setButtonEnable(false)
        }, [userPrompt, formData])

        // const [proposal, setProposal] = useState({
        //         "Summary": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Rationale": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Project Description": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Partnerships and Coordination": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Monitoring": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Evaluation": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Results Matrix": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Work Plan": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Budget": {
        //                 content: "",
        //                 open: true
        //         },
        //         "Annex 1. Risk Assessment Plan": {
        //                 content: "",
        //                 open: true
        //         }
        // })

        // Load proposal sections from the API...
        const [proposal, setProposal] = useState({})

        useEffect(() => {
                fetch(`${API_BASE_URL}/sections`)
                  .then(res => res.json())
                  .then(data => {
                    const sectionState = {}
                    data.sections.forEach(section => {
                      sectionState[section.section_name] = {
                        content: "",
                        open: true
                      }
                    })
                    setProposal(sectionState)
                  })
                  .catch(err => console.error("Failed to load sections:", err))
              }, [])
               

        async function getSections(latestSection = Object.keys(proposal)[0])
        {
                let i
                for (i = 0; Object.keys(proposal)[i] !== latestSection; i++);

                setSelectedSection(i)
                proposalRef?.current?.children[i]?.scrollIntoView({behavior: "smooth"})

                for(let j = i; j < Object.keys(proposal).length; j++)
                {
                        const response = await fetch(`${API_BASE_URL}/process_section/${sessionStorage.getItem("session_id")}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        section: Object.keys(proposal)[j],
                                        proposal_id: sessionStorage.getItem("proposal_id")
                                }),
                                credentials: 'include'
                        })

                        if(response.ok) {
                                const data = await response.json()

                                setProposal(p => ({
                                        ...p,
                                        [Object.keys(p)[j]]: { // We have index, not key, hence
                                                open: Object.values(p)[j].open,
                                                content: data.generated_text
                                        }
                                }))
                                setSelectedSection(j)
                                const el = proposalRef.current?.children[j];
                                if (typeof el?.scrollIntoView === 'function') {
                                        el.scrollIntoView({ behavior: 'smooth' });
                                }
                        }

                        else
                                console.log(response)
                }

                setGenerateLoading(false)
                setGenerateLabel("Regenerate")
        }

        useEffect(() => {
                if(sidebarOpen)
                {
                        if(titleName === "Generate Draft Proposal")
                                setTitleName("Generate Draft Proposal")
                }
        // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [sidebarOpen])

        const [generateLoading, setGenerateLoading] = useState(false)
        const [generateLabel, setGenerateLabel] = useState("Generate")
        async function saveDraft ()
        {
                setGenerateLoading(true)
                setFormExpanded(false)

                for (const section in proposal)
                        proposal[section].content = ""

                try
                {
                        const donor = formData["Targeted Donor"].value;
                        const template_name = donor === "CERF"
                                ? "unhcr_cerf_proposal_template.json"
                                : donor === "ECHO"
                                ? "iom_proposal_template.json"
                                : "unhcr_cerf_proposal_template.json";

                        const response = await fetch(`${API_BASE_URL}/save-draft`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        session_id: sessionStorage.getItem("session_id"),
                                        project_description: userPrompt,
                                        form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
                                        template_name: template_name
                                }),
                                credentials: 'include'
                        })

                        if(response.ok)
                        {
                                const data = await response.json()
                                sessionStorage.setItem("proposal_id", data.proposal_id)
                                setSidebarOpen(true)
                                getSections()
                        }
                        else
                        {
                                setGenerateLoading(false)
                                setGenerateLabel("Regenerate")
                                console.log("Error: ", response)
                        }
                }
                catch (error)
                {
                        setGenerateLoading(false)
                        setGenerateLabel("Regenerate")
                        console.log("Error", error)
                }
        }
        async function handleGenerateClick ()
        {
                setGenerateLoading(true)
                setFormExpanded(false)

                for (const section in proposal)
                        proposal[section].content = ""

                try
                {
                        const donor = formData["Targeted Donor"].value;
                        const template_name = donor === "CERF"
                                ? "unhcr_cerf_proposal_template.json"
                                : donor === "ECHO"
                                ? "iom_proposal_template.json"
                                : "unhcr_cerf_proposal_template.json";

                        const response = await fetch(`${API_BASE_URL}/store_base_data`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        project_description: userPrompt,
                                        form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value])),
                                        template_name: template_name
                                }),
                                credentials: 'include'
                        })

                        if(response.ok)
                        {
                                const data = await response.json()
                                sessionStorage.setItem("session_id", data.session_id)
                                saveDraft()
                        }
                        else if(response.status === 401)
                        {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                        else
                        {
                                setGenerateLoading(false)
                                setGenerateLabel("Regenerate")
                                console.log("Error: ", response)
                        }
                }
                catch (error)
                {
                        setGenerateLoading(false)
                        setGenerateLabel("Regenerate")
                        console.log("Error", error)
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
                                proposal_id: sessionStorage.getItem("proposal_id")
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
        function handleEditClick (section)
        {
                if(!isEdit)
                {
                        setSelectedSection(section)
                        setIsEdit(true)
                        setEditorContent(Object.values(proposal)[section].content)
                }
                else
                {
                        setProposal(p => ({
                                ...p,
                                [Object.keys(p)[selectedSection]]: {
                                        ...Object.values(p)[selectedSection],
                                        content: ""
                                }
                        }))
                        handleRegenerateButtonClick("Message to the AI assistant: The below content is what was manually entered by the user. ENSURE it is within the **specified word limit** for this section, AT ALL COSTS. If it is, leave it be, else COMPULSORILY bring it **BELOW** the word limit. Even a few words above the limit are NOT ACCEPTABLE by our system. You can go so far as to omit content if need be in order to fit it within the word limit. Even tightening up the language via very short and concise sentences and bullet points will also be acceptable AND IN FACT ENCOURAGED.  \n\n" + editorContent)
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

                                setProposal(p => Object.fromEntries(Object.entries(data.generated_sections).map(section =>
                                        [section[0], {
                                                content: section[1],
                                                open: p[section[0]].open
                                        }]
                                )))

                                setIsApproved(data.is_accepted)

                                setSidebarOpen(true)

                                if(!data.is_accepted && !data.generated_sections["Evaluation"])
                                {
                                        setGenerateLoading(true)
                                        setFormExpanded(false)

                                        let i
                                        for(i = 0; Object.entries(data.generated_sections)[i][1]; i++);

                                        getSections(Object.entries(data.generated_sections)[i][0])
                                }
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
                        link.download = formData["Project title"].value ?? "proposal" + "." + format;
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
                        getContent()
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
                                                        <textarea value={userPrompt} onChange={e => setUserPrompt(e.target.value)} placeholder='Provide as much details as possible on your initial project idea!' className='Chat_inputArea_prompt' />

                                                        <span onClick={() => setFormExpanded(p => !p)} className={`Chat_inputArea_additionalDetails ${form_expanded && "expanded"}`}>
                                                                Specify Parameters
                                                                <img src={arrow} alt="Arrow" />
                                                        </span>

                                                        {form_expanded ? <form className='Chat_form'>


                                                                {Object.entries(formData).map((fieldObj, i) => {
                                                                const label = fieldObj[0];
                                                                    const isDropdown =
                                                                        label === "Main Outcome" ||
                                                                        label === "Secondary Outcome" ||
                                                                        label === "Duration" ||
                                                                        label === "Targeted Donor" ||
                                                                        label === "Budget Range" ||
                                                                        label === "Geographical Scope" ||
                                                                        label === "Duration";
                                                                const datalistId = `datalist_${label.replaceAll(' ', '_')}`;
                                                                const options = label === "Main Outcome"
                                                                        ? [    "OA1-Access/Documentation",
                                                                               "OA2-Status",
                                                                                "OA3-Protection Policy",
                                                                                "OA4-GBV",
                                                                                "OA5-Child protection",
                                                                                "OA6-Justice",
                                                                                "OA7-Community",
                                                                                "OA8-Well-Being",
                                                                                "OA9-Housing",
                                                                                "OA10-Health",
                                                                                "OA11-Education",
                                                                                "OA12-WASH",
                                                                                "OA13-Livelihoods",
                                                                                "OA14-Return",
                                                                                "OA15-Resettlement",
                                                                                "OA16-Integrate"  ]
                                                                        : label === "Secondary Outcome"
                                                                        ? [    "OA1-Access/Documentation",
                                                                               "OA2-Status",
                                                                                "OA3-Protection Policy",
                                                                                "OA4-GBV",
                                                                                "OA5-Child protection",
                                                                                "OA6-Justice",
                                                                                "OA7-Community",
                                                                                "OA8-Well-Being",
                                                                                "OA9-Housing",
                                                                                "OA10-Health",
                                                                                "OA11-Education",
                                                                                "OA12-WASH",
                                                                                "OA13-Livelihoods",
                                                                                "OA14-Return",
                                                                                "OA15-Resettlement",
                                                                                "OA16-Integrate"  ]
                                                                        : label === "Duration"
                                                                        ? ["1 month", "3 months", "6 months", "12 months", "18 months", "24 months", "30 months", "36 months"]
                                                                        : label === "Targeted Donor"
                                                                        ? ["CERF", "ECHO"]
                                                                        : label === "Budget Range"
                                                                        ? ["50k$", "100k$","250k$","500k$","1M$","2M$","5M$","10M$","15M$","25M$"]         
                                                                        : label === "Geographical Scope"
                                                                        ? ["One Area", "One Country Operation", "Multiple Country","One Region","Route-Based-Approach","Global"]         
                                                                        : [];

                                                                return (
                                                                        <div key={i} className='Chat_form_inputContainer'>
                                                                        <label className='Chat_form_inputLabel' htmlFor={`Chat_form_input_${label.replaceAll(' ', '')}`}>
                                                                                {label}
                                                                                <span className={`Chat_form_input_mandatoryAsterisk ${!fieldObj[1].mandatory ? "hidden" : ""}`}>*</span>
                                                                        </label>

                                                                        {isDropdown ? (
                                                                                <>
                                                                                <input
                                                                                        list={datalistId}
                                                                                        className='Chat_form_input'
                                                                                        id={`Chat_form_input_${label.replaceAll(' ', '')}`}
                                                                                        placeholder={`Enter or select ${label}`}
                                                                                        value={fieldObj[1].value}
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
                                                                                id={`Chat_form_input_${label.replaceAll(' ', '')}`}
                                                                                placeholder={`Enter ${label}`}
                                                                                value={fieldObj[1].value}
                                                                                onChange={e => handleFormInput(e, label)}
                                                                                />
                                                                        )}
                                                                        </div>
                                                                );
                                                                })}


                                                        </form> : ""}

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

                                                {proposal.Evaluation.content ? <div className='Chat_exportButtons'>
                                                        <button type="button" onClick={() => handleExport("docx")}>
                                                                <img src={word_icon} />
                                                                Download .DOCX
                                                        </button>
                                                        <button type="button" onClick={() => handleExport("pdf")}>
                                                                <img src={pdf_icon} />
                                                                Download .PDF
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
                                                <textarea value={regenerateInput} onChange={e => setRegenerateInput(e.target.value)} className='Chat_inputArea_prompt' />

                                                <div className="Chat_inputArea_buttonContainer" style={{marginTop: "20px"}}>
                                                        <CommonButton icon={generateIcon} onClick={() => handleRegenerateButtonClick()} label="Regenerate" loading={regenerateSectionLoading} loadingLabel="Regenerating" disabled={!regenerateInput} />
                                                </div>
                                        </section>
                                </main>
                        </dialog>
                </div>
        </Base>
}
