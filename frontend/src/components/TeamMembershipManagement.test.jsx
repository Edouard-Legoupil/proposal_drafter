import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useTeamMembership } from '../hooks/useTeamMembership'
import { TeamMembershipManagement } from './TeamMembershipManagement'

vi.mock('../hooks/useTeamMembership', () => ({
  useTeamMembership: vi.fn()
}))

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: null })
}))

describe('TeamMembershipManagement', () => {
  it('renders an empty state when no team is selected', () => {
    useTeamMembership.mockReturnValue({
      isLoading: false,
      error: null,
      getPendingRequests: vi.fn(),
      approveMembership: vi.fn(),
      rejectMembership: vi.fn(),
      getTeamRoles: vi.fn(),
      assignRoleToTeam: vi.fn(),
      removeRoleFromTeam: vi.fn(),
      canApproveMembership: vi.fn(() => false),
      canManageTeamRoles: vi.fn(() => false)
    })

    render(<TeamMembershipManagement team={null} />)

    expect(screen.getByText('No team selected')).toBeInTheDocument()
  })
})
