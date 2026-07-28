import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useTeamMembership } from '../hooks/useTeamMembership'
import { TeamMembershipManagement } from './TeamMembershipManagement'

vi.mock('../hooks/useTeamMembership', () => ({
  useTeamMembership: vi.fn()
}))

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: null })
}))

describe('TeamMembershipManagement', () => {
  let membership

  beforeEach(() => {
    membership = {
      isLoading: false,
      error: null,
      getMembers: vi.fn().mockResolvedValue([
        { user_id: 'user-1', name: 'Amina', email: 'amina@example.com', is_leader: false }
      ]),
      getAvailableUsers: vi.fn().mockResolvedValue([
        { id: 'user-3', name: 'Leila', email: 'leila@example.com' }
      ]),
      addMember: vi.fn().mockResolvedValue(true),
      getPendingRequests: vi.fn().mockResolvedValue([
        { user_id: 'user-2', user_name: 'Kiran', user_email: 'kiran@example.com' }
      ]),
      approveMembership: vi.fn().mockResolvedValue(true),
      rejectMembership: vi.fn().mockResolvedValue(true),
      removeMember: vi.fn().mockResolvedValue(true),
      assignLeader: vi.fn().mockResolvedValue(true),
      removeLeader: vi.fn().mockResolvedValue(true),
      getAvailableRoles: vi.fn().mockResolvedValue([
        { role_key: 'access_template', name: 'Template access', component: 'TemplateWorkspace' },
        { role_key: 'TEAM_LEADER', name: 'Team leader', component: null }
      ]),
      getTeamRoles: vi.fn().mockResolvedValue([
        { role_key: 'access_template', name: 'Template access', component: 'TemplateWorkspace' }
      ]),
      assignRoleToTeam: vi.fn().mockResolvedValue(true),
      removeRoleFromTeam: vi.fn().mockResolvedValue(true),
      canApproveMembership: vi.fn(() => true),
      canManageTeamRoles: vi.fn(() => true)
    }
    useTeamMembership.mockReturnValue(membership)
  })

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

  it('loads members, requests, and static component roles from the API', async () => {
    render(<TeamMembershipManagement team={{ id: 'team-1', name: 'Shelter' }} />)

    expect(await screen.findByText(/Amina.*amina@example.com/i)).toBeInTheDocument()
    expect(await screen.findByText(/Kiran.*kiran@example.com/i)).toBeInTheDocument()
    expect(await screen.findByText('Template access')).toBeInTheDocument()
    expect(screen.getByText('TemplateWorkspace')).toBeInTheDocument()
    expect(screen.getByText(/TEAM_LEADER is assigned per member/i)).toBeInTheDocument()
    expect(membership.getAvailableRoles).toHaveBeenCalled()
  })

  it('uses member-scoped leader actions and role keys', async () => {
    const user = userEvent.setup()
    membership.getTeamRoles.mockResolvedValue([])
    render(<TeamMembershipManagement team={{ id: 'team-1', name: 'Shelter' }} />)

    await user.click(await screen.findByRole('button', { name: /make Amina team leader/i }))
    expect(membership.assignLeader).toHaveBeenCalledWith('team-1', 'user-1')

    await user.click(screen.getByRole('button', { name: /assign Template access/i }))
    expect(membership.assignRoleToTeam).toHaveBeenCalledWith('team-1', 'access_template')
  })

  it('adds a selected user through the canonical membership API', async () => {
    const user = userEvent.setup()
    render(<TeamMembershipManagement team={{ id: 'team-1', name: 'Shelter' }} />)

    const picker = await screen.findByRole('combobox', { name: /user to add/i })
    await user.selectOptions(picker, 'user-3')
    await user.click(screen.getByRole('button', { name: /add member/i }))

    expect(membership.addMember).toHaveBeenCalledWith('team-1', 'user-3')
  })
})
