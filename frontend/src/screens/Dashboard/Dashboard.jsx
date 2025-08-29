import './Dashboard.css'

import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import Base from '../../components/Base/Base'
import Project from './components/Project/Project'
import KnowledgeCard from './components/KnowledgeCard/KnowledgeCard'
import MetricsDashboard from './components/MetricsDashboard/MetricsDashboard'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

export default function Dashboard ()
{
        const navigate = useNavigate()

        const [projects, setProjects] = useState([])
        const [reviews, setReviews] = useState([])
        const [knowledgeCards, setKnowledgeCards] = useState([])
        const [selectedTab, setSelectedTab] = useState('proposals')
        const [isFilterModalOpen, setIsFilterModalOpen] = useState(false)

        const tabRefs = {
                proposals: useRef(null),
                reviews: useRef(null),
                knowledge: useRef(null),
                metrics: useRef(null)
        };

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

        async function getKnowledgeCards ()
        {
                const response = await fetch(`${API_BASE_URL}/knowledge-cards`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if(response.ok)
                {
                        const data = await response.json()
                        setKnowledgeCards(data.knowledge_cards)
                }
        }

        useEffect(() => {
                sessionStorage.removeItem("proposal_id")
                getProjects()
                getReviews()
                getKnowledgeCards()
        }, [])

        async function handleProjectClick(e, proposal_id, isReview = false)
        {
                // This logic might need to be adapted depending on the final card structure in Project.jsx
                sessionStorage.setItem("proposal_id", proposal_id)
                if (isReview) {
                        navigate(`/review/${proposal_id}`)
                } else {
                        navigate("/chat")
                }
        }

        function cleanedDate (date)
        {
                const cleaned = date.replace(/\.\d+/, "");
                const data = new Date(cleaned);
                const readable = data.toISOString().split('T')[0];
                return readable
        }

        const [searchTerm, setSearchTerm] = useState("")
        const [displayProjects, setDisplayProjects] = useState([])
        useEffect(() => {
                let source = [];
                if (selectedTab === 'proposals') {
                    source = projects;
                } else if (selectedTab === 'reviews') {
                    source = reviews;
                }

                if (source && source.length > 0) {
                    setDisplayProjects(source.filter(project =>
                        project.project_title.toLowerCase().includes(searchTerm.toLowerCase())
                    ));
                } else {
                    setDisplayProjects([]); // Reset if source is empty or not applicable
                }
            }, [projects, reviews, searchTerm, selectedTab]);

        const activateTab = (tabId) => {
                setSelectedTab(tabId);
        }

        const onTabKeydown = (e) => {
                const tabs = ['proposals', 'reviews'];
                const i = tabs.indexOf(selectedTab);
                let nextIndex = i;
                if (e.key === 'ArrowLeft') nextIndex = (i - 1 + tabs.length) % tabs.length;
                if (e.key === 'ArrowRight') nextIndex = (i + 1) % tabs.length;
                if (e.key === 'Home') nextIndex = 0;
                if (e.key === 'End') nextIndex = tabs.length - 1;

                if (nextIndex !== i) {
                        const nextTabId = tabs[nextIndex];
                        activateTab(nextTabId);
                        tabRefs[nextTabId].current.focus();
                }
        }

        return  <Base>
                <div className="Dashboard">
                        <header className="Dashboard_top">
                                <div className='Dashboard_label'>
                                     Draft Smart Proposal with AI, Curated Knowledge and Peer Review. 
                                         
                                </div> 
                        </header>  

                        <nav className="tabs" aria-label="Dashboard sections">
                                <div role="tablist" aria-orientation="horizontal" className="tablist">
                                        <button
                                                id="proposals-tab"
                                                ref={tabRefs.proposals}
                                                role="tab"
                                                aria-selected={selectedTab === 'proposals'}
                                                aria-controls="proposals-panel"
                                                className="tab"
                                                data-tab="proposals"
                                                onClick={() => activateTab('proposals')}
                                                onKeyDown={onTabKeydown}
                                                tabIndex={selectedTab === 'proposals' ? 0 : -1}
                                        >
                                                 <i className="fa-solid fa-file-lines" aria-hidden="true"></i>  My Proposals 
                                        </button>
                                        <button
                                                id="knowledge-tab"
                                                ref={tabRefs.reviews}
                                                role="tab"
                                                aria-selected={selectedTab === 'knowledge'}
                                                aria-controls="knowledge-panel"
                                                className="tab"
                                                data-tab="knowledge"
                                                onClick={() => activateTab('knowledge')}
                                                onKeyDown={onTabKeydown}
                                                tabIndex={selectedTab === 'knowledge' ? 0 : -1}
                                        >
                                                <i className="fa-solid fa-book-open" aria-hidden="true"></i>  Knowledge Card 
                                        </button>
                                        <button
                                                id="reviews-tab"
                                                ref={tabRefs.reviews}
                                                role="tab"
                                                aria-selected={selectedTab === 'reviews'}
                                                aria-controls="reviews-panel"
                                                className="tab"
                                                data-tab="reviews"
                                                onClick={() => activateTab('reviews')}
                                                onKeyDown={onTabKeydown}
                                                tabIndex={selectedTab === 'reviews' ? 0 : -1}
                                        >
                                                <i className="fa-solid fa-magnifying-glass" aria-hidden="true"></i>  Pending Reviews 
                                        </button>

                                        <button
                                                id="metrics-tab"
                                                ref={tabRefs.reviews}
                                                role="tab"
                                                aria-selected={selectedTab === 'metrics'}
                                                aria-controls="metrics-panel"
                                                className="tab"
                                                data-tab="metrics"
                                                onClick={() => activateTab('metrics')}
                                                onKeyDown={onTabKeydown}
                                                tabIndex={selectedTab === 'metrics' ? 0 : -1}
                                        >
                                                <i className="fa-solid fa-gauge-high" aria-hidden="true"></i>  Metrics 
                                        </button>
                                </div>
                        </nav>

                        {selectedTab !== 'metrics' &&
                                <div className="Dashboard_search" role="search">
                                        <i className="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
                                        <label htmlFor="quick-search" className="sr-only">Quick search</label>
                                        <input id="quick-search" type="text" placeholder="Quick search..." className="Dashboard_search_input" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                                        <button className="filter-btn" id="filter-btn" aria-label="Open filters" onClick={() => setIsFilterModalOpen(true)}>
                                                <i className="fa-solid fa-sliders"></i>
                                        </button>
                                </div>
                        }

                        <section id="proposals-panel" role="tabpanel" aria-labelledby="proposals-tab" className={`tab-panel ${selectedTab === 'proposals' ? 'active' : ''}`} hidden={selectedTab !== 'proposals'}>
                                <div className="Dashboard_projects" id="proposals-grid">
                                        <div className="card card--cta">
                                                <button className="btn" type="button" aria-label="Start a new proposal" onClick={() => navigate("/chat")}>Start New Proposal</button>
                                        </div>
                                        {displayProjects && displayProjects.map((project, i) =>
                                                <Project
                                                        key={i}
                                                        project={project}
                                                        date={cleanedDate(project.updated_at)}
                                                        onClick={(e) => handleProjectClick(e, project.proposal_id, false)}
                                                />
                                        )}
                                </div>
                        </section>

                        <section id="knowledge-panel" role="tabpanel" aria-labelledby="knowledge-tab" className={`tab-panel ${selectedTab === 'knowledge' ? 'active' : ''}`} hidden={selectedTab !== 'knowledge'}>
                                <div className="Dashboard_projects" id="knowledge-grid">
                                        <div className="card card--cta">
                                                <button className="btn" type="button" aria-label="Start a new knowledge card" onClick={() => navigate("/knowledge-card/new")}>Create New Knowledge Card</button>
                                        </div>
                                        {knowledgeCards && knowledgeCards.map((card, i) =>
                                                <KnowledgeCard
                                                        key={i}
                                                        card={card}
                                                        onClick={() => navigate(`/knowledge-card/${card.id}`)}
                                                />
                                        )}
                                </div>
                        </section>

                        <section id="reviews-panel" role="tabpanel" aria-labelledby="reviews-tab" className={`tab-panel ${selectedTab === 'reviews' ? 'active' : ''}`} hidden={selectedTab !== 'reviews'}>
                                <div className="Dashboard_projects" id="reviews-grid">
                                {displayProjects && displayProjects.map((review, i) =>
                                        <Project
                                                key={i}
                                                project={review}
                                                date={cleanedDate(review.updated_at)}
                                                onClick={(e) => handleProjectClick(e, review.proposal_id, true)}
                                                isReview={true}
                                        />
                                )}
                                </div>
                        </section>

                        <section id="metrics-panel" role="tabpanel" aria-labelledby="metrics-tab" className={`tab-panel ${selectedTab === 'metrics' ? 'active' : ''}`} hidden={selectedTab !== 'metrics'}>
                                <MetricsDashboard />
                        </section>
                </div>

                <div className={`modal ${isFilterModalOpen ? 'active' : ''}`} id="filter-modal" role="dialog" aria-modal="true" aria-labelledby="filter-title">
                        <div className="modal-content">
                                <span className="modal-close" onClick={() => setIsFilterModalOpen(false)}>&times;</span>
                                <h3 id="filter-title">Apply Content Filters</h3>

                                <div className="filter-section" data-tab="proposals" hidden={selectedTab !== 'proposals'}>
                                        <label htmlFor="status-filter">Status</label>
                                        <select id="status-filter">
                                                <option value="">All</option>
                                                <option value="draft">Drafting</option>
                                                <option value="review">Pending Review</option>
                                                <option value="submission">Pending Submission</option>
                                                <option value="submitted">Submitted</option>
                                                <option value="approved">Approved</option>
                                        </select>

                                        {/* Add other filters as needed */}
                                </div>

                                <div className="filter-section" data-tab="reviews" hidden={selectedTab !== 'reviews'}>
                                        <label htmlFor="deadline-filter">Deadline before</label>
                                        <input type="date" id="deadline-filter" />
                                </div>
                        </div>
                </div>
        </Base>
}
