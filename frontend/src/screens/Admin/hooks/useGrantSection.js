import { useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

/**
 * Hook to manage grant form state and operations.
 * @param {{ endpoint: string, initialForm: object, refresh: Function }} params
 */
export function useGrantSection({ endpoint, initialForm, refresh }) {
  const [grantForm, setGrantForm] = useState(initialForm || { subjectType: 'user', subjectId: '', permissions: [], dataScope: 'self' })
  const [statusMessage, setStatusMessage] = useState(endpoint ? '' : 'Metrics access management not available')
  const [actionLoading, setActionLoading] = useState(false)

  const togglePermission = (key) => {
    setGrantForm((prev) => {
      const has = prev.permissions.includes(key)
      const permissions = has
        ? prev.permissions.filter((p) => p !== key)
        : [...prev.permissions, key]
      return { ...prev, permissions }
    })
  }

  const handleGrant = async (e) => {
    e.preventDefault()
    if (!endpoint) {
      setStatusMessage('Metrics access management not available')
      return
    }
    if (!grantForm.subjectId) {
      setStatusMessage('Select a subject before granting access')
      return
    }
    setActionLoading(true)
    setStatusMessage('Saving grant…')
    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(grantForm)
      })
      if (!res.ok) throw new Error('Failed to grant access')
      setStatusMessage('Access granted')
      setGrantForm((prev) => ({ ...prev, subjectId: '' }))
      await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const revokeGrant = async (grantId) => {
    if (!endpoint) {
      setStatusMessage('Metrics access management not available')
      return
    }
    setActionLoading(true)
    setStatusMessage('Revoking grant…')
    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_id: grantId })
      })
      if (!res.ok) throw new Error('Failed to revoke grant')
      setStatusMessage('Grant revoked')
      await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  return {
    grantForm,
    setGrantForm,
    statusMessage,
    actionLoading,
    togglePermission,
    handleGrant,
    revokeGrant
  }
}
