import React from 'react'

export default function AuditTimeline({ events, emptyMessage = 'No audit events yet' }) {
  if (!events?.length) {
    return <div className="audit-empty">{emptyMessage}</div>
  }

  return (
    <ul className="audit-list">
      {events.map(event => (
        <li key={event.id || event.event_id}>
          <div className="audit-headline">
            <strong>{event.action || event.event_type}</strong>
            <span>{event.actor_name || event.actor_user_id}</span>
            <span className="audit-timestamp">{event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'}</span>
          </div>
          <p>{event.reason || event.detail || '—'}</p>
        </li>
      ))}
    </ul>
  )
}
