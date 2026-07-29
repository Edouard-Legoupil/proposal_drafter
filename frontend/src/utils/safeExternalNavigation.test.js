import { describe, expect, it, vi } from 'vitest'

import { openSafeExternalUrl } from './safeExternalNavigation'

describe('openSafeExternalUrl', () => {
  it('opens an HTTPS URL without granting access to window.opener', () => {
    const openWindow = vi.fn()

    expect(openSafeExternalUrl('https://sharepoint.example/document', openWindow)).toBe(true)
    expect(openWindow).toHaveBeenCalledWith(
      'https://sharepoint.example/document',
      '_blank',
      'noopener,noreferrer'
    )
  })

  it.each([
    'javascript:alert(1)',
    'data:text/html,unsafe',
    'file:///etc/passwd',
    'https://user:password@example.org/private',
    '/relative/path',
    'not a url'
  ])('rejects unsafe URL %s', (url) => {
    const openWindow = vi.fn()

    expect(openSafeExternalUrl(url, openWindow)).toBe(false)
    expect(openWindow).not.toHaveBeenCalled()
  })
})
