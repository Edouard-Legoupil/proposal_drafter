import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuth } from '../context/AuthContext'
import { withTeamAccess } from './withTeamAccess'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn()
}))

function ProtectedContent() {
  return <div>Protected content</div>
}

const ProtectedRoute = withTeamAccess({})(ProtectedContent)

function renderRoute() {
  return render(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route path="/protected" element={<ProtectedRoute />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>
  )
}

describe('withTeamAccess', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('waits for authentication before rendering protected content', () => {
    useAuth.mockReturnValue({ user: null, loading: true })

    renderRoute()

    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
    expect(screen.queryByText('Login page')).not.toBeInTheDocument()
  })

  it('redirects anonymous users to login', () => {
    useAuth.mockReturnValue({ user: null, loading: false })

    renderRoute()

    expect(screen.getByText('Login page')).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })
})
