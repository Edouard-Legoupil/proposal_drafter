import './Chat.css'

import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import fileIcon from "../../assets/images/chat-titleIcon.svg"
import arrow from "../../assets/images/expanderArrow.svg"
import generateIcon from "../../assets/images/generateIcon.svg"
import resultsIcon from "../../assets/images/Chat_resultsIcon.svg"
import edit from "../../assets/images/Chat_edit.svg"
import save from "../../assets/images/Chat_save.svg"
import copy from "../../assets/images/Chat_copy.svg"
import tick from "../../assets/images/Chat_copiedTick.svg"
import regenerate from "../../assets/images/Chat_regenerate.svg"
import regenerateClose from "../../assets/images/Chat_regenerateClose.svg"

export default function Chat (props)
{
        const [sidebarOpen, setSidebarOpen] = useState(false)

        const [titleName, setTitleName] = useState(props?.title ?? "Create Proposal")

        const [userPrompt, setUserPrompt] = useState("")

        const [form_expanded, setFormExpanded] = useState(true)
        const [formData, setFormData] = useState({
                "Project type": {
                        mandatory: true,
                        value: ""
                },
                "Secondary project type": {
                        mandatory: false,
                        value: ""
                },
                "Geographical Coverage": {
                        mandatory: true,
                        value: ""
                },
                "Executing agency": {
                        mandatory: true,
                        value: ""
                },
                "Beneficiaries": {
                        mandatory: true,
                        value: ""
                },
                "Partner(s)": {
                        mandatory: true,
                        value: ""
                },
                "Management site": {
                        mandatory: true,
                        value: ""
                },
                "Duration": {
                        mandatory: true,
                        value: ""
                },
                "Budget": {
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

                        for (const property in formData)
                                if(!formData[property].value && !(property === "Secondary project type"))
                                        setButtonEnable(false)
                }
                else
                        setButtonEnable(false)
        }, [userPrompt, formData])

        const [proposal, setProposal] = useState({
                "Summary": {
                        content: "",
                        open: true
                },
                "Rationale": {
                        content: "",
                        open: true
                },
                "Project Description": {
                        content: "",
                        open: true
                },
                "Partnerships and Coordination": {
                        content: "",
                        open: true
                },
                "Monitoring": {
                        content: "",
                        open: true
                },
                "Evaluation": {
                        content: "",
                        open: true
                }
        })
        const [latestSection, setLatestSection] = useState(Object.keys(proposal)[0])
        async function getSections()
        {
                let i
                for (i = 0; Object.keys(proposal)[i] !== latestSection; i++);

                setSelectedSection(i)
                proposalRef?.current?.children[i]?.scrollIntoView({behavior: "smooth"})

                for(let j = i; j < Object.keys(proposal).length; j++)
                {
                        const response = await fetch(`${API_BASE_URL}/process_section/${localStorage.getItem("session_id")}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        section: Object.keys(proposal)[j],
                                })
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
                                proposalRef?.current?.children[j]?.scrollIntoView({behavior: "smooth"})
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
                        if(titleName === "Create Proposal")
                                setTitleName("Generate Proposal")
                }
        // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [sidebarOpen])

        const [generateLoading, setGenerateLoading] = useState(false)
        const [generateLabel, setGenerateLabel] = useState("Generate")
        async function handleGenerateClick ()
        {
                setGenerateLoading(true)
                setFormExpanded(false)

                for (const section in proposal)
                        proposal[section].content = ""

                try
                {
                        const response = await fetch(`${API_BASE_URL}/store_base_data`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                        project_description: userPrompt,
                                        form_data: Object.fromEntries(Object.entries(formData).map(item => [item[0], item[1].value]))
                                })
                        })

                        if(response.ok)
                        {
                                const data = await response.json()
                                localStorage.setItem("session_id", data.session_id)
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

                const response = await fetch(`${API_BASE_URL}/regenerate_section/${localStorage.getItem("session_id")}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                section: Object.keys(proposal)[selectedSection],
                                concise_input: ip
                        })
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
                else
                        console.log("Error: ", response)

                setRegenerateInput("")
                dialogRef.current.close()
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
                                <div className='Dashboard_top'>
                                        <div className='Dashboard_label'>
                                                <img className='Dashboard_label_fileIcon' src={fileIcon} />
                                                {titleName}
                                        </div>
                                </div>

                                <div className="Chat_inputArea">
                                        <textarea value={userPrompt} onChange={e => setUserPrompt(e.target.value)} placeholder='Enter your project requirements' className='Chat_inputArea_prompt' />

                                        <span onClick={() => setFormExpanded(p => !p)} className={`Chat_inputArea_additionalDetails ${form_expanded && "expanded"}`}>
                                                Additional Details
                                                <img src={arrow} alt="Arrow" />
                                        </span>

                                        {form_expanded ? <form className='Chat_form'>
                                                {Object.entries(formData).map((fieldObj, i) => <div key={i} className='Chat_form_inputContainer'>
                                                        <label className='Chat_form_inputLabel'>{fieldObj[0]} <span className={`Chat_form_input_mandatoryAsterisk ${!fieldObj[1].mandatory ? "hidden" : ""}`}>*</span></label>
                                                        <input type="text" className='Chat_form_input' placeholder={`Enter ${fieldObj[0]}`} value={fieldObj[1].value} onChange={e => handleFormInput(e, fieldObj[0])} />
                                                </div>)}
                                        </form> : ""}

                                        <div className="Chat_inputArea_buttonContainer">
                                                <CommonButton onClick={handleGenerateClick} icon={generateIcon} label={generateLabel} loading={generateLoading} loadingLabel={generateLabel === "Generate" ? "Generating" : "Regenerating"} disabled={!buttonEnable}/>
                                        </div>
                                </div>

                                {sidebarOpen ? <>
                                        <div className='Dashboard_top' style={{marginTop: "30px"}}>
                                                <div className='Dashboard_label'>
                                                        <img className='Dashboard_label_fileIcon' src={resultsIcon} />
                                                        Results
                                                </div>
                                        </div>

                                        <div ref={proposalRef} className="Chat_proposalContainer">
                                                {Object.entries(proposal).map((sectionObj, i) =>
                                                        <div key={i} className="Chat_proposalSection">
                                                                <div className="Chat_sectionHeader">
                                                                        <div className="Chat_sectionTitle">{sectionObj[0]}</div>

                                                                        <div className="Chat_sectionOptions">
                                                                                <button type="button" onClick={() => handleEditClick(i)} style={(selectedSection === i && isEdit && regenerateSectionLoading) ? {pointerEvents: "none"} : {}}>
                                                                                        <img src={(selectedSection === i && isEdit) ? save : edit} />
                                                                                        <span>{(selectedSection === i && isEdit) ? "Save" : "Edit"}</span>
                                                                                </button>

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
                                                                        </div>

                                                                        <div className={`Chat_expanderArrow ${sectionObj[1].open ? "" : "closed"}`} onClick={() => handleExpanderToggle(i)}>
                                                                                <img src={arrow} />
                                                                        </div>
                                                                </div>

                                                                {sectionObj[1].open ? <div className='Chat_sectionContent'>
                                                                        {sectionObj[1].content ?
                                                                                (selectedSection === i && isEdit) ?
                                                                                        <textarea value={editorContent} onChange={e => setEditorContent(e.target.value)}/>
                                                                                        :
                                                                                        <Markdown>{sectionObj[1].content}</Markdown>
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
