import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

let authState

vi.mock('./context/AuthContext', () => ({ useAuth: () => authState }))
vi.mock('./screens/Login/Login', () => ({ default: () => <div>Login screen</div> }))
vi.mock('./screens/Dashboard/Dashboard', () => ({ default: () => <div>Dashboard screen</div> }))
vi.mock('./screens/Chat/Chat', () => ({ default: () => <div>Chat screen</div> }))
vi.mock('./screens/KnowledgeCard/KnowledgeCard', () => ({ default: () => <div>Knowledge card screen</div> }))
vi.mock('./screens/DonorTemplateRequest/DonorTemplateRequest', () => ({ default: () => <div>Template request screen</div> }))
vi.mock('./screens/DonorTemplateDetail/DonorTemplateDetail', () => ({ default: () => <div>Template screen</div> }))
vi.mock('./screens/QualityGate/QualityGate', () => ({ default: () => <div>Quality gate screen</div> }))
vi.mock('./screens/Admin/AccessManagement', () => ({ default: () => <div>Admin screen</div> }))
vi.mock('./components/Wizard/WizardModal', () => ({ default: () => null }))
vi.mock('./components/Wizard/WizardDebug', () => ({ default: () => null }))

import App from './App'

describe('application route protection', () => {
  beforeEach(() => {
    authState = { user: null, loading: false }
  })

  it('redirects anonymous users away from authenticated routes', () => {
    render(<MemoryRouter initialEntries={['/dashboard']}><App /></MemoryRouter>)
    expect(screen.getByText('Login screen')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard screen')).not.toBeInTheDocument()
  })

  it('shows loading feedback while an authenticated screen is downloaded', async () => {
    authState = { user: { id: 'user-1', is_admin: false }, loading: false }
    render(<MemoryRouter initialEntries={['/dashboard']}><App /></MemoryRouter>)
    expect(screen.getByRole('status', { name: /loading page/i })).toBeInTheDocument()
    expect(await screen.findByText('Dashboard screen')).toBeInTheDocument()
  })

  it('allows authenticated users into ordinary application routes', async () => {
    authState = { user: { id: 'user-1', is_admin: false }, loading: false }
    render(<MemoryRouter initialEntries={['/dashboard']}><App /></MemoryRouter>)
    expect(await screen.findByText('Dashboard screen')).toBeInTheDocument()
  })

  it('redirects non-admin users away from access management', async () => {
    authState = { user: { id: 'user-1', is_admin: false }, loading: false }
    render(<MemoryRouter initialEntries={['/admin/access/proposals/latest']}><App /></MemoryRouter>)
    expect(await screen.findByText('Dashboard screen')).toBeInTheDocument()
    expect(screen.queryByText('Admin screen')).not.toBeInTheDocument()
  })

  it('waits for profile loading before rendering a protected route', () => {
    authState = { user: null, loading: true }
    render(<MemoryRouter initialEntries={['/dashboard']}><App /></MemoryRouter>)
    expect(screen.getByText(/checking session/i)).toBeInTheDocument()
    expect(screen.queryByText('Login screen')).not.toBeInTheDocument()
  })
})
