import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'

import KnowledgeCardAccessPanel from './KnowledgeCardAccessPanel'

describe('KnowledgeCardAccessPanel', () => {
  it('renders owner info after payload loads', async () => {
    server.use(
      http.get('/api/admin/knowledge-cards/list', () =>
        HttpResponse.json(
          [{ id: 'kc-1', title: 'Evacuation Plan', status: 'draft', owner_name: 'Amina' }],
          { status: 200 }
        )
      ),
      http.get('/api/admin/knowledge-cards/kc-1/access', () =>
        HttpResponse.json(
          {
            knowledge_card: {
              id: 'kc-1',
              title: 'Evacuation Plan',
              owner: { id: 'owner-1', name: 'Amina' }
            },
            grants: [],
            audit: []
          },
          { status: 200 }
        )
      ),
      http.get('/api/admin/users', () =>
        HttpResponse.json(
          [{ id: 'owner-1', name: 'Amina' }],
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

    render(<KnowledgeCardAccessPanel resourceId="kc-1" />)

    expect(await screen.findByText(/owner:/i)).toBeInTheDocument()
    expect(await screen.findByText(/Evacuation Plan/i)).toBeInTheDocument()
  })
})
