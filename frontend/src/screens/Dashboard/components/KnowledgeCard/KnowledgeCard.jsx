import './KnowledgeCard.css'

export default function KnowledgeCard({ card, onClick }) {
    const linked_to = card.donor_name ? `Donor: ${card.donor_name}`
                    : card.outcome_name ? `Outcome: ${card.outcome_name}`
                    : card.field_context_name ? `Field Context: ${card.field_context_name}`
                    : 'Not Linked';

    return (
        <article className="card" onClick={onClick}>
            <h3 id={`kc-${card.id}`}>{card.title}</h3>
            <p><small>{card.summary || 'No summary.'}</small></p>
            <p><strong>Linked To:</strong> {linked_to}</p>
            {card.references && card.references.length > 0 && (
                <div className='card-references'>
                    <strong>References:</strong>
                    <ul>
                        {card.references.map((ref, i) => (
                            <li key={i}><a href={ref.url} target="_blank" rel="noopener noreferrer">{ref.url}</a> ({ref.reference_type})</li>
                        ))}
                    </ul>
                </div>
            )}
        </article>
    );
}
