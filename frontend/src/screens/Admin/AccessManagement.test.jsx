import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AccessManagement from './AccessManagement'

describe('AccessManagement shell', () => {
  it('renders the section header', () => {
    render(
      <MemoryRouter>
        <AccessManagement />
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: /access management/i })).toBeInTheDocument()
  })
})
