import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'
import { MemoryRouter } from 'react-router-dom'
import { WizardProvider } from '../../../context/WizardContext'

import ProposalAccessPanel from './ProposalAccessPanel'

describe('ProposalAccessPanel', () => {
  const mockProposals = [
    {
      id: 'abc123',
      title: 'Shelter Proposal',
      status: 'Draft',
      owner_name: 'Amina Nyongo',
      updated_at: '2026-05-13T09:00:00Z'
    },
    {
      id: 'def456',
      title: 'Health Proposal',
      status: 'Review',
      owner_name: 'Kiran Patel',
      updated_at: '2026-05-14T10:30:00Z'
    }
  ]

  const mockAccessData = {
    proposal: {
      id: 'abc123',
      title: 'Shelter Proposal',
      status: 'Draft',
      owner: { id: 'owner-1', name: 'Amina Nyongo' },
      updated_at: '2026-05-13T09:00:00Z'
    },
    grants: [
      {
        id: 'grant-1',
        subject_id: 'user-2',
        subject_name: 'Kiran Patel',
        subject_type: 'user',
        permissions: ['read', 'write'],
        granted_by: 'admin-1',
        granted_at: '2026-05-12T08:00:00Z'
      }
    ],
    audit: [
      {
        id: 'audit-1',
        action: 'grant_access',
        performed_by: 'Amina Nyongo',
        performed_at: '2026-05-12T08:00:00Z',
        details: 'Granted read/write access to Kiran Patel'
      }
    ]
  }

  const mockUsers = [
    { id: 'owner-1', name: 'Amina Nyongo', email: 'amina@example.com' },
    { id: 'user-2', name: 'Kiran Patel', email: 'kiran@example.com' },
    { id: 'user-3', name: 'Leila Chen', email: 'leila@example.com' }
  ]

  const mockOptions = {
    roles: [
      { id: 'role-1', name: 'Editor' },
      { id: 'role-2', name: 'Reviewer' }
    ],
    donor_groups: ['UNHCR', 'WHO'],
    outcomes: [],
    field_contexts: [],
    teams: [
      { id: 'team-1', name: 'Shelter Team' },
      { id: 'team-2', name: 'Health Team' }
    ]
  }

  beforeEach(() => {
    server.use(
      http.get('/api/admin/proposals/list', () =>
        HttpResponse.json(mockProposals, { status: 200 })
      ),
      http.get('/api/admin/proposals/abc123/access', () =>
        HttpResponse.json(mockAccessData, { status: 200 })
      ),
      http.get('/api/admin/users', () =>
        HttpResponse.json(mockUsers, { status: 200 })
      ),
      http.get('/api/admin/options', () =>
        HttpResponse.json(mockOptions, { status: 200 })
      )
    )
  })

  it('shows owner after fetching access payload', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel resourceId="abc123" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/owner:/i)).toBeInTheDocument()
    expect(await screen.findByText(/Shelter Proposal/i)).toBeInTheDocument()
  })

  it('displays proposal details and owner information', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel resourceId="abc123" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Shelter Proposal/i)).toBeInTheDocument()
    expect(screen.getByText(/Amina Nyongo/i)).toBeInTheDocument()
    expect(screen.getByText(/Draft/i)).toBeInTheDocument()
    expect(screen.getByText(/Owner/i)).toBeInTheDocument()
  })

  it('shows existing grants and access permissions', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel resourceId="abc123" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Kiran Patel/i)).toBeInTheDocument()
    expect(screen.getByText(/read/i)).toBeInTheDocument()
    expect(screen.getByText(/write/i)).toBeInTheDocument()
  })

  it('displays audit timeline with access history', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel resourceId="abc123" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Audit Timeline/i)).toBeInTheDocument()
    expect(screen.getByText(/Granted read\/write access to Kiran Patel/i)).toBeInTheDocument()
    expect(screen.getByText(/Amina Nyongo/i)).toBeInTheDocument()
  })

  it('allows adding new grants to users', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel resourceId="abc123" />
        </MemoryRouter>
      </WizardProvider>
    )

    // Wait for the panel to load
    expect(await screen.findByText(/Shelter Proposal/i)).toBeInTheDocument()

    // Check for grant section
    expect(screen.getByText(/Grant Access/i)).toBeInTheDocument()
    expect(screen.getByText(/Select a user or team/i)).toBeInTheDocument()
  })

  it('shows error when proposal access data fails to load', async () => {
    server.use(
      http.get('/api/admin/proposals/abc123/access', () =>
        HttpResponse.json(null, { status: 500 })
      )
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel resourceId="abc123" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Failed to load access data/i)).toBeInTheDocument()
  })

  it('handles proposal list loading and selection', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <ProposalAccessPanel />
        </MemoryRouter>
      </WizardProvider>
    )

    // Should show resource picker when no resourceId is provided
    expect(await screen.findByText(/Select a Proposal/i)).toBeInTheDocument()
    expect(screen.getByText(/Shelter Proposal/i)).toBeInTheDocument()
    expect(screen.getByText(/Health Proposal/i)).toBeInTheDocument()
  })
})
