import './KnowledgeCard.css'

export default function KnowledgeCard({ card, onClick }) {
    let linked_to_element;

    if (card.donor_name) {
        linked_to_element = (
            <p>
                <i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i>
                <strong>Linked To:</strong> Donor: {card.donor_name}
            </p>
        );
    } else if (card.outcome_name) {
        linked_to_element = (
            <p>
                <i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i>
                <strong>Linked To:</strong> Outcome: {card.outcome_name}
            </p>
        );
    } else if (card.field_context_name) {
        linked_to_element = (
            <p>
                <i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i>
                <strong>Linked To:</strong> Field Context: {card.field_context_name}
            </p>
        );
    } else {
        linked_to_element = <p><strong>Linked To:</strong> Not Linked</p>;
    }


    return (
        <article className="card" onClick={onClick} data-testid="knowledge-card">
            <h3 id={`kc-${card.id}`}>{card.title}</h3>
            <p><small>{card.summary || 'No summary.'}</small></p>
            {linked_to_element}
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
