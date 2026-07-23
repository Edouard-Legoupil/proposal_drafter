import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from './api'

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns parsed response data with credentials', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ roles: ['admin'] })
    })

    const response = await api.get('/teams/team-1/roles')

    expect(response.data).toEqual({ roles: ['admin'] })
    expect(fetch).toHaveBeenCalledWith('/api/teams/team-1/roles', {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    })
  })
})
