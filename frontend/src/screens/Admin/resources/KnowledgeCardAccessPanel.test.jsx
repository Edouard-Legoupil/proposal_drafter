import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'
import { MemoryRouter } from 'react-router-dom'
import { WizardProvider } from '../../../context/WizardContext'

import KnowledgeCardAccessPanel from './KnowledgeCardAccessPanel'

describe('KnowledgeCardAccessPanel', () => {
  const mockKnowledgeCards = [
    {
      id: 'kc-1',
      title: 'Evacuation Plan for Sudan Crisis',
      status: 'draft',
      owner_name: 'Amina',
      type: 'evacuation',
      donor_name: 'UNHCR',
      updated_at: '2026-05-15T14:30:00Z'
    },
    {
      id: 'kc-2',
      title: 'Health Response Protocol',
      status: 'published',
      owner_name: 'Kiran',
      type: 'protocol',
      outcome_name: 'Health Improved',
      updated_at: '2026-05-10T09:15:00Z'
    }
  ]

  const mockAccessData = {
    knowledge_card: {
      id: 'kc-1',
      title: 'Evacuation Plan for Sudan Crisis',
      status: 'draft',
      owner: { id: 'owner-1', name: 'Amina Nyongo' },
      updated_at: '2026-05-15T14:30:00Z'
    },
    grants: [
      {
        id: 'grant-1',
        subject_id: 'user-2',
        subject_name: 'Kiran Patel',
        subject_type: 'user',
        permissions: ['read', 'write'],
        granted_by: 'owner-1',
        granted_at: '2026-05-14T10:00:00Z'
      }
    ],
    audit: [
      {
        id: 'audit-1',
        action: 'create',
        performed_by: 'Amina Nyongo',
        performed_at: '2026-05-15T14:30:00Z',
        details: 'Created knowledge card'
      },
      {
        id: 'audit-2',
        action: 'grant_access',
        performed_by: 'Amina Nyongo',
        performed_at: '2026-05-14T10:00:00Z',
        details: 'Granted read/write access to Kiran Patel'
      }
    ]
  }

  const mockUsers = [
    { id: 'owner-1', name: 'Amina Nyongo', email: 'amina@example.com' },
    { id: 'user-2', name: 'Kiran Patel', email: 'kiran@example.com' }
  ]

  const mockOptions = {
    roles: [],
    donor_groups: ['UNHCR', 'WHO'],
    outcomes: ['Health Improved', 'Shelter Provided'],
    field_contexts: ['Sudan', 'Kenya'],
    teams: []
  }

  beforeEach(() => {
    server.use(
      http.get('/api/admin/knowledge-cards/list', () =>
        HttpResponse.json(mockKnowledgeCards, { status: 200 })
      ),
      http.get('/api/admin/knowledge-cards/kc-1/access', () =>
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

  it('renders owner info after payload loads', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/owner:/i)).toBeInTheDocument()
    expect(await screen.findByText(/Evacuation Plan for Sudan Crisis/i)).toBeInTheDocument()
  })

  it('displays knowledge card details and metadata', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Evacuation Plan for Sudan Crisis/i)).toBeInTheDocument()
    const header = document.querySelector('.knowledge-card-access > header')
    expect(within(header).getByText(/Amina Nyongo/i)).toBeInTheDocument()
    expect(within(header).getByText(/Status: draft/i)).toBeInTheDocument()
    expect(within(header).getByText(/Owner:/i)).toBeInTheDocument()
  })

  it('shows existing grants for the knowledge card', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    await screen.findByRole('heading', { name: /Evacuation Plan for Sudan Crisis/i })
    const grants = document.querySelector('.grants-list')
    expect(within(grants).getByText(/Kiran Patel.*read, write/i)).toBeInTheDocument()
  })

  it('displays audit timeline with knowledge card history', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Audit Timeline/i)).toBeInTheDocument()
    expect(screen.getByText(/Created knowledge card/i)).toBeInTheDocument()
    expect(screen.getByText(/Granted read\/write access to Kiran Patel/i)).toBeInTheDocument()
  })

  it('allows granting access only to teams', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Grant Access/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Select a team/i).length).toBeGreaterThan(0)
    expect(screen.getByDisplayValue('Team')).toHaveAttribute('readonly')
  })

  it('tests effective access only for teams', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    await screen.findByRole('heading', { name: 'Tester' })
    const tester = document.querySelector('.tester-panel')
    const subjectType = within(tester).getByRole('combobox', { name: /Subject type/i })
    expect(subjectType).toHaveValue('team')
    expect(within(subjectType).getAllByRole('option')).toHaveLength(1)
  })

  it('shows knowledge card list when no specific card is selected', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="latest" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByRole('heading', { name: /Knowledge Cards.*Select a card/i })).toBeInTheDocument()
    expect(screen.getByText(/Evacuation Plan for Sudan Crisis/i)).toBeInTheDocument()
    expect(screen.getByText(/Health Response Protocol/i)).toBeInTheDocument()
  })

  it('displays error when knowledge card access data fails to load', async () => {
    server.use(
      http.get('/api/admin/knowledge-cards/kc-1/access', () =>
        HttpResponse.json(null, { status: 500 })
      )
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="kc-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Failed to load access data/i)).toBeInTheDocument()
  })

  it('shows different knowledge card types and metadata in list', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <KnowledgeCardAccessPanel resourceId="latest" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/^evacuation · UNHCR$/i)).toBeInTheDocument()
    expect(screen.getByText(/UNHCR/i)).toBeInTheDocument()
    expect(screen.getByText(/^protocol · Health Improved$/i)).toBeInTheDocument()
    expect(screen.getByText(/Health Improved/i)).toBeInTheDocument()
  })
})
