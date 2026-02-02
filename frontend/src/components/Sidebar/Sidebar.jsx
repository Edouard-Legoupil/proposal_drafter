import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = ({ userRoles, isOpen }) => {
    const [expandedFolders, setExpandedFolders] = useState({
        proposals: true,
        knowledge: true
    });

    const toggleFolder = (folder) => {
        setExpandedFolders(prev => ({
            ...prev,
            [folder]: !prev[folder]
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
                                <NavLink to="/dashboard/proposals/all" className="Sidebar_link" data-testid="sidebar-link-proposals-all">All</NavLink>
                                <NavLink to="/dashboard/proposals/draft" className="Sidebar_link" data-testid="sidebar-link-proposals-draft">Drafting</NavLink>
                                <NavLink to="/dashboard/proposals/in_review" className="Sidebar_link" data-testid="sidebar-link-proposals-in_review">In Review</NavLink>
                                <NavLink to="/dashboard/proposals/pre_submission" className="Sidebar_link" data-testid="sidebar-link-proposals-pre_submission">Pre-Submission</NavLink>
                                <NavLink to="/dashboard/proposals/submitted" className="Sidebar_link" data-testid="sidebar-link-proposals-submitted">Submitted</NavLink>
                                <NavLink to="/dashboard/proposals/deleted" className="Sidebar_link" data-testid="sidebar-link-proposals-deleted">Deleted</NavLink>
                                <NavLink to="/dashboard/proposals/generating_sections" className="Sidebar_link" data-testid="sidebar-link-proposals-generating_sections">Generating</NavLink>
                                <NavLink to="/dashboard/proposals/failed" className="Sidebar_link" data-testid="sidebar-link-proposals-failed">Failed</NavLink>
                            </div>
                        )}
                    </div>
                )}

                <div className="Sidebar_folder">
                    <div className="Sidebar_folderHeader" onClick={() => toggleFolder('knowledge')} data-testid="sidebar-knowledge-folder">
                        <i className={`fa-solid ${expandedFolders.knowledge ? 'fa-folder-open' : 'fa-folder'}`}></i>
                        <span>Knowledge Cards</span>
                        <i className={`fa-solid fa-chevron-${expandedFolders.knowledge ? 'down' : 'right'} Sidebar_chevron`}></i>
                    </div>
                    {expandedFolders.knowledge && (
                        <div className="Sidebar_subItems">
                            <NavLink to="/dashboard/knowledge/all" className="Sidebar_link" data-testid="sidebar-link-knowledge-all">All</NavLink>
                            <NavLink to="/dashboard/knowledge/donor" className="Sidebar_link" data-testid="sidebar-link-knowledge-donor">Donor</NavLink>
                            <NavLink to="/dashboard/knowledge/outcome" className="Sidebar_link" data-testid="sidebar-link-knowledge-outcome">Outcome</NavLink>
                            <NavLink to="/dashboard/knowledge/field_context" className="Sidebar_link" data-testid="sidebar-link-knowledge-field_context">Field Context</NavLink>
                        </div>
                    )}
                </div>

                {userRoles.includes('project reviewer') && (
                    <NavLink to="/dashboard/reviews" className="Sidebar_folderHeader Sidebar_link_header" data-testid="sidebar-link-reviews">
                        <i className="fa-solid fa-magnifying-glass"></i>
                        <span>Pending Reviews</span>
                    </NavLink>
                )}

                <NavLink to="/dashboard/metrics" className="Sidebar_folderHeader Sidebar_link_header" data-testid="sidebar-link-metrics">
                    <i className="fa-solid fa-gauge-high"></i>
                    <span>Metrics</span>
                </NavLink>
            </nav>
        </aside>
    );
};

export default Sidebar;
