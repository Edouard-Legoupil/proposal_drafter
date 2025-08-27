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

        const [projects, setProjects] = useState([])
        const [reviews, setReviews] = useState([])
        const [selectedTab, setSelectedTab] = useState('my_proposals')

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

        async function getReviews ()
        {
                const response = await fetch(`${API_BASE_URL}/proposals/reviews`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if(response.ok)
                {
                        const data = await response.json()
                        setReviews(data.reviews)
                }
        }

        useEffect(() => {
                sessionStorage.removeItem("proposal_id")
                getProjects()
                getReviews()
        }, [])

        async function handleProjectClick(e, proposal_id, isReview = false)
        {
                if(e.target.className !== "Dashboard_project_tripleDots" && !(e.target.className === "Project_optionsPopover_option_delete" || e.target.className === "Project_optionsPopover_option" && e.target.innerText === "Delete"))
                {
                        sessionStorage.setItem("proposal_id", proposal_id)
                        if (isReview) {
                                navigate(`/review/${proposal_id}`)
                        } else {
                                navigate("/chat")
                        }
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
                const source = selectedTab === 'my_proposals' ? projects : reviews;
                if(source && source.length)
                        setDisplayProjects(source.filter(project =>
                                project.project_title.toLowerCase().includes(searchTerm.toLowerCase())
                ))
        }, [projects, reviews, searchTerm, selectedTab])

        return  <Base>
                <div className="Dashboard">
                        <div className='Dashboard_top'>
                                <div className='Dashboard_label'>
                                        <img className='Dashboard_label_fileIcon' src={fileIcon} />
                                        Proposals
                                </div>
                                <CommonButton icon={createNew} label="Generate New Proposal" onClick={() => navigate("/chat")} />
                        </div>

                        <div className="Dashboard_tabs">
                                <button
                                        className={`Dashboard_tab ${selectedTab === 'my_proposals' ? 'active' : ''}`}
                                        onClick={() => setSelectedTab('my_proposals')}
                                >
                                        My Proposals
                                </button>
                                <button
                                        className={`Dashboard_tab ${selectedTab === 'for_review' ? 'active' : ''}`}
                                        onClick={() => setSelectedTab('for_review')}
                                >
                                        For Review
                                </button>
                        </div>

                        {displayProjects && displayProjects.filter(project => !project.is_sample).length ?
                                <div className='Dashboard_search'>
                                        <img src={search} />
                                        <input type="text" id="dashboard-search" name="dashboard-search" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className='Dashboard_search_input' placeholder='Search' />
                                </div>
                                :
                                <h3 className='Dashboard_sectionHeading'>{selectedTab === 'my_proposals' ? 'Sample proposals' : 'No proposals to review'}</h3>
                        }

                        <div className='Dashboard_projects'>
                                {displayProjects && displayProjects.filter(project => !project.is_sample).length ?
                                        displayProjects.filter(project => !project.is_sample).map((project, i) =>
                                                <Project
                                                        key={i}
                                                        projectIndex={i}
                                                        project_title={project.project_title}
                                                        proposal_id={project.proposal_id}
                                                        date={cleanedDate(project.updated_at)}
                                                        onClick={(e, proposal_id) => handleProjectClick(e, proposal_id, selectedTab === 'for_review')}
                                                        status={project.is_accepted}
                                                >
                                                        {project.summary}
                                                </Project>
                                        )
                                        :
                                        displayProjects.filter(project => project.is_sample).map((project, i) =>
                                                <Project
                                                        key={i}
                                                        projectIndex={i}
                                                        project_title={project.project_title}
                                                        proposal_id={project.proposal_id}
                                                        date={cleanedDate(project.updated_at)}
                                                        onClick={(e, proposal_id) => handleProjectClick(e, proposal_id, selectedTab === 'for_review')}
                                                        status={project.is_accepted}
                                                        sample
                                                >
                                                        {project.summary}
                                                </Project>
                                        )
                                }
                        </div>
                </div>
        </Base>
}
