import React from 'react'
import { render, screen } from '@testing-library/react'

import AuditTimeline from './AuditTimeline'

describe('AuditTimeline', () => {
  it('renders structured audit details as readable text', () => {
    render(
      <AuditTimeline
        events={[{
          id: 'event-1',
          action: 'grant_updated',
          actor_id: 'admin-1',
          details: {
            subject_type: 'team',
            subject_id: 'team-123',
            permissions: ['read', 'edit'],
            data_scope: 'team'
          },
          created_at: '2026-07-28T10:00:00Z'
        }]}
      />
    )

    expect(screen.getByText('grant_updated')).toBeInTheDocument()
    expect(screen.getByText(/subject type: team/i)).toBeInTheDocument()
    expect(screen.getByText(/subject id: team-123/i)).toBeInTheDocument()
    expect(screen.getByText(/permissions: read, edit/i)).toBeInTheDocument()
  })
})
