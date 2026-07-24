import { act, renderHook, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useInteractionTracking } from './useInteractionTracking'

function wrapper({ children }) {
  return <MemoryRouter>{children}</MemoryRouter>
}

describe('useInteractionTracking', () => {
  beforeEach(() => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.stubGlobal('fetch', vi.fn(async url => {
      if (String(url).endsWith('/interactions/sessions/')) {
        return new Response(JSON.stringify({ session_id: 'session-1' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      }
      return new Response(JSON.stringify({ interaction_id: 'interaction-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      })
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('starts analytics with cookie authentication and no bearer token', async () => {
    const { unmount } = renderHook(() => useInteractionTracking({ id: 'user-1' }), { wrapper })

    await waitFor(() => expect(fetch).toHaveBeenCalled())
    const [, request] = fetch.mock.calls[0]

    expect(request.credentials).toBe('include')
    expect(request.headers).not.toHaveProperty('Authorization')
    unmount()
  })

  it('logs wizard interactions through the authenticated session', async () => {
    const { result, unmount } = renderHook(
      () => useInteractionTracking({ id: 'user-1' }),
      { wrapper }
    )

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/interactions/sessions/'),
      expect.any(Object)
    ))

    await act(async () => {
      await result.current.logWizardInteraction({ action_type: 'open' })
    })

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/interactions/log/'),
      expect.objectContaining({ credentials: 'include' })
    ))
    unmount()
  })
})
