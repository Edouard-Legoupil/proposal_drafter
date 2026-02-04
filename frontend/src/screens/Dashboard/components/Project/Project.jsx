import './Project.css'
import { useState } from 'react';

import view from '../../../../assets/images/dashboard-fileIcon.svg';
import bin from '../../../../assets/images/delete.svg';
import transfer from '../../../../assets/images/prop.svg';
import tripleDots from '../../../../assets/images/dashboard-tripleDots.svg';


export default function Project({ project, date, onClick, isReview = false, projectIndex, handleDeleteProject, handleRestoreProject, handleTransferOwnership }) {
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
                        case 'pre_submission':
                                return { text: 'Pre-Submission', className: 'status-pre-submission' };
                        case 'submission':
                                return { text: 'Pending Submission', className: 'status-submission' };
                        case 'submitted':
                                return { text: 'Submitted', className: 'status-submitted' };
                        case 'approved':
                                return { text: 'Approved', className: 'status-approved' };
                        case 'deleted':
                                return { text: 'Deleted', className: 'status-deleted' };
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
                                <div className="Dashboard_project_title">
                                        <h3 id={`review-${project.proposal_id}`}>{project.project_title}</h3>
                                        {!isReview &&
                                                <button className="Dashboard_project_tripleDotsContainer" onClick={togglePopover} aria-haspopup="true" aria-expanded={popoverVisible} data-testid="project-options-button">
                                                        <img src={tripleDots} alt="Options" />
                                                </button>
                                        }
                                        <div className={`Project_optionsPopover ${popoverVisible ? 'visible' : ''}`} id={`popover-${projectIndex + 1}`} >
                                                <div className={`Project_optionsPopover_option`} onClick={(e) => { e.stopPropagation(); onClick(e); }} data-testid="project-view-button">
                                                        <img src={view} alt="View" />
                                                        View
                                                </div>
                                                {project.status === 'deleted' ? (
                                                        <div className={`Project_optionsPopover_option`} onClick={(e) => { e.stopPropagation(); handleRestoreProject(project.proposal_id); setPopoverVisible(false); }} data-testid="project-restore-button">
                                                                <i className="fa-solid fa-trash-arrow-up" style={{ width: '20px', marginRight: '10px' }}></i>
                                                                Restore
                                                        </div>
                                                ) : (
                                                        <>
                                                                <div className={`Project_optionsPopover_option ${project.status === 'in_review' ? 'disabled' : ''}`} onClick={(e) => { e.stopPropagation(); if (project.status !== 'in_review') { handleTransferOwnership(project.proposal_id) } }} data-testid="project-transfer-button">
                                                                        <img className='Project_optionsPopover_option_transfer' src={transfer} alt="Transfer" />
                                                                        Transfer
                                                                </div>
                                                                <div className={`Project_optionsPopover_option ${project.status === 'in_review' ? 'disabled' : ''}`} onClick={(e) => { e.stopPropagation(); if (project.status !== 'in_review') { handleDeleteProject(project.proposal_id) } }} data-testid="project-delete-button">
                                                                        <img className='Project_optionsPopover_option_delete' src={bin} alt="Delete" />
                                                                        Delete
                                                                </div>
                                                        </>
                                                )}
                                        </div>
                                </div>
                                <h2>Author: {project.author_name || 'N/A'}</h2>
                                {project.review_status === 'completed' ? (
                                        <p><strong>Completed on:</strong> <time dateTime={project.review_completed_at}>{new Date(project.review_completed_at).toLocaleDateString()}</time></p>
                                ) : (
                                        project.deadline && <p><strong>Deadline:</strong> <time dateTime={project.deadline}>{new Date(project.deadline).toLocaleDateString()}</time></p>
                                )}
                                <p>
                                        <i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {project.country || 'N/A'} -
                                        <i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {project.donor || 'N/A'} -
                                        <i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {project.outcomes?.join(', ') || 'N/A'} -
                                        <i className="fa-solid fa-money-check-dollar" aria-hidden="true"></i> Budget: {project.budget || 'N/A'}
                                </p>
                        </article>
                )
        }

        return <article className={`Dashboard_project ${popoverVisible ? 'popover-active' : ''}`} onClick={onClick} data-testid="project-card">
                <div className="Dashboard_project_title">
                        <h3 id={`proj-${project.proposal_id}`}>{project.project_title}</h3>
                        <button className="Dashboard_project_tripleDotsContainer" onClick={togglePopover} aria-haspopup="true" aria-expanded={popoverVisible} data-testid="project-options-button">
                                <img src={tripleDots} alt="Options" />
                        </button>
                        <div className={`Project_optionsPopover ${popoverVisible ? 'visible' : ''}`} id={`popover-${projectIndex + 1}`} >
                                <div className={`Project_optionsPopover_option`} onClick={(e) => { e.stopPropagation(); onClick(e); }} data-testid="project-view-button">
                                        <img src={view} alt="View" />
                                        View
                                </div>
                                {project.status === 'deleted' ? (
                                        <div className={`Project_optionsPopover_option`} onClick={(e) => { e.stopPropagation(); handleRestoreProject(project.proposal_id); setPopoverVisible(false); }} data-testid="project-restore-button">
                                                <i className="fa-solid fa-trash-arrow-up" style={{ width: '20px', marginRight: '10px' }}></i>
                                                Restore
                                        </div>
                                ) : (
                                        <>
                                                <div className={`Project_optionsPopover_option ${project.status === 'in_review' ? 'disabled' : ''}`} onClick={(e) => { e.stopPropagation(); if (project.status !== 'in_review') { handleTransferOwnership(project.proposal_id) } }} data-testid="project-transfer-button">
                                                        <img className='Project_optionsPopover_option_transfer' src={transfer} alt="Transfer" />
                                                        Transfer
                                                </div>
                                                <div className={`Project_optionsPopover_option ${project.status === 'in_review' ? 'disabled' : ''}`} onClick={(e) => { e.stopPropagation(); if (project.status !== 'in_review') { handleDeleteProject(project.proposal_id) } }} data-testid="project-delete-button">
                                                        <img className='Project_optionsPopover_option_delete' src={bin} alt="Delete" />
                                                        Delete
                                                </div>
                                        </>
                                )}
                        </div>
                </div>
                <p>
                        <i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {project.country || 'N/A'} -
                        <i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {project.donor || 'N/A'} -
                        <i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {project.outcomes?.join(', ') || 'N/A'} -
                        <i className="fa-solid fa-money-check-dollar" aria-hidden="true"></i> Budget: {project.budget || 'N/A'}
                </p>
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
