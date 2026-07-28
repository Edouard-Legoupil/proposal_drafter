import React from 'react'

function formatDetail(value) {
  if (value === null || value === undefined || value === '') return '—'
  if (Array.isArray(value)) return value.map(formatDetail).join(', ')
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([key, entry]) => `${key.replaceAll('_', ' ')}: ${formatDetail(entry)}`)
      .join(' · ')
  }
  return String(value)
}

export default function AuditTimeline({ events, emptyMessage = 'No audit events yet' }) {
  if (!events?.length) {
    return <div className="audit-empty">{emptyMessage}</div>
  }

  return (
    <ul className="audit-list">
      {events.map((event, index) => {
        const actor = event.actor_name || event.actor_user_id || event.performed_by || '—'
        const timestamp = event.timestamp || event.performed_at || event.created_at
        const detail = formatDetail(event.reason ?? event.detail ?? event.details)
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
