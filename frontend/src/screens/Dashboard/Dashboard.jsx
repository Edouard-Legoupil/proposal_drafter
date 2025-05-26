import './Dashboard.css'

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import Project from './components/Project/Project'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import createNew from "../../assets/images/dashboard-createnew.svg"
import fileIcon from "../../assets/images/dashboard-fileIcon.svg"
import search from "../../assets/images/dashboard-search.svg"

export default function Dashboard ()
{
        const navigate = useNavigate()

        const [projects, setProjects] = useState()
        async function getProjects ()
        {
                const response = await fetch(`${API_BASE_URL}/list-drafts`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if(response.ok)
                {
                        const data = await response.json()
                        setProjects(data.drafts)
                }
        }
        useEffect(() => {
                sessionStorage.removeItem("proposal_id")
                getProjects()
        }, [])

        async function handleProjectClick(e, proposal_id)
        {
                if(e.target.className !== "Dashboard_project_tripleDots" && !(e.target.className === "Project_optionsPopover_option_delete" || e.target.className === "Project_optionsPopover_option" && e.target.innerText === "Delete"))
                {
                        sessionStorage.setItem("proposal_id", proposal_id)
                        navigate("/chat")
                }
        }

        function cleanedDate (date)
        {
                const cleaned = date.replace(/\.\d+/, "");
                const data = new Date(cleaned);

                const readable = data.toLocaleString();
                return readable
        }

        const [searchTerm, setSearchTerm] = useState("")
        const [displayProjects, setDisplayProjects] = useState([])
        useEffect(() => {
                if(projects && projects.length)
                        setDisplayProjects(projects.filter(project =>
                                project.project_title.toLowerCase().includes(searchTerm.toLowerCase())
                ))
        }, [projects, searchTerm])

        return  <Base>
                <div className="Dashboard">
                        <div className='Dashboard_top'>
                                <div className='Dashboard_label'>
                                        <img className='Dashboard_label_fileIcon' src={fileIcon} />
                                        Proposals
                                </div>
                                <CommonButton icon={createNew} label="Create New Proposal" onClick={() => navigate("/chat")} />
                        </div>

                        {projects && projects.length ?
                                <div className='Dashboard_search'>
                                        <img src={search} />
                                        <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className='Dashboard_search_input' placeholder='Search' />
                                </div>
                                :
                                ""
                        }

                        <div className='Dashboard_projects'>
                                {displayProjects && displayProjects.length ?
                                        displayProjects.map((project, i) =>
                                                <Project
                                                        key={i}
                                                        projectIndex={i}
                                                        project_title={project.project_title}
                                                        proposal_id={project.proposal_id}
                                                        date={cleanedDate(project.updated_at)}
                                                        onClick={handleProjectClick}
                                                        status={project.is_accepted}
                                                >
                                                        {project.summary}
                                                </Project>
                                        )
                                        :
                                        <h2 className='Dashboard_noDraftsNotice'>No drafts found.</h2>
                                }
                        </div>
                </div>
        </Base>
}
