import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'

import ProposalAccessPanel from './ProposalAccessPanel'

describe('ProposalAccessPanel', () => {
  it('shows owner after fetching access payload', async () => {
    server.use(
      http.get('/api/admin/proposals/list', () =>
        HttpResponse.json(
          [{ id: 'abc123', title: 'Shelter Proposal', status: 'Draft', owner_name: 'Amina Nyongo' }],
          { status: 200 }
        )
      ),
      http.get('/api/admin/proposals/abc123/access', () =>
        HttpResponse.json(
          {
            proposal: {
              id: 'abc123',
              title: 'Shelter Proposal',
              status: 'Draft',
              owner: { id: 'owner-1', name: 'Amina Nyongo' },
              updated_at: '2026-05-13T09:00:00Z'
            },
            grants: [],
            audit: []
          },
          { status: 200 }
        )
      ),
      http.get('/api/admin/users', () =>
        HttpResponse.json(
          [
            { id: 'owner-1', name: 'Amina Nyongo' },
            { id: 'user-2', email: 'leila@example.com' }
          ],
          { status: 200 }
        )
      ),
      http.get('/api/admin/options', () =>
        HttpResponse.json(
          { roles: [], donor_groups: [], outcomes: [], field_contexts: [], teams: [] },
          { status: 200 }
        )
      )
    )

    // Resource picker shown first — find and click a resource
    render(<ProposalAccessPanel resourceId="abc123" />)

    expect(await screen.findByText(/owner:/i)).toBeInTheDocument()
    expect(await screen.findByText(/Shelter Proposal/i)).toBeInTheDocument()
  })
})
