import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import GrantSection from './GrantSection'

describe('GrantSection', () => {
  const props = {
    grants: [],
    permissionOptions: [{ key: 'p1', label: 'Perm1' }],
    showScope: true,
    dataScopeOptions: ['self', 'team'],
    grantForm: { subjectType: 'user', subjectId: '', permissions: ['p1'], dataScope: 'self' },
    setGrantForm: vi.fn(),
    statusMessage: 'status-msg',
    actionLoading: false,
    onGrant: vi.fn(),
    onRevoke: vi.fn(),
    users: [],
    options: {},
    emptyMessage: 'no grants'
  }

  it('shows empty grants message', () => {
    render(<GrantSection {...props} />)
    expect(screen.getByText(/no grants/i)).toBeInTheDocument()
  })

  it('calls onGrant when form is submitted', () => {
    render(<GrantSection {...props} />)
    fireEvent.submit(screen.getByRole('button', { name: /save grant/i }).closest('form'))
    expect(props.onGrant).toHaveBeenCalled()
  })
})
