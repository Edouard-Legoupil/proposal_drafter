import { describe, it, expect } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'
import { MemoryRouter } from 'react-router-dom'
import { WizardProvider } from '../../../context/WizardContext'

import TemplateAccessPanel from './TemplateAccessPanel'

describe('TemplateAccessPanel', () => {
  const mockTemplates = [
    {
      id: 'tpl-1',
      name: 'Shelter Template',
      status: 'active',
      owner_name: 'Kiran',
      template_type: 'donor',
      is_default: false,
      updated_at: '2026-05-12T14:00:00Z'
    },
    {
      id: 'tpl-2',
      name: 'Health Response Template',
      status: 'draft',
      owner_name: 'Amina',
      template_type: 'outcome',
      is_default: true,
      updated_at: '2026-05-10T09:30:00Z'
    }
  ]

  const mockAccessData = {
    template: {
      id: 'tpl-1',
      title: 'Shelter Template',
      name: 'Shelter Template',
      status: 'active',
      owner: { id: 'owner-2', name: 'Kiran Patel' },
      visibility: 'organization',
      template_type: 'donor',
      updated_at: '2026-05-12T14:00:00Z'
    },
    grants: [
      {
        id: 'grant-1',
        subject_id: 'user-1',
        subject_name: 'Amina Nyongo',
        subject_type: 'user',
        permissions: ['read', 'edit'],
        granted_by: 'owner-2',
        granted_at: '2026-05-11T10:00:00Z'
      }
    ],
    audit: [
      {
        id: 'audit-1',
        action: 'create',
        performed_by: 'Kiran Patel',
        performed_at: '2026-05-12T14:00:00Z',
        details: 'Created template'
      },
      {
        id: 'audit-2',
        action: 'grant_access',
        performed_by: 'Kiran Patel',
        performed_at: '2026-05-11T10:00:00Z',
        details: 'Granted read/edit access to Amina Nyongo'
      }
    ]
  }

  const mockUsers = [
    { id: 'owner-2', name: 'Kiran Patel', email: 'kiran@example.com' },
    { id: 'user-1', name: 'Amina Nyongo', email: 'amina@example.com' },
    { id: 'user-3', name: 'Leila Chen', email: 'leila@example.com' }
  ]

  const mockOptions = {
    roles: [],
    donor_groups: ['UNHCR', 'WHO'],
    outcomes: ['Health Improved', 'Shelter Provided'],
    field_contexts: ['Sudan', 'Kenya'],
    teams: [
      { id: 'team-1', name: 'Shelter Team' },
      { id: 'team-2', name: 'Health Team' }
    ]
  }

  beforeEach(() => {
    server.use(
      http.get('/api/admin/templates/list', () =>
        HttpResponse.json(mockTemplates, { status: 200 })
      ),
      http.get('/api/admin/templates/tpl-1/access', () =>
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

  it('renders owner info', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    // Wait for loading to complete and check for content
    await waitFor(async () => {
      expect(await screen.findByText(/Owner:/i)).toBeInTheDocument()
      expect(await screen.findByText(/Shelter Template/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('displays template details and owner information', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Shelter Template/i)).toBeInTheDocument()
    const header = document.querySelector('.template-access > header')
    expect(within(header).getByText(/Kiran Patel/i)).toBeInTheDocument()
    expect(within(header).getByText(/Status: active/i)).toBeInTheDocument()
    expect(within(header).getByText(/Owner:/i)).toBeInTheDocument()
    expect(within(header).getByText(/Visibility: organization/i)).toBeInTheDocument()
  })

  it('shows existing grants and permissions for the template', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    await screen.findByRole('heading', { name: /Shelter Template/i })
    const grants = document.querySelector('.grants-list')
    expect(within(grants).getByText(/Amina Nyongo.*read, edit/i)).toBeInTheDocument()
  })

  it('displays audit timeline with template history', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Audit Timeline/i)).toBeInTheDocument()
    expect(screen.getByText(/Created template/i)).toBeInTheDocument()
    expect(screen.getByText(/Granted read\/edit access to Amina Nyongo/i)).toBeInTheDocument()
  })

  it('allows granting access only to teams', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
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
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    await screen.findByRole('heading', { name: 'Tester' })
    const tester = document.querySelector('.tester-panel')
    const subjectType = within(tester).getByRole('combobox', { name: /Subject type/i })
    expect(subjectType).toHaveValue('team')
    expect(within(subjectType).getAllByRole('option')).toHaveLength(1)
  })

  it('shows template list with types and status when no specific template is selected', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="latest" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Select a Template/i)).toBeInTheDocument()
    expect(screen.getByText(/Shelter Template/i)).toBeInTheDocument()
    expect(screen.getByText(/Health Response Template/i)).toBeInTheDocument()
    expect(screen.getByText(/donor/i)).toBeInTheDocument()
    expect(screen.getByText(/outcome/i)).toBeInTheDocument()
    expect(screen.getByText(/Default/i)).toBeInTheDocument()
  })

  it('displays error when template access data fails to load', async () => {
    server.use(
      http.get('/api/admin/templates/tpl-1/access', () =>
        HttpResponse.json(null, { status: 500 })
      )
    )

    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/Failed to load access data/i)).toBeInTheDocument()
  })

  it('shows visibility mode and allows changing it', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="tpl-1" />
        </MemoryRouter>
      </WizardProvider>
    )

    await screen.findByRole('heading', { name: /Shelter Template/i })
    const header = document.querySelector('.template-access > header')
    expect(within(header).getByText(/Visibility: organization/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /Visibility mode/i })).toBeInTheDocument()
  })

  it('displays different template types in the list', async () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <TemplateAccessPanel resourceId="latest" />
        </MemoryRouter>
      </WizardProvider>
    )

    expect(await screen.findByText(/donor/i)).toBeInTheDocument()
    expect(screen.getByText(/outcome/i)).toBeInTheDocument()
  })
})
