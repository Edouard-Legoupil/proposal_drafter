import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'

import UserSettingsModal from './UserSettingsModal'

describe('UserSettingsModal', () => {
  it('submits only self-service preferences and requested team memberships', async () => {
    let submitted
    const onClose = vi.fn()
    server.use(
      http.get('/api/users/me/settings', () => HttpResponse.json({
        geographic_coverage_type: 'regional',
        geographic_coverage_region: 'East Africa',
        geographic_coverage_country: null,
        team_memberships: ['approved-team'],
        requested_team_memberships: ['pending-team'],
        roles: [1]
      })),
      http.get('/api/teams', () => HttpResponse.json({
        teams: [
          { id: 'approved-team', name: 'Approved Team' },
          { id: 'pending-team', name: 'Pending Team' }
        ]
      })),
      http.get('/api/settings/requests/pending', () => HttpResponse.json({
        pending_requests: [
          { setting_type: 'team_membership', setting_value: 'pending-team' }
        ]
      })),
      http.get('/api/users/me/approved-settings', () => HttpResponse.json({ approved_settings: [] })),
      http.put('/api/users/me/settings', async ({ request }) => {
        submitted = await request.json()
        return new HttpResponse(null, { status: 204 })
      })
    )

    render(<UserSettingsModal show onClose={onClose} />)

    await screen.findByText('Approved Team')
    await userEvent.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(submitted).toEqual({
      geographic_coverage_type: 'regional',
      geographic_coverage_region: 'East Africa',
      geographic_coverage_country: null,
      requested_team_memberships: ['pending-team']
    })
    expect(submitted).not.toHaveProperty('roles')
    expect(submitted).not.toHaveProperty('team_memberships')
  })
})
