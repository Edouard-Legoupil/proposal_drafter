import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AccessManagement from './AccessManagement'
import { WizardProvider } from '../../context/WizardContext'

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
    expect(screen.getByRole('button', { name: /proposals/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /knowledge cards/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /templates/i })).toBeInTheDocument()
  })
})
