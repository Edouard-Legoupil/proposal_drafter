import './Dashboard.css'

import { useEffect, useState, useRef, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import Base from '../../components/Base/Base'
import Project from './components/Project/Project'
import KnowledgeCard from './components/KnowledgeCard/KnowledgeCard'
import MetricsDashboard from './components/MetricsDashboard/MetricsDashboard'
import SingleSelectUserModal from '../../components/SingleSelectUserModal/SingleSelectUserModal'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function Dashboard() {
        const navigate = useNavigate()
        const { folder, subfolder, filter } = useParams()

        const [userRoles, setUserRoles] = useState([]);
        const [currentUser, setCurrentUser] = useState(null);
        const [projects, setProjects] = useState([])
        const [allProposals, setAllProposals] = useState([])
        const [reviews, setReviews] = useState([])
        const [knowledgeCards, setKnowledgeCards] = useState([])
        const [displayKnowledgeCards, setDisplayKnowledgeCards] = useState(knowledgeCards)
        const [selectedTab, setSelectedTab] = useState('proposals')
        const [isFilterModalOpen, setIsFilterModalOpen] = useState(false)
        const [isTransferModalOpen, setIsTransferModalOpen] = useState(false)
        const [transferProposalId, setTransferProposalId] = useState(null)
        const [users, setUsers] = useState([])
        const [knowledgeCardTypeFilter, setKnowledgeCardTypeFilter] = useState('')
        const [statusFilter, setStatusFilter] = useState('')
        const [duplicateCardIds, setDuplicateCardIds] = useState(new Set());
        const [viewMode, setViewMode] = useState('vignette')
        const [sortConfig, setSortConfig] = useState({ key: 'updated_at', direction: 'desc' });
        const [teams, setTeams] = useState([]);

        async function getProfile() {
                try {
                        const response = await fetch(`${API_BASE_URL}/profile`, {
                                method: 'GET',
                                headers: { 'Content-Type': 'application/json' },
                                credentials: 'include'
                        });

                        if (response.ok) {
                                const data = await response.json();
                                setCurrentUser(data.user);
                                setUserRoles(data.user?.roles || []);
                        }
                } catch (err) {
                        console.error("Profile fetch error", err);
                }
        }

        async function getProjects() {
                const url = subfolder === 'deleted'
                        ? `${API_BASE_URL}/list-drafts?status=deleted`
                        : `${API_BASE_URL}/list-drafts`;

                const response = await fetch(url, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setProjects(data.drafts)
                }
        }

        async function fetchTeams() {
                try {
                        const response = await fetch(`${API_BASE_URL}/teams`);
                        const data = await response.json();
                        if (data.teams) {
                                setTeams(data.teams);
                        }
                } catch (error) {
                        console.error('Error fetching teams:', error);
                }
        }

        async function getReviews() {
                const response = await fetch(`${API_BASE_URL}/proposals/reviews`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setReviews(data.reviews)
                }
        }

        async function getKnowledgeCards() {
                const response = await fetch(`${API_BASE_URL}/knowledge-cards`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setKnowledgeCards(data.knowledge_cards)
                }
        }

        async function getAllProposals() {
                const response = await fetch(`${API_BASE_URL}/list-all-proposals`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setAllProposals(data.proposals)
                }
        }

        async function getUsers() {
                const response = await fetch(`${API_BASE_URL}/users`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        const data = await response.json()
                        setUsers((data || []).map(user => ({ id: user.id, name: user.name })))
                }
        }

        useEffect(() => {
                sessionStorage.removeItem("proposal_id")
                getProfile();
                getProjects()
                getReviews()
                getKnowledgeCards()
                getUsers()
                getAllProposals()
                fetchTeams()
        }, [])

        useEffect(() => {
                if (folder === 'proposals') {
                        getProjects();
                }
        }, [subfolder]);

        useEffect(() => {
                if (folder) {
                        setSelectedTab(folder);
                } else {
                        setSelectedTab('proposals');
                }

                if (folder === 'proposals') {
                        setStatusFilter(subfolder === 'all' ? '' : subfolder || '');
                        setKnowledgeCardTypeFilter('');
                } else if (folder === 'knowledge') {
                        setKnowledgeCardTypeFilter(subfolder === 'all' ? '' : subfolder || '');
                        setStatusFilter('');
                } else {
                        setStatusFilter('');
                        setKnowledgeCardTypeFilter('');
                }
        }, [folder, subfolder]);

        async function handleProjectClick(e, proposal_id, isReview = false) {
                sessionStorage.setItem("proposal_id", proposal_id)
                if (isReview || selectedTab === 'other') {
                        navigate(`/review/proposal/${proposal_id}`)
                } else {
                        navigate(`/chat/${proposal_id}`)
                }
        }

        async function handleDeleteProject(proposal_id) {
                const response = await fetch(`${API_BASE_URL}/proposals/${proposal_id}/delete`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        getProjects()
                        getReviews()
                        getAllProposals()
                }
        }

        async function handleRestoreProject(proposal_id) {
                const response = await fetch(`${API_BASE_URL}/proposals/${proposal_id}/restore`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if (response.ok) {
                        getProjects()
                        getAllProposals()
                }
        }

        function handleTransferOwnership(proposal_id) {
                setTransferProposalId(proposal_id)
                setIsTransferModalOpen(true)
        }

        async function confirmTransfer(new_owner_id) {
                const response = await fetch(`${API_BASE_URL}/proposals/${transferProposalId}/transfer`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ new_owner_id }),
                        credentials: 'include'
                })

                if (response.ok) {
                        getProjects()
                        getReviews()
                        setIsTransferModalOpen(false)
                        setTransferProposalId(null)
                }
        }

        function cleanedDate(date) {
                if (!date) return 'N/A';
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
                } else if (selectedTab === 'other') {
                        source = allProposals;
                }

                if (source && source.length > 0) {
                        let filteredProjects = source.filter(project =>
                                project.project_title.toLowerCase().includes(searchTerm.toLowerCase())
                        );

                        if (statusFilter) {
                                filteredProjects = filteredProjects.filter(project => project.status === statusFilter);
                        }

                        if (selectedTab === 'other' && subfolder && subfolder !== 'all') {
                                filteredProjects = filteredProjects.filter(project => project.team_id === subfolder);
                                if (filter && filter !== 'all') {
                                        filteredProjects = filteredProjects.filter(project => project.status === filter);
                                }
                        }

                        if (selectedTab === 'reviews') {
                                filteredProjects = filteredProjects.filter(project => project.status !== 'deleted');
                        }

                        setDisplayProjects(filteredProjects);
                } else {
                        setDisplayProjects([]);
                }
        }, [projects, reviews, allProposals, searchTerm, selectedTab, statusFilter, subfolder, filter]);

        useEffect(() => {
                let filteredCards = knowledgeCards;

                if (knowledgeCardTypeFilter) {
                        filteredCards = filteredCards.filter(card => {
                                if (knowledgeCardTypeFilter === 'donor') return card.donor_name;
                                if (knowledgeCardTypeFilter === 'outcome') return card.outcome_name;
                                if (knowledgeCardTypeFilter === 'field_context') return card.field_context_name;
                                return true;
                        });
                }

                if (searchTerm) {
                        filteredCards = filteredCards.filter(card =>
                                (card.summary && card.summary.toLowerCase().includes(searchTerm.toLowerCase())) ||
                                (card.donor_name && card.donor_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
                                (card.outcome_name && card.outcome_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
                                (card.field_context_name && card.field_context_name.toLowerCase().includes(searchTerm.toLowerCase()))
                        );
                }

                if (userRoles && userRoles.includes('knowledge manager donors')) {
                        const donorCards = filteredCards.filter(card => card.donor_name);
                        const otherCards = filteredCards.filter(card => !card.donor_name);
                        filteredCards = [...donorCards, ...otherCards];
                }

                setDisplayKnowledgeCards(filteredCards);
        }, [knowledgeCards, searchTerm, knowledgeCardTypeFilter, userRoles]);

        useEffect(() => {
                const findDuplicates = () => {
                        if (knowledgeCards.length === 0) return;
                        const groups = {};
                        knowledgeCards.forEach(card => {
                                let key = null;
                                if (card.donor_id) key = `donor-${card.donor_id}`;
                                else if (card.outcome_id) key = `outcome-${card.outcome_id}`;
                                else if (card.field_context_id) key = `field_context-${card.field_context_id}`;

                                if (key) {
                                        if (!groups[key]) {
                                                groups[key] = [];
                                        }
                                        groups[key].push(card.id);
                                }
                        });

                        const duplicates = new Set();
                        for (const key in groups) {
                                if (groups[key].length > 1) {
                                        groups[key].forEach(id => duplicates.add(id));
                                }
                        }
                        setDuplicateCardIds(duplicates);
                };

                findDuplicates();
        }, [knowledgeCards]);

        async function handleDeleteKnowledgeCard(cardId) {
                const response = await fetch(`${API_BASE_URL}/knowledge-cards/${cardId}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                });

                if (response.ok) {
                        getKnowledgeCards();
                } else {
                        alert('Failed to delete knowledge card.');
                }
        }

        const handleSort = (key) => {
                let direction = 'asc';
                if (sortConfig.key === key && sortConfig.direction === 'asc') {
                        direction = 'desc';
                }
                setSortConfig({ key, direction });
        };

        const sortedProjects = useMemo(() => {
                let sortableProjects = [...displayProjects];
                if (sortConfig.key !== null) {
                        sortableProjects.sort((a, b) => {
                                if (a[sortConfig.key] < b[sortConfig.key]) {
                                        return sortConfig.direction === 'asc' ? -1 : 1;
                                }
                                if (a[sortConfig.key] > b[sortConfig.key]) {
                                        return sortConfig.direction === 'asc' ? 1 : -1;
                                }
                                return 0;
                        });
                }
                return sortableProjects;
        }, [displayProjects, sortConfig]);

        const sortedKnowledgeCards = useMemo(() => {
                let sortableCards = [...displayKnowledgeCards];
                if (sortConfig.key !== null) {
                        sortableCards.sort((a, b) => {
                                let aValue = a[sortConfig.key];
                                let bValue = b[sortConfig.key];

                                if (sortConfig.key === 'name') {
                                        aValue = a.donor_name || a.outcome_name || a.field_context_name || '';
                                        bValue = b.donor_name || b.outcome_name || b.field_context_name || '';
                                }

                                if (aValue < bValue) {
                                        return sortConfig.direction === 'asc' ? -1 : 1;
                                }
                                if (aValue > bValue) {
                                        return sortConfig.direction === 'asc' ? 1 : -1;
                                }
                                return 0;
                        });
                }
                return sortableCards;
        }, [displayKnowledgeCards, sortConfig]);

        return <Base>
                <div className="Dashboard">
                        <header className="Dashboard_top" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                        <div className='Dashboard_label'>
                                                {selectedTab.charAt(0).toUpperCase() + selectedTab.slice(1)} Explorer
                                                {selectedTab === 'other' && subfolder && subfolder !== 'all' && teams.length > 0 && (
                                                        ` > ${teams.find(t => t.id === subfolder)?.name || subfolder}`
                                                )}
                                                {selectedTab === 'other' && subfolder === 'all' && ` > All`}
                                                {selectedTab !== 'other' && subfolder && subfolder !== 'all' && ` > ${subfolder}`}
                                                {filter && filter !== 'all' && ` > ${filter}`}
                                        </div>
                                        {selectedTab !== 'metrics' && (
                                                <div className="Dashboard_search" role="search" style={{ marginLeft: 8 }}>
                                                        <i className="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
                                                        <label htmlFor="quick-search" className="sr-only">Quick search</label>
                                                        <input id="quick-search" type="text" placeholder="Quick search..." className="Dashboard_search_input" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} data-testid="search-input" />
                                                </div>
                                        )}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <div className="view-mode-toggle">
                                                <button className={`view-btn ${viewMode === 'vignette' ? 'active' : ''}`} onClick={() => setViewMode('vignette')} title="Vignette View" data-testid="vignette-view-button">
                                                        <i className="fa-solid fa-grip"></i>
                                                </button>
                                                <button className={`view-btn ${viewMode === 'table' ? 'active' : ''}`} onClick={() => setViewMode('table')} title="Table View" data-testid="table-view-button">
                                                        <i className="fa-solid fa-table-list"></i>
                                                </button>
                                        </div>
                                        <div
                                                className="ai-disclaimer"
                                                style={{
                                                        background: "#fff8e1", border: "1px solid #fdd835",
                                                        color: "#372800", borderRadius: "8px", fontSize: "12px",
                                                        padding: "7px 16px",
                                                        boxShadow: "0 2px 10px 0 rgb(0 0 0 / 7%)", zIndex: 3, position: "relative", minWidth: 210
                                                }}
                                        >
                                                <strong>Note:</strong> AI-generated content may be inaccurate and should be verified.
                                        </div>
                                </div>
                        </header>

                        <section id="proposals-panel" data-testid="proposals-panel" role="tabpanel" className={`tab-panel ${selectedTab === 'proposals' ? 'active' : ''}`} hidden={selectedTab !== 'proposals'}>
                                {viewMode === 'vignette' ? (
                                        <div className="Dashboard_projects" id="proposals-grid">
                                                <div className="card card--cta">
                                                        <button className="btn" type="button" aria-label="Start a new proposal" onClick={() => navigate("/chat")} data-testid="new-proposal-button">Start New Proposal</button>
                                                </div>
                                                {displayProjects && displayProjects.map((project) =>
                                                        <Project
                                                                key={project.proposal_id}
                                                                project={project}
                                                                date={cleanedDate(project.updated_at)}
                                                                onClick={(e) => handleProjectClick(e, project.proposal_id, false)}
                                                                handleDeleteProject={handleDeleteProject}
                                                                handleRestoreProject={handleRestoreProject}
                                                                handleTransferOwnership={handleTransferOwnership}
                                                        />
                                                )}
                                        </div>
                                ) : (
                                        <div className="Dashboard_tableContainer">
                                                <div className="card card--cta" style={{ marginBottom: '20px', width: 'fit-content' }}>
                                                        <button className="btn" type="button" aria-label="Start a new proposal" onClick={() => navigate("/chat")} data-testid="new-proposal-button-table">Start New Proposal</button>
                                                </div>
                                                <table className="table table-hover">
                                                        <thead>
                                                                <tr>
                                                                        <th onClick={() => handleSort('project_title')} className="sortable">Title {sortConfig.key === 'project_title' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('country')} className="sortable">Country {sortConfig.key === 'country' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('donor')} className="sortable">Donor {sortConfig.key === 'donor' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('budget')} className="sortable">Budget {sortConfig.key === 'budget' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th>Outcomes</th>
                                                                        <th onClick={() => handleSort('status')} className="sortable">Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('updated_at')} className="sortable">Last Updated {sortConfig.key === 'updated_at' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th>Actions</th>
                                                                </tr>
                                                        </thead>
                                                        <tbody>
                                                                {sortedProjects.map((project) => (
                                                                        <tr key={project.proposal_id} onClick={(e) => handleProjectClick(e, project.proposal_id, false)} style={{ cursor: 'pointer' }}>
                                                                                <td>{project.project_title}</td>
                                                                                <td>{project.country}</td>
                                                                                <td>{project.donor}</td>
                                                                                <td>{project.budget}</td>
                                                                                <td title={project.outcomes?.join(', ')}>
                                                                                        {project.outcomes && project.outcomes.length > 0
                                                                                                ? (project.outcomes.length > 1 ? `${project.outcomes[0]} +${project.outcomes.length - 1}` : project.outcomes[0])
                                                                                                : 'N/A'
                                                                                        }
                                                                                </td>
                                                                                <td><span className={`Dashboard_project_label status-${project.status}`}>{project.status}</span></td>
                                                                                <td>{cleanedDate(project.updated_at)}</td>
                                                                                <td onClick={(e) => e.stopPropagation()}>
                                                                                        <div style={{ display: 'flex', gap: '10px' }}>
                                                                                                <i className="fa-solid fa-eye" title="View" onClick={(e) => handleProjectClick(e, project.proposal_id, false)}></i>
                                                                                                {project.status === 'deleted' ? (
                                                                                                        <i className="fa-solid fa-trash-arrow-up" title="Restore" onClick={() => handleRestoreProject(project.proposal_id)}></i>
                                                                                                ) : (
                                                                                                        <>
                                                                                                                <i className="fa-solid fa-trash-can" title="Delete" onClick={() => handleDeleteProject(project.proposal_id)}></i>
                                                                                                                <i className="fa-solid fa-share-from-square" title="Transfer" onClick={() => handleTransferOwnership(project.proposal_id)}></i>
                                                                                                        </>
                                                                                                )}
                                                                                        </div>
                                                                                </td>
                                                                        </tr>
                                                                ))}
                                                        </tbody>
                                                </table>
                                        </div>
                                )}
                        </section>

                        <section id="knowledge-panel" role="tabpanel" className={`tab-panel ${selectedTab === 'knowledge' ? 'active' : ''}`} hidden={selectedTab !== 'knowledge'}>
                                {viewMode === 'vignette' ? (
                                        <div className="Dashboard_projects" id="knowledge-grid">
                                                <div className="card card--cta">
                                                        <button className="btn" type="button" aria-label="Start a new knowledge card" onClick={() => navigate("/knowledge-card/new")} data-testid="new-knowledge-card-button">Create New Knowledge Card</button>
                                                </div>
                                                {displayKnowledgeCards && displayKnowledgeCards.map((card) => {
                                                        const isKCOwner = currentUser && (currentUser.id === card.created_by || currentUser.user_id === card.created_by);
                                                        return <KnowledgeCard
                                                                key={card.id}
                                                                card={card}
                                                                date={cleanedDate(card.updated_at)}
                                                                onClick={() => isKCOwner ? navigate(`/knowledge-card/${card.id}`) : navigate(`/review/knowledge-card/${card.id}`)}
                                                                isDuplicate={duplicateCardIds.has(card.id)}
                                                                onDelete={() => handleDeleteKnowledgeCard(card.id)}
                                                        />
                                                })}
                                        </div>
                                ) : (
                                        <div className="Dashboard_tableContainer">
                                                <div className="card card--cta" style={{ marginBottom: '20px', width: 'fit-content' }}>
                                                        <button className="btn" type="button" aria-label="Start a new knowledge card" onClick={() => navigate("/knowledge-card/new")} data-testid="new-knowledge-card-button-table">Create New Knowledge Card</button>
                                                </div>
                                                <table className="table table-hover">
                                                        <thead>
                                                                <tr>
                                                                        <th onClick={() => handleSort('card_type')} className="sortable">Type {sortConfig.key === 'card_type' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('name')} className="sortable">Name {sortConfig.key === 'name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('summary')} className="sortable">Summary {sortConfig.key === 'summary' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('updated_at')} className="sortable">Last Updated {sortConfig.key === 'updated_at' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                </tr>
                                                        </thead>
                                                        <tbody>
                                                                {sortedKnowledgeCards.map((card) => {
                                                                        const isKCOwner = currentUser && (currentUser.id === card.created_by || currentUser.user_id === card.created_by);
                                                                        const cardType = card.donor_name ? 'Donor' : card.outcome_name ? 'Outcome' : 'Field Context';
                                                                        const cardName = card.donor_name || card.outcome_name || card.field_context_name || 'N/A';

                                                                        return (
                                                                                <tr key={card.id} onClick={() => isKCOwner ? navigate(`/knowledge-card/${card.id}`) : navigate(`/review/knowledge-card/${card.id}`)} style={{ cursor: 'pointer' }}>
                                                                                        <td>
                                                                                                {card.donor_name && <i className="fa-solid fa-money-bill-wave donor"></i>}
                                                                                                {card.outcome_name && <i className="fa-solid fa-bullseye outcome"></i>}
                                                                                                {card.field_context_name && <i className="fa-solid fa-earth-americas field-context"></i>}
                                                                                                {' '}{cardType}
                                                                                        </td>
                                                                                        <td>{cardName}</td>
                                                                                        <td style={{ maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{card.summary}</td>
                                                                                        <td>{cleanedDate(card.updated_at)}</td>
                                                                                </tr>
                                                                        );
                                                                })}
                                                        </tbody>
                                                </table>
                                        </div>
                                )}
                        </section>

                        <section id="reviews-panel" role="tabpanel" className={`tab-panel ${selectedTab === 'reviews' ? 'active' : ''}`} hidden={selectedTab !== 'reviews'}>
                                {viewMode === 'vignette' ? (
                                        <div className="Dashboard_projects" id="reviews-grid">
                                                {displayProjects && displayProjects.map((review) =>
                                                        <Project
                                                                key={review.proposal_id}
                                                                project={review}
                                                                date={cleanedDate(review.updated_at)}
                                                                onClick={(e) => handleProjectClick(e, review.proposal_id, true)}
                                                                isReview={true}
                                                                handleDeleteProject={handleDeleteProject}
                                                                handleTransferOwnership={handleTransferOwnership}
                                                        />
                                                )}
                                        </div>
                                ) : (
                                        <div className="Dashboard_tableContainer">
                                                <table className="table table-hover">
                                                        <thead>
                                                                <tr>
                                                                        <th onClick={() => handleSort('project_title')} className="sortable">Title {sortConfig.key === 'project_title' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('requester_name')} className="sortable">Requester {sortConfig.key === 'requester_name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('deadline')} className="sortable">Deadline {sortConfig.key === 'deadline' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('updated_at')} className="sortable">Last Updated {sortConfig.key === 'updated_at' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                </tr>
                                                        </thead>
                                                        <tbody>
                                                                {sortedProjects.map((review) => (
                                                                        <tr key={review.proposal_id} onClick={(e) => handleProjectClick(e, review.proposal_id, true)} style={{ cursor: 'pointer' }}>
                                                                                <td>{review.project_title}</td>
                                                                                <td>{review.requester_name || 'N/A'}</td>
                                                                                <td>{review.deadline ? new Date(review.deadline).toLocaleDateString() : 'N/A'}</td>
                                                                                <td>{cleanedDate(review.updated_at)}</td>
                                                                        </tr>
                                                                ))}
                                                        </tbody>
                                                </table>
                                        </div>
                                )}
                        </section>

                        <section id="metrics-panel" role="tabpanel" className={`tab-panel ${selectedTab === 'metrics' ? 'active' : ''}`} hidden={selectedTab !== 'metrics'}>
                                {selectedTab === 'metrics' && <MetricsDashboard />}
                        </section>

                        <section id="other-panel" role="tabpanel" className={`tab-panel ${selectedTab === 'other' ? 'active' : ''}`} hidden={selectedTab !== 'other'}>
                                {viewMode === 'vignette' ? (
                                        <div className="Dashboard_projects" id="other-grid">
                                                {displayProjects && displayProjects.map((review) =>
                                                        <Project
                                                                key={review.proposal_id}
                                                                project={review}
                                                                date={cleanedDate(review.updated_at)}
                                                                onClick={(e) => handleProjectClick(e, review.proposal_id, true)}
                                                                isReview={true}
                                                                handleDeleteProject={handleDeleteProject}
                                                                handleRestoreProject={handleRestoreProject}
                                                                handleTransferOwnership={handleTransferOwnership}
                                                        />
                                                )}
                                        </div>
                                ) : (
                                        <div className="Dashboard_tableContainer">
                                                <table className="table table-hover">
                                                        <thead>
                                                                <tr>
                                                                        <th onClick={() => handleSort('project_title')} className="sortable">Title {sortConfig.key === 'project_title' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('team_name')} className="sortable">Team {sortConfig.key === 'team_name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('author_name')} className="sortable">Author {sortConfig.key === 'author_name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('country')} className="sortable">Country {sortConfig.key === 'country' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('donor')} className="sortable">Donor {sortConfig.key === 'donor' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('budget')} className="sortable">Budget {sortConfig.key === 'budget' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('status')} className="sortable">Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                        <th onClick={() => handleSort('updated_at')} className="sortable">Last Updated {sortConfig.key === 'updated_at' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                                                </tr>
                                                        </thead>
                                                        <tbody>
                                                                {sortedProjects.map((project) => (
                                                                        <tr key={project.proposal_id} onClick={(e) => handleProjectClick(e, project.proposal_id, false)} style={{ cursor: 'pointer' }}>
                                                                                <td>{project.project_title}</td>
                                                                                <td>{project.team_name}</td>
                                                                                <td>{project.author_name}</td>
                                                                                <td>{project.country || '-'}</td>
                                                                                <td>{project.donor || '-'}</td>
                                                                                <td>{project.budget || '-'}</td>
                                                                                <td><span className={`Dashboard_project_label status-${project.status}`}>{project.status}</span></td>
                                                                                <td>{cleanedDate(project.updated_at)}</td>
                                                                        </tr>
                                                                ))}
                                                        </tbody>
                                                </table>
                                        </div>
                                )}
                        </section>
                </div>

                <div className={`modal ${isFilterModalOpen ? 'active' : ''}`} id="filter-modal" role="dialog" aria-modal="true" aria-labelledby="filter-title">
                        <div className="modal-content">
                                <span className="modal-close" onClick={() => setIsFilterModalOpen(false)} data-testid="filter-modal-close-button">&times;</span>
                                <h3 id="filter-title">Apply Content Filters</h3>

                                <div className="filter-section" data-tab="proposals" hidden={selectedTab !== 'proposals'}>
                                        <label htmlFor="status-filter">Status</label>
                                        <select id="status-filter" data-testid="status-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                                                <option value="">All</option>
                                                <option value="draft">Drafting</option>
                                                <option value="in_review">Pending Review</option>
                                                <option value="pre_submission">Pre-Submission</option>
                                                <option value="submission">Pending Submission</option>
                                                <option value="submitted">Submitted</option>
                                                <option value="approved">Approved</option>
                                        </select>
                                </div>

                                <div className="filter-section" data-tab="reviews" hidden={selectedTab !== 'reviews'}>
                                        <label htmlFor="deadline-filter">Deadline before</label>
                                        <input type="date" id="deadline-filter" data-testid="deadline-filter" />
                                </div>

                                <div className="filter-section" data-tab="knowledge" hidden={selectedTab !== 'knowledge'}>
                                        <label htmlFor="knowledge-card-type-filter">Card Type</label>
                                        <select id="knowledge-card-type-filter" data-testid="knowledge-card-type-filter" value={knowledgeCardTypeFilter} onChange={e => setKnowledgeCardTypeFilter(e.target.value)}>
                                                <option value="">All</option>
                                                <option value="donor">Donor</option>
                                                <option value="outcome">Outcome</option>
                                                <option value="field_context">Field Context</option>
                                        </select>
                                </div>
                        </div>
                </div>
                <SingleSelectUserModal
                        isOpen={isTransferModalOpen}
                        onClose={() => setIsTransferModalOpen(false)}
                        options={users}
                        title="Transfer Proposal Ownership to another Focal Point"
                        onConfirm={confirmTransfer}
                />
        </Base>
}
