import './DonorTemplate.css'

export default function DonorTemplate({ template, date, onClick, creator }) {
    const isPublished = template.status === 'published';
    
    let icon = <i className="fa-solid fa-file-invoice donor" aria-hidden="true"></i>;
    let label = "Template Request";
    
    if (isPublished) {
        icon = <i className="fa-solid fa-file-circle-check published-icon" aria-hidden="true"></i>;
        label = "Published Template";
    }

    return (
        <article className={`card donor-template-card ${template.status}`} onClick={onClick} data-testid="donor-template-card">
            <h3>
                <div className="template-type-header">
                    {icon}
                    <strong> {label}</strong>
                </div>
                <div className="template-name">{template.name}</div>
            </h3>
            
            {template.donor && (
                <p><small><strong>Donor:</strong> {template.donor}</small></p>
            )}
            
            {creator && (
                <p><small><strong>Requested by:</strong> {creator}</small></p>
            )}

            <div className="card-footer">
                <span className={`status-badge ${template.status}`}>{template.status}</span>
                {date && (
                    <span className="card-date">
                         {date}
                    </span>
                )}
            </div>
        </article>
    );
}
