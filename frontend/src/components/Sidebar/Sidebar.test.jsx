import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuth } from '../../context/AuthContext'
import Sidebar from './Sidebar'

vi.mock('../../context/AuthContext', () => ({ useAuth: vi.fn() }))

describe('Sidebar active-team access', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: true, json: async () => ({ teams: [] }) })
  })

  it('renders navigation only for roles in the active team context', () => {
    useAuth.mockReturnValue({
      user: { id: 'user-1', is_admin: false },
      roles: ['access_template'],
      activeTeam: { id: 'team-a', name: 'Alpha' }
    })

    render(<MemoryRouter><Sidebar isOpen /></MemoryRouter>)

    expect(screen.getByText('Donor Templates')).toBeInTheDocument()
    expect(screen.queryByText('Metrics')).not.toBeInTheDocument()
  })

  it('does not fetch or render teams outside the profile context', () => {
    useAuth.mockReturnValue({
      user: { id: 'user-1', is_admin: false },
      roles: ['project reviewer'],
      memberships: [{ id: 'team-a', name: 'Alpha' }]
    })

    render(<MemoryRouter><Sidebar isOpen /></MemoryRouter>)

    expect(fetch).not.toHaveBeenCalled()
  })
})
