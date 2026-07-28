import { fireEvent, render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { server } from '../../../mocks/server'
import UserAccessPanel from './UserAccessPanel'

describe('UserAccessPanel membership overview', () => {
  beforeEach(() => {
    server.use(http.get('/api/admin/users', () => HttpResponse.json([
      { id: 'user-1', name: 'Amina', email: 'amina@example.com', memberships: [{ id: 'team-1', name: 'Shelter', status: 'ACTIVE' }] },
      { id: 'user-2', name: 'Kiran', email: 'kiran@example.com', memberships: [] }
    ])))
  })

  it('shows membership-centric user information without direct role controls', async () => {
    render(<UserAccessPanel />)
    expect(await screen.findByText('Amina')).toBeInTheDocument()
    expect(screen.getByText('Shelter (ACTIVE)')).toBeInTheDocument()
    expect(screen.getByText(/manage membership and roles from teams/i)).toBeInTheDocument()
    expect(screen.queryByText(/assign direct role/i)).not.toBeInTheDocument()
  })

  it('searches users by name or email', async () => {
    render(<UserAccessPanel />)
    await screen.findByText('Amina')
    fireEvent.change(screen.getByPlaceholderText(/search users/i), { target: { value: 'Kiran' } })
    expect(screen.getByText('Kiran')).toBeInTheDocument()
    expect(screen.queryByText('Amina')).not.toBeInTheDocument()
  })
})
