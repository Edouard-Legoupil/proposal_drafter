import './Project.css'

export default function Project ({ project, date, onClick, isReview = false })
{
        const getStatusInfo = (status) => {
                switch (status) {
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

        const statusInfo = getStatusInfo(project.status);

        if (isReview) {
                return (
                        <article className="card" onClick={onClick}>
                                <h3 id={`review-${project.proposal_id}`}>{project.project_title}</h3>
                                <h2>Requester: {project.requester_name || 'N/A'}</h2>
                                <p><strong>Deadline:</strong> <time dateTime={project.deadline || ''}>{project.deadline || 'N/A'}</time></p>
                                <p><i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {project.form_data?.['Country / Location(s)'] || 'N/A'}</p>
                                <p><i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {project.form_data?.['Targeted Donor'] || 'N/A'}</p>
                                <p><i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {project.form_data?.['Main Outcome']?.join(', ') || 'N/A'}</p>
                        </article>
                )
        }

        return  <article className="card" onClick={onClick}>
                        <h3 id={`proj-${project.proposal_id}`}>{project.project_title}</h3>
                        <p>{project.summary || 'No summary available.'}</p>
                        <p><span className={`status-badge ${statusInfo.className}`}>{statusInfo.text}</span></p>
                        <p><i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i> {project.form_data?.['Country / Location(s)'] || 'N/A'}</p>
                        <p><i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i> {project.form_data?.['Targeted Donor'] || 'N/A'}</p>
                        <p><i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i> {project.form_data?.['Main Outcome']?.join(', ') || 'N/A'}</p>
                        <p><small>Last Updated: <time dateTime={date}>{date}</time></small></p>
                </article>
}
