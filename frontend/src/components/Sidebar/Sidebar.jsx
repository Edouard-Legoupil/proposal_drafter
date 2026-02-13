import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

const Sidebar = ({ userRoles, isOpen }) => {
    const [expandedFolders, setExpandedFolders] = useState({
        proposals: true,
        knowledge: true,
        otherProposals: false
    });

    const [teams, setTeams] = useState([]);
    const [expandedTeams, setExpandedTeams] = useState({});

    useEffect(() => {
        const fetchTeams = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/teams`);
                const data = await response.json();
                if (data.teams) {
                    setTeams(data.teams);
                }
            } catch (error) {
                console.error('Error fetching teams:', error);
            }
        };

        if (isOpen) {
            fetchTeams();
        }
    }, [isOpen]);

    const toggleFolder = (folder) => {
        setExpandedFolders(prev => ({
            ...prev,
            [folder]: !prev[folder]
        }));
    };

    const toggleTeam = (teamId) => {
        setExpandedTeams(prev => ({
            ...prev,
            [teamId]: !prev[teamId]
        }));
    };

    if (!isOpen) return null;

    return (
        <aside className="Sidebar" data-testid="sidebar">
            <nav className="Sidebar_nav">
                {userRoles.includes('proposal writer') && (
                    <div className="Sidebar_folder">
                        <div className="Sidebar_folderHeader" onClick={() => toggleFolder('proposals')} data-testid="sidebar-proposals-folder">
                            <i className={`fa-solid ${expandedFolders.proposals ? 'fa-folder-open' : 'fa-folder'}`}></i>
                            <span>My Proposals</span>
                            <i className={`fa-solid fa-chevron-${expandedFolders.proposals ? 'down' : 'right'} Sidebar_chevron`}></i>
                        </div>
                        {expandedFolders.proposals && (
                            <div className="Sidebar_subItems">
                                <NavLink to="/dashboard/proposals/all" className="Sidebar_link" data-testid="sidebar-link-proposals-all">
                                    <i className="fa-solid fa-list-ul"></i> All
                                </NavLink>
                                <NavLink to="/dashboard/proposals/draft" className="Sidebar_link" data-testid="sidebar-link-proposals-draft">
                                    <i className="fa-solid fa-pen-to-square status-draft-icon"></i> Drafting
                                </NavLink>
                                <NavLink to="/dashboard/proposals/in_review" className="Sidebar_link" data-testid="sidebar-link-proposals-in_review">
                                    <i className="fa-solid fa-comments status-review-icon"></i> Peer Review
                                </NavLink>
                                <NavLink to="/dashboard/proposals/pre_submission" className="Sidebar_link" data-testid="sidebar-link-proposals-pre_submission">
                                    <i className="fa-solid fa-paper-plane status-pre-submission-icon"></i> Pre-Submission
                                </NavLink>
                                <NavLink to="/dashboard/proposals/submitted" className="Sidebar_link" data-testid="sidebar-link-proposals-submitted">
                                    <i className="fa-solid fa-circle-check status-submitted-icon"></i> Submitted
                                </NavLink>
                                <NavLink to="/dashboard/proposals/deleted" className="Sidebar_link" data-testid="sidebar-link-proposals-deleted">
                                    <i className="fa-solid fa-trash-can"></i> Deleted
                                </NavLink>
                            </div>
                        )}
                    </div>
                )}

                {userRoles.includes('project reviewer') && (
                    <NavLink to="/dashboard/reviews" className="Sidebar_folderHeader Sidebar_link_header" data-testid="sidebar-link-reviews">
                        <i className="fa-solid fa-clipboard-check"></i>
                        <span>For Review</span>
                    </NavLink>
                )}

                <div className="Sidebar_folder">
                    <div className="Sidebar_folderHeader" onClick={() => toggleFolder('knowledge')} data-testid="sidebar-knowledge-folder">
                        <i className={`fa-solid ${expandedFolders.knowledge ? 'fa-folder-open' : 'fa-folder'}`}></i>
                        <span>Knowledge Cards</span>
                        <i className={`fa-solid fa-chevron-${expandedFolders.knowledge ? 'down' : 'right'} Sidebar_chevron`}></i>
                    </div>
                    {expandedFolders.knowledge && (
                        <div className="Sidebar_subItems">
                            <NavLink to="/dashboard/knowledge/all" className="Sidebar_link" data-testid="sidebar-link-knowledge-all">
                                <i className="fa-solid fa-layer-group"></i> All
                            </NavLink>
                            <NavLink to="/dashboard/knowledge/donor" className="Sidebar_link" data-testid="sidebar-link-knowledge-donor">
                                <i className="fa-solid fa-money-bill-wave donor"></i> Donors
                            </NavLink>
                            <NavLink to="/dashboard/knowledge/outcome" className="Sidebar_link" data-testid="sidebar-link-knowledge-outcome">
                                <i className="fa-solid fa-bullseye outcome"></i> Outcome
                            </NavLink>
                            <NavLink to="/dashboard/knowledge/field_context" className="Sidebar_link" data-testid="sidebar-link-knowledge-field_context">
                                <i className="fa-solid fa-earth-americas field-context"></i> Field Context
                            </NavLink>
                        </div>
                    )}
                </div>

                <NavLink to="/dashboard/metrics" className="Sidebar_folderHeader Sidebar_link_header" data-testid="sidebar-link-metrics">
                    <i className="fa-solid fa-gauge-high"></i>
                    <span>Metrics</span>
                </NavLink>

                {userRoles.includes('project reviewer') && (
                    <div className="Sidebar_folder">
                        <div className="Sidebar_folderHeader" onClick={() => toggleFolder('otherProposals')} data-testid="sidebar-other-proposals-folder">
                            <i className={`fa-solid ${expandedFolders.otherProposals ? 'fa-folder-open' : 'fa-folder'}`}></i>
                            <span>Other Proposals</span>
                            <i className={`fa-solid fa-chevron-${expandedFolders.otherProposals ? 'down' : 'right'} Sidebar_chevron`}></i>
                        </div>
                        {expandedFolders.otherProposals && (
                            <div className="Sidebar_subItems">
                                <NavLink to="/dashboard/other/all" className="Sidebar_link" data-testid="sidebar-link-other-all">
                                    <i className="fa-solid fa-list-ul"></i> All
                                </NavLink>
                                {teams.map(team => (
                                    <div key={team.id} className="Sidebar_teamFolder">
                                        <div className="Sidebar_folderHeader Sidebar_subFolderHeader" onClick={() => toggleTeam(team.id)}>
                                            <i className={`fa-solid ${expandedTeams[team.id] ? 'fa-folder-open' : 'fa-folder'}`}></i>
                                            <span>{team.name}</span>
                                            <i className={`fa-solid fa-chevron-${expandedTeams[team.id] ? 'down' : 'right'} Sidebar_chevron`}></i>
                                        </div>
                                        {expandedTeams[team.id] && (
                                            <div className="Sidebar_subItems Sidebar_nestedSubItems">
                                                <NavLink to={`/dashboard/other/${team.id}/all`} className="Sidebar_link">
                                                    <i className="fa-solid fa-list-ul"></i> All
                                                </NavLink>
                                                <NavLink to={`/dashboard/other/${team.id}/draft`} className="Sidebar_link">
                                                    <i className="fa-solid fa-pen-to-square status-draft-icon"></i> Drafting
                                                </NavLink>
                                                <NavLink to={`/dashboard/other/${team.id}/in_review`} className="Sidebar_link">
                                                    <i className="fa-solid fa-comments status-review-icon"></i> Peer Review
                                                </NavLink>
                                                <NavLink to={`/dashboard/other/${team.id}/pre_submission`} className="Sidebar_link">
                                                    <i className="fa-solid fa-paper-plane status-pre-submission-icon"></i> Pre-Submission
                                                </NavLink>
                                                <NavLink to={`/dashboard/other/${team.id}/submitted`} className="Sidebar_link">
                                                    <i className="fa-solid fa-circle-check status-submitted-icon"></i> Submitted
                                                </NavLink>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </nav>
        </aside>
    );
};

export default Sidebar;
