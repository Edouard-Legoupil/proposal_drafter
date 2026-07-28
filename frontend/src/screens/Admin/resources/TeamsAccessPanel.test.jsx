import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { server } from '../../../mocks/server'
import TeamsAccessPanel from './TeamsAccessPanel'

vi.mock('../../../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 'admin-1', is_admin: true } })
}))
vi.mock('../../../components/TeamMembershipManagement', () => ({
  TeamMembershipManagement: ({ team }) => <div>Managing {team.name}</div>
}))

describe('TeamsAccessPanel', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/teams', () => HttpResponse.json({ teams: [
        { id: 'team-1', name: 'Shelter', description: 'Shelter team' },
        { id: 'team-2', name: 'Health', description: 'Health team' }
      ] }))
    )
  })

  it('searches teams and creates one through the canonical API', async () => {
    const user = userEvent.setup()
    let createdPayload
    server.use(http.post('/api/teams', async ({ request }) => {
      createdPayload = await request.json()
      return HttpResponse.json({ id: 'team-3', ...createdPayload }, { status: 201 })
    }))

    render(<TeamsAccessPanel />)
    expect(await screen.findByText('Shelter')).toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText(/search teams/i), { target: { value: 'Health' } })
    expect(screen.queryByText('Shelter')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /create team/i }))
    await user.clear(screen.getByLabelText(/team name/i))
    await user.type(screen.getByLabelText(/team name/i), 'Protection')
    await user.type(screen.getByLabelText(/description/i), 'Protection team')
    await user.click(screen.getByRole('button', { name: /^create$/i }))

    await waitFor(() => expect(createdPayload).toEqual({ name: 'Protection', description: 'Protection team' }))
  })

  it('surfaces dependent-resource conflicts when deleting a team', async () => {
    const user = userEvent.setup()
    server.use(http.delete('/api/teams/team-1', () =>
      HttpResponse.json({ detail: { message: 'Team owns protected resources.' } }, { status: 409 })
    ))

    render(<TeamsAccessPanel />)
    await user.click(await screen.findByRole('button', { name: /manage shelter/i }))
    await user.click(screen.getByRole('button', { name: /delete team/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/protected resources/i)
  })
})
