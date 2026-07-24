import React from 'react'

export default function AuditTimeline({ events, emptyMessage = 'No audit events yet' }) {
  if (!events?.length) {
    return <div className="audit-empty">{emptyMessage}</div>
  }

  return (
    <ul className="audit-list">
      {events.map((event, index) => {
        const actor = event.actor_name || event.actor_user_id || event.performed_by || '—'
        const timestamp = event.timestamp || event.performed_at || event.created_at
        const detail = event.reason || event.detail || event.details || '—'
        return <li key={event.id || event.event_id || index}>
          <div className="audit-headline">
            <strong>{event.action || event.event_type}</strong>
            <span>{actor}</span>
            <span className="audit-timestamp">{timestamp ? new Date(timestamp).toLocaleString() : '—'}</span>
          </div>
          <p>{detail}</p>
        </li>
      })}
    </ul>
  )
}
