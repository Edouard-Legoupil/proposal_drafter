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

    const fetchAllData = async () => {
        try {
            const [proposalsRes, knowledgeRes, reviewsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/list-drafts`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/knowledge`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/proposals/reviews`, { credentials: 'include' })
            ]);
            const proposalsData = await proposalsRes.json();
            const knowledgeData = await knowledgeRes.json();
            const reviewsData = await reviewsRes.json();

            setProposals(Array.isArray(proposalsData) ? proposalsData : []);
            setKnowledgeCards(Array.isArray(knowledgeData) ? knowledgeData : []);
            setReviews(Array.isArray(reviewsData) ? reviewsData : []);

        } catch (error) {
            console.error("Failed to fetch data:", error);
        }
    };

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

    const handleTabClick = (tabId) => setActiveTab(tabId);
    const openFilterModal = () => setIsFilterModalOpen(true);
    const closeFilterModal = () => setIsFilterModalOpen(false);
    const openNewProposalModal = () => setIsNewProposalModalOpen(true);
    const closeNewProposalModal = () => setIsNewProposalModalOpen(false);

    const handleCreateProposal = async (newProposalData) => {
        const response = await fetch(`${API_BASE_URL}/save-draft`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                form_data: { "Project title": "New Proposal" },
                project_description: "",
                generated_sections: {},
                ...newProposalData
            })
        });
        if (response.ok) {
            const data = await response.json();
            closeNewProposalModal();
            fetchAllData();
            navigate(`/chat?proposal_id=${data.proposal_id}`);
        } else {
            console.error("Failed to create proposal");
        }
    };

    const handleSubmitForReview = async (proposal_id) => {
        await fetch(`${API_BASE_URL}/proposals/${proposal_id}/submit-for-review`, {
            method: 'POST',
            credentials: 'include'
        });
        fetchAllData();
    };

    const filteredProposals = proposals.filter(p => p.project_title.toLowerCase().includes(searchTerm.toLowerCase()));
    const filteredKnowledgeCards = knowledgeCards.filter(kc => kc.title.toLowerCase().includes(searchTerm.toLowerCase()));
    const filteredReviews = reviews.filter(r => r.project_title.toLowerCase().includes(searchTerm.toLowerCase()));

    return (
        <Base>
            <div className="Dashboard">
                <header className="Dashboard_top">
                    <div className="Dashboard_label">Project Proposals Workspace</div>
                    <p>Build Smart proposals with AI based on curated knowledge and organised peer review.</p>
                </header>

                <nav className="tabs" aria-label="Dashboard sections">
                    <div role="tablist" aria-orientation="horizontal" className="tablist">
                        <button id="proposals-tab" role="tab" aria-selected={activeTab === 'proposals'} onClick={() => handleTabClick('proposals')} className="tab">My Proposals</button>
                        <button id="library-tab" role="tab" aria-selected={activeTab === 'library'} onClick={() => handleTabClick('library')} className="tab">Knowledge Library</button>
                        <button id="reviews-tab" role="tab" aria-selected={activeTab === 'reviews'} onClick={() => handleTabClick('reviews')} className="tab">Pending Reviews</button>
                    </div>
                </nav>

                <div className="Dashboard_search" role="search">
                    <i className="fa-solid fa-magnifying-glass"></i>
                    <input id="quick-search" type="text" placeholder="Quick search..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="Dashboard_search_input" />
                    <button className="filter-btn" aria-label="Open filters" onClick={openFilterModal}>
                        <i className="fa-solid fa-sliders"></i>
                    </button>
                </div>

                <div className="tab-content">
                    {activeTab === 'proposals' && <ProposalsTab proposals={filteredProposals} openNewProposalModal={openNewProposalModal} onSubmitForReview={handleSubmitForReview} />}
                    {activeTab === 'library' && <LibraryTab knowledgeCards={filteredKnowledgeCards} />}
                    {activeTab === 'reviews' && <ReviewsTab reviews={filteredReviews} />}
                </div>

                {isFilterModalOpen && <FilterModal closeModal={closeFilterModal} activeTab={activeTab} />}
                {isNewProposalModalOpen && <NewProposalModal closeModal={closeNewProposalModal} onCreate={handleCreateProposal} />}
            </div>
        </Base>
    );
}

function ProposalsTab({ proposals, openNewProposalModal, onSubmitForReview }) {
    const navigate = useNavigate();
    return (
        <section className="tab-panel active">
            <div className="Dashboard_projects">
                <div className="card card--cta">
                    <button className="btn" onClick={openNewProposalModal}>Start New Proposal</button>
                </div>
                {proposals.map(p => <ProposalCard key={p.proposal_id} proposal={p} onClick={() => navigate(`/chat?proposal_id=${p.proposal_id}`)} onSubmitForReview={() => onSubmitForReview(p.proposal_id)} />)}
            </div>
        </section>
    );
}

function LibraryTab({ knowledgeCards }) {
    return (
        <section className="tab-panel active">
            <div className="Dashboard_projects">
                <div className="card card--cta">
                    <button className="btn">Create new knowledge card</button>
                </div>
                {knowledgeCards.map(kc => <KnowledgeCard key={kc.id} {...kc} />)}
            </div>
        </section>
    );
}

function ReviewsTab({ reviews }) {
    return (
        <section className="tab-panel active">
            <div className="Dashboard_projects">
                {reviews.map(r => <ReviewCard key={r.proposal_id} {...r} />)}
            </div>
        </section>
    );
}

function ProposalCard({ proposal, onClick, onSubmitForReview }) {
    const { proposal_id, project_title, summary, status, field_contexts, donors, outcomes, updated_at } = proposal;
    const statusClass = `status-${status?.toLowerCase().replace(/ /g, '-') || 'draft'}`;
    return (
        <article className="card">
            <div onClick={onClick} style={{cursor: 'pointer'}}>
                <h3>{project_title}</h3>
                <p>{summary}</p>
                <p><span className={`status-badge ${statusClass}`}>{status}</span></p>
                <p><i className="fa-solid fa-earth-americas field-context"></i> {field_contexts?.join(', ') || 'N/A'}</p>
                <p><i className="fa-solid fa-money-bill-wave donor"></i> {donors?.join(', ') || 'N/A'}</p>
                <p><i className="fa-solid fa-bullseye outcome"></i> {outcomes?.join(', ') || 'N/A'}</p>
                <p><small>Last Updated: <time>{new Date(updated_at).toLocaleDateString()}</time></small></p>
            </div>
            {status === 'draft' && <button className="btn" style={{marginTop: "1rem"}} onClick={onSubmitForReview}>Submit for Review</button>}
        </article>
    );
}

function KnowledgeCard({ category, title, summary, last_updated }) {
    const icon = category === 'Donor Insights' ? "fa-solid fa-money-bill-wave donor" :
                 category === 'Field Context' ? "fa-solid fa-earth-americas field-context" :
                 "fa-solid fa-bullseye outcome";
    return (
        <article className="card">
            <h3><i className={icon}></i> {category}</h3>
            <h2>{title}</h2>
            <p>{summary}</p>
            <p><small>Last Updated: <time>{new Date(last_updated).toLocaleDateString()}</time></small></p>
        </article>
    );
}

function ReviewCard({ project_title, field_contexts, donors, outcomes }) {
    return (
        <article className="card">
            <h3>{project_title}</h3>
            <h2>Requester: Unknown</h2>
            <p><strong>Deadline:</strong> N/A</p>
            <p><i className="fa-solid fa-earth-americas field-context"></i> {field_contexts?.join(', ') || 'N/A'}</p>
            <p><i className="fa-solid fa-money-bill-wave donor"></i> {donors?.join(', ') || 'N/A'}</p>
            <p><i className="fa-solid fa-bullseye outcome"></i> {outcomes?.join(', ') || 'N/A'}</p>
        </article>
    );
}

function FilterModal({ closeModal }) {
    return (
        <div className="modal">
            <div className="modal-content">
                <span className="modal-close" onClick={closeModal}>&times;</span>
                <h3>Apply Content Filters</h3>
            </div>
        </div>
    );
}

function NewProposalModal({ closeModal, onCreate }) {
    const [donors, setDonors] = useState("");
    const [field_contexts, setFieldContexts] = useState("");
    const [outcomes, setOutcomes] = useState("");

    const handleSubmit = () => {
        onCreate({
            donors: donors.split(',').map(s => s.trim()).filter(Boolean),
            field_contexts: field_contexts.split(',').map(s => s.trim()).filter(Boolean),
            outcomes: outcomes.split(',').map(s => s.trim()).filter(Boolean),
        });
    };

    return (
        <div className="modal">
            <div className="modal-content">
                <span className="modal-close" onClick={closeModal}>&times;</span>
                <h3>Start New Proposal</h3>
                <div className="filter-section">
                    <label>Donors (comma-separated)</label>
                    <input type="text" value={donors} onChange={e => setDonors(e.target.value)} />
                </div>
                <div className="filter-section">
                    <label>Field Contexts (comma-separated)</label>
                    <input type="text" value={field_contexts} onChange={e => setFieldContexts(e.target.value)} />
                </div>
                <div className="filter-section">
                    <label>Outcomes (comma-separated)</label>
                    <input type="text" value={outcomes} onChange={e => setOutcomes(e.target.value)} />
                </div>
                <button className="btn" style={{marginTop: "1rem"}} onClick={handleSubmit}>Create and Start</button>
            </div>
        </div>
    );
}
