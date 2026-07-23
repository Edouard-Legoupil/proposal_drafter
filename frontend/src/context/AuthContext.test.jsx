import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'

function UserProbe() {
  const { user } = useAuth()
  return <span>{user?.email || 'anonymous'}</span>
}

describe('AuthProvider', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads the authenticated profile for consumers', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ user: { email: 'user@example.com', is_admin: true } })
    })

    render(
      <AuthProvider>
        <UserProbe />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('user@example.com')).toBeInTheDocument()
    })
    expect(fetch).toHaveBeenCalledWith('/api/profile', {
      credentials: 'include'
    })
  })
})
