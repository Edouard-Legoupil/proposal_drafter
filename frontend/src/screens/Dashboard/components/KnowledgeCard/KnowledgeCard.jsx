import './KnowledgeCard.css'

export default function KnowledgeCard({ card, date, onClick, isDuplicate, onDelete }) {
    let linked_to_element;
    let title = card.summary;

    if (card.donor_name) {
        title = `Donor: ${card.donor_name}`;
        linked_to_element = (
            <><p>
                <i className="fa-solid fa-money-bill-wave donor" aria-hidden="true"></i>
                <strong> Donor Card</strong>
            </p><p>
                    {card.donor_name}
                </p></>
        );
    } else if (card.outcome_name) {
        title = `Outcome: ${card.outcome_name}`;
        linked_to_element = (
            <><p>
                <i className="fa-solid fa-bullseye outcome" aria-hidden="true"></i>
                <strong> Outcome Card</strong>
            </p><p>
                    {card.outcome_name}
                </p></>
        );
    } else if (card.field_context_name) {
        title = `Field Context: ${card.field_context_name}`;
        linked_to_element = (
            <><p>
                <i className="fa-solid fa-earth-americas field-context" aria-hidden="true"></i>
                <strong> Field Context Card</strong>
            </p><p>
                    {card.field_context_name}
                </p></>
        );
    } else {
        linked_to_element = <p><strong>Type </strong> Missing... </p>;
    }


    return (
        <article className="card" onClick={onClick} data-testid="knowledge-card">
            {isDuplicate && (
                <div className="duplicate-container">
                    <span className="duplicate-badge">Duplicate</span>
                    <button
                        className="delete-button"
                        onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm('Are you sure you want to delete this duplicate card?')) {
                                onDelete();
                            }
                        }}
                    >
                        Delete
                    </button>
                </div>
            )}
            <h3 id={`kc-${card.id}`}>{linked_to_element}</h3>
            <p><small>{card.summary || 'No description.'}</small></p>
            <span className="ard-references_date">
                Last Updated: <time dateTime={date}>{date}</time>
            </span>
        </article>
    );
}
