import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'
import { MemoryRouter } from 'react-router-dom'
import { WizardProvider } from '../../../context/WizardContext'

import UserAccessPanel from './UserAccessPanel'

describe('UserAccessPanel', () => {
  const mockUsers = [
    {
      id: 'user-1',
      name: 'Amina Nyongo',
      email: 'amina@example.com',
      team_name: 'Shelter Team',
      team_id: 'team-1',
      roles: [{ id: 'role-1', name: 'Editor' }],
      donor_groups: ['UNHCR'],
      outcomes: ['outcome-1'],
      field_contexts: ['field-1']
    },
    {
      id: 'user-2',
      name: 'Kiran Patel',
      email: 'kiran@example.com',
      team_name: 'Health Team',
      team_id: 'team-2',
      roles: [{ id: 'role-2', name: 'Reviewer' }],
      donor_groups: ['WHO'],
      outcomes: ['outcome-2'],
      field_contexts: ['field-2']
    }
  ]

  const mockOptions = {
    roles: [
      { id: 'role-1', name: 'Editor' },
      { id: 'role-2', name: 'Reviewer' },
      { id: 'role-3', name: 'Admin' }
    ],
    donor_groups: ['UNHCR', 'WHO', 'UNICEF'],
    outcomes: [
      { id: 'outcome-1', name: 'Shelter Provided' },
      { id: 'outcome-2', name: 'Health Improved' }
    ],
    field_contexts: [
      { id: 'field-1', name: 'Kenya' },
      { id: 'field-2', name: 'Sudan' }
    ],
    teams: [
      { id: 'team-1', name: 'Shelter Team' },
      { id: 'team-2', name: 'Health Team' }
    ],
    template_requests: []
  }

  const mockRoleRequests = [
    {
      user_id: 'user-1',
      user_name: 'Amina Nyongo',
      user_email: 'amina@example.com',
      requested_role_name: 'Admin',
      requested_at: '2026-05-20T10:00:00Z'
    }
  ]

  const mockSettingsRequests = [
    {
      request_id: 'req-1',
      user_id: 'user-2',
      user_name: 'Kiran Patel',
      user_email: 'kiran@example.com',
      setting_type: 'donor_focal',
      setting_value: 'UNICEF',
      display_name: 'UNICEF',
      requested_at: '2026-05-21T14:30:00Z'
    }
  ]

  beforeEach(() => {
    vi.spyOn(window, 'alert').mockImplementation(() => {})
    server.use(
      http.get('/api/admin/users', () =>
        HttpResponse.json(mockUsers, { status: 200 })
      ),
      http.get('/api/admin/options', () =>
        HttpResponse.json(mockOptions, { status: 200 })
      ),
      http.get('/api/admin/template-requests', () =>
        HttpResponse.json([], { status: 200 })
      ),
      http.get('/api/admin/role-requests', () =>
        HttpResponse.json(mockRoleRequests, { status: 200 })
      ),
      http.get('/api/admin/settings-requests', () =>
        HttpResponse.json(mockSettingsRequests, { status: 200 })
      )
    )
  })

  it('renders the user access management header', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/User Access Management/i)).toBeInTheDocument()
    expect(screen.getByText(/Manage users, teams, roles, and access settings/i)).toBeInTheDocument()
  })

  it('displays user statistics cards', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Total Users/i)).toBeInTheDocument()
    expect(screen.getByText(/^Teams$/i)).toBeInTheDocument()
  })

  it('displays user list with search functionality', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    // Wait for users to load
    await screen.findAllByText(/Amina Nyongo/i)
    const userTable = document.querySelector('.users-table')
    expect(within(userTable).getByText(/Amina Nyongo/i)).toBeInTheDocument()
    expect(within(userTable).getByText(/Kiran Patel/i)).toBeInTheDocument()

    // Test search functionality
    const searchInput = screen.getByPlaceholderText(/Search users by name, email or team…/i)
    fireEvent.change(searchInput, { target: { value: 'Amina' } })

    expect(within(userTable).getByText(/Amina Nyongo/i)).toBeInTheDocument()
    expect(within(userTable).queryByText(/Kiran Patel/i)).not.toBeInTheDocument()

    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } })
    expect(await within(userTable).findByText(/Kiran Patel/i)).toBeInTheDocument()
  })

  it('allows team creation', async () => {
    // Mock the team creation endpoint
    server.use(
      http.post('/api/admin/teams', () =>
        HttpResponse.json(
          { team: { id: 'team-3', name: 'New Team' } },
          { status: 200 }
        )
      )
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    const teamInput = screen.getByPlaceholderText(/New Team Name/i)
    const createButton = screen.getByText(/Create Team/i)

    fireEvent.change(teamInput, { target: { value: 'New Team' } })
    fireEvent.click(createButton)

    // Verify the team was created (input should be cleared)
    await waitFor(() => {
      expect(teamInput).toHaveValue('')
    })
  })

  it('shows bulk action toolbar when users are selected', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    // Wait for users to load
    const checkboxes = await screen.findAllByRole('checkbox')
    const userCheckbox = checkboxes.find(checkbox =>
      checkbox.closest('tr')?.textContent?.includes('Amina Nyongo')
    )

    if (userCheckbox) {
      fireEvent.click(userCheckbox)
      expect(await screen.findByText(/1 selected/i)).toBeInTheDocument()
      expect(screen.getByText(/Bulk action…/i)).toBeInTheDocument()
    }
  })

  it('displays pending role requests', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    const heading = await screen.findByRole('heading', { name: /Pending Role Requests/i })
    const section = heading.closest('.admin-section')
    expect(within(section).getByText(/Amina Nyongo/i)).toBeInTheDocument()
    expect(within(section).getByText(/Admin/i)).toBeInTheDocument()
    expect(within(section).getByText(/Review/i)).toBeInTheDocument()
  })

  it('displays pending settings requests', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    const heading = await screen.findByRole('heading', { name: /Pending Settings Requests/i })
    const section = heading.closest('.admin-section')
    expect(within(section).getByText(/Kiran Patel/i)).toBeInTheDocument()
    expect(within(section).getByText(/donor/i)).toBeInTheDocument()
    expect(within(section).getByText(/UNICEF/i)).toBeInTheDocument()
  })

  it('reviews and approves a pending settings request', async () => {
    let approvalRequest
    server.use(
      http.post('/api/admin/settings-requests/req-1/approve', ({ request }) => {
        approvalRequest = request
        return HttpResponse.json({
          user_id: 'user-2',
          user_name: 'Kiran Patel',
          setting_type: 'donor_focal',
          setting_value: 'UNICEF'
        })
      })
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    const heading = await screen.findByRole('heading', { name: /Pending Settings Requests/i })
    const section = heading.closest('.admin-section')
    fireEvent.click(within(section).getByRole('button', { name: /Review/i }))

    expect(screen.getByRole('heading', { name: /Settings Request Review/i })).toBeInTheDocument()
    expect(screen.getByText(/Kiran Patel/i, { selector: '.modal *' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText(/Admin Note/i), { target: { value: 'Approved for programme work' } })
    fireEvent.click(screen.getByRole('button', { name: /Approve Request/i }))

    await waitFor(() => expect(approvalRequest).toBeDefined())
    expect(new URL(approvalRequest.url).searchParams.get('admin_note')).toBe('Approved for programme work')
    await waitFor(() => expect(screen.queryByRole('heading', { name: /Settings Request Review/i })).not.toBeInTheDocument())
  })

  it('shows error message when data fetching fails', async () => {
    server.use(
      http.get('/api/admin/users', () =>
        HttpResponse.json(null, { status: 500 })
      )
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Failed to fetch admin data/i)).toBeInTheDocument()
  })

  it('displays loading state initially', async () => {
    // Slow down the response to see loading state
    server.use(
      http.get('/api/admin/users', async () => {
        await new Promise(resolve => setTimeout(resolve, 100))
        return HttpResponse.json(mockUsers, { status: 200 })
      })
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <UserAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(screen.getByText(/Loading users…/i)).toBeInTheDocument()
    expect((await screen.findAllByText(/Amina Nyongo/i)).length).toBeGreaterThan(0)
  })
})
