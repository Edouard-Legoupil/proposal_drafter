import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'

function UserProbe() {
  const { user, activeTeam, roles, switchTeam } = useAuth()
  return (
    <div>
      <span>{user?.email || 'anonymous'}</span>
      <span>{activeTeam?.name || 'no team'}</span>
      <span>{roles.join(',')}</span>
      <button onClick={() => switchTeam('team-b')}>Switch team</button>
    </div>
  )
}

describe('AuthProvider', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads the authenticated profile for consumers', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ user: { email: 'user@example.com', is_admin: true } })
    })

    render(
      <AuthProvider>
        <UserProbe />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('user@example.com')).toBeInTheDocument()
    })
    expect(fetch).toHaveBeenCalledWith('/api/profile', {
      credentials: 'include'
    })
  })

  it('replaces the active team roles when the user switches teams', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: {
            email: 'user@example.com',
            memberships: [
              { id: 'team-a', name: 'Alpha' },
              { id: 'team-b', name: 'Beta' }
            ],
            active_team: { id: 'team-a', name: 'Alpha' },
            roles: ['access_template']
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          active_team: { id: 'team-b', name: 'Beta' },
          memberships: [
            { id: 'team-a', name: 'Alpha' },
            { id: 'team-b', name: 'Beta' }
          ],
          roles: ['access_metrics'],
          role_keys: ['access_metrics'],
          team_leadership: false,
          settings: {}
        })
      })

    render(<AuthProvider><UserProbe /></AuthProvider>)

    expect(await screen.findByText('access_template')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /switch team/i }))

    await waitFor(() => {
      expect(screen.getByText('Beta')).toBeInTheDocument()
      expect(screen.getByText('access_metrics')).toBeInTheDocument()
    })
    expect(screen.queryByText('access_template')).not.toBeInTheDocument()
    expect(fetch).toHaveBeenLastCalledWith('/api/profile/active-team', {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: 'team-b' })
    })
  })
})
