import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AccessManagement from './AccessManagement'
import { WizardProvider } from '../../context/WizardContext'

vi.mock('../../components/Base/Base', () => ({ default: ({ children }) => <div>{children}</div> }))

describe('AccessManagement shell', () => {
  it('renders the section header', () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <AccessManagement />
        </MemoryRouter>
      </WizardProvider>
    )
    expect(screen.getByRole('heading', { name: /access management/i })).toBeInTheDocument()
  })

  it('renders navigation tabs', () => {
    render(
      <WizardProvider>
        <MemoryRouter>
          <AccessManagement />
        </MemoryRouter>
      </WizardProvider>
    )
    expect(screen.getByRole('button', { name: /user access/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /overview/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^teams$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /proposals/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /knowledge cards/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /templates/i })).toBeInTheDocument()
  })
})
