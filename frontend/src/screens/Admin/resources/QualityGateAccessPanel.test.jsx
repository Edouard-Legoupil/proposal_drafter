import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'

import QualityGateAccessPanel from './QualityGateAccessPanel'

describe('QualityGateAccessPanel', () => {
  it('renders header text', async () => {
    server.use(
      http.get('/api/admin/quality-gate/access/qg-1', () =>
        HttpResponse.json(
          { grants: [], audit: [] },
          { status: 200 }
        )
      ),
      http.get('/api/admin/users', () => HttpResponse.json([], { status: 200 })),
      http.get('/api/admin/options', () =>
        HttpResponse.json(
          { roles: [], donor_groups: [], outcomes: [], field_contexts: [], teams: [] },
          { status: 200 }
        )
      )
    )

    render(<QualityGateAccessPanel resourceId="qg-1" />)

    expect(await screen.findByText(/Quality Gate \/ Incident Access/i)).toBeInTheDocument()
  })
})
