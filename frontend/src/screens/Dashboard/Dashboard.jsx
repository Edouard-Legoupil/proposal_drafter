import { useState, useEffect } from 'react';
import './Dashboard.css';
import Base from '../../components/Base/Base';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function Dashboard() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('proposals');
    const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
    const [isNewProposalModalOpen, setIsNewProposalModalOpen] = useState(false);

    const [proposals, setProposals] = useState([]);
    const [knowledgeCards, setKnowledgeCards] = useState([]);
    const [reviews, setReviews] = useState([]);

    const [searchTerm, setSearchTerm] = useState("");

    async function getProposals() {
        const response = await fetch(`${API_BASE_URL}/list-drafts`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            setProposals(data.drafts);
        }
    }

    async function getKnowledgeCards() {
        const response = await fetch(`${API_BASE_URL}/knowledge`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            setKnowledgeCards(data.knowledge_cards);
        }
    }

    async function getReviews() {
        const response = await fetch(`${API_BASE_URL}/proposals/reviews`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            setReviews(data.reviews);
        }
    }

    const fetchAllData = () => {
        getProposals();
        getKnowledgeCards();
        getReviews();
    }

    useEffect(() => {
        fetchAllData();
    }, []);

    useEffect(() => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css';
        link.crossOrigin = 'anonymous';
        link.referrerPolicy = 'no-referrer';
        document.head.appendChild(link);

        return () => {
            if (document.head.contains(link)) {
                document.head.removeChild(link);
            }
        };
    }, []);

    const handleTabClick = (tabId) => {
        setActiveTab(tabId);
    };

    const openFilterModal = () => setIsFilterModalOpen(true);
    const closeFilterModal = () => setIsFilterModalOpen(false);
    const openNewProposalModal = () => setIsNewProposalModalOpen(true);
    const closeNewProposalModal = () => setIsNewProposalModalOpen(false);


    function handleProjectClick(proposal_id) {
        sessionStorage.setItem("proposal_id", proposal_id)
        navigate("/chat")
    }

    async function handleCreateProposal(newProposalData) {
        const response = await fetch(`${API_BASE_URL}/save-draft`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                form_data: { "Project title": "New Proposal" }, // Default title
                project_description: "",
                generated_sections: {},
                ...newProposalData
            })
        });
        if (response.ok) {
            const data = await response.json();
            closeNewProposalModal();
            fetchAllData();
            handleProjectClick(data.proposal_id);
        } else {
            console.error("Failed to create proposal");
        }
    }

    async function handleSubmitForReview(proposal_id) {
        const response = await fetch(`${API_BASE_URL}/proposals/${proposal_id}/submit-for-review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (response.ok) {
            fetchAllData();
        } else {
            console.error("Failed to submit for review");
        }
    }


    const filteredProposals = proposals.filter(p => p.project_title && p.project_title.toLowerCase().includes(searchTerm.toLowerCase()));
    const filteredKnowledgeCards = knowledgeCards.filter(kc => kc.title && kc.title.toLowerCase().includes(searchTerm.toLowerCase()));
    const filteredReviews = reviews.filter(r => r.project_title && r.project_title.toLowerCase().includes(searchTerm.toLowerCase()));


    return (
        <Base>
            <div className="Dashboard">
                <header className="Dashboard_top">
                    <div className="Dashboard_label" aria-label="Workspace name">Project Proposals Workspace -- 'Draft Wireframe'</div>
                    <p>Build Smart proposals with AI based on curated knowledge and organised peer review.</p>
                </header>

                <nav className="tabs" aria-label="Dashboard sections">
                    <div role="tablist" aria-orientation="horizontal" className="tablist">
                        <button id="proposals-tab" role="tab" aria-selected={activeTab === 'proposals'} aria-controls="proposals-panel" className="tab" onClick={() => handleTabClick('proposals')}>My Proposals</button>
                        <button id="library-tab" role="tab" aria-selected={activeTab === 'library'} aria-controls="library-panel" className="tab" onClick={() => handleTabClick('library')}>Knowledge Library</button>
                        <button id="reviews-tab" role="tab" aria-selected={activeTab === 'reviews'} aria-controls="reviews-panel" className="tab" onClick={() => handleTabClick('reviews')}>Pending Reviews</button>
                    </div>
                </nav>

                <div className="Dashboard_search" role="search">
                    <i className="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
                    <label htmlFor="quick-search" className="sr-only">Quick search</label>
                    <input id="quick-search" type="text" placeholder="Quick search..." className="Dashboard_search_input" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                    <button className="filter-btn" id="filter-btn" aria-label="Open filters" onClick={openFilterModal}>
                        <i className="fa-solid fa-sliders"></i>
                    </button>
                </div>

                <div className="tab-content">
                    {activeTab === 'proposals' && (
                        <section id="proposals-panel" role="tabpanel" aria-labelledby="proposals-tab" className="tab-panel active">
                            <div className="Dashboard_projects" id="proposals-grid">
                                <div className="card card--cta">
                                    <button className="btn" type="button" aria-label="Start a new proposal" onClick={openNewProposalModal}>Start New Proposal</button>
                                </div>
                                {filteredProposals.map(p => (
                                    <ProposalCard
                                        key={p.proposal_id}
                                        proposal={p}
                                        onClick={() => handleProjectClick(p.proposal_id)}
                                        onSubmitForReview={() => handleSubmitForReview(p.proposal_id)}
                                    />
                                ))}
                            </div>
                        </section>
                    )}
                    {activeTab === 'library' && (
                        <section id="library-panel" role="tabpanel" aria-labelledby="library-tab" className="tab-panel active">
                             <div className="Dashboard_projects" id="library-grid">
                                <div className="card card--cta">
                                    <button className="btn" type="button" aria-label="Create new knowledge card">Create new knowledge card</button>
                                </div>
                                {filteredKnowledgeCards.map(kc => (
                                    <KnowledgeCard
                                        key={kc.id}
                                        category={kc.category}
                                        title={kc.title}
                                        summary={kc.summary}
                                        lastUpdated={kc.last_updated}
                                        icon={
                                            kc.category === 'Donor Insights' ? "fa-solid fa-money-bill-wave donor" :
                                            kc.category === 'Field Context' ? "fa-solid fa-earth-americas field-context" :
                                            "fa-solid fa-bullseye outcome"
                                        }
                                    />
                                ))}
                            </div>
                        </section>
                    )}
                    {activeTab === 'reviews' && (
                        <section id="reviews-panel" role="tabpanel" aria-labelledby="reviews-tab" className="tab-panel active">
                            <div className="Dashboard_projects" id="reviews-grid">
                            {filteredReviews.map(r => (
                                    <ReviewCard
                                        key={r.proposal_id}
                                        title={r.project_title}
                                        requester="Unknown"
                                        deadline="N/A"
                                        country={r.field_context}
                                        donor={r.donor}
                                        outcome={r.outcome}
                                    />
                            ))}
                            </div>
                        </section>
                    )}
                </div>

                {isFilterModalOpen && <FilterModal closeModal={closeFilterModal} activeTab={activeTab} />}
                {isNewProposalModalOpen && <NewProposalModal closeModal={closeNewProposalModal} onCreate={handleCreateProposal} />}
            </div>
        </Base>
    );
}

function ProposalCard({ proposal, onClick, onSubmitForReview }) {
    const { proposal_id, project_title, summary, status, field_context, donor, outcome, updated_at } = proposal;
    const statusClass = `status-${status ? status.toLowerCase().replace(/ /g, '-') : 'draft'}`;
    const date = updated_at ? new Date(updated_at).toLocaleDateString() : 'N/A';

    return (
        <article className="card" aria-labelledby={`proposal-${proposal_id}`}>
            <div onClick={onClick} style={{cursor: 'pointer'}}>
                <h3 id={`proposal-${proposal_id}`}>{project_title}</h3>
                <p>{summary}</p>
                <p><span className={`status-badge ${statusClass}`}>{status}</span></p>
                <p><i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {field_context || 'N/A'}</p>
                <p><i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {donor || 'N/A'}</p>
                <p><i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {outcome || 'N/A'}</p>
                <p><small>Last Updated: <time dateTime={updated_at}>{date}</time></small></p>
            </div>
            {status === 'draft' && (
                <button className="btn" style={{marginTop: "1rem"}} onClick={onSubmitForReview}>Submit for Review</button>
            )}
        </article>
    );
}

function KnowledgeCard({ category, title, summary, lastUpdated, icon }) {
    return (
        <article className="card" aria-labelledby={`kc-${title.replace(/\s+/g, '-').toLowerCase()}`}>
            <h3><i className={icon} aria-hidden="true"></i> {category}</h3>
            <h2 id={`kc-${title.replace(/\s+/g, '-').toLowerCase()}`}>{title}</h2>
            <p>{summary}</p>
            <p><small>Last Updated: <time dateTime={lastUpdated}>{lastUpdated}</time></small></p>
        </article>
    );
}

function ReviewCard({ title, requester, deadline, country, donor, outcome }) {
    return (
        <article className="card" aria-labelledby={`review-${title.replace(/\s+/g, '-').toLowerCase()}`}>
            <h3 id={`review-${title.replace(/\s+/g, '-').toLowerCase()}`}>{title}</h3>
            <h2>Requester: {requester}</h2>
            <p><strong>Deadline:</strong> <time dateTime={deadline}>{deadline}</time></p>
            <p><i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {country || 'N/A'}</p>
            <p><i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {donor || 'N/A'}</p>
            <p><i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {outcome || 'N/A'}</p>
        </article>
    );
}

function FilterModal({ closeModal, activeTab }) {
    return (
        <div className="modal active" id="filter-modal" role="dialog" aria-modal="true" aria-labelledby="filter-title">
            <div className="modal-content">
                <span className="modal-close" id="filter-close" onClick={closeModal}>&times;</span>
                <h3 id="filter-title">Apply Content Filters</h3>

                <div className="filter-section" style={{display: activeTab === 'proposals' ? 'block' : 'none'}}>
                    <label htmlFor="status-filter">Status</label>
                    <select id="status-filter">
                        <option value="">All</option>
                        <option value="draft">Drafting</option>
                        <option value="review">Pending Review</option>
                        <option value="submission">Pending Submission</option>
                        <option value="submitted">Submitted</option>
                        <option value="approved">Approved</option>
                    </select>
                </div>

                <div className="filter-section" style={{display: activeTab === 'library' ? 'block' : 'none'}}>
                    <label htmlFor="library-type">Category</label>
                    <select id="library-type">
                        <option value="">All</option>
                        <option value="donor">Donor Insights</option>
                        <option value="context">Country Context</option>
                        <option value="outcome">Outcome Lessons</option>
                    </select>
                </div>

                <div className="filter-.section" style={{display: activeTab === 'reviews' ? 'block' : 'none'}}>
                    <label htmlFor="deadline-filter">Deadline before</label>
                    <input type="date" id="deadline-filter" />
                </div>
            </div>
        </div>
    );
}

function NewProposalModal({ closeModal, onCreate }) {
    const [donor, setDonor] = useState("");
    const [fieldContext, setFieldContext] = useState("");
    const [outcome, setOutcome] = useState("");

    const handleSubmit = () => {
        onCreate({
            donor,
            field_context: fieldContext,
            outcome,
            status: 'draft'
        });
    };

    return (
        <div className="modal active" role="dialog" aria-modal="true" aria-labelledby="new-proposal-title">
            <div className="modal-content">
                <span className="modal-close" onClick={closeModal}>&times;</span>
                <h3 id="new-proposal-title">Start New Proposal</h3>
                <div className="filter-section">
                    <label htmlFor="donor-input">Donor</label>
                    <input id="donor-input" type="text" value={donor} onChange={e => setDonor(e.target.value)} />
                </div>
                <div className="filter-section">
                    <label htmlFor="context-input">Field Context</label>
                    <input id="context-input" type="text" value={fieldContext} onChange={e => setFieldContext(e.target.value)} />
                </div>
                <div className="filter-section">
                    <label htmlFor="outcome-input">Outcome</label>
                    <input id="outcome-input" type="text" value={outcome} onChange={e => setOutcome(e.target.value)} />
                </div>
                <button className="btn" style={{marginTop: "1rem"}} onClick={handleSubmit}>Create and Start</button>
            </div>
        </div>
    )
}
