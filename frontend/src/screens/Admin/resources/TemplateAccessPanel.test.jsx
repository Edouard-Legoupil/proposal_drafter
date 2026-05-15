import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'

import TemplateAccessPanel from './TemplateAccessPanel'

describe('TemplateAccessPanel', () => {
  it('renders owner info', async () => {
    server.use(
      http.get('/api/admin/templates/list', () =>
        HttpResponse.json(
          [{ id: 'tpl-1', name: 'Shelter Template', status: 'active', owner_name: 'Kiran' }],
          { status: 200 }
        )
      ),
      http.get('/api/admin/templates/tpl-1/access', () =>
        HttpResponse.json(
          {
            template: {
              id: 'tpl-1',
              title: 'Shelter Template',
              owner: { id: 'owner-2', name: 'Kiran' },
              visibility: 'organization'
            },
            grants: [],
            audit: []
          },
          { status: 200 }
        )
      ),
      http.get('/api/admin/users', () =>
        HttpResponse.json(
          [{ id: 'owner-2', name: 'Kiran' }],
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

    render(<TemplateAccessPanel resourceId="tpl-1" />)

    expect(await screen.findByText(/owner:/i)).toBeInTheDocument()
    expect(await screen.findByText(/Shelter Template/i)).toBeInTheDocument()
  })
})
