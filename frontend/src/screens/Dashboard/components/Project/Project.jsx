import './Project.css'
import { useState } from 'react';

import view from '../../../../assets/images/dashboard-fileIcon.svg';
import bin from '../../../../assets/images/delete.svg';
import transfer from '../../../../assets/images/prop.svg';
import tripleDots from '../../../../assets/images/dashboard-tripleDots.svg';


export default function Project ({ project, date, onClick, isReview = false, projectIndex, handleDeleteProject, handleTransferOwnership })
{
        const [popoverVisible, setPopoverVisible] = useState(false);

        const getStatusInfo = (project) => {
                if (project.is_accepted) {
                        return { text: 'Shared', className: 'status-shared' };
                }
                switch (project.status) {
                        case 'draft':
                                return { text: 'Drafting', className: 'status-draft' };
                        case 'in_review':
                                return { text: 'Pending Peer Review', className: 'status-review' };
                        case 'submission':
                                return { text: 'Pending Submission', className: 'status-submission' };
                        case 'submitted':
                                return { text: 'Submitted', className: 'status-submitted' };
                        case 'approved':
                                return { text: 'Approved', className: 'status-approved' };
                        default:
                                return { text: 'Drafting', className: 'status-draft' };
                }
        };

        const togglePopover = (e) => {
                e.stopPropagation(); // Prevent card's onClick from firing
                setPopoverVisible(!popoverVisible);
        };

        const trimSummary = (summary) => {
                const summaryText = typeof summary === 'string' ? summary : '';
                if (!summaryText) return 'No summary available.';
                const lines = summaryText.split('\n');
                if (lines.length > 5) {
                    return lines.slice(0, 5).join('\n') + '...';
                }
                return summaryText;
        };

        const statusInfo = getStatusInfo(project);

        if (isReview) {
                return (
                        <article className="card" onClick={onClick} data-testid="review-card">
                                <h3 id={`review-${project.proposal_id}`}>{project.project_title}</h3>
                                <h2>Requester: {project.requester_name || 'N/A'}</h2>
                                <p><strong>Deadline:</strong> <time dateTime={project.deadline || ''}>{project.deadline ? new Date(project.deadline).toLocaleDateString() : 'N/A'}</time></p>
                                <p>
                                        <i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {project.country || 'N/A'} -
                                        <i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {project.donor || 'N/A'} -
                                        <i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {project.outcomes?.join(', ') || 'N/A'} -
                                        <i className="fa-solid fa-money-check-dollar" aria-hidden="true"></i> Budget: {project.budget || 'N/A'}
                                </p>
                        </article>
                )
        }

        return  <article className={`Dashboard_project ${popoverVisible ? 'popover-active' : ''}`} onClick={onClick} data-testid="project-card">
                        <div className="Dashboard_project_title">
                                <h3 id={`proj-${project.proposal_id}`}>{project.project_title}</h3>
                                <button className="Dashboard_project_tripleDotsContainer" onClick={togglePopover} aria-haspopup="true" aria-expanded={popoverVisible} data-testid="project-options-button">
                                        <img src={tripleDots} alt="Options" />
                                </button>
                                {popoverVisible && (
                                        <div popover="auto" className='Project_optionsPopover' id={`popover-${projectIndex+1}`} >
                                                <div className='Project_optionsPopover_option' onClick={(e) => { e.stopPropagation(); onClick(e); }} data-testid="project-view-button">
                                                        <img src={view} alt="View" />
                                                        View
                                                </div>
                                                <div className='Project_optionsPopover_option' onClick={(e) => { e.stopPropagation(); handleTransferOwnership(project.proposal_id); }} data-testid="project-transfer-button">
                                                        <img className='Project_optionsPopover_option_transfer' src={transfer} alt="Transfer" />
                                                        Transfer
                                                </div>
                                                <div className='Project_optionsPopover_option' onClick={(e) => { e.stopPropagation(); handleDeleteProject(project.proposal_id); }} data-testid="project-delete-button">
                                                        <img className='Project_optionsPopover_option_delete' src={bin} alt="Delete" />
                                                        Delete
                                                </div>
                                        </div>
                                )}
                        </div>
                        <div className="Dashboard_project_description">
                            <div className="Dashboard_project_fade"></div>
                            <p><small> {trimSummary(project.summary)} </small></p>
                        </div>
                        <div className="Dashboard_project_footer">
                            <span className={`Dashboard_project_label ${statusInfo.className}`}>{statusInfo.text}</span>
                            <span className="Dashboard_project_date">
                                Last Updated: <time dateTime={date}>{date}</time>
                            </span>
                        </div>
                </article>
}
