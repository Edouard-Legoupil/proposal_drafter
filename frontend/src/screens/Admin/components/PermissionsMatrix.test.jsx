import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import PermissionsMatrix from './PermissionsMatrix'

describe('PermissionsMatrix', () => {
  const rows = [
    { id: '1', subject: 'Shelter team', resource: 'Proposal A', permissions: ['read', 'edit'] },
    { id: '2', subject: 'Health team', resource: 'Template B', permissions: ['read', 'delete'] }
  ]

  it('renders accessible read edit and delete status cells', () => {
    render(<PermissionsMatrix rows={rows} />)
    expect(screen.getByRole('columnheader', { name: 'Read' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Edit' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Delete' })).toBeInTheDocument()
    expect(screen.getAllByText('Granted').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Not granted').length).toBeGreaterThan(0)
  })

  it('searches across subjects and resources', () => {
    render(<PermissionsMatrix rows={rows} />)
    fireEvent.change(screen.getByPlaceholderText(/search permissions/i), { target: { value: 'Health' } })
    expect(screen.getByText('Health team')).toBeInTheDocument()
    expect(screen.queryByText('Shelter team')).not.toBeInTheDocument()
  })
})
