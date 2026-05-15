import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'

import MetricsAccessPanel from './MetricsAccessPanel'

describe('MetricsAccessPanel', () => {
  it('renders dashboard heading', async () => {
    server.use(
      http.get('/api/admin/metrics/access/dashboard-1', () =>
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

    render(<MetricsAccessPanel resourceId="dashboard-1" />)

    expect(await screen.findByText(/Metrics Dashboard/i)).toBeInTheDocument()
  })
})
